"""Japan: rollover clock and inflation layer at fiscal-year ends (31 March), consolidated
government (MOF + Bank of Japan), on the same definitions as the U.S. (paper, Sections 3-4).

Interest-bearing liabilities to the private sector:
  - JGBs by issue (general + FILP bonds, MOF yearbook Table 34) minus BoJ holdings by issue
    (BoJ release) minus government holdings (PF02, pro rata);
  - treasury discount bills: TB by issue (Table 34) and financing bills (PF02 total minus TB,
    repricing at 3 months), minus BoJ and government holdings (pro rata);
  - BoJ current accounts that earn a non-zero rate (repricing overnight).
Zero-interest base (erosion only): banknotes, required reserves, and current-account
balances at a zero rate (the 0% tier of 2016-March 2024).
Repricing: maturity for fixed-rate and index-linked bonds and bills; 6 months for
floating-rate JGBs (15-year floaters, retail floating 10-year). Index-linked JGBs are not
eroded by inflation.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.clock.consolidated_clock import OVERNIGHT
from src.clock.inflation_layer import GRID, exact_F, layer

IN = Path("data/interim/jp")
OUT = Path("data/processed/jp")
FB_TENOR = 0.25
FLOAT_RESET = 0.5
TIERS_END = 202402                      # last month of the three-tier system


def monthly(db: str) -> pd.DataFrame:
    d = pd.read_csv(f"data/raw/jp/boj_api/{db}.csv")
    return d[d.value.notna()].pivot(index="date", columns="series", values="value") * 1e5   # -> thousand yen


def gdp_fy() -> pd.Series:
    d = pd.read_csv("data/raw/fred/JPNNGDP.csv")
    d["date"] = pd.to_datetime(d.observation_date)
    d["fy"] = d.date.dt.year - (d.date.dt.month < 4)
    g = d.groupby("fy").JPNNGDP.agg(["mean", "count"])
    return g.loc[g["count"] == 4, "mean"] * 1e6                         # billion yen -> thousand yen


def trailing_growth(fy: int, gdp: pd.Series, n: int = 10) -> float:
    return float(gdp.pct_change().loc[fy - n + 1:fy].mean())


def portfolio(fy: int, issues: pd.DataFrame, boj: pd.DataFrame, pf, bs, md, rr) -> dict:
    as_of = pd.Timestamp(year=fy + 1, month=3, day=31)
    ym = (fy + 1) * 100 + 3
    x = issues[issues.fy == fy].merge(boj[boj.fy == fy][["name", "issue_no", "boj"]],
                                      on=["name", "issue_no"], how="left").fillna({"boj": 0.0})
    x["tau"] = (pd.to_datetime(x.maturity) - as_of).dt.days / 365.25
    x.loc[x.kind == "floating", "tau"] = np.minimum(x.loc[x.kind == "floating", "tau"], FLOAT_RESET)
    coupon, bills = x[x.kind != "bill"].copy(), x[x.kind == "bill"].copy()
    fb = pf.loc[ym, "PFGD@01"] - bills.outstanding.sum()                 # financing bills
    bills = pd.concat([bills, pd.DataFrame([{"name": "政府短期証券(FB)", "kind": "bill", "tau": FB_TENOR,
                                              "outstanding": fb, "boj": 0.0}])], ignore_index=True)
    # BoJ and government bill holdings, and government JGB holdings, pro rata
    bills["boj"] = bills.outstanding * bs.loc[ym, "MABJMA5A"] / bills.outstanding.sum()
    bills["gov"] = bills.outstanding * pf.loc[ym, "PFGD@02"] / bills.outstanding.sum()
    coupon["gov"] = coupon.outstanding * pf.loc[ym, "PFGD211"] / coupon.outstanding.sum()
    sec = pd.concat([coupon, bills], ignore_index=True)
    sec["private"] = (sec.outstanding - sec.boj - sec.gov).clip(lower=0)
    # current accounts
    ca, req = bs.loc[ym, "MABJML11"], rr.loc[ym, "MAREM3"]
    if ym <= TIERS_END:                     # three tiers; after 19 March 2024 only required reserves earn 0%
        t = md.loc[ym]
        zero_share = t["MACAB3203"] / t[["MACAB3202", "MACAB3203", "MACAB3204"]].sum()
        ca_zero = zero_share * ca
    else:
        ca_zero = req
    ca_ib = ca - ca_zero
    zero = bs.loc[ym, "MABJML1"] + ca_zero
    return {"sec": sec, "ca_ib": ca_ib, "ca_zero": ca_zero, "banknotes": bs.loc[ym, "MABJML1"], "zero": zero}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    issues = pd.read_csv(IN / "jgb_by_issue.csv")
    boj = pd.read_csv(IN / "boj_holdings.csv")
    pf, bs, md, rr = monthly("PF02"), monthly("BS01"), monthly("MD08"), monthly("MD07")
    gdp = gdp_fy()
    rows = []
    for fy in sorted(issues.fy.unique()):
        p = portfolio(fy, issues, boj, pf, bs, md, rr)
        s = p["sec"]
        g_jp = trailing_growth(fy, gdp)
        # consolidated: private holdings + interest-bearing current accounts
        tau = np.r_[s.tau.values, OVERNIGHT]
        w = np.r_[s.private.values, p["ca_ib"]]
        ix = np.r_[(s.kind == "indexed").values, False]
        # the government's own liabilities: all JGBs and bills, no central bank
        tau_t, w_t, ix_t = s.tau.values, s.outstanding.values, (s.kind == "indexed").values
        row = {"fy": fy, "gdp": gdp[fy], "g_trailing10": g_jp,
               "b_consol": w.sum() / gdp[fy], "b_gross": w_t.sum() / gdp[fy],
               "boj_share_jgb": s.boj.sum() / s.outstanding.sum(),
               "overnight_share": p["ca_ib"] / w.sum(), "zero_ratio": p["zero"] / w.sum(),
               "banknotes_gdp": p["banknotes"] / gdp[fy], "ca_zero_gdp": p["ca_zero"] / gdp[fy],
               "indexed_share": w[ix].sum() / w.sum(),
               "wam_consol": float((w * np.maximum(tau, 0)).sum() / w.sum()),
               "wam_gross": float((w_t * tau_t).sum() / w_t.sum())}
        for g, tag in ((g_jp, "gjp"), (0.04, "g4")):
            F = exact_F(tau, w, GRID)
            row[f"P1_consol_{tag}"] = float(1 - (1 - np.interp(1, GRID, F)) * np.exp(-g))
            Ft = exact_F(tau_t, w_t, GRID)
            row[f"P1_gross_{tag}"] = float(1 - (1 - np.interp(1, GRID, Ft)) * np.exp(-g))
            row[f"ratio_consol_{tag}"] = layer(tau, w, ix, p["zero"], 10, g)["ratio"]
            row[f"ratio_consol_nocur_{tag}"] = layer(tau, w, ix, 0.0, 10, g)["ratio"]
            row[f"ratio_gross_{tag}"] = layer(tau_t, w_t, ix_t, 0.0, 10, g)["ratio"]
        rows.append(row)
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "jp_clock.csv", index=False)
    pd.set_option("display.width", 250)
    print(d.round(3).T.to_string())


if __name__ == "__main__":
    main()
