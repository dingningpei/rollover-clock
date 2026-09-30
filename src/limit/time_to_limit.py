"""Time to the limit with a capped primary surplus (paper, Section 3.5 and Figure 4).

With a linear fiscal rule, maturity does not change whether debt is stable (Result 1).
With a ceiling on the primary surplus, s <= s_max (fiscal fatigue), a large enough
permanent rate shock dr breaks the limit for any maturity, and the rollover clock decides
when. The debt-stabilizing primary balance after the shock is

    s_req(h) = (rbar(h) - g) b - g z - dpi * b * E(h),
    rbar(h)  = rbar0 + (r + dr - rbar0) P(h),

(z: zero-interest base / GDP; dpi: an optional sustained surprise inflation, which buys
time through the erosion share E). The time to the limit is the first h with
s_req(h) > s_max; it is infinite when the long-run requirement stays below s_max.

All clock variants use the end-2025 fiscal position (b, rbar0, r, g, z) and differ only in
the repricing profile, so the comparison isolates maturity:
  - consolidated, end-2025;
  - no QE at end-2025 (Fed Treasuries = currency, no reserves; Section 6);
  - the end-2007 consolidated clock.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.clock.consolidated_clock import OVERNIGHT
from src.clock.inflation_layer import IOR_START, exact_F
from src.limit.decompose import portfolio
from src.limit.level_metric import average_rate

OUT = Path("data/processed/limit")
HGRID = np.linspace(0, 40, 4801)                  # years, monthly-ish step
S_MAX = (1.0, 2.0, 3.0)                           # % of GDP
DR = np.round(np.arange(0.0, 6.01, 0.05), 2)      # pp
MAX_REPORT = 40.0


def clock(tau, w, ix, zero, g):
    F = exact_F(np.asarray(tau, float), np.asarray(w, float), HGRID)
    P = 1 - (1 - F) * np.exp(-g * HGRID)
    nom = ~np.asarray(ix, bool)
    Pn = 1 - (1 - exact_F(np.asarray(tau, float)[nom], np.asarray(w, float)[nom], HGRID)) * np.exp(-g * HGRID)
    E = np.asarray(w)[nom].sum() / np.sum(w) * (1 - Pn) + zero / np.sum(w)
    return P, E


def variants():
    lm = pd.read_csv(OUT / "limit_map_1980_2025.csv").set_index("year")
    x5, l5 = portfolio(2025)
    g, r, b = lm.loc[2025, "g_forward"], lm.loc[2025, "r"], lm.loc[2025, "b"]
    rbar0 = average_rate(2025, x5, l5)[0] / 100
    priv = (x5.par - x5.soma_par).values
    tau5 = np.r_[x5.tau.values, OVERNIGHT]
    ix5 = np.r_[(x5.kind == "tips").values, False]
    w5 = np.r_[priv, l5.reserves + l5.reverse_repo]
    z = b * l5.currency / w5.sum()
    keep = l5.currency / x5.soma_par.sum()
    w_noqe = np.r_[x5.par.values - x5.soma_par.values * keep, 0.0]
    x7, l7 = portfolio(2007)
    paid7 = 2007 >= IOR_START
    w7 = np.r_[(x7.par - x7.soma_par).values, l7.reverse_repo + (l7.reserves if paid7 else 0.0)]
    tau7 = np.r_[x7.tau.values, OVERNIGHT]
    ix7 = np.r_[(x7.kind == "tips").values, False]
    zero5 = l5.currency
    out = {
        "Consolidated, end-2025": clock(tau5, w5, ix5, zero5, g),
        "No QE, end-2025": clock(tau5, w_noqe, ix5, zero5 * w_noqe.sum() / w5.sum(), g),
        "End-2007 clock": clock(tau7, w7, ix7, zero5 * w7.sum() / w5.sum(), g),
    }
    return out, {"g": g, "r": r, "b": b, "rbar0": rbar0, "z": z}


def time_to_limit(P, E, par, dr, s_max, dpi=0.0):
    rbar = par["rbar0"] + (par["r"] + dr / 100 - par["rbar0"]) * P
    s_req = 100 * ((rbar - par["g"]) * par["b"] - par["g"] * par["z"] - dpi / 100 * par["b"] * E)
    hit = np.nonzero(s_req > s_max)[0]
    return HGRID[hit[0]] if len(hit) else np.inf


def main() -> None:
    v, par = variants()
    rows = []
    for name, (P, E) in v.items():
        for s_max in S_MAX:
            for dpi in (0.0, 2.0):
                if dpi and name == "End-2007 clock":
                    continue
                for dr in DR:
                    rows.append({"clock": name, "s_max": s_max, "dpi": dpi, "dr": dr,
                                 "years": time_to_limit(P, E, par, dr, s_max, dpi)})
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "time_to_limit.csv", index=False)
    # threshold shock: smallest dr that breaks the limit at all (long run)
    s_long = 100 * ((par["r"] - par["g"]) * par["b"] - par["g"] * par["z"])
    print(f"end-2025: b={par['b']:.3f} rbar0={par['rbar0']:.4f} r={par['r']:.4f} g={par['g']:.4f} z={par['z']:.3f}; "
          f"long-run stabilizing balance {s_long:.2f}% of GDP")
    for s_max in S_MAX:
        print(f"  s_max={s_max}%: limit broken in the long run for dr > {(s_max - s_long) / par['b']:.2f} pp")
    t = d[d.dr.isin([2.5, 3.0, 4.0, 5.0])].pivot_table(index=["s_max", "dpi", "dr"], columns="clock", values="years")
    pd.set_option("display.width", 200)
    print(t.round(1).to_string())
    for name, (P, E) in v.items():
        print(name, "P(1), P(2), P(5):", [round(float(np.interp(h, HGRID, P)), 3) for h in (1, 2, 5)])


if __name__ == "__main__":
    main()
