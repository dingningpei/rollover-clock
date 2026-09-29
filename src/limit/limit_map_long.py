"""Two-layer limit map, 1980-2025 (FD-5 buckets 1980-2002; MSPD+SOMA 2003-2025).

g (expected long-run nominal growth): baseline = realized forward 10-year average
nominal GDP growth where available (<= 2015); from 2016, FOMC SEP longer-run median
real GDP growth (December SEP, data/manual/sep_longrun.csv) + 2% inflation objective;
sensitivity = trailing 10-year average.
phi_hat regimes (Auerbach-Yagan 2024): 0.39 through 2003, 0 from 2004; 0.25
(Bohn-based average) as a middle reference.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .limit_map import gdp

OUT = Path("data/processed/limit")
PSI_BASE, PSI_LO, PSI_HI = 0.03, 0.02, 0.045
G_POST = 0.04
PHI_ALT = (0.0, 0.15, 0.25, 0.35, 0.39)


def phi_hat_regime(year: int) -> float:
    return 0.39 if year <= 2003 else 0.0


def build() -> pd.DataFrame:
    sep = pd.read_csv("data/manual/sep_longrun.csv").set_index("year").longrun_real_gdp
    y = gdp()
    gr = y.pct_change()
    early = pd.read_csv(OUT / "limit_map_fd5_era.csv").set_index("year")
    late = pd.read_csv(OUT / "limit_map_yearend.csv").set_index("year")
    rows = []
    for t in range(1980, 2026):
        src = early if t <= 2002 else late
        r, b = src.loc[t, "r_stock"], src.loc[t, "b_consol"]
        ratio, intP, jb = src.loc[t, "ratio_H10_consol"], src.loc[t, "intP_H10_consol"], src.loc[t, "jump_base_H10_consol"]
        g_tr = gr.loc[t - 9:t].mean()
        g_fw = gr.loc[t + 1:t + 10].mean() if t + 10 <= gr.index.max() else (sep[t] + 2.0) / 100
        g_sep = (sep[t] + 2.0) / 100 if t in sep.index else np.nan
        row = {"year": t, "source": "FD-5 buckets" if t <= 2002 else "MSPD+SOMA", "r": r, "b": b,
               "g_forward": g_fw, "g_trailing": g_tr, "g_sep": g_sep, "ratio10_consol": ratio,
               "ratio5_consol": src.loc[t, "ratio_H5_consol"], "ratio15_consol": src.loc[t, "ratio_H15_consol"],
               "ratio10_narrow_consol": src.loc[t, "ratio_narrow_H10_consol"],
               "ratio10_treasury": late.loc[t, "ratio_H10_treasury"] if t in late.index else np.nan,
               "intP_consol": intP, "jump_base_consol": jb}
        row["phistar"] = 1 - g_fw / (r + PSI_BASE * b)
        band = [1 - g / (r + p * b) for g in (g_fw, g_tr) for p in (PSI_LO, PSI_BASE, PSI_HI)]
        row["phistar_lo"], row["phistar_hi"] = min(band), max(band)
        row["phistar_trailing"] = 1 - g_tr / (r + PSI_BASE * b)
        row["phi_hat"] = phi_hat_regime(t)
        row["gap"] = max(row["phistar"] - row["phi_hat"], 0.0)
        row["dpi_to_cover_gap"] = row["gap"] * ratio
        row["dpi_to_cover_gap_H5"] = row["gap"] * row["ratio5_consol"]
        row["dpi_to_cover_gap_H15"] = row["gap"] * row["ratio15_consol"]
        row["dpi_to_cover_gap_narrow"] = row["gap"] * row["ratio10_narrow_consol"]
        # fiscal-response alternatives (paper, Section 5.3): one common phi_hat in every year,
        # and the regime split with other post-2004 values
        for ph in PHI_ALT:
            row[f"dpi_common_{ph:.2f}"] = max(row["phistar"] - ph, 0.0) * ratio
            post = ph if t >= 2004 else 0.39
            row[f"dpi_regime_post_{ph:.2f}"] = max(row["phistar"] - post, 0.0) * ratio
        # one-time permanent price-level jump covering the same gap over H = 10 (undiscounted), % of debt:
        # dp = gap * dr * int_0^H P_r / (N/b + C/b)   (paper, Section 3.4 and Appendix B.4)
        row["dp_jump_to_cover_gap"] = row["gap"] * 1.0 * intP / jb
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    d = build()
    d.to_csv(OUT / "limit_map_1980_2025.csv", index=False)
    print(d[["year", "r", "b", "g_forward", "phistar", "phi_hat", "gap", "ratio10_treasury", "ratio10_consol",
             "ratio10_narrow_consol", "dpi_to_cover_gap", "dpi_to_cover_gap_narrow", "dp_jump_to_cover_gap"]]
          .round(3).to_string(index=False))


if __name__ == "__main__":
    main()
