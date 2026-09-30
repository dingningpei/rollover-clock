"""United States, United Kingdom, Japan: comparison table and Figure 5 (paper, Section 6).

Inputs are the country clocks (g = 4% growth issuance, H = 10), the cross-country fiscal
threshold (src/intl/phi_star.py) and the two 2021-25 inflation tests.
Outputs: data/processed/intl_comparison.csv, paper/figures/fig5_three_countries.{png,svg}.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.paper.figures import CONSOL, GRIDC, INK, INK2, SURFACE, THIRD, TREASURY, style

OUT = Path("data/processed")
FIG = Path("paper/figures")
COLOR = {"United States": TREASURY, "United Kingdom": CONSOL, "Japan": THIRD}


def panel() -> pd.DataFrame:
    il = pd.read_csv("data/processed/clock/inflation_layer_yearend.csv")
    il = il[il.year >= 2007].pivot(index="year", columns="version")
    cc = pd.read_csv("data/processed/clock/consolidated_clock_yearend.csv").set_index("year")
    tc = pd.read_csv("data/processed/clock/treasury_clock_yearend.csv")
    tc["year"] = pd.to_datetime(tc.record_date).dt.year
    tc = tc.set_index("year")
    us = pd.DataFrame({"P1_own": tc.P_1, "P1_consol": cc.P_1, "wam_own": tc.wam_years, "wam_consol": cc.wam_years,
                       "overnight_share": cc.overnight_share, "zero_ratio": il["cur_ratio", "consolidated"],
                       "indexed_share": il["tips_share", "consolidated"],
                       "ratio_own": il["ratio_H10", "treasury"], "ratio_consol": il["ratio_H10", "consolidated"],
                       "ratio_consol_nocur": il["ratio_nocur_H10", "consolidated"]}).loc[2007:]
    us["country"] = "United States"
    u = pd.read_csv("data/processed/uk/uk_clock.csv").set_index("year")
    uk = pd.DataFrame({"country": "United Kingdom", "b_own": u.b_gross, "b_consol": u.b_consol,
                       "cb_share": u.apf_share, "P1_own": u.P1_gross_g4, "P1_consol": u.P1_consol_g4,
                       "wam_own": u.wam_gross, "wam_consol": u.wam_consol, "overnight_share": u.overnight_share,
                       "zero_ratio": u.zero_ratio, "indexed_share": u.indexed_share_consol,
                       "ratio_own": u.ratio_gross_g4, "ratio_consol": u.ratio_consol_g4,
                       "ratio_consol_nocur": u.ratio_consol_nocur_g4})
    j = pd.read_csv("data/processed/jp/jp_clock.csv").set_index("fy")
    jp = pd.DataFrame({"country": "Japan", "b_own": j.b_gross, "b_consol": j.b_consol, "cb_share": j.boj_share_jgb,
                       "P1_own": j.P1_gross_g4, "P1_consol": j.P1_consol_g4, "wam_own": j.wam_gross,
                       "wam_consol": j.wam_consol, "overnight_share": j.overnight_share, "zero_ratio": j.zero_ratio,
                       "indexed_share": j.indexed_share, "ratio_own": j.ratio_gross_g4,
                       "ratio_consol": j.ratio_consol_g4, "ratio_consol_nocur": j.ratio_consol_nocur_g4})
    d = pd.concat([x.rename_axis("year").reset_index() for x in (us, uk, jp)], ignore_index=True)
    ps = pd.read_csv(OUT / "intl_phistar.csv").replace({"country": {"Japan (FY)": "Japan"}})
    keep = ["country", "year", "r", "g", "b", "phistar_0bp", "phistar_1bp", "phistar_3bp", "phistar_4.5bp",
            "dpi_3bp_phihat_0.00", "dpi_3bp_phihat_0.25"]
    d = d.merge(ps[keep].rename(columns={"b": "b_phistar"}), on=["country", "year"], how="left")
    d["b_consol"] = d.b_consol.fillna(d.b_phistar)                  # U.S.: consolidated b from the limit map
    return d[["country", "year"] + [c for c in d.columns if c not in ("country", "year", "b_phistar")]]


def figure(d: pd.DataFrame) -> None:
    fig = plt.figure(figsize=(10, 8.4), facecolor=SURFACE)
    gs = fig.add_gridspec(2, 2)
    a, b, c = fig.add_subplot(gs[0, :]), fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])
    for ax in (a, b, c):
        style(ax)
        ax.tick_params(colors=INK2)
    for k, x in d.groupby("country", sort=False):
        mk = "o" if len(x) < 8 else None
        a.plot(x.year, x.ratio_consol, color=COLOR[k], lw=2, marker=mk, ms=4, label=k)
        a.plot(x.year, x.ratio_own, color=COLOR[k], lw=1.4, ls="--", marker=mk, ms=3)
    a.plot([], [], color=INK2, lw=2, label="consolidated")
    a.plot([], [], color=INK2, lw=1.4, ls="--", label="own debt")
    a.set_ylim(0, 3.3)
    a.set_xticks(range(2008, 2026, 4))
    a.set_title("A. Inflation-layer ratio ∫P/∫E, H = 10\n(Japan: fiscal years)", loc="left", color=INK, fontsize=10)
    a.legend(frameon=False, fontsize=9, labelcolor=INK, loc="lower left", ncol=2)
    psi = np.linspace(0, 0.05, 101)
    ps = pd.read_csv(OUT / "intl_phistar.csv")
    for k in COLOR:
        x = ps[ps.country == k].sort_values("year").iloc[-1]
        b.plot(psi * 1e4 / 100, 1 - x.g / (x.r + psi * x.b), color=COLOR[k], lw=2,
               label=f"{k} {int(x.year)}: r − g = {100 * (x.r - x.g):+.1f}pp, b = {x.b:.2f}")
    b.axhline(0, color=INK2, lw=0.8)
    b.axvline(3, color=GRIDC, lw=1.2, ls=":")
    b.set_ylim(-1.0, 0.85)
    b.set_xlabel("ψ, bp per pp of debt/GDP", color=INK2)
    b.set_title("B. Fiscal threshold φ* = 1 − g/(r + ψb)\n(g = trailing real growth + 2%)", loc="left", color=INK,
                fontsize=10)
    b.legend(frameon=False, fontsize=9, labelcolor=INK, loc="lower right")
    us = pd.read_csv("data/processed/clock/inflation_test_summary.csv")
    uk = pd.read_csv("data/processed/uk/uk_inflation_test_summary.csv")
    for k, x in (("United States", us), ("United Kingdom", uk)):
        c.plot(x.year, x.transfer_D_pct_gdp20, color=COLOR[k], lw=1.4, ls=":", marker="o", ms=3)
        c.plot(x.year, x.transfer_B_pct_gdp20, color=COLOR[k], lw=1.4, ls="--", marker="o", ms=3)
        c.plot(x.year, x.transfer_C_pct_gdp20, color=COLOR[k], lw=2, marker="o", ms=4, label=k)
    c.plot([], [], color=INK2, lw=1.4, ls=":", label="inflation as priced (D)")
    c.plot([], [], color=INK2, lw=1.4, ls="--", label="full Fisher repricing (B)")
    c.plot([], [], color=INK2, lw=2, label="actual yields (C)")
    c.set_xticks(range(2021, 2026))
    c.set_title("C. Transfer from the 2021–25 inflation surprise,\ncumulative, % of 2020 GDP", loc="left",
                color=INK, fontsize=10)
    c.legend(frameon=False, fontsize=9, labelcolor=INK, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIG / "fig5_three_countries.png", dpi=160, facecolor=SURFACE)
    fig.savefig(FIG / "fig5_three_countries.svg", facecolor=SURFACE)


def main() -> None:
    d = panel()
    d.to_csv(OUT / "intl_comparison.csv", index=False)
    figure(d)
    pd.set_option("display.width", 250)
    sel = d[d.year.isin([2007, 2012, 2019, 2020, 2021, 2023, 2024, 2025])]
    print(sel.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
