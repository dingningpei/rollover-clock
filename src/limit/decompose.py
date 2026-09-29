"""Decompose the rise of the consolidated inflation-layer ratio, end-2007 to end-2025
(paper, Section 5.2). A chain of counterfactual balance sheets, H = 10, g = 4%:

  R0  end-2007 actual (zero-interest base = currency + unremunerated reserves)
  R1  end-2007 with the zero-interest base scaled to its end-2025 share of b
      -> currency falling relative to debt
  R2  end-2025 without QE: the Fed holds Treasuries equal to its currency, pro rata to
      the end-2025 SOMA maturity structure; no reserves or reverse repos
      -> Treasury's own maturity and TIPS choices (and the maturity of the Fed's
         currency-backed holdings), 2007 -> 2025
  R3  end-2025 actual
      -> QE: reserves, not currency, fund the rest of the Fed's book

Second ordering: the QE step measured on the end-2007 structure. QE shows up in how the
Fed's book is funded, not in its share of Treasuries (16% of marketable debt in 2007, 14%
in 2025). On the end-2007 balance sheet, the Fed's Treasuries are scaled to the end-2025
ratio of SOMA Treasuries to currency (pro rata to the end-2007 SOMA maturity structure),
and remunerated overnight liabilities are added in the end-2025 proportion to currency:
the excess Treasuries plus the reserves that fund the Fed's other assets (MBS).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.clock.consolidated_clock import OVERNIGHT, soma_by_cusip
from src.clock.inflation_layer import IOR_START, layer
from src.clock.treasury_clock import G_BASELINE, securities

OUT = Path("data/processed/limit")
H = 10.0


def portfolio(year: int):
    sec = securities(pd.read_csv("data/interim/mspd/table3_market_yearend.csv", dtype=str))
    x = sec[sec.record_date.dt.year == year].copy()
    soma = soma_by_cusip(pd.read_csv("data/interim/fed/soma_tsy_yearend.csv", dtype=str))
    s = soma[soma.year.astype(int) == year]
    lev = pd.read_csv("data/interim/fed/h41_wednesday_levels.csv")
    lev = lev.loc[lev.date <= s.asOfDate.iloc[0]].iloc[-1]
    x = x.merge(s[["cusip", "soma_par"]], on="cusip", how="left").fillna({"soma_par": 0})
    return x, lev


def ratio(x, soma_par, overnight, zero):
    """Consolidated ratio for a Treasury portfolio x, Fed holdings soma_par by security,
    overnight interest-bearing liabilities and the zero-interest base."""
    priv = x.par.values - soma_par
    lay = layer(np.r_[x.tau.values, OVERNIGHT], np.r_[priv, overnight], np.r_[(x.kind == "tips").values, False],
                zero, H, G_BASELINE)
    return lay["ratio"], priv.sum() + overnight


def main() -> None:
    x7, l7 = portfolio(2007)
    x5, l5 = portfolio(2025)
    paid7 = 2007 >= IOR_START
    z7 = l7.currency + (0.0 if paid7 else l7.reserves)
    o7 = l7.reverse_repo + (l7.reserves if paid7 else 0.0)
    R0, b7 = ratio(x7, x7.soma_par.values, o7, z7)
    R3, b5 = ratio(x5, x5.soma_par.values, l5.reserves + l5.reverse_repo, l5.currency)
    zshare25 = l5.currency / b5
    R1, _ = ratio(x7, x7.soma_par.values, o7, zshare25 * b7)
    # No QE at end-2025: Fed Treasuries = currency; b held at baseline (composition only)
    keep = l5.currency / x5.soma_par.sum()
    returned = x5.soma_par.values * (1 - keep)
    R2, _ = ratio(x5, x5.soma_par.values * keep, 0.0, l5.currency)
    # second ordering: QE funding structure on the end-2007 balance sheet
    share25 = x5.soma_par.sum() / x5.par.sum()
    t_per_c = x5.soma_par.sum() / l5.currency                       # SOMA Treasuries per $ of currency
    other_per_c = (l5.reserves + l5.reverse_repo - (x5.soma_par.sum() - l5.currency)) / l5.currency
    scale = t_per_c * l7.currency / x7.soma_par.sum()
    extra_t = x7.soma_par.sum() * (scale - 1)
    R0q, _ = ratio(x7, x7.soma_par.values * scale, o7 + extra_t + other_per_c * l7.currency, z7)
    rows = [
        {"step": "end-2007 actual", "ratio": R0},
        {"step": "currency falls relative to debt (to its end-2025 share)", "ratio": R1, "contribution": R1 - R0},
        {"step": "Treasury maturity and TIPS, 2007 -> 2025 (no-QE Fed)", "ratio": R2, "contribution": R2 - R1},
        {"step": "QE: reserves fund the rest of the Fed's book", "ratio": R3, "contribution": R3 - R2},
        {"step": "end-2025 actual", "ratio": R3, "contribution": R3 - R0},
        {"step": "alt. ordering: QE funding on the end-2007 balance sheet", "ratio": R0q, "contribution": R0q - R0},
    ]
    d = pd.DataFrame(rows)
    d["share_of_rise"] = d.contribution / (R3 - R0)
    d.to_csv(OUT / "decomposition_2007_2025.csv", index=False)
    print(f"b 2007 ${b7/1e6:.2f}tn, zero-interest share {z7/b7:.3f}; b 2025 ${b5/1e6:.2f}tn, currency share {zshare25:.3f}")
    print(f"SOMA share of marketable: 2007 {x7.soma_par.sum()/x7.par.sum():.3f}, 2025 {share25:.3f}; "
          f"SOMA/currency 2007 {x7.soma_par.sum()/l7.currency:.2f}, 2025 {t_per_c:.2f}; other overnight per currency {other_per_c:.2f}")
    print(d.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
