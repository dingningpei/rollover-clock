"""Does the cross-year comparison survive a debt sensitivity of rates (psi) that changes by regime?

(a) Evidence: Laubach-style estimates by regime. The 5-year forward 5-year Treasury rate (H.15,
    month of each CBO baseline) against CBO's projected debt held by the public five years ahead,
    as % of projected GDP (GDP projected at 4.5% nominal growth before 2008 and 4% after, since
    the baselines file carries no GDP). Changes between consecutive baselines, which remove slow-
    moving trends in the level of rates; regime-specific slopes.
(b) Robustness: psi set separately in four regimes (1980-87, 1988-2007, 2008-21, 2022-25), each
    in {1, 2, 3, 4.5} bp per pp of debt/GDP: 256 combinations. For each, with the paper's
    phi_hat assumptions, check
      - whether 2023-25 still has the largest inflation requirement since 1980, and
      - whether phi* in 2023-25 lies within its 1980-2007 range.
Output: data/processed/limit/psi_regimes_estimates.csv, psi_regimes_grid.csv
"""
from __future__ import annotations

import itertools
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

OUT = Path("data/processed/limit")
REGIMES = {"1980-87": (1980, 1987), "1988-2007": (1988, 2007), "2008-21": (2008, 2021), "2022-25": (2022, 2026)}                # 2026: the February 2026 baseline
GRID = (0.01, 0.02, 0.03, 0.045)


def regime(year: int) -> str:
    return next(k for k, (a, z) in REGIMES.items() if a <= year <= z)


def laubach() -> pd.DataFrame:
    b = pd.read_csv("data/raw/us/cbo_eval/baselines.csv", parse_dates=["baseline_date"])
    g = pd.read_csv("data/raw/us/cbo_eval/actual_GDP.csv").set_index("fiscal_year").GDP
    debt = b[(b.component == "debt") & (b.projected_year_number == 6)]          # five years after the first year
    h = pd.read_csv("data/interim/backtest/h15_monthly.csv").set_index("month")
    rows = []
    for x in debt.itertuples():
        fy0 = x.projected_fiscal_year - 5
        if fy0 - 1 not in g.index:
            continue
        growth = 1.045 if x.baseline_date.year < 2008 else 1.04
        gdp5 = g[fy0 - 1] * growth ** 6
        m = x.baseline_date.strftime("%Y-%m")
        f55 = (10 * h.loc[m, "n10"] - 5 * h.loc[m, "n5"]) / 5
        rows.append({"date": x.baseline_date, "debt5": 100 * x.value / gdp5, "f55": f55})
    d = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    d["d_debt"], d["d_f55"] = d.debt5.diff(), d.f55.diff()
    d["regime"] = [regime(max(t.year, 1980)) if t.year >= 1980 else None for t in d.date]
    out = []
    for lab, k in [("all", d)] + [(r, d[d.regime == r]) for r in REGIMES]:
        k = k.dropna(subset=["d_debt", "d_f55"])
        if len(k) < 5:
            continue
        m = sm.OLS(k.d_f55, sm.add_constant(k.d_debt)).fit(cov_type="HC1")
        out.append({"regime": lab, "n": len(k), "psi_bp": 100 * m.params["d_debt"], "se_bp": 100 * m.bse["d_debt"]})
    return pd.DataFrame(out)


def grid() -> pd.DataFrame:
    lm = pd.read_csv(OUT / "limit_map_1980_2025.csv").set_index("year")
    reg = pd.Series([regime(t) for t in lm.index], index=lm.index)
    rows = []
    for combo in itertools.product(GRID, repeat=len(REGIMES)):
        psi = reg.map(dict(zip(REGIMES, combo)))
        phistar = 1 - lm.g_forward / (lm.r + psi * lm.b)
        rec = {f"psi_{k}": v for k, v in zip(REGIMES, combo)}
        for lab, ph in (("regime", pd.Series(np.where(lm.index <= 2003, 0.39, 0.0), index=lm.index)),
                        ("common0.00", 0.0), ("common0.25", 0.25)):
            dpi = (phistar - ph).clip(lower=0) * lm.ratio10_consol
            recent, other = dpi.loc[2023:2025], dpi.loc[:2022]
            rec[f"top_{lab}"] = bool(recent.max() >= other.max())
            rec[f"dpi2325_{lab}"] = recent.mean()
            rec[f"maxother_{lab}"] = other.max()
            rec[f"argmaxother_{lab}"] = int(other.idxmax())
        pre = phistar.loc[1980:2007]
        rec["phistar_2325"] = phistar.loc[2023:2025].mean()
        rec["phistar_pre_min"], rec["phistar_pre_max"] = pre.min(), pre.max()
        rec["within_pre_range"] = bool(pre.min() <= rec["phistar_2325"] <= pre.max())
        rows.append(rec)
    return pd.DataFrame(rows)


def main() -> None:
    e = laubach()
    e.to_csv(OUT / "psi_regimes_estimates.csv", index=False)
    print("Laubach-style estimates (bp per pp of projected debt/GDP, changes between baselines):")
    print(e.round(2).to_string(index=False))
    g = grid()
    g.to_csv(OUT / "psi_regimes_grid.csv", index=False)
    print(f"\n{len(g)} combinations of regime-specific psi")
    for lab in ("regime", "common0.00", "common0.25"):
        print(f"  phi_hat {lab:11s}: 2023-25 largest since 1980 in {100 * g[f'top_{lab}'].mean():.0f}% "
              f"of combinations; requirement 2023-25 {g[f'dpi2325_{lab}'].min():.2f}-{g[f'dpi2325_{lab}'].max():.2f}")
    print(f"  phi* 2023-25 within its 1980-2007 range in {100 * g.within_pre_range.mean():.0f}% of combinations; "
          f"phi* 2023-25 {g.phistar_2325.min():.2f}-{g.phistar_2325.max():.2f}")
    fail = g[~g.top_regime]
    if len(fail):
        print("\nCombinations where 2023-25 is not the largest (phi_hat regime):")
        print(fail[[c for c in g if c.startswith("psi_")] + ["dpi2325_regime", "maxother_regime",
                                                            "argmaxother_regime"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
