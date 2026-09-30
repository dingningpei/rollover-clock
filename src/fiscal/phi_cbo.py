"""Identify the fiscal response phi from CBO baseline updates, 1992-2026 (Auerbach-Yagan design;
same specification as the UK in src/fiscal/phi_obr.py).

Data: CBO's own record of its baselines and of the changes between them, by source (legislative,
economic, technical), from github.com/US-CBO/eval-projections (input_data). For baseline update e,
over fiscal years 1-5 after the update's fiscal year, as % of GDP (positive = larger deficit):
  policy_e   legislative change in the primary deficit
             = legislative change in the deficit - legislative change in net interest
  di_e       economic + technical change in net interest
  receipts_e economic + technical change in the revenue shortfall, and
  nonint_e   economic + technical change in non-interest outlays, both from the change in
             consecutive baselines less the legislative change (where both baselines are published).
    policy_e = a + beta * di_e + controls + u_e,   phi = -beta.
IV: di is instrumented with the change in market yields between the two baseline dates
(H.15 10-year and 3-month, monthly averages), which moves interest projections and is outside
Congress's control.
Output: data/processed/fiscal/phi_cbo_events.csv, phi_cbo.csv
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src.fiscal.phi_panel import tsls

RAW = Path("data/raw/us/cbo_eval")
OUT = Path("data/processed/fiscal")
H = range(1, 6)


def fiscal_year(date: pd.Timestamp) -> int:
    return date.year + (date.month >= 10)


def gdp() -> pd.Series:
    g = pd.read_csv(RAW / "actual_GDP.csv").set_index("fiscal_year").GDP
    last = g.index.max()
    for y in range(last + 1, last + 12):                         # beyond the data: 4% nominal growth
        g.loc[y] = g.loc[y - 1] * 1.04
    return g


def events() -> pd.DataFrame:
    c = pd.read_csv(RAW / "baseline_changes.csv", parse_dates=["changes_baseline_date"])
    b = pd.read_csv(RAW / "baselines.csv", parse_dates=["baseline_date"])
    Y = gdp()

    def chg(comp, cat, kind):
        x = c[(c.component == comp) & (c.category == cat) & (c.change_category.isin(kind))]
        return x.groupby(["changes_baseline_date", "projected_fiscal_year"]).value.sum()

    def base(comp, cat):
        x = b[(b.component == comp) & (b.category == cat) & (b.subcategory == cat)]
        return x.set_index(["baseline_date", "projected_fiscal_year"]).value

    leg_def, leg_ni = chg("deficit", "Total", ["Legislative"]), chg("outlay", "Net Interest", ["Legislative"])
    non_ni = chg("outlay", "Net Interest", ["Economic", "Technical"])
    leg_rev, leg_out = chg("revenue", "Total", ["Legislative"]), chg("outlay", "Total", ["Legislative"])
    rev, out = base("revenue", "Total"), base("outlay", "Total")
    bdates = sorted(b.baseline_date.unique())
    rows = []
    for e in sorted(non_ni.index.get_level_values(0).unique()):
        fy0 = fiscal_year(e)
        ys = [fy0 + h for h in H]
        pct = lambda s: np.mean([s.get((e, y), np.nan) / Y[y] * 100 for y in ys])
        rec = {"date": e, "fy0": fy0, "policy": pct(leg_def) - pct(leg_ni), "di": pct(non_ni),
               "leg_ni": pct(leg_ni)}
        if e in bdates and bdates.index(e) > 0:
            p = bdates[bdates.index(e) - 1]
            dv = lambda s: np.array([s.get((e, y), np.nan) - s.get((p, y), np.nan) for y in ys])
            lr = np.array([leg_rev.get((e, y), 0.0) for y in ys])
            lo = np.array([leg_out.get((e, y), 0.0) for y in ys])
            ni = np.array([non_ni.get((e, y), 0.0) for y in ys])
            y_ = np.array([Y[y] for y in ys])
            rec["receipts"] = float(np.nanmean(-(dv(rev) - lr) / y_ * 100))          # shortfall: + = worse
            rec["nonint"] = float(np.nanmean((dv(out) - lo - ni) / y_ * 100))
            rec["prev"] = p
        rows.append(rec)
    d = pd.DataFrame(rows)
    # market yields between consecutive update dates
    h = pd.read_csv("data/interim/backtest/h15_monthly.csv").set_index("month")
    m = d.date.dt.strftime("%Y-%m")
    prev = m.shift(1)
    d["d10"] = [h.loc[a, "n10"] - h.loc[p_, "n10"] if isinstance(p_, str) else np.nan for a, p_ in zip(m, prev)]
    d["d3m"] = [h.loc[a, "n0.25"] - h.loc[p_, "n0.25"] if isinstance(p_, str) else np.nan for a, p_ in zip(m, prev)]
    return d


def ols(d, xs, y="policy"):
    k = d.dropna(subset=[y] + xs)
    m = sm.OLS(k[y], sm.add_constant(k[xs])).fit(cov_type="HC1")
    return {"spec": "OLS " + "+".join(xs), "n": int(m.nobs), "phi": -m.params["di"], "se": m.bse["di"], "F": np.nan}


def iv(d, z, ctl, y="policy"):
    k = d.dropna(subset=[y, "di"] + z + ctl)
    W = np.column_stack([np.ones(len(k))] + [k[c].values for c in ctl])
    fs = sm.OLS(k.di, sm.add_constant(k[z + ctl])).fit(cov_type="HC1")
    F = float(fs.f_test(", ".join(f"{v} = 0" for v in z)).fvalue)
    b, se = tsls(k[y].values, k[["di"]].values, W, k[z].values, np.arange(len(k)))
    return {"spec": f"IV({'+'.join(z)}) ctl {'+'.join(ctl) or '-'}", "n": len(k), "phi": -float(b[0]),
            "se": float(se[0]), "F": F}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = events()
    d["policy_next"] = d.policy.shift(-1)
    d["policy_2"] = d.policy + d.policy_next
    d.to_csv(OUT / "phi_cbo_events.csv", index=False)
    rows = []
    for lab, k in (("all", d), ("pre-2004", d[d.date < "2004-01-01"]), ("2004-", d[d.date >= "2004-01-01"]),
                   ("2004- excl 2020-21", d[(d.date >= "2004-01-01") & ~d.date.dt.year.isin([2020, 2021])])):
        for r in (ols(k, ["di"]), ols(k, ["di", "receipts", "nonint"]), iv(k, ["d10", "d3m"], []),
                  iv(k, ["d10", "d3m"], ["receipts", "nonint"]), iv(k, ["d10", "d3m"], [], y="policy_2")):
            rows.append({"sample": lab, **r})
    r = pd.DataFrame(rows)
    r.to_csv(OUT / "phi_cbo.csv", index=False)
    pd.set_option("display.width", 200)
    print(d[["date", "policy", "di", "receipts", "nonint", "d10", "d3m"]].describe().round(2).to_string())
    print(r.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
