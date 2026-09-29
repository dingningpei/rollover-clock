"""Inflation layer: required sustained surprise inflation by year (paper, Section 3.3).

Two clocks. A permanent real-rate rise dr raises interest on all interest-bearing
liabilities b as they reprice: extra interest dr * b * P_r(h), with P_r built from every
interest-bearing liability (TIPS reprice their real coupon at maturity). A sustained
surprise inflation dpi erodes only nominal liabilities that have not yet repriced:
non-indexed debt N (clock P_N) and currency C, which pays no interest and never reprices.
TIPS are indexed and cannot be eroded. Per unit of b,

    dpi_req(H) = u * dr * int P_r / [ (N/b) int (1 - P_N) + (C/b) H ],
    dp_jump    = u * dr * int P_r / (N/b + C/b)          (one-time price-level jump),

with P(h) = 1 - (1 - F(h)) exp(-g h). Reported per 1pp permanent rate rise, u = 1.
"narrow" = the earlier definition: int P_r / int (1 - P_r), all debt erodable, no currency.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .consolidated_clock import OVERNIGHT, soma_by_cusip
from .treasury_clock import G_BASELINE, securities

OUT = Path("data/processed/clock")
GRID = np.linspace(0, 15, 1801)                    # years; step 1/120
HORIZONS = (5, 10, 15)
IOR_START = 2008                                   # interest on reserves from October 2008


def fred_december(series: str) -> pd.Series:
    """FRED monthly series, December value, $ millions, by year (CURRCIR, RESBALNS are in $bn)."""
    d = pd.read_csv(f"data/raw/fred/{series}.csv")
    d["date"] = pd.to_datetime(d.observation_date)
    d = d[d.date.dt.month == 12]
    return pd.Series(d[series].values * 1e3, index=d.date.dt.year.values)


def zero_interest_base_december() -> pd.Series:
    """Currency in circulation + (unremunerated) reserve balances, December, $ millions.
    Used for 1980-2002, before the weekly H.4.1 series starts."""
    return fred_december("CURRCIR") + fred_december("RESBALNS")


def exact_F(tau: np.ndarray, w: np.ndarray, h: np.ndarray = GRID) -> np.ndarray:
    """Share of w repricing within h, from security-level repricing dates tau."""
    o = np.argsort(tau)
    t, cw = tau[o], np.cumsum(w[o]) / w.sum()
    F = np.interp(h, t, cw, left=0.0, right=1.0)
    F[h < t[0]] = 0.0
    return F


def integrals(F_r: np.ndarray, F_n: np.ndarray, nom_share: float, cur_ratio: float,
              H: float, g: float = G_BASELINE, h: np.ndarray = GRID) -> dict:
    """Layer integrals per unit of interest-bearing debt b over [0, H]."""
    m = h <= H + 1e-9
    hh = h[m]
    P_r = 1 - (1 - F_r[m]) * np.exp(-g * hh)
    P_n = 1 - (1 - F_n[m]) * np.exp(-g * hh)
    intP = np.trapezoid(P_r, hh)
    ero_debt = nom_share * np.trapezoid(1 - P_n, hh)
    ero_cur = cur_ratio * H
    return {"intP": intP, "ero_debt": ero_debt, "ero_cur": ero_cur,
            "ratio": intP / (ero_debt + ero_cur),
            "ratio_nocur": intP / ero_debt,
            "ratio_narrow": intP / np.trapezoid(1 - P_r, hh),
            "jump_base": nom_share + cur_ratio}


def layer(tau: np.ndarray, w: np.ndarray, indexed: np.ndarray, currency: float,
          H: float, g: float = G_BASELINE) -> dict:
    """Security-level version: tau repricing dates, w amounts, indexed = TIPS flags."""
    tau, w, indexed = np.asarray(tau, float), np.asarray(w, float), np.asarray(indexed, bool)
    nom = ~indexed
    return integrals(exact_F(tau, w), exact_F(tau[nom], w[nom]), w[nom].sum() / w.sum(),
                     currency / w.sum(), H, g)


def portfolios():
    """(year, version, tau, w, indexed, currency) for the Treasury-only and consolidated stocks.
    Currency is a central-bank liability: it enters the consolidated stock only (H.4.1
    currency in circulation, same week as reserves). Reserves paid no interest before
    October 2008, so through 2007 they join currency in the zero-interest base; from 2008
    they are overnight interest-bearing debt. The Treasury-only benchmark is the
    Treasury's own liabilities: all marketable debt, no currency."""
    sec = securities(pd.read_csv("data/interim/mspd/table3_market_yearend.csv", dtype=str))
    sec["year"] = sec.record_date.dt.year
    soma = soma_by_cusip(pd.read_csv("data/interim/fed/soma_tsy_yearend.csv", dtype=str))
    soma["year"] = soma.year.astype(int)
    h41 = pd.read_csv("data/interim/fed/h41_wednesday_levels.csv")
    for y, x in sec.groupby("year"):
        s = soma[soma.year == y]
        yield y, "treasury", x.tau.values, x.par.values, (x.kind == "tips").values, 0.0
        if s.empty:
            continue
        lev = h41.loc[h41.date <= s.asOfDate.iloc[0]].iloc[-1]
        m = x.merge(s[["cusip", "soma_par"]], on="cusip", how="left").fillna({"soma_par": 0})
        paid = y >= IOR_START
        yield (y, "consolidated", np.r_[m.tau.values, OVERNIGHT],
               np.r_[(m.par - m.soma_par).values, lev.reverse_repo + (lev.reserves if paid else 0.0)],
               np.r_[(m.kind == "tips").values, False], lev.currency + (0.0 if paid else lev.reserves))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for y, v, tau, w, ix, cur in portfolios():
        row = {"year": y, "version": v, "b_total": w.sum(), "zero_interest": cur,
               "cur_ratio": cur / w.sum(), "tips_share": w[ix].sum() / w.sum()}
        for H in HORIZONS:
            for k, val in layer(tau, w, ix, cur, H).items():
                row[f"{k}_H{H}"] = val
        rows.append(row)
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "inflation_layer_yearend.csv", index=False)
    print("Required sustained inflation, pp/yr per +1pp permanent rate rise, no fiscal offset, H = 10")
    print(d.pivot(index="year", columns="version",
                  values=["ratio_H10", "ratio_nocur_H10", "ratio_narrow_H10", "cur_ratio", "tips_share"])
          .round(3).to_string())


if __name__ == "__main__":
    main()
