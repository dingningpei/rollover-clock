"""Counterfactuals at end-2025 for the two-layer limit (Step 6).

Baseline: consolidated end-2025 portfolio (MSPD by CUSIP net of SOMA + reserves + RRP;
currency in the zero-interest base), r = stock-structure rate, b = consolidated debt/GDP,
g = 3.8% (Dec-2025 SEP longer-run real growth 1.8% + 2%), psi = 3bp,
phi_hat = 0 (post-2004), +1pp permanent rate rise, H = 10.

No QE: the Fed's Treasury holdings shrink to its currency liability (the pre-2008 funding
structure: SOMA Treasuries ~ currency, no MBS, negligible reserves); the rest returns to
private holders pro rata to the SOMA maturity structure; reserves and RRP go to zero.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.clock.consolidated_clock import OVERNIGHT, soma_by_cusip
from src.clock.inflation_layer import layer
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


def metrics(tau, w, ix, cur, r, b, g=G_SEP_2025, psi=0.03, phi_hat=0.0, dr=1.0):
    lay = layer(tau, w, ix, cur, H, g)
    phistar = 1 - g / (r + psi * b)
    gap = max(phistar - phi_hat, 0.0)
    return {"b": b, "ratio10": lay["ratio"], "phistar": phistar, "gap": gap,
            "dpi_gap_pp_per_yr": gap * dr * lay["ratio"],
            "dp_jump_pct": gap * dr * lay["intP"] / lay["jump_base"]}


def main() -> None:
    x, lev = portfolio_2025()
    lm = pd.read_csv(OUT / "limit_map_1980_2025.csv").set_index("year").loc[Y]
    r, b = lm.r, lm.b
    priv = (x.par - x.soma_par).values
    on = lev.reserves + lev.reverse_repo
    tips = (x.kind == "tips").values
    base_tau, base_w, base_ix = np.r_[x.tau.values, OVERNIGHT], np.r_[priv, on], np.r_[tips, False]
    rows = []

    def add(name, tau=base_tau, w=base_w, ix=base_ix, cur=lev.currency, adjust_b=False, **kw):
        """adjust_b: debt/GDP moves with the interest-bearing stock (otherwise composition only)."""
        bb = b * np.sum(w) / np.sum(base_w) if adjust_b else kw.pop("b", b)
        rows.append({"scenario": name, "b_adjusted": adjust_b,
                     **metrics(tau, w, ix, cur, kw.pop("r", r), bb, **kw)})

    def private_plus(returned, overnight):
        """Consolidated stock after SOMA Treasuries `returned` go back to private holders pro rata."""
        return np.r_[priv + x.soma_par.values * returned / x.soma_par.sum(), overnight]

    add("Baseline (consolidated, phi_hat=0)")
    # b is held at baseline to isolate the change in composition (the reserves that fund the
    # Fed's MBS would disappear with the MBS, lowering b and phi* slightly)
    add("No QE: Fed Treasuries = currency, no reserves", w=private_plus(x.soma_par.sum() - lev.currency, 0.0))
    add("Treasury-only clock (Fed ignored)", tau=x.tau.values, w=x.par.values, ix=tips, cur=0.0)
    # QT: Fed holdings shrink by the reserve reduction; those Treasuries return to private
    # holders pro rata to the SOMA maturity structure; RRP unchanged.
    cut = lev.reserves - 1.9e6
    add("QT: reserves to ~$1.9tn (2019), Treasuries back to private", w=private_plus(cut, on - cut))
    bills = (x.kind == "bill").values
    shift = 0.10 * x.par[bills].sum()
    tau_to = np.r_[x.tau.values, OVERNIGHT, 10.0]
    w_to = np.r_[np.where(bills, priv * (1 - shift / priv[bills].sum()), priv), on, shift]
    add("Treasury terms out: 10% of bills -> 10y", tau=tau_to, w=w_to, ix=np.r_[tips, False, False])
    add("No QE, and debt/GDP without the MBS-funding reserves", w=private_plus(x.soma_par.sum() - lev.currency, 0.0),
        adjust_b=True)
    # --- policy scenarios (paper, Section 6) ---
    res, rrp = lev.reserves, lev.reverse_repo
    for k, lab in ((1.0, "Ending interest on reserves"), (0.5, "Tiering: 50% of reserves unremunerated"),
                   (0.25, "Tiering: 25% of reserves unremunerated")):
        for adj in (False, True):
            add(lab + (", debt/GDP adjusted" if adj else ""), w=np.r_[priv, rrp + (1 - k) * res],
                cur=lev.currency + k * res, adjust_b=adj)
    # Fed shifts its Treasury portfolio to bills (TBAC 2026 charge): SOMA bill share to 50%;
    # coupons sold pro rata to private holders, bills bought pro rata from private holders
    soma = x.soma_par.values
    sb = soma[bills].sum()
    move = 0.5 * soma.sum() - sb
    soma_new = np.where(bills, soma + priv * move / priv[bills].sum(),
                        soma * (1 - move / soma[~bills].sum()))
    add("Fed Treasury portfolio 50% bills (from 5.5%)", w=np.r_[x.par.values - soma_new, on])
    # Treasury raises the bill share of marketable debt; coupons (incl. TIPS, FRNs) shrink pro rata
    for target in (0.25, 0.30):
        d_bills = (target - x.par[bills].sum() / x.par.sum()) * x.par.sum()
        pb, pc = priv[bills].sum(), priv[~bills].sum()
        w_b = np.where(bills, priv * (1 + d_bills / pb), priv * (1 - d_bills / pc))
        add(f"Treasury bill share {target:.0%} (from 21.6%)", w=np.r_[w_b, on])
    add("Fiscal response restored (phi_hat=0.39)", phi_hat=0.39)
    add("Fiscal response at intermediate 0.25", phi_hat=0.25)
    add("Convenience yield lost 50bp (r+0.5pp)", r=r + 0.005)
    add("Convenience yield lost 100bp (r+1pp)", r=r + 0.010)
    add("Growth g=4% (earlier assumption)", g=0.04)
    add("Lower growth g=3.5%", g=0.035)
    add("psi = 2bp (CBO)", psi=0.02)
    add("psi = 4.5bp", psi=0.045)
    d = pd.DataFrame(rows)
    d["change_vs_baseline"] = d.dpi_gap_pp_per_yr / d.dpi_gap_pp_per_yr.iloc[0] - 1
    d.to_csv(OUT / "counterfactuals_2025.csv", index=False)
    print(f"end-2025: r={r:.4f}, b={b:.3f}, reserves+RRP=${on/1e6:.2f}tn, currency=${lev.currency/1e6:.2f}tn, "
          f"SOMA Treasuries=${x.soma_par.sum()/1e6:.2f}tn")
    print(d.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
