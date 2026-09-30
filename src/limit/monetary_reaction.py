"""Pricing the inflation route when the central bank reacts (paper, Sections 3.3 and 5.2).

Sustained surprise inflation dpi erodes b*E(h) per year at horizon h. If the central bank raises
the real rate by kappa per point of surprise inflation, the debt that has repriced by h (the
clock P(h), including growth issuance and reserves) pays kappa*dpi more in real terms. Over
[0, H], first order and undiscounted as in the combined metric:
    net relief per point of inflation = b * (int E - kappa * int P),
so the inflation needed to cover a gap u after a permanent rate rise dr is
    dpi(kappa) = u * dr * R / (1 - kappa * R),   R = int P / int E,
finite only if kappa < kappa* = 1 / R. Above kappa* no rate of inflation covers any gap: the
real-rate response takes back more than the inflation erodes.

Outputs (data/processed/limit/):
  monetary_reaction_kappa_star.csv  kappa* by year: United States 1980-2025 (consolidated and
                                    Treasury-only), UK 2007-2025, Japan FY2020-2024
  monetary_reaction_requirement.csv requirement for kappa in {0, 0.25, 0.5}, selected U.S. years
  monetary_reaction_implied.csv     kappa implied by the post-2020 tests: the real-rate part of the
                                    take-back (inflation as priced, D, minus actual, C) divided by
                                    its value at kappa = 1, sum_t s_t * W0 * P(t); an upper bound,
                                    since real rates also rose for reasons other than the inflation
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.clock.consolidated_clock import OVERNIGHT, soma_by_cusip
from src.clock.inflation_layer import GRID, exact_F
from src.clock.treasury_clock import G_BASELINE, securities

OUT = Path("data/processed/limit")
KAPPAS = (0.0, 0.25, 0.5)


def requirement(u: float, R: float, kappa: float, dr: float = 1.0) -> float:
    return u * dr * R / (1 - kappa * R) if kappa * R < 1 else np.inf


def kappa_star() -> pd.DataFrame:
    us = pd.read_csv(OUT / "limit_map_1980_2025.csv").set_index("year")
    rows = [{"country": "United States", "year": t, "R_consol": r.ratio10_consol, "R_own": r.ratio10_treasury,
             "R_consol_H5": r.ratio5_consol, "R_consol_H15": r.ratio15_consol} for t, r in us.iterrows()]
    uk = pd.read_csv("data/processed/uk/uk_clock.csv").set_index("year")
    rows += [{"country": "United Kingdom", "year": t, "R_consol": r.ratio_consol_g4, "R_own": r.ratio_gross_g4,
              "R_consol_H5": r.ratio_consol_g4_H5, "R_consol_H15": r.ratio_consol_g4_H15} for t, r in uk.iterrows()]
    jp = pd.read_csv("data/processed/jp/jp_clock.csv").set_index("fy")
    rows += [{"country": "Japan", "year": t, "R_consol": r.ratio_consol_g4, "R_own": r.ratio_gross_g4,
              "R_consol_H5": r.ratio_consol_g4_H5, "R_consol_H15": r.ratio_consol_g4_H15} for t, r in jp.iterrows()]
    d = pd.DataFrame(rows)
    d["kappa_star_consol"] = 1 / d.R_consol
    d["kappa_star_own"] = 1 / d.R_own
    for H in (5, 15):
        d[f"kappa_star_H{H}"] = 1 / d[f"R_consol_H{H}"]
    return d


def requirements() -> pd.DataFrame:
    us = pd.read_csv(OUT / "limit_map_1980_2025.csv").set_index("year")
    rows = []
    for t in (1981, 1984, 2007, 2019, 2023, 2024, 2025):
        r = us.loc[t]
        for lab, ph in (("regime", 0.39 if t <= 2003 else 0.0), ("common0.25", 0.25)):
            u = max(r.phistar - ph, 0.0)
            rec = {"year": t, "phi_hat": lab, "u": u, "R": r.ratio10_consol, "kappa_star": 1 / r.ratio10_consol}
            for k in KAPPAS:
                rec[f"dpi_k{k:.2f}"] = requirement(u, r.ratio10_consol, k)
            for H, col in ((5, "ratio5_consol"), (15, "ratio15_consol")):
                rec[f"kappa_star_H{H}"] = 1 / r[col]
                rec[f"dpi_k0.50_H{H}"] = requirement(u, r[col], 0.5)
            rows.append(rec)
    return pd.DataFrame(rows)


def P_path(tau: np.ndarray, w: np.ndarray, months: int, g: float = G_BASELINE) -> np.ndarray:
    P = 1 - (1 - exact_F(tau, w, GRID)) * np.exp(-g * GRID)
    return np.interp(np.arange(1, months + 1) / 12, GRID, P)


def implied_us() -> dict:
    m = pd.read_csv("data/processed/clock/inflation_test_monthly.csv", index_col=0)
    sec = securities(pd.read_csv("data/interim/mspd/table3_market_yearend.csv", dtype=str))
    x = sec[sec.record_date.dt.year == 2020]
    soma = soma_by_cusip(pd.read_csv("data/interim/fed/soma_tsy_yearend.csv", dtype=str))
    x = x.merge(soma[soma.year.astype(int) == 2020][["cusip", "soma_par"]], on="cusip", how="left").fillna({"soma_par": 0})
    h41 = pd.read_csv("data/interim/fed/h41_wednesday_levels.csv")
    lev = h41.loc[h41.date <= "2020-12-31"].iloc[-1]
    tau = np.r_[x.tau.values, OVERNIGHT]
    w = np.r_[(x.par - x.soma_par).values, lev.reserves + lev.reverse_repo]
    P = P_path(tau, w, len(m))
    at_one = float((m.s.values / 100 / 12 * w.sum() * P).sum())
    taken = float((m.transfer_D - m.transfer_C).sum())
    return {"country": "United States", "window": "2021-2025", "real_rate_takeback": taken,
            "value_at_kappa_1": at_one, "kappa_implied": taken / at_one}


def implied_uk() -> dict:
    from src.intl.uk_inflation_test import balance_sheet
    m = pd.read_csv("data/processed/uk/uk_inflation_test_monthly.csv", index_col=0)
    gilts, reserves, notes, il = balance_sheet()
    tau = np.r_[gilts.tau.values, OVERNIGHT]
    w = np.r_[gilts.private.values, reserves]
    P = P_path(tau, w, len(m))
    at_one = float((m.s.values / 100 / 12 * w.sum() * P).sum())
    taken = float((m.transfer_D - m.transfer_C).sum())
    return {"country": "United Kingdom", "window": "2021-2025", "real_rate_takeback": taken,
            "value_at_kappa_1": at_one, "kappa_implied": taken / at_one}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    k = kappa_star()
    k.to_csv(OUT / "monetary_reaction_kappa_star.csv", index=False)
    r = requirements()
    r.to_csv(OUT / "monetary_reaction_requirement.csv", index=False)
    i = pd.DataFrame([implied_us(), implied_uk()])
    i.to_csv(OUT / "monetary_reaction_implied.csv", index=False)
    pd.set_option("display.width", 200)
    sel = k[(k.country != "United States") | k.year.isin([1981, 1990, 2000, 2007, 2012, 2019, 2021, 2023, 2025])]
    print(sel.round(3).to_string(index=False))
    print(r.round(3).to_string(index=False))
    print(i.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
