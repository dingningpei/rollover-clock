"""Fiscal threshold and combined metric for Japan, the UK and the U.S. on a common basis
(phase 2, cross-country comparison).

  phi* = 1 - g / (r + psi * b)
  inflation to cover the gap = (phi* - phi_hat)^+ * ratio   (per +1pp permanent rate rise, H = 10)

r   marginal cost of the existing structure: each security priced at the year's average
    yield for its ORIGINAL tenor (index-linked at the nominal yield of the same tenor,
    floating-rate and bills at the short rate), weighted by amount outstanding
    (gross, incl. central-bank holdings), as for the U.S. in the paper;
    Japan: MOF constant-maturity JGB yields (1-40 years), fiscal-year average;
    UK: Bank of England par yields at 5, 10 and 20 years and SONIA, calendar-year average,
    interpolated; tenors beyond 20 years at the 20-year yield.
g   baseline: trailing 10-year average REAL GDP growth plus the 2% inflation target that all
    three central banks share (the logic of the FOMC's longer-run projection used for the U.S.);
    sensitivity: trailing 10-year nominal growth, which is inflated by 2021-22.
b   consolidated interest-bearing debt / GDP (country clocks).
psi reported on a grid (0, 1, 2, 3, 4.5bp per pp of debt/GDP). The U.S. literature's 3bp is
    not a safe assumption for Japan, where yields stayed near zero at debt near 200% of GDP;
    psi = 0 gives the pure r - g threshold.
ratio  consolidated inflation-layer ratio from each country's clock with g = 4% growth issuance, as
       for the U.S. clock (at each country's trailing nominal g it is 2-10% lower).
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

from src.intl.jp_stock import era_date

OUT = Path("data/processed")
PSI = {"0bp": 0.0, "1bp": 0.01, "2bp": 0.02, "3bp": 0.03, "4.5bp": 0.045}
TARGET = 0.02


def real_growth(series: str, fiscal_april: bool = False) -> pd.Series:
    """Annual real GDP growth from a FRED quarterly real GDP series (calendar or April-March years)."""
    d = pd.read_csv(f"data/raw/fred/{series}.csv")
    d["date"] = pd.to_datetime(d.observation_date)
    d["y"] = d.date.dt.year - ((d.date.dt.month < 4) if fiscal_april else 0)
    a = d.groupby("y")[series].agg(["mean", "count"])
    return a.loc[a["count"] == 4, "mean"].pct_change()


def g_target(growth: pd.Series, year: int) -> float:
    return float(growth.loc[year - 9:year].mean()) + TARGET
PHI_HAT = (0.0, 0.25)
JP_TENOR = {"2年": 2, "5年": 5, "10年": 10, "20年": 20, "30年": 30, "40年": 40, "固定3年": 3, "固定5年": 5}


def jp_yields() -> pd.DataFrame:
    d = pd.read_csv("data/raw/jp/mof/jgbcm_all.csv", encoding="shift_jis", skiprows=1)
    d["date"] = d["基準日"].map(era_date)
    d = d.set_index("date").drop(columns="基準日").apply(pd.to_numeric, errors="coerce")
    d.columns = [int(re.sub(r"\D", "", c)) for c in d.columns]
    d["fy"] = d.index.year - (d.index.month < 4)
    return d.groupby("fy").mean()


def jp_tenor(name: str, kind: str) -> float:
    n = unicodedata.normalize("NFKC", name)
    if kind in ("bill", "floating"):
        return 1.0                                   # bills, 15-year floaters, retail floating: short rate
    for k, v in JP_TENOR.items():
        if k in n:
            return float(v)
    if "物価連動" in n:
        return 10.0
    raise ValueError(n)


def interp_yield(tenor: np.ndarray, curve: dict) -> np.ndarray:
    t = np.array(sorted(curve))
    return np.interp(np.minimum(tenor, t.max()), t, [curve[k] for k in t])


def japan() -> pd.DataFrame:
    y = jp_yields()
    iss = pd.read_csv("data/interim/jp/jgb_by_issue.csv")
    clk = pd.read_csv("data/processed/jp/jp_clock.csv").set_index("fy")
    rows = []
    for fy, x in iss.groupby("fy"):
        ten = np.array([jp_tenor(n, k) for n, k in zip(x.name, x.kind)])
        curve = {k: y.loc[fy, k] for k in y.columns if not np.isnan(y.loc[fy, k])}
        r = float((x.outstanding * interp_yield(ten, curve)).sum() / x.outstanding.sum()) / 100
        c = clk.loc[fy]
        rows.append({"country": "Japan", "year": fy, "r": r, "g": g_target(JP_REAL, fy),
                     "g_nominal_trailing": c.g_trailing10, "b": c.b_consol, "ratio": c.ratio_consol_g4})
    return pd.DataFrame(rows)


def uk() -> pd.DataFrame:
    yl = pd.read_csv("data/raw/uk/boe_db/boe_yields.csv")
    yl["DATE"] = pd.to_datetime(yl.DATE, format="%d %b %Y")
    yl = yl.set_index("DATE").apply(pd.to_numeric, errors="coerce")
    ya = yl.groupby(yl.index.year).mean()
    gilts = pd.read_csv("data/interim/uk/gilts_by_isin.csv", parse_dates=["as_of", "maturity", "first_issue"])
    clk = pd.read_csv("data/processed/uk/uk_clock.csv").set_index("year")
    rows = []
    for as_of, x in gilts.groupby("as_of"):
        yr = as_of.year
        ten = ((x.maturity - x.first_issue).dt.days / 365.25).fillna(20.0).values   # undated: long rate
        curve = {0.0: ya.loc[yr, "IUDSOIA"], 5.0: ya.loc[yr, "IUDSNPY"], 10.0: ya.loc[yr, "IUDMNPY"],
                 20.0: ya.loc[yr, "IUDLNPY"]}
        r = float((x.amount * interp_yield(ten, curve)).sum() / x.amount.sum()) / 100
        c = clk.loc[yr]
        rows.append({"country": "United Kingdom", "year": yr, "r": r, "g": g_target(UK_REAL, yr),
                     "g_nominal_trailing": c.g_trailing10, "b": c.b_consol, "ratio": c.ratio_consol_g4})
    return pd.DataFrame(rows)


def us() -> pd.DataFrame:
    d = pd.read_csv("data/processed/limit/limit_map_1980_2025.csv")
    d = d[d.year >= 2007]
    n = pd.read_csv("data/raw/bea/NipaDataA.txt", dtype=str)
    n.columns = [c.strip() for c in n.columns]
    x = n[n.iloc[:, 0] == "A191RL"]
    real = pd.Series(pd.to_numeric(x.iloc[:, 2]).values / 100, index=x.iloc[:, 1].astype(int).values)
    return pd.DataFrame({"country": "United States", "year": d.year, "r": d.r,
                         "g": [g_target(real, y) for y in d.year], "g_nominal_trailing": d.g_trailing,
                         "b": d.b, "ratio": d.ratio10_consol})


JP_REAL = real_growth("JPNRGDPEXP", fiscal_april=True)
UK_REAL = real_growth("NGDPRSAXDCGBQ")


def main() -> None:
    d = pd.concat([us(), uk(), japan()], ignore_index=True)
    for k, psi in PSI.items():
        d[f"phistar_{k}"] = 1 - d.g / (d.r + psi * d.b)
    d["phistar_3bp_nominal_g"] = 1 - d.g_nominal_trailing / (d.r + 0.03 * d.b)
    for ph in PHI_HAT:
        for k in ("0bp", "3bp"):
            d[f"dpi_{k}_phihat_{ph:.2f}"] = (d[f"phistar_{k}"] - ph).clip(lower=0) * d.ratio
    d["r_minus_g"] = d.r - d.g
    d.to_csv(OUT / "intl_phistar.csv", index=False)
    pd.set_option("display.width", 220)
    sel = d[d.year.isin([2007, 2012, 2019, 2021, 2023, 2024, 2025]) | (d.country == "Japan")]
    print(sel[["country", "year", "r", "g", "r_minus_g", "b", "phistar_0bp", "phistar_1bp", "phistar_3bp",
               "phistar_3bp_nominal_g", "ratio", "dpi_0bp_phihat_0.00", "dpi_3bp_phihat_0.00"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
