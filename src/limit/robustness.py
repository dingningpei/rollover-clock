"""Robustness of the two-layer limit to its parameters (paper, Section 5.2, Table 4).

Recomputes phi* and the inflation needed to cover the fiscal gap (per +1pp permanent rate
rise, H = 10) under alternative parameters, holding the measured clock (the inflation-
layer ratio) and the stock-structure rate r fixed:

  g   ex ante: trailing 10-year real GDP growth known at t + the Cleveland Fed's 10-year
      expected inflation in December of t (FRED EXPINF10YR, from 1982; trailing nominal
      growth in 1980-81); trailing nominal growth; the baseline (realized forward growth
      to 2015, FOMC SEP longer-run growth + 2% from 2016)
  psi applied to all consolidated debt (baseline), to privately held marketable debt only
      (excluding reserves and reverse repos), or to debt held by the public (FRED FYGFDPUN)
  currency held abroad (Z.1, FL263025003): share of currency, and the consolidated ratio
      with only domestically held currency in the erosion base (2007, 2025)
  Monte Carlo (10,000 draws): psi ~ U[2, 4.5] bp; g_t = baseline g_t + e, e ~ N(0, 0.5 pp)
      common to all years; phi_hat ~ U[0.25, 0.50] through 2003 and U[0, 0.25] from 2004.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.limit.limit_map import gdp

OUT = Path("data/processed/limit")
PSI = 0.03
N_DRAWS = 10_000
SEED = 20260930


def inputs() -> pd.DataFrame:
    d = pd.read_csv(OUT / "limit_map_1980_2025.csv").set_index("year")
    n = pd.read_csv("data/raw/bea/NipaDataA.txt", dtype=str)
    n.columns = [c.strip() for c in n.columns]
    x = n[n.iloc[:, 0] == "A191RL"]
    real = pd.Series(pd.to_numeric(x.iloc[:, 2]).values, index=x.iloc[:, 1].astype(int).values) / 100
    e = pd.read_csv("data/raw/fred/EXPINF10YR.csv")
    e = e[e.observation_date.str[5:7] == "12"]
    expinf = pd.Series(e.EXPINF10YR.values / 100, index=e.observation_date.str[:4].astype(int).values)
    d["g_exante"] = [real.loc[t - 9:t].mean() + expinf[t] if t in expinf.index else d.loc[t, "g_trailing"]
                     for t in d.index]
    # privately held marketable debt (excluding reserves and reverse repos) / GDP
    h41 = pd.read_csv("data/interim/fed/h41_wednesday_levels.csv")
    con = pd.read_csv("data/processed/clock/consolidated_clock_yearend.csv").set_index("year")
    y = gdp()
    b_priv = []
    for t in d.index:
        if t in con.index:
            lev = h41.loc[h41.date <= f"{t}-12-31"].iloc[-1]
            b_priv.append(d.loc[t, "b"] - (lev.reserves + lev.reverse_repo) / y[t])
        else:
            b_priv.append(d.loc[t, "b"])                    # FD-5 era: privately held marketable
    d["b_privmkt"] = b_priv
    f = pd.read_csv("data/raw/fred/FYGFDPUN.csv")
    f = f[f.observation_date.str[5:7] == "10"]
    pub = pd.Series(f.FYGFDPUN.values, index=f.observation_date.str[:4].astype(int).values)
    d["b_public"] = [pub[t] / y[t] if t in pub.index else np.nan for t in d.index]
    return d


def requirement(d: pd.DataFrame, g: pd.Series, psi: float, b_psi: pd.Series, phi_hat: pd.Series) -> pd.DataFrame:
    phistar = 1 - g / (d.r + psi * b_psi)
    dpi = (phistar - phi_hat).clip(lower=0) * d.ratio10_consol
    return pd.DataFrame({"phistar": phistar, "dpi": dpi})


def summary(name: str, x: pd.DataFrame) -> dict:
    pre = x.dpi.loc[:2021]
    return {"variant": name, "phistar_2023_25_lo": x.phistar.loc[2023:2025].min(),
            "phistar_2023_25_hi": x.phistar.loc[2023:2025].max(),
            "dpi_2023_25_lo": x.dpi.loc[2023:2025].min(), "dpi_2023_25_hi": x.dpi.loc[2023:2025].max(),
            "max_pre2022": pre.max(), "max_pre2022_year": int(pre.idxmax()),
            "ranked_first": x.dpi.loc[2023:2025].max() > pre.max()}


def foreign_currency() -> pd.DataFrame:
    from src.clock.consolidated_clock import OVERNIGHT
    from src.clock.inflation_layer import IOR_START, layer
    from src.limit.decompose import portfolio
    z = pd.read_csv("data/interim/fed/z1_currency_abroad.csv").set_index("date")
    rows = []
    for y in (2007, 2019, 2025):
        x, lev = portfolio(y)
        paid = y >= IOR_START
        tau = np.r_[x.tau.values, OVERNIGHT]
        w = np.r_[(x.par - x.soma_par).values, lev.reverse_repo + (lev.reserves if paid else 0.0)]
        ix = np.r_[(x.kind == "tips").values, False]
        zero = lev.currency + (0.0 if paid else lev.reserves)
        abroad = z.loc[f"{y}-12-31", "currency_abroad"]
        rows.append({"year": y, "share_abroad": abroad / lev.currency, "ratio": layer(tau, w, ix, zero, 10)["ratio"],
                     "ratio_domestic_currency": layer(tau, w, ix, zero - abroad, 10)["ratio"]})
    return pd.DataFrame(rows)


def main() -> None:
    fc = foreign_currency()
    fc.to_csv(OUT / "robustness_foreign_currency.csv", index=False)
    print(fc.round(3).to_string(index=False))
    d = inputs()
    phi_regime = pd.Series(np.where(d.index <= 2003, 0.39, 0.0), index=d.index)
    g0 = d.g_forward
    rows = [summary("Baseline", requirement(d, g0, PSI, d.b, phi_regime)),
            summary("g ex ante (trailing real growth + 10-year expected inflation)",
                    requirement(d, d.g_exante, PSI, d.b, phi_regime)),
            summary("g trailing 10-year nominal growth", requirement(d, d.g_trailing, PSI, d.b, phi_regime)),
            summary("psi on privately held marketable debt (no reserves)",
                    requirement(d, g0, PSI, d.b_privmkt, phi_regime)),
            summary("psi on debt held by the public", requirement(d, g0, PSI, d.b_public, phi_regime)),
            summary("psi = 2bp", requirement(d, g0, 0.02, d.b, phi_regime)),
            summary("psi = 4.5bp", requirement(d, g0, 0.045, d.b, phi_regime))]
    rng = np.random.default_rng(SEED)
    draws, first = [], 0
    for _ in range(N_DRAWS):
        psi = rng.uniform(0.02, 0.045)
        g = g0 + rng.normal(0, 0.005)
        ph = pd.Series(np.where(d.index <= 2003, rng.uniform(0.25, 0.50), rng.uniform(0.0, 0.25)), index=d.index)
        x = requirement(d, g, psi, d.b, ph)
        draws.append(x.dpi.values)
        first += x.dpi.loc[2023:2025].max() > x.dpi.loc[:2021].max()
    draws = np.array(draws)
    band = pd.DataFrame({"p05": np.percentile(draws, 5, axis=0), "p50": np.percentile(draws, 50, axis=0),
                         "p95": np.percentile(draws, 95, axis=0)}, index=d.index)
    band.to_csv(OUT / "robustness_mc_band.csv")
    mc = band.loc[2023:2025]
    rows.append({"variant": "Monte Carlo, 90% band", "dpi_2023_25_lo": mc.p05.min(), "dpi_2023_25_hi": mc.p95.max(),
                 "ranked_first_share": first / N_DRAWS})
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "robustness.csv", index=False)
    d[["g_forward", "g_exante", "g_trailing", "b", "b_privmkt", "b_public"]].to_csv(OUT / "robustness_inputs.csv")
    pd.set_option("display.width", 220)
    print(t.round(3).to_string(index=False))
    print(d.loc[[1985, 2000, 2007, 2015, 2023, 2025], ["g_forward", "g_exante", "g_trailing", "b", "b_privmkt", "b_public"]].round(3))
    print(band.loc[2020:2025].round(2))


if __name__ == "__main__":
    main()
