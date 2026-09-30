"""Identify the fiscal response phi from UK fiscal events, 2010-2026 (Auerbach-Yagan design).

At each fiscal event the OBR decomposes the revision to its borrowing (PSNB) forecast since the
previous forecast into policy decisions and underlying forecast changes, and the underlying
change into receipts, debt interest and non-interest spending (OBR fiscal forecast revisions
database; % of GDP; positive = higher borrowing). The Treasury sees the pre-measures forecast
before deciding policy, so policy at an event can respond to the underlying revisions at
that event.

For event e and the five fiscal years after the current one (h = 1..5):
    Policy_e = a + beta_DI * DI_e + beta_R * Receipts_e + beta_N * NonInterest_e + u_e
phi = -beta_DI: the share of an upward revision to debt interest offset by policy at the same
event. Debt interest (net of the APF) is driven mainly by gilt yields, Bank Rate and, through
index-linked gilts, RPI inflation, which are outside the Chancellor's control.
IV: the debt-interest revision is instrumented with the revisions, between consecutive
forecasts, of the market assumptions behind it (OBR historical official forecasts database):
Bank Rate / short rates and gilt rates (average over the current and next five years) and the
RPI price level (cumulative revision, which raises index-linked uplift in all later years).
This removes the part of the debt-interest revision that comes from revisions to borrowing.
Output: data/processed/fiscal/phi_obr_events.csv, phi_obr.csv
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

RAW = Path("data/raw/uk/obr/forecast-revisions-database-march-2025.xlsx")
HIST = Path("data/raw/uk/obr/historical-official-forecasts-database.xlsx")
OUT = Path("data/processed/fiscal")
MONTHS = {m: i for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August",
                                      "September", "October", "November", "December"], start=1)}
LINES = {"Policy": "policy", "of which: receipts": None, "of which: spending": None, "Underlying": "underlying",
         "of which: debt interest": "di", "of which: non-interest spend": "nonint"}


def events(sheet: str = "Revisions (Per cent of GDP)") -> pd.DataFrame:
    r = pd.read_excel(RAW, sheet, header=None)
    years = {j: int(str(v)[:4]) for j, v in r.iloc[1].items() if isinstance(v, str) and v[:4].isdigit()}
    rows, ev, block = [], None, None
    for i in range(2, len(r)):
        lab = str(r.iloc[i, 0]).strip()
        first = lab.split(" ")[0]
        if first in MONTHS and lab.split(" ")[1][:4].isdigit():
            ev = lab.replace(" restated", "R")
            m, y = MONTHS[first], int(lab.split(" ")[1][:4])
            cur = y if m >= 4 else y - 1                          # fiscal year in progress at the event
            block, under = {}, False
            rows.append({"event": ev, "month": m, "year": y, "fy0": cur, "_b": block})
            continue
        if ev is None:
            continue
        key = lab.rstrip("0123456789")                           # footnote digits (Underlying2)
        if key == "Underlying":
            under = True
        name = {"Policy": "policy", "Underlying": "underlying"}.get(key)
        if key == "of which: receipts":
            name = "und_receipts" if under else "pol_receipts"
        elif key == "of which: spending":
            name = "pol_spending"
        elif key == "of which: debt interest":
            name = "di"
        elif key.startswith("of which: non-interest"):
            name = "nonint"
        if name:
            block[name] = {fy: pd.to_numeric(r.iloc[i, j], errors="coerce") for j, fy in years.items()}
    out = []
    for e in rows:
        b = e.pop("_b")
        rec = dict(e)
        for name, s in b.items():
            v = [s.get(e["fy0"] + h, np.nan) for h in range(1, 6)]
            rec[name] = np.nanmean(v) if np.isfinite(v).any() else np.nan     # average over years 1-5
            rec[f"{name}_h1"] = v[0]
        out.append(rec)
    d = pd.DataFrame(out)
    return d[d.policy.notna() & d.di.notna()]


def vintages(sheet: str) -> dict[str, dict[int, float]]:
    """Forecast vintages of one series: {vintage: {year: value}} (fiscal years by start year)."""
    r = pd.read_excel(HIST, sheet, header=None)
    years = {j: int(str(v)[:4]) for j, v in r.iloc[3].items() if str(v)[:4].isdigit()}
    out = {}
    for i in range(4, len(r)):
        lab = re.sub(r"[^A-Za-z0-9 ]", "", str(r.iloc[i, 0])).strip()        # footnote markers
        if lab.split(" ")[0] in MONTHS:
            out[lab] = {y: pd.to_numeric(r.iloc[i, j], errors="coerce") for j, y in years.items()}
    return out


def assumption_revisions(d: pd.DataFrame) -> pd.DataFrame:
    """Revisions since the previous forecast to short rates, gilt rates and the RPI level."""
    series = {k: vintages(sh) for k, sh in (("short", "Shorttermrates"), ("gilt", "Gilts"), ("rpi", "RPI"))}
    rows = []
    for e in d.itertuples():
        ev = e.event.strip()
        rec = {"event": e.event}
        prev = {k: list(v)[list(v).index(ev) - 1] if ev in v and list(v).index(ev) > 0 else None
                for k, v in series.items()}
        if None in prev.values():
            rows.append(rec)
            continue
        for k in ("short", "gilt"):
            v = [series[k][ev].get(e.fy0 + h, np.nan) - series[k][prev[k]].get(e.fy0 + h, np.nan) for h in range(6)]
            rec[f"rev_{k}"] = np.nanmean(v) if np.isfinite(v).any() else np.nan
        v = np.array([series["rpi"][ev].get(e.fy0 + h, np.nan) - series["rpi"][prev["rpi"]].get(e.fy0 + h, np.nan)
                      for h in range(6)])
        lvl = np.nancumsum(np.nan_to_num(v))[1:]                                 # price-level revision, h = 1..5
        rec["rev_rpi"] = float(lvl.mean())
        rows.append(rec)
    return d.merge(pd.DataFrame(rows), on="event", how="left")


def iv(d: pd.DataFrame, instruments: list[str], controls: list[str]) -> dict:
    from src.fiscal.phi_panel import tsls
    k = d.dropna(subset=["policy", "di"] + instruments + controls)
    W = np.column_stack([np.ones(len(k))] + [k[c].values for c in controls])
    fs = sm.OLS(k.di, sm.add_constant(k[instruments + controls])).fit(cov_type="HC1")
    F = float(fs.f_test(" = ".join(instruments) + " = 0" if len(instruments) == 1 else
                        ", ".join(f"{z} = 0" for z in instruments)).fvalue)
    b, se = tsls(k.policy.values, k[["di"]].values, W, k[instruments].values, np.arange(len(k)))
    return {"y": "policy", "x": "di (IV: " + "+".join(instruments) + ")", "n": len(k), "b_di": float(b[0]),
            "se_di": float(se[0]), "first_stage_F": F}


def fit(d: pd.DataFrame, y: str, xs: list[str]) -> dict:
    m = sm.OLS(d[y], sm.add_constant(d[xs])).fit(cov_type="HC1")
    return {"y": y, "x": "+".join(xs), "n": int(m.nobs), **{f"b_{x}": m.params[x] for x in xs},
            **{f"se_{x}": m.bse[x] for x in xs}, "r2": m.rsquared}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = events()
    d = d[~d.event.str.endswith("R")]                            # drop the restated March 2019 duplicate
    d = assumption_revisions(d)
    d.to_csv(OUT / "phi_obr_events.csv", index=False)
    pd.set_option("display.width", 220)
    print(d[["event", "fy0", "policy", "pol_receipts", "pol_spending", "underlying", "und_receipts", "di",
             "nonint"]].round(2).to_string(index=False))
    res = [fit(d, "policy", ["di"]), fit(d, "policy", ["di", "und_receipts", "nonint"]),
           fit(d, "policy", ["underlying"]), fit(d, "policy_h1", ["di_h1", "und_receipts_h1", "nonint_h1"]),
           fit(d[d.year < 2020], "policy", ["di", "und_receipts", "nonint"]),
           fit(d[d.year >= 2020], "policy", ["di", "und_receipts", "nonint"])]
    ctl = ["und_receipts", "nonint"]
    covid = d.event.isin(["March 2020", "November 2020", "March 2021"])
    res += [iv(d, ["rev_short", "rev_gilt", "rev_rpi"], ctl), iv(d[~covid], ["rev_short", "rev_gilt", "rev_rpi"], ctl),
            iv(d, ["rev_gilt", "rev_rpi"], ctl), iv(d[~covid], ["rev_gilt", "rev_rpi"], ctl)]
    print(d[["event", "di", "rev_short", "rev_gilt", "rev_rpi"]].round(2).to_string(index=False))
    r = pd.DataFrame(res)
    r.to_csv(OUT / "phi_obr.csv", index=False)
    print(r.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
