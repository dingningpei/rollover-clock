"""Level version of the inflation layer (paper, Section 5.4).

How much sustained surprise inflation would hold consolidated debt/GDP constant over H
years, given the actual (or projected) primary balance and today's rates?

  shortfall(h) = (rbar(h) - g) * b - s(h),     rbar(h) = rbar0 + (r - rbar0) * P(h)
  dpi_level(H) = int_0^H shortfall / ( b * int_0^H E ),

with the rollover clock P and the erosion share E of Section 3.3 (inflation_layer.layer).
rbar0 is the average rate on the consolidated interest-bearing stock at the year-end:
each privately held security at its own rate, calibrated to the official average rate on
marketable debt (TIPS: real coupon + 2% expected inflation),
reserves at the interest rate on reserves, reverse repos at the ON RRP rate (EFFR before
2021). r is the marginal cost of the existing structure (limit map), g expected growth.
s(h): end-2025, CBO's August 2026 baseline primary balance for FY2026-2036; other years,
the actual primary balance held constant. Both exclude Fed remittances where known and
are shares of potential GDP (CBO). Discounted variant: flows weighted by exp(-(r - g) h).
The fiscal accounts are otherwise held fixed in real terms: no bracket creep or lags in
indexation, which would reduce the requirement.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.clock.backtest import IN, security_rates
from src.clock.consolidated_clock import OVERNIGHT
from src.clock.freeze_2021 import policy_rates
from src.clock.inflation_layer import GRID, IOR_START, exact_F
from src.fiscal.fiscal_response import CBO_FILE
from src.limit.decompose import portfolio

OUT = Path("data/processed/limit")
TIPS_INFLATION = 2.0          # pp, expected inflation accrual on TIPS principal
YEARS = (2007, 2019, 2025)
H = 10.0


def cbo_primary() -> pd.DataFrame:
    """CBO primary balance (with stabilizers), % of potential GDP, by fiscal year; projections 2026-36."""
    x = pd.read_excel(CBO_FILE, "2. Def or Surp - % of GDP", header=None)
    x = x[pd.to_numeric(x[0], errors="coerce").between(1960, 2040)]
    return pd.DataFrame({"primary": pd.to_numeric(x[3]).values + pd.to_numeric(x[16]).values},
                        index=x[0].astype(int).values)


def overnight_rates(year: int) -> tuple[float, float]:
    """(rate on reserves, rate on reverse repos) at the year-end, percent."""
    if year >= 2021:
        p = policy_rates()
        p = p[p.index <= f"{year}-12-31"].iloc[-1]
        return float(p.iorb), float(p.rrp)
    h = pd.read_csv(IN / "h15_monthly.csv").set_index("month")
    e = float(h.loc[f"{year}-12", "effr"])
    return (e if year >= IOR_START else 0.0), e


def official_rate(year: int) -> float:
    """Treasury's official average interest rate on total marketable debt, December, percent."""
    avg = pd.read_csv(IN / "avg_interest_rates.csv", dtype=str)
    off = avg[avg.security_desc.str.replace(" ", "").eq("TotalMarketable") & avg.record_date.str.startswith(f"{year}-12")]
    return float(off.avg_interest_rate_amt.iloc[0])


def average_rate(year: int, x: pd.DataFrame, lev) -> tuple[float, float]:
    """Average rate on the consolidated interest-bearing stock, percent, and the calibration
    offset. Security-level rates (TIPS at the real coupon) are shifted by a constant so that
    their par-weighted average over all marketable debt equals the official average rate;
    the security-level average is 0.2-0.3 pp lower. TIPS then add expected inflation."""
    market = pd.read_csv("data/interim/mspd/table3_market_yearend.csv", dtype=str)
    rates = security_rates(market)
    rates = rates[rates.record_date.dt.year == year][["cusip", "rate"]]
    y = x.merge(rates, on="cusip", how="left")
    offset = official_rate(year) - (y.par * y.rate).sum() / y.par.sum()
    y["rate"] = y.rate + offset + np.where(y.kind == "tips", TIPS_INFLATION, 0.0)
    priv = y.par - y.soma_par
    ior, rrp = overnight_rates(year)
    res = lev.reserves if year >= IOR_START else 0.0
    num = (priv * y.rate).sum() + res * ior + lev.reverse_repo * rrp
    return num / (priv.sum() + res + lev.reverse_repo), offset


def level(year: int, s_path: np.ndarray, H: float = H) -> dict:
    x, lev = portfolio(year)
    lm = pd.read_csv(OUT / "limit_map_1980_2025.csv").set_index("year").loc[year]
    r, g, b = lm.r, lm.g_forward, lm.b
    paid = year >= IOR_START
    priv = (x.par - x.soma_par).values
    on = lev.reverse_repo + (lev.reserves if paid else 0.0)
    zero = lev.currency + (0.0 if paid else lev.reserves)
    tau, w = np.r_[x.tau.values, OVERNIGHT], np.r_[priv, on]
    ix = np.r_[(x.kind == "tips").values, False]
    h = GRID[GRID <= H + 1e-9]
    P = 1 - (1 - exact_F(tau, w, GRID)[: len(h)]) * np.exp(-g * h)
    Pn = 1 - (1 - exact_F(tau[~ix], w[~ix], GRID)[: len(h)]) * np.exp(-g * h)
    E = (w[~ix].sum() / w.sum()) * (1 - Pn) + zero / w.sum()
    rbar0, offset = average_rate(year, x, lev)
    rbar0 /= 100
    rbar = rbar0 + (r - rbar0) * P
    s = np.interp(h, np.arange(len(s_path)) + 0.5, s_path) / 100       # annual path, mid-year
    shortfall = (rbar - g) * b - s
    out = {"year": year, "b": b, "r": r, "g": g, "rbar0": rbar0, "rate_offset_pp": offset, "s_first": s_path[0], "s_mean": s_path.mean(),
           "stabilizing_s_0": (rbar0 - g) * b * 100, "stabilizing_s_H": (rbar[-1] - g) * b * 100,
           "shortfall_mean_pct_gdp": 100 * np.trapezoid(shortfall, h) / H,
           "erosion_share_mean": np.trapezoid(E, h) / H}
    for tag, wt in (("", np.ones_like(h)), ("_disc", np.exp(-(r - g) * h))):
        out[f"dpi_level{tag}"] = 100 * np.trapezoid(wt * shortfall, h) / (b * np.trapezoid(wt * E, h))
    return out


def main() -> None:
    cbo = cbo_primary()
    remit = pd.read_csv("data/processed/fiscal/fiscal_response_data_cbo.csv", index_col=0).remit
    gdp = pd.read_csv("data/raw/bea/NipaDataA.txt", dtype=str)
    gdp.columns = [c.strip() for c in gdp.columns]
    gdp = gdp[gdp.iloc[:, 0] == "A191RC"]
    gdp = pd.Series(pd.to_numeric(gdp.iloc[:, 2].str.replace(",", "")).values, index=gdp.iloc[:, 1].astype(int).values)
    rows = []
    for y in YEARS:
        if y == 2025:
            path = cbo.loc[2026:2035, "primary"].values                     # CBO baseline, FY2026-2035
            label = "CBO baseline primary balance, FY2026-35"
        else:
            path = np.repeat(cbo.loc[y, "primary"] - remit.get(y, 0.0), int(H))
            label = f"actual FY{y} primary balance (ex Fed remittances), held constant"
        for HH in (5.0, 10.0):
            row = level(y, path[: int(HH)], HH)
            row.update({"H": HH, "primary_path": label, "gdp_bn": gdp[y] / 1e3})
            row["erosion_per_pp_bn"] = row["b"] * row["gdp_bn"] * row["erosion_share_mean"] / 100
            rows.append(row)
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "level_metric.csv", index=False)
    pd.set_option("display.width", 220)
    print(d.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
