"""Paper figures 1-2 (figure 3 = src/limit/plot_limit_map_long.py)."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.clock.fd5_clock import F_bucketed
from src.clock.inflation_layer import GRID

SURFACE, INK, INK2, GRIDC = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
TREASURY, CONSOL, THIRD = "#2a78d6", "#eb6834", "#1baf7a"
OUT = Path("paper/figures")


def style(ax):
    ax.set_facecolor(SURFACE)
    ax.grid(axis="y", color=GRIDC, lw=0.8)
    ax.spines[["top", "right"]].set_visible(False)


def fig1():
    t = pd.read_csv("data/processed/clock/treasury_clock_yearend.csv")
    t["year"] = pd.to_datetime(t.record_date).dt.year
    c = pd.read_csv("data/processed/clock/consolidated_clock_yearend.csv")
    f = pd.read_csv("data/processed/clock/fd5_clock_1980_2003.csv")
    f = f[f.year <= 2002]
    fp1 = 1 - (1 - f.F1) * np.exp(-0.04)          # P(1) from bucketed F(1); bucket F(1) error ~0 (fd5_clock.py)
    fig, ax = plt.subplots(figsize=(8, 4.2), facecolor=SURFACE)
    style(ax)
    ax.axvspan(1979.5, 2002.5, color=GRIDC, alpha=0.35, lw=0)
    ax.plot(f.year, fp1, color=CONSOL, lw=2, marker="o", ms=4, mfc=SURFACE)
    ax.plot(c.year, c.P_1, color=CONSOL, lw=2, marker="o", ms=4, label="Consolidated with the Fed (1980–2002: privately held, FD-5)")
    ax.plot(t.year, t.P_1, color=TREASURY, lw=2, marker="o", ms=4, label="Treasury only")
    ax.set_ylim(0, 0.65)
    ax.set_ylabel("share reaching the average rate within 1 year", color=INK2)
    ax.set_title("Rollover clock: P(1), share of a permanent rate shock passed to the average\n"
                 "interest rate on debt within one year (g = 4% growth issuance)", loc="left", color=INK, fontsize=10.5)
    ax.legend(frameon=False, loc="lower left", fontsize=9, labelcolor=INK)
    ax.tick_params(colors=INK2)
    fig.tight_layout()
    fig.savefig(OUT / "fig1_rollover_clock.png", dpi=160, facecolor=SURFACE)
    fig.savefig(OUT / "fig1_rollover_clock.svg", facecolor=SURFACE)


def fig2():
    t = pd.read_csv("data/processed/clock/freeze2021_treasury.csv")
    f = pd.read_csv("data/processed/clock/freeze2021_fed_actual.csv")
    t["d"] = pd.to_datetime(t.date)
    f["d"] = pd.to_datetime(f.date)
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 4.2), facecolor=SURFACE)
    for ax in (a, b):
        style(ax)
        ax.tick_params(colors=INK2)
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    a.plot(t.d, t.d_actual, color=INK, lw=2, label="Actual (official)")
    a.plot(t.d, t.d_clock, color=CONSOL, lw=2, ls="--", label="Rollover clock")
    a.plot(t.d, t.d_scalar, color=TREASURY, lw=2, ls=":", label="WAM-only clock")
    a.set_title("A. Treasury average rate on marketable debt\nchange since Dec 2021, pp", loc="left", color=INK, fontsize=10)
    a.legend(frameon=False, fontsize=9, labelcolor=INK)
    b.plot(f.d, f.actual_deferred_asset / 1e3, color=INK, lw=2, label="Actual (H.4.1)")
    b.plot(f.d, f.pred_deferred_asset / 1e3, color=CONSOL, lw=2, ls="--", label="Frozen end-2021 book,\novernight reserves")
    b.set_title("B. Fed deferred asset, $bn", loc="left", color=INK, fontsize=10)
    b.legend(frameon=False, fontsize=9, labelcolor=INK, loc="lower left")
    fig.tight_layout()
    fig.savefig(OUT / "fig2_2022_test.png", dpi=160, facecolor=SURFACE)
    fig.savefig(OUT / "fig2_2022_test.svg", facecolor=SURFACE)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    fig1()
    fig2()
