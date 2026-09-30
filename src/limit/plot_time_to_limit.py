"""Figure 4: years until a permanent rate shock breaks a 2% of GDP ceiling on the primary
surplus, end-2025 fiscal position, by repricing clock (paper/figures/fig4_time_to_limit)."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
CONSOL, THIRD = "#eb6834", "#1baf7a"
S_MAX = 2.0


def main() -> None:
    d = pd.read_csv("data/processed/limit/time_to_limit.csv")
    d = d[(d.s_max == S_MAX) & (d.dr >= 2.2)]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID,
                         "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2})
    fig, ax = plt.subplots(figsize=(8, 4.4), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    series = [("Consolidated, end-2025", 0.0, CONSOL, "-", "Consolidated clock, end-2025"),
              ("No QE, end-2025", 0.0, THIRD, "-", "Without QE"),
              ("Consolidated, end-2025", 2.0, CONSOL, "--", "Consolidated + 2 pp sustained inflation")]
    for clock, dpi, color, ls, label in series:
        x = d[(d.clock == clock) & (d.dpi == dpi)].sort_values("dr")
        y = x.years.replace(np.inf, np.nan)
        ax.plot(x.dr, y, color=color, lw=2, ls=ls, label=label)
        i = y.last_valid_index()
        ax.annotate(label, xy=(x.dr[i], y[i]), xytext=(6, 0), textcoords="offset points",
                    va="center", color=INK, fontsize=9)
    ax.set_xlim(2.2, 7.4)
    ax.set_ylim(0, 16)
    ax.set_xticks([2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6])
    ax.set_xlabel("permanent rise in the marginal interest rate (pp)")
    ax.set_ylabel("years until the limit binds")
    ax.set_title("Time to the limit: years until the debt-stabilizing primary surplus exceeds 2% of GDP\n"
                 "end-2025 debt, rates and growth; only the repricing clock differs", loc="left", color=INK, fontsize=10.5)
    ax.legend(frameon=False, loc="upper right", fontsize=9, labelcolor=INK)
    fig.tight_layout()
    out = Path("paper/figures")
    fig.savefig(out / "fig4_time_to_limit.png", dpi=160, facecolor=SURFACE)
    fig.savefig(out / "fig4_time_to_limit.svg", facecolor=SURFACE)


if __name__ == "__main__":
    main()
