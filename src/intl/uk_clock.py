"""United Kingdom: rollover clock and inflation layer at year-ends, consolidated government
(HM Treasury + Bank of England), on the same definitions as the U.S. and Japan.

Interest-bearing liabilities to the private sector:
  - gilts by ISIN (DMO; index-linked at their inflation-uplifted amount) minus APF holdings
    (Bank of England operations; index-linked holdings uplifted with the DMO index ratio);
  - reserve balances, remunerated at Bank Rate throughout the sample (repricing overnight).
Zero-interest base (erosion only): notes and coin in circulation.
Repricing: maturity; undated gilts (perpetuals until 2014-15) never reprice unless a
redemption date has been announced. Index-linked gilts are not eroded by inflation.
Not yet included: Treasury bills (about 3-4% of marketable debt), cash ratio deposits.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.clock.consolidated_clock import OVERNIGHT
from src.clock.inflation_layer import GRID, exact_F, layer

IN = Path("data/interim/uk")
OUT = Path("data/processed/uk")
UNDATED_TAU = 100.0


def boe_series() -> pd.DataFrame:
    d = pd.read_csv("data/raw/uk/boe_db/boe_series.csv")
    d["DATE"] = pd.to_datetime(d.DATE, format="%d %b %Y")
    return d.set_index("DATE")


def gdp_cy() -> pd.Series:
    d = pd.read_csv("data/raw/fred/UKNGDP.csv")
    d["year"] = pd.to_datetime(d.observation_date).dt.year
    g = d.groupby("year").UKNGDP.agg(["sum", "count"])
    return g.loc[g["count"] == 4, "sum"]                           # £ million


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    gilts = pd.read_csv(IN / "gilts_by_isin.csv", parse_dates=["as_of", "maturity"])
    apf = pd.read_csv(IN / "apf_by_isin.csv")
    boe, gdp = boe_series(), gdp_cy()
    rows = []
    for as_of, x in gilts.groupby("as_of"):
        y = as_of.year
        x = x.merge(apf[apf.year == y][["isin", "apf_nominal"]], on="isin", how="left").fillna({"apf_nominal": 0.0})
        x["apf"] = x.apf_nominal * x.amount / x.nominal               # uplift index-linked holdings
        x["private"] = (x.amount - x.apf).clip(lower=0)
        x["tau"] = ((x.maturity - as_of).dt.days / 365.25).fillna(UNDATED_TAU)
        dec = boe.loc[f"{y}-12"]
        reserves = dec.LPMBL22.dropna().iloc[-1] if dec.LPMBL22.notna().any() else 0.0
        notes = dec.LPMAVAA.dropna().iloc[-1]
        tau = np.r_[x.tau.values, OVERNIGHT]
        w = np.r_[x.private.values, reserves]
        ix = np.r_[(x.kind == "indexed").values, False]
        tau_t, w_t, ix_t = x.tau.values, x.amount.values, (x.kind == "indexed").values
        g_tr = float(gdp.pct_change().loc[y - 9:y].mean())
        row = {"year": y, "gdp": gdp[y], "g_trailing10": g_tr, "b_consol": w.sum() / gdp[y],
               "b_gross": w_t.sum() / gdp[y], "apf_share": x.apf.sum() / x.amount.sum(),
               "overnight_share": reserves / w.sum(), "zero_ratio": notes / w.sum(),
               "notes_gdp": notes / gdp[y], "indexed_share_consol": w[ix].sum() / w.sum(),
               "indexed_share_gross": w_t[ix_t].sum() / w_t.sum(),
               "wam_consol": float((w * np.minimum(tau, 60)).sum() / w.sum()),
               "wam_gross": float((w_t * np.minimum(tau_t, 60)).sum() / w_t.sum())}
        for g, tag in ((g_tr, "gtr"), (0.04, "g4")):
            row[f"P1_consol_{tag}"] = float(1 - (1 - np.interp(1, GRID, exact_F(tau, w, GRID))) * np.exp(-g))
            row[f"P1_gross_{tag}"] = float(1 - (1 - np.interp(1, GRID, exact_F(tau_t, w_t, GRID))) * np.exp(-g))
            row[f"ratio_consol_{tag}"] = layer(tau, w, ix, notes, 10, g)["ratio"]
            row[f"ratio_consol_nocur_{tag}"] = layer(tau, w, ix, 0.0, 10, g)["ratio"]
            row[f"ratio_gross_{tag}"] = layer(tau_t, w_t, ix_t, 0.0, 10, g)["ratio"]
        for H in (5, 15):                                             # horizon sensitivity, g = 4%
            row[f"ratio_consol_g4_H{H}"] = layer(tau, w, ix, notes, H, 0.04)["ratio"]
        rows.append(row)
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "uk_clock.csv", index=False)
    pd.set_option("display.width", 250)
    cols = ["year", "b_consol", "apf_share", "overnight_share", "zero_ratio", "indexed_share_consol", "wam_gross",
            "wam_consol", "P1_gross_g4", "P1_consol_g4", "ratio_gross_g4", "ratio_consol_g4", "ratio_consol_nocur_g4"]
    print(d[cols].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
