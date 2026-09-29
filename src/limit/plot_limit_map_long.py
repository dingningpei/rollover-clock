"""Figure 3: two-layer limit 1980-2025 (paper/figures/fig3_limit_map.{png,svg})."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
TREASURY, CONSOL = "#2a78d6", "#eb6834"


def main() -> None:
    d = pd.read_csv("data/processed/limit/limit_map_1980_2025.csv")
    early, late = d[d.year <= 2002], d[d.year >= 2002]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID,
                         "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2})
    fig, (a, b, c) = plt.subplots(3, 1, figsize=(8.5, 10), sharex=True, facecolor=SURFACE)
    for ax in (a, b, c):
        ax.set_facecolor(SURFACE)
        ax.grid(axis="y", color=GRID, lw=0.8)
        ax.spines[["top", "right"]].set_visible(False)
        ax.axvspan(1979.5, 2002.5, color=GRID, alpha=0.35, lw=0)

    a.fill_between(d.year, d.phistar_lo, d.phistar_hi, color=CONSOL, alpha=0.18, lw=0)
    a.plot(d.year, d.phistar, color=CONSOL, lw=2, marker="o", ms=3.5)
    a.step(d.year, d.phi_hat, where="mid", color=INK, lw=1.2, ls="--")
    a.axhline(0, color=INK2, lw=0.8)
    a.set_ylabel("share of extra interest")
    a.set_title("Fiscal layer: minimum offset φ* (line: forward g, ψ = 3bp; band: trailing/forward g, ψ 2–4.5bp)\n"
                "vs historical offset φ̂ (dashed: 0.39 to 2003, ≈0 since 2004; Auerbach–Yagan)",
                loc="left", color=INK, fontsize=10)
    a.annotate("φ̂", xy=(1981, 0.42), color=INK, fontsize=10)
    a.set_ylim(-1.0, 0.8)

    b.plot(early.year, early.ratio10_consol, color=CONSOL, lw=2, marker="o", ms=4, mfc=SURFACE, label="Consolidated (1980–2002: privately held, FD-5 buckets)")
    b.plot(late.year, late.ratio10_consol, color=CONSOL, lw=2, marker="o", ms=4)
    b.plot(d.year, d.ratio10_treasury, color=TREASURY, lw=2, marker="o", ms=4, label="Treasury only: marketable debt, no currency (MSPD, 2001–)")
    b.set_ylabel("pp inflation per pp rate")
    b.set_title("Inflation layer: sustained surprise inflation per +1pp permanent rate rise (10 years, no fiscal offset)\n"
                "erosion base: non-indexed debt not yet repriced + currency (+ reserves before 2008)",
                loc="left", color=INK, fontsize=10)
    b.legend(frameon=False, loc="upper left", labelcolor=INK, fontsize=9)
    b.set_ylim(0, 4)

    c.bar(d.year, d.dpi_to_cover_gap, color=CONSOL, width=0.75, label="φ̂ = 0.39 to 2003, 0 from 2004 (baseline)")
    c.plot(d.year, d["dpi_common_0.25"], color=INK, lw=1.2, marker="o", ms=2.5, label="φ̂ = 0.25 in every year")
    c.legend(frameon=False, loc="upper left", labelcolor=INK, fontsize=9)
    c.set_ylabel("pp per year")
    c.set_title("Combined: inflation needed to cover the fiscal gap (φ* − φ̂)+ after a +1pp rate rise",
                loc="left", color=INK, fontsize=10)
    for yr in (1981, 2007, 2023):
        v = d.loc[d.year == yr, "dpi_to_cover_gap"].item()
        c.annotate(f"{v:.2f}", xy=(yr, v), xytext=(0, 3), textcoords="offset points", ha="center", color=INK, fontsize=9)
    c.set_xlabel("year-end   (shaded: 1980–2002 from Treasury Bulletin FD-5 maturity buckets)")
    fig.tight_layout()
    targets = [(Path("paper/figures"), "fig3_limit_map")]                  # Figure 3 of the paper
    if Path("docs/figures").is_dir():
        targets.append((Path("docs/figures"), "limit_map_1980_2025"))
    for out, name in targets:
        out.mkdir(parents=True, exist_ok=True)
        fig.savefig(out / f"{name}.png", dpi=160, facecolor=SURFACE)
        fig.savefig(out / f"{name}.svg", facecolor=SURFACE)


if __name__ == "__main__":
    main()
