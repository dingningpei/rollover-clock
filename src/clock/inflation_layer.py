"""Inflation layer: required sustained surprise inflation by year (paper, Section 3.3).

dpi_req(H) = (1-theta) * dr * int_0^H P(h) dh / int_0^H [1-P(h)] dh,
with P(h) = 1 - (1-F(h)) exp(-g h) and F from the security-level repricing dates.
Reported per 1pp permanent real-rate rise, theta = 0 (no fiscal offset).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .consolidated_clock import OVERNIGHT, soma_by_cusip
from .treasury_clock import G_BASELINE, securities

OUT = Path("data/processed/clock")
GRID = np.linspace(0, 10, 1201)


def required_inflation(tau: np.ndarray, w: np.ndarray, H: float, g: float = G_BASELINE) -> float:
    order = np.argsort(tau)
    tau, cw = tau[order], np.cumsum(w[order]) / w.sum()
    h = GRID[GRID <= H]
    F = np.interp(h, tau, cw, left=0.0, right=1.0)
    F[h < tau[0]] = 0.0
    P = 1 - (1 - F) * np.exp(-g * h)
    return np.trapezoid(P, h) / np.trapezoid(1 - P, h)


def portfolios():
    sec = securities(pd.read_csv("data/interim/mspd/table3_market_yearend.csv", dtype=str))
    sec["year"] = sec.record_date.dt.year
    soma = soma_by_cusip(pd.read_csv("data/interim/fed/soma_tsy_yearend.csv", dtype=str))
    soma["year"] = soma.year.astype(int)
    h41 = pd.read_csv("data/interim/fed/h41_wednesday_levels.csv")
    for y, x in sec.groupby("year"):
        yield y, "treasury", x.tau.values, x.par.values
        s = soma[soma.year == y]
        if s.empty:
            continue
        lev = h41.loc[h41.date <= s.asOfDate.iloc[0]].iloc[-1]
        m = x.merge(s[["cusip", "soma_par"]], on="cusip", how="left").fillna({"soma_par": 0})
        yield (y, "consolidated", np.r_[m.tau.values, OVERNIGHT],
               np.r_[(m.par - m.soma_par).values, lev.reserves + lev.reverse_repo])


def main() -> None:
    rows = [{"year": y, "version": v, **{f"dpi_req_H{H}": required_inflation(t, w, H) for H in (3, 5, 10)}}
            for y, v, t, w in portfolios()]
    df = pd.DataFrame(rows).pivot(index="year", columns="version")
    df.columns = [f"{a}_{b}" for a, b in df.columns]
    df.to_csv(OUT / "inflation_layer_yearend.csv")
    print("Required sustained inflation, pp/yr, per +1pp permanent real-rate shock, no fiscal offset")
    print(df.round(2).to_string())


if __name__ == "__main__":
    main()
