"""Identify the fiscal response phi in a panel of advanced economies (extends Appendix C).

phi is the share of a rise in interest cost that the primary surplus offsets. The U.S. time
series cannot identify it because its repricing speed barely varies. Across countries it
varies widely, so the same rate change raises interest costs by different amounts.

  Instrument  Z_it = x_{i,t-1} * b_{i,t-1} * dr_it
      x  = share of government debt that reprices within a year:
           (a) bills share of general-government debt securities (BIS, 1990-2025), or
           (b) OECD RFSH, marketable debt to refinance within the coming year (2013-2025);
      b  = gross government debt / GDP (OECD GGFLQ);  dr = change in the short-term rate (IRS).
  Local projections, h = 0..3:
      S_{t+h} - S_{t-1} = phi_h (IC_{t+h} - IC_{t-1}) + controls + country FE + year FE,
      IC_{t+h} - IC_{t-1} instrumented by Z_it.
  S  = underlying primary balance (% of potential GDP; OECD NLGXQU), or actual (NLGXQ);
  IC = net interest payments, % of GDP (GNINTQ), or gross (GGINTP / GDP).
  Controls: dr_it, x_{t-1}, b_{t-1}, output gap_{t-1}, dS_{t-1}; "strict" adds dr_it * b_{t-1},
  so identification comes only from differences in x.
Year fixed effects absorb the global cycle and common shocks. Standard errors clustered by country.
Output: data/processed/fiscal/phi_panel.csv
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path("data/raw/panel")
OUT = Path("data/processed/fiscal")
LAST = 2025                                          # Economic Outlook years after this are projections
ISO2 = {"AUS": "AU", "AUT": "AT", "BEL": "BE", "CAN": "CA", "CHE": "CH", "DEU": "DE", "DNK": "DK", "ESP": "ES",
        "FIN": "FI", "FRA": "FR", "GBR": "GB", "GRC": "GR", "IRL": "IE", "ISL": "IS", "ITA": "IT", "JPN": "JP",
        "KOR": "KR", "NLD": "NL", "NOR": "NO", "NZL": "NZ", "PRT": "PT", "SWE": "SE", "USA": "US"}


def panel() -> pd.DataFrame:
    e = pd.read_csv(RAW / "oecd_eo.csv", usecols=["REF_AREA", "MEASURE", "TIME_PERIOD", "OBS_VALUE"])
    d = e.pivot_table(index=["REF_AREA", "TIME_PERIOD"], columns="MEASURE", values="OBS_VALUE").reset_index()
    d = d.rename(columns={"REF_AREA": "c", "TIME_PERIOD": "t"})
    d = d[d.t <= LAST]
    d["ICg"] = 100 * d.GGINTP / d.GDP
    b = pd.read_csv(RAW / "bis_dss_gg.csv", usecols=["REF_AREA", "MATURITY", "VALUATION", "CURRENCY_DENOM",
                                                      "UNIT_MEASURE", "TIME_PERIOD", "OBS_VALUE"])
    b = b[(b.CURRENCY_DENOM == "_T") & (b.UNIT_MEASURE == "USD") & b.MATURITY.isin(["S", "T"])
          & b.TIME_PERIOD.str.endswith("Q4")]                     # same unit for both, all currencies
    b["t"] = b.TIME_PERIOD.str[:4].astype(int)
    # nominal value where available, else market value
    b = b.sort_values("VALUATION", ascending=False).drop_duplicates(["REF_AREA", "MATURITY", "t"])
    s = b.pivot_table(index=["REF_AREA", "t"], columns="MATURITY", values="OBS_VALUE").reset_index()
    s["bills"] = s.S / s["T"]
    inv = {v: k for k, v in ISO2.items()}
    s["c"] = s.REF_AREA.map(inv)
    d = d.merge(s[["c", "t", "bills"]], on=["c", "t"], how="left").sort_values(["c", "t"])
    g = d.groupby("c")
    d["b_l"] = g.GGFLQ.shift(1) / 100
    d["dr"] = d.IRS - g.IRS.shift(1)
    d["gap_l"] = g.GAP.shift(1)
    for x in ("bills", "RFSH"):
        d[f"{x}_l"] = g[x].shift(1)
    return d


def tsls(y, X, W, Z, cl):
    """2SLS of y on [X, W] with instruments [Z, W]; cluster-robust s.e. for X."""
    R = np.column_stack([X, W])
    Q = np.column_stack([Z, W])
    Rh = Q @ np.linalg.lstsq(Q, R, rcond=None)[0]              # first-stage fitted values
    A = np.linalg.pinv(Rh.T @ Rh)
    beta = A @ Rh.T @ y
    u = y - R @ beta
    meat = np.zeros((R.shape[1], R.shape[1]))
    for gid in np.unique(cl):
        m = cl == gid
        s = Rh[m].T @ u[m]
        meat += np.outer(s, s)
    G, n, k = len(np.unique(cl)), len(y), R.shape[1]
    V = A @ meat @ A * G / (G - 1) * (n - 1) / (n - k)
    return beta[: X.shape[1]], np.sqrt(np.diag(V))[: X.shape[1]]


def first_stage_F(x, Z, W, cl):
    b, se = tsls(x, Z, W, Z, cl)                     # OLS of x on Z and W (exactly identified)
    return float((b[0] / se[0]) ** 2), float(b[0]), float(se[0])


def estimate(d: pd.DataFrame, S: str, IC: str, xname: str, h: int, strict: bool, years=None) -> dict:
    d = d.copy()
    g = d.groupby("c")
    d["y"] = g[S].shift(-h) - g[S].shift(1)
    d["x"] = g[IC].shift(-h) - g[IC].shift(1)
    d["dS_l"] = g[S].shift(1) - g[S].shift(2)
    d["Z"] = d[f"{xname}_l"] * d.b_l * d.dr
    d["drb"] = d.dr * d.b_l
    ctrl = ["dr", f"{xname}_l", "b_l", "gap_l", "dS_l"] + (["drb"] if strict else [])
    k = d.replace([np.inf, -np.inf], np.nan).dropna(subset=["y", "x", "Z"] + ctrl)
    if years:
        k = k[(k.t >= years[0]) & (k.t <= years[1])]
    fe = pd.get_dummies(k.c, drop_first=True, dtype=float).join(pd.get_dummies(k.t, prefix="t", drop_first=True,
                                                                                 dtype=float))
    W = np.column_stack([np.ones(len(k)), k[ctrl].values, fe.values])
    cl = k.c.values
    F, fs, fs_se = first_stage_F(k.x.values, k[["Z"]].values, W, cl)
    b, se = tsls(k.y.values, k[["x"]].values, W, k[["Z"]].values, cl)
    rf, rf_se = tsls(k.y.values, k[["Z"]].values, W, k[["Z"]].values, cl)
    return {"S": S, "IC": IC, "x": xname, "h": h, "strict": strict, "years": f"{k.t.min()}-{k.t.max()}",
            "n": len(k), "countries": k.c.nunique(), "first_stage": fs, "fs_se": fs_se, "F": F,
            "reduced_form": float(rf[0]), "rf_se": float(rf_se[0]), "phi": float(b[0]), "phi_se": float(se[0])}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = panel()
    rows = []
    for xname in ("bills", "RFSH"):
        for S in ("NLGXQU", "NLGXQ"):
            for IC in ("GNINTQ", "ICg"):
                for strict in (False, True):
                    for h in range(4):
                        rows.append(estimate(d, S, IC, xname, h, strict))
    r = pd.DataFrame(rows)
    r.to_csv(OUT / "phi_panel.csv", index=False)
    pd.set_option("display.width", 250)
    cols = ["x", "S", "IC", "strict", "h", "years", "n", "countries", "first_stage", "F", "phi", "phi_se"]
    print(r[cols].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
