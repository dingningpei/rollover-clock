"""Two-layer limit map by year (paper, Section 5).

Fiscal layer:    phi*_t = 1 - g_t / (r_t + psi * b_t)          (maturity-free)
Inflation layer: dpi_req_t(H) = (1 - phi_hat) * dr * [int P / int (1-P)]_t   (clock-dependent)

r_t: steady-state marginal cost of the existing structure: each outstanding security's
     ORIGINAL tenor priced at the year-t average H.15 yield for that tenor, par-weighted
     (TIPS priced at the nominal yield of the same tenor, i.e. nominal-equivalent; FRN at 3m).
     The gross auction mix is reported as r_mix for comparison (bill-dominated by rollover).
g_t: trailing 10-year average nominal GDP growth (BEA), known at t; sensitivities g = 3.5%, 4%.
b_t: debt/GDP at year-end t; Treasury-only (all marketable) and consolidated
     (marketable held outside the Fed + reserves + reverse repos).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.clock.backtest import IN, col, issuance_mix

OUT = Path("data/processed/limit")
PSI = {"low": 0.02, "base": 0.03, "high": 0.045}         # dr/db, per unit of debt/GDP (paper, Section 5.1)
PHI_HAT = {"none": 0.0, "base": 0.25, "high": 0.7}        # historical 10-year offset share (paper, Section 5.1)


def gdp() -> pd.Series:
    d = pd.read_csv("data/raw/bea/NipaDataA.txt", dtype=str)
    d.columns = [c.strip() for c in d.columns]
    d = d[d.iloc[:, 0] == "A191RC"]
    return pd.Series(pd.to_numeric(d.iloc[:, 2].str.replace(",", "")).values,
                     index=d.iloc[:, 1].astype(int).values)             # $ millions


def new_issue_rate(year: int, auc: pd.DataFrame, h15: pd.DataFrame) -> float:
    mix = issuance_mix(auc, year)
    h = h15[h15.month.str.startswith(str(year))].mean(numeric_only=True)
    return sum(r.share * (h["n0.25"] if r.frn else (h[r.col] if not np.isnan(h[r.col]) else h["n10"]))
               for r in mix.itertuples()) / 100


def stock_rate(year: int, market: pd.DataFrame, h15: pd.DataFrame) -> float:
    m = market[(market.record_date == f"{year}-12-31") & market.security_class2_desc.str.match(r"^[0-9A-Z]{9}$", na=False)].copy()
    m["par"] = pd.to_numeric(m.outstanding_amt, errors="coerce")
    first = m.dropna(subset=["par"]).copy()
    first["tenor"] = (pd.to_datetime(first.maturity_date) - pd.to_datetime(first.issue_date)).dt.days / 365.25
    h = h15[h15.month.str.startswith(str(year))].mean(numeric_only=True)
    frn = first.security_class1_desc.eq("Floating Rate Notes")
    rates = np.array([h["n0.25"] if f else (h[col(tn, False)] if not np.isnan(h[col(tn, False)]) else h["n10"])
                      for tn, f in zip(first.tenor, frn)])
    return float((first.par * rates).sum() / first.par.sum() / 100)


def build() -> pd.DataFrame:
    y = gdp()
    growth = y.pct_change()
    tre = pd.read_csv("data/processed/clock/treasury_clock_yearend.csv")
    tre["year"] = pd.to_datetime(tre.record_date).dt.year
    con = pd.read_csv("data/processed/clock/consolidated_clock_yearend.csv")
    inf = pd.read_csv("data/processed/clock/inflation_layer_yearend.csv")
    auc = pd.read_csv(IN / "auctions.csv", dtype=str)
    h15 = pd.read_csv(IN / "h15_monthly.csv")
    market = pd.read_csv("data/interim/mspd/table3_market_yearend.csv", dtype=str)
    rows = []
    for t in tre.year:
        g10 = growth.loc[t - 9:t].mean()
        r = stock_rate(t, market, h15)
        row = {"year": t, "r_stock": r, "r_mix": new_issue_rate(t, auc, h15), "g_trend": g10, "gdp": y[t],
               "b_treasury": tre.loc[tre.year == t, "par_total"].item() / y[t]}
        c = con[con.year == t]
        row["b_consol"] = c.consol_total.item() / y[t] if len(c) else np.nan
        for v in ("treasury", "consol"):
            for k, psi in PSI.items():
                row[f"phistar_{v}_{k}"] = 1 - g10 / (r + psi * row[f"b_{v}"])
            for gname, g in (("g35", 0.035), ("g40", 0.04)):
                row[f"phistar_{v}_base_{gname}"] = 1 - g / (r + PSI["base"] * row[f"b_{v}"])
        i = inf[inf.year == t]
        for v, name in (("treasury", "treasury"), ("consol", "consolidated")):
            ratio = i[f"dpi_req_H10_{name}"].item() if len(i) and not i[f"dpi_req_H10_{name}"].isna().all() else np.nan
            for k, ph in PHI_HAT.items():
                row[f"dpi_{v}_{k}"] = (1 - ph) * ratio
                # combined two-layer metric: inflation must cover only the fiscal gap (phi* - phi_hat)+
                gap = max(row[f"phistar_{v}_base_g40"] - ph, 0.0) if not np.isnan(row[f"b_{v}"]) else np.nan
                row[f"gap_{v}_{k}"] = gap
                row[f"dpi_gap_{v}_{k}"] = gap * ratio
        rows.append(row)
    return pd.DataFrame(rows)


BUCKET_RATIO_BIAS = -0.157   # FD-5 bucketed minus exact ratio10, private Treasuries 2003-07 (fd5_clock.py)
R_REM_BIAS = -0.0028         # remaining-maturity pricing minus r_stock, mean over 2003-2025


def r_remaining(year: int, shares: np.ndarray, h15: pd.DataFrame) -> float:
    y = h15[h15.month.str.startswith(str(year))].mean(numeric_only=True)
    n30 = y["n30"] if not np.isnan(y["n30"]) else y["n20"]
    n20 = y["n20"] if not np.isnan(y["n20"]) else n30
    return float(np.dot(shares, [y["n1"], y["n3"], y["n7"], (y["n10"] + n20) / 2, n30])) / 100


def build_fd5_era() -> pd.DataFrame:
    """1980-2002 consolidated (= privately held; reserves unremunerated) from FD-5 buckets."""
    f = pd.read_csv("data/processed/clock/fd5_clock_1980_2003.csv")
    f = f[f.year <= 2002]
    y = gdp()
    h15 = pd.read_csv(IN / "h15_monthly.csv")
    rows = []
    for r in f.itertuples():
        sh = np.array([r.share_b1, r.share_b1_5, r.share_b5_10, r.share_b10_20, r.share_b20])
        rr = r_remaining(r.year, sh, h15) - R_REM_BIAS
        b = r.total_private / y[r.year]
        row = {"year": r.year, "source": "FD-5 buckets", "r_stock": rr, "b_consol": b,
               "dpi_consol_none": r.ratio10 - BUCKET_RATIO_BIAS}
        for k, psi in PSI.items():
            row[f"phistar_consol_{k}"] = 1 - 0.04 / (rr + psi * b)
        row["phistar_consol_base_g40"] = row["phistar_consol_base"]
        for k, ph in PHI_HAT.items():
            gap = max(row["phistar_consol_base_g40"] - ph, 0.0)
            row[f"gap_consol_{k}"], row[f"dpi_gap_consol_{k}"] = gap, gap * row["dpi_consol_none"]
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    m = build()
    m["source"] = "MSPD+SOMA"
    early = build_fd5_era()
    early.to_csv(OUT / "limit_map_fd5_era.csv", index=False)
    print(early[["year", "r_stock", "b_consol", "phistar_consol_base_g40", "gap_consol_base", "dpi_consol_none",
                 "dpi_gap_consol_base"]].round(3).to_string(index=False))
    m.to_csv(OUT / "limit_map_yearend.csv", index=False)
    cols = ["year", "r_stock", "r_mix", "g_trend", "b_treasury", "b_consol", "phistar_consol_base",
            "phistar_consol_base_g40", "dpi_treasury_none", "dpi_consol_none", "gap_consol_base", "dpi_gap_consol_base",
            "dpi_gap_treasury_base"]
    print(m[cols].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
