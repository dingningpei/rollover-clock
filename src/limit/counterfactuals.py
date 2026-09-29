"""Counterfactuals at end-2025 for the two-layer limit (Step 6).

Baseline: consolidated end-2025 portfolio (MSPD by CUSIP net of SOMA + reserves + RRP),
r = 4.20% (stock-structure rate), b = consolidated debt/GDP, g = 3.8% (Dec-2025 SEP
longer-run real growth 1.8% + 2%), psi = 3bp,
phi_hat = 0 (post-2004), +1pp permanent rate rise, H = 10.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.clock.consolidated_clock import OVERNIGHT, soma_by_cusip
from src.clock.inflation_layer import required_inflation
from src.clock.treasury_clock import securities

OUT = Path("data/processed/limit")
Y, H = 2025, 10.0


def portfolio_2025():
    sec = securities(pd.read_csv("data/interim/mspd/table3_market_yearend.csv", dtype=str))
    x = sec[sec.record_date.dt.year == Y].copy()
    soma = soma_by_cusip(pd.read_csv("data/interim/fed/soma_tsy_yearend.csv", dtype=str))
    s = soma[soma.year.astype(int) == Y]
    lev = pd.read_csv("data/interim/fed/h41_wednesday_levels.csv")
    lev = lev.loc[lev.date <= s.asOfDate.iloc[0]].iloc[-1]
    x = x.merge(s[["cusip", "soma_par"]], on="cusip", how="left").fillna({"soma_par": 0})
    return x, lev


G_SEP_2025 = 0.038


def metrics(tau, w, r, b, g=G_SEP_2025, psi=0.03, phi_hat=0.0, dr=1.0):
    ratio = required_inflation(np.asarray(tau), np.asarray(w, dtype=float), H, g)
    phistar = 1 - g / (r + psi * b)
    gap = max(phistar - phi_hat, 0.0)
    intP = H * ratio / (1 + ratio)
    return {"ratio10": ratio, "phistar": phistar, "gap": gap,
            "dpi_gap_pp_per_yr": gap * dr * ratio, "dp_jump_pct": gap * dr * intP}


def main() -> None:
    x, lev = portfolio_2025()
    lm = pd.read_csv(OUT / "limit_map_1980_2025.csv").set_index("year").loc[Y]
    r, b = lm.r, lm.b
    priv = (x.par - x.soma_par).values
    on = lev.reserves + lev.reverse_repo
    base_tau, base_w = np.r_[x.tau.values, OVERNIGHT], np.r_[priv, on]
    rows = []

    def add(name, tau=base_tau, w=base_w, **kw):
        rows.append({"scenario": name, **metrics(tau, w, kw.pop("r", r), kw.pop("b", b), **kw)})

    add("Baseline (consolidated, phi_hat=0)")
    add("No QE: Treasury-only clock", tau=x.tau.values, w=x.par.values)
    # QT: Fed holdings shrink by the reserve reduction; those Treasuries return to private
    # holders pro rata to the SOMA maturity structure; RRP unchanged.
    cut = lev.reserves - 1.9e6
    priv_qt = priv + x.soma_par.values * cut / x.soma_par.sum()
    add("QT: reserves to ~$1.9tn (2019), Treasuries back to private", w=np.r_[priv_qt, on - cut])
    bills = (x.kind == "bill").values
    shift = 0.10 * x.par[bills].sum()
    tau_to = np.r_[x.tau.values, OVERNIGHT, 10.0]
    w_to = np.r_[np.where(bills, priv * (1 - shift / priv[bills].sum()), priv), on, shift]
    add("Treasury terms out: 10% of bills -> 10y", tau=tau_to, w=w_to)
    add("Fiscal response restored (phi_hat=0.39)", phi_hat=0.39)
    add("Fiscal response at Bohn-based 0.25", phi_hat=0.25)
    add("Convenience yield lost 50bp (r+0.5pp)", r=r + 0.005)
    add("Convenience yield lost 100bp (r+1pp)", r=r + 0.010)
    add("Growth g=4% (earlier assumption)", g=0.04)
    add("Lower growth g=3.5%", g=0.035)
    add("psi = 2bp (CBO)", psi=0.02)
    add("psi = 4.5bp", psi=0.045)
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "counterfactuals_2025.csv", index=False)
    print(f"end-2025: r={r:.4f}, b={b:.3f}, reserves+RRP=${on/1e6:.2f}tn")
    print(d.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
