"""The rollover clock as a monthly data series, January 2003 to the latest MSPD month.

Same construction as the paper's year-end measures (treasury_clock, consolidated_clock,
inflation_layer, monetary_reaction), applied at every month-end:
  marketable Treasuries by CUSIP (MSPD) net of SOMA holdings by CUSIP (NY Fed), plus reserves
  and reverse repos (H.4.1, Wednesday on or before the SOMA as-of date); currency is the
  zero-interest base, and reserves join it before interest on reserves (October 2008).
December values reproduce the year-end files exactly.

Usage:
  python -m src.release.monthly_clock           # download what is new, then build
  python -m src.release.monthly_clock --no-fetch
Writes data/release/rollover_clock_monthly.csv (committed) and a figure in data/release/.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import zipfile
from pathlib import Path
from urllib.request import urlopen

import numpy as np
import pandas as pd

from src.clock.consolidated_clock import OVERNIGHT, soma_by_cusip
from src.clock.fetch_fed import h41_levels
from src.clock.fiscaldata import fetch_all
from src.clock.inflation_layer import layer
from src.clock.treasury_clock import G_BASELINE, securities

MARKET = "/v1/debt/mspd/mspd_table_3_market"
SOMA = "https://markets.newyorkfed.org/api/soma"
H41_ZIP = "https://www.federalreserve.gov/datadownload/Output.aspx?rel=H41&filetype=zip"
RAW_MSPD = Path("data/raw/fiscaldata/mspd_table_3_market_monthly")
RAW_FED = Path("data/raw/fed")
OUT = Path("data/release")
START = "2003-01-01"
IOR_START = "2008-10-01"
H41_MAX_GAP_DAYS = 6
CLOCK_H = (1, 2, 5, 10)


def mspd_dates() -> list[str]:
    rows = fetch_all(MARKET, {"fields": "record_date", "filter": f"record_date:gte:{START}",
                              "sort": "record_date"})
    return sorted({r["record_date"] for r in rows})


def mspd_month(d: str, fetch: bool) -> pd.DataFrame | None:
    cache = RAW_MSPD / d
    if not cache.exists() and not fetch:
        return None
    return pd.DataFrame(fetch_all(MARKET, {"filter": f"record_date:eq:{d}"}, cache))


def soma_asof_dates(fetch: bool) -> list[str]:
    cache = RAW_FED / "soma" / "asofdates.json"
    if fetch or not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(urlopen(f"{SOMA}/asofdates/list.json", timeout=120).read().decode())
    return sorted(json.loads(cache.read_text())["soma"]["asOfDates"])


def soma_holdings(d: str, fetch: bool) -> pd.DataFrame | None:
    cache = RAW_FED / "soma" / f"{d}.json"
    if not cache.exists():
        if not fetch:
            return None
        cache.write_text(urlopen(f"{SOMA}/tsy/get/asof/{d}.json", timeout=120).read().decode())
    h = pd.DataFrame(json.loads(cache.read_text())["soma"]["holdings"])
    h["year"] = 0
    return soma_by_cusip(h)


def refresh_h41() -> None:
    """Same download as reproduce.sh (curl; the Board's server refuses Python's default client)."""
    z = RAW_FED / "h41.zip"
    z.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["curl", "-fsSL", "-o", str(z), H41_ZIP], check=True)
    zipfile.ZipFile(z).extract("H41_data.xml", RAW_FED)


def month_row(d: str, sec: pd.DataFrame, soma: pd.DataFrame, asof: str, lev: pd.Series) -> dict:
    x = sec.merge(soma[["cusip", "soma_par"]], on="cusip", how="left").fillna({"soma_par": 0})
    paid = d >= IOR_START
    on = lev.reverse_repo + (lev.reserves if paid else 0.0)
    zero = lev.currency + (0.0 if paid else lev.reserves)
    tips = (x.kind == "tips").values
    tau_t, w_t = x.tau.values, x.par.values
    tau_c = np.r_[x.tau.values, OVERNIGHT]
    w_c = np.r_[(x.par - x.soma_par).values, on]
    ix_c = np.r_[tips, False]
    b = w_c.sum()
    row = {"date": d, "soma_asof": asof, "h41_date": lev.date,
           "treasury_marketable_bn": w_t.sum() / 1e3,
           "soma_treasury_bn": x.soma_par.sum() / 1e3,
           "reserves_bn": lev.reserves / 1e3, "reverse_repo_bn": lev.reverse_repo / 1e3,
           "currency_bn": lev.currency / 1e3,
           "interest_bearing_bn": b / 1e3, "zero_interest_bn": zero / 1e3,
           "overnight_share": (on + w_c[:-1][(x.kind == "frn").values].sum()) / b,
           "tips_share": w_c[ix_c].sum() / b,
           "wam_years": (w_c * tau_c).sum() / b,
           "wam_treasury_years": (w_t * tau_t).sum() / w_t.sum()}
    for h in CLOCK_H:
        row[f"P{h}"] = 1 - (1 - w_c[tau_c <= h].sum() / b) * np.exp(-G_BASELINE * h)
    for h in CLOCK_H:
        row[f"P{h}_treasury"] = 1 - (1 - w_t[tau_t <= h].sum() / w_t.sum()) * np.exp(-G_BASELINE * h)
    for h in (1, 10):
        row[f"extra_interest_y{h}_bn"] = 0.01 * row[f"P{h}"] * b / 1e3
    for H in (5, 10):
        R = layer(tau_c, w_c, ix_c, zero, H)["ratio"]
        row[f"R_H{H}"] = R
        row[f"kappa_star_H{H}"] = 1 / R
    return row


def build(fetch: bool) -> pd.DataFrame:
    if fetch:
        refresh_h41()
    h41 = h41_levels()
    h41 = h41[h41.reserves.notna() & h41.currency.notna()]
    asofs = soma_asof_dates(fetch)
    rows = []
    for d in mspd_dates() if fetch else sorted(p.name for p in RAW_MSPD.iterdir()):
        cands = [a for a in asofs if a <= d]
        if not cands:
            continue
        asof = cands[-1]
        lev = h41.loc[h41.date <= asof]
        if lev.empty or (pd.Timestamp(asof) - pd.Timestamp(lev.date.iloc[-1])).days > H41_MAX_GAP_DAYS:
            print(f"{d}: H.4.1 not yet available for SOMA as-of {asof}; skipped")
            continue
        m, s = mspd_month(d, fetch), soma_holdings(asof, fetch)
        if m is None or s is None or m.empty:
            continue
        rows.append(month_row(d, securities(m), s, asof, lev.iloc[-1]))
    return pd.DataFrame(rows)


def check_yearend(c: pd.DataFrame) -> pd.DataFrame:
    """December rows against the paper's year-end files (where those have been built)."""
    p = Path("data/processed/clock/inflation_layer_yearend.csv")
    if not p.exists():
        return pd.DataFrame()
    y = pd.read_csv(p)
    y = y[y.version == "consolidated"].set_index("year")
    cc = pd.read_csv("data/processed/clock/consolidated_clock_yearend.csv").set_index("year")
    dec = c[c.date.str[5:7] == "12"].assign(year=lambda t: t.date.str[:4].astype(int)).set_index("year")
    j = dec.join(y[["ratio_H10", "ratio_H5"]]).join(cc[["P_1", "P_10", "wam_years"]], rsuffix="_paper")
    return pd.DataFrame({"dR_H10": j.R_H10 - j.ratio_H10, "dR_H5": j.R_H5 - j.ratio_H5,
                         "dP1": j.P1 - j.P_1, "dP10": j.P10 - j.P_10,
                         "dwam": j.wam_years - j.wam_years_paper}).dropna()


def figure(c: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    t = pd.to_datetime(c.date)
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
    ax[0].plot(t, c.P1, label="1 year")
    ax[0].plot(t, c.P5, label="5 years")
    ax[0].plot(t, c.P1_treasury, ls="--", lw=1, color="C0", label="1 year, Treasury only")
    ax[0].set_title("Rollover clock P(h): share of consolidated\nliabilities repriced within h years")
    ax[0].set_ylim(0, 1)
    ax[0].legend(frameon=False, fontsize=8)
    ax[1].plot(t, c.kappa_star_H10, color="C3", label="κ*, 10-year horizon")
    ax[1].axhline(0.5, color="grey", lw=0.8, ls=":")
    ax[1].text(t.iloc[0], 0.51, "Taylor rule (0.5)", fontsize=8, color="grey")
    ax[1].set_title("Monetary tolerance threshold κ*: real-rate response\nabove which inflation cannot close a fiscal gap")
    ax[1].legend(frameon=False, fontsize=8)
    for a in ax:
        a.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.01, f"Ding (2026), The Rollover Clock. Data through {c.date.iloc[-1]}.", fontsize=7, color="grey")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(OUT / "rollover_clock_monthly.png", dpi=150)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-fetch", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    c = build(fetch=not a.no_fetch)
    c.round(6).to_csv(OUT / "rollover_clock_monthly.csv", index=False)
    figure(c)
    chk = check_yearend(c)
    if not chk.empty:
        print("December vs paper year-end, max abs difference:")
        print(chk.abs().max().to_string())
    pd.set_option("display.width", 200)
    print(c[["date", "interest_bearing_bn", "overnight_share", "wam_years", "P1", "P10",
             "extra_interest_y1_bn", "R_H10", "kappa_star_H10"]].tail(13).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
