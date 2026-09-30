"""Backtest of the rollover clock against official average interest rates.

From each year-end t (portfolio known at t), project the average interest rate on
marketable Treasury debt month by month for 36 months:
  - securities outstanding at t keep their rate until maturity (bills: issue yield;
    notes/bonds: coupon; TIPS: real coupon; FRNs: 3-month rate + spread, floating);
  - maturing principal plus net new borrowing is reissued each month at that month's
    H.15 yield for the tenor, using the gross issuance mix of year t (auctions).
Realized yields and realized debt totals are used (the test isolates repricing).
Benchmarks: (i) no change; (ii) scalar clock: d rb = (1/WAM + g)(r_new - rb) dt.
Scored on the change in the official 'Total Marketable' average rate from t.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .treasury_clock import G_BASELINE, securities

IN = Path("data/interim/backtest")
OUT = Path("data/processed/clock")
NOM = np.array([1 / 12, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30])
REAL = np.array([5, 7, 10, 20, 30])


def nearest(x: float, grid: np.ndarray) -> float:
    return float(grid[np.abs(grid - x).argmin()])


def col(t: float, real: bool) -> str:
    if real:
        return f"r{nearest(t, REAL):g}"
    c = nearest(t, NOM)
    return {1 / 12: "n0.0833", 0.25: "n0.25", 0.5: "n0.5"}.get(c, f"n{c:g}")


def security_rates(market: pd.DataFrame) -> pd.DataFrame:
    """Rate per (record_date, cusip): issued-amount-weighted across reopening lines."""
    m = market[market.security_class2_desc.str.match(r"^[0-9A-Z]{9}$", na=False)].copy()
    m["w"] = pd.to_numeric(m.issued_amt, errors="coerce").clip(lower=0).fillna(0)
    m["rate"] = np.where(m.security_class1_desc.str.startswith("Bills") | (m.security_class1_desc == "Floating Rate Notes"),
                         pd.to_numeric(m.yield_pct, errors="coerce"), pd.to_numeric(m.interest_rate_pct, errors="coerce"))
    m = m.dropna(subset=["rate"])
    m["rw"] = m.rate * m.w
    g = m.groupby(["record_date", "security_class2_desc"]).agg(rw=("rw", "sum"), w=("w", "sum"), r0=("rate", "first"))
    g["rate"] = np.where(g.w > 0, g.rw / g.w.where(g.w > 0), g.r0)
    g = g.reset_index().rename(columns={"security_class2_desc": "cusip"})
    g["record_date"] = pd.to_datetime(g.record_date)
    return g[["record_date", "cusip", "rate"]]


def issuance_mix(auc: pd.DataFrame, year: int) -> pd.DataFrame:
    a = auc[pd.to_datetime(auc.issue_date).dt.year == year].copy()
    a["amt"] = pd.to_numeric(a.total_accepted, errors="coerce")
    a["tenor"] = (pd.to_datetime(a.maturity_date) - pd.to_datetime(a.issue_date)).dt.days / 365.25
    a["real"] = a.inflation_index_security.eq("Yes")
    a["frn"] = a.floating_rate.eq("Yes")
    a["col"] = [col(t, r) for t, r in zip(a.tenor, a.real)]
    mix = a.groupby(["col", "real", "frn"], as_index=False).agg(amt=("amt", "sum"), tenor=("tenor", "mean"))
    mix["share"] = mix.amt / mix.amt.sum()
    return mix


def project(t_year: int, sec, rates, auc, h15, totals, months=36, realized_totals=True, beyond_last_year=False):
    t0 = pd.Timestamp(f"{t_year}-12-31")
    x = sec[sec.record_date == t0].merge(rates[rates.record_date == t0][["cusip", "rate"]], on="cusip", how="left")
    x = x.dropna(subset=["rate"])
    orig = pd.DataFrame({"par": x.par.values, "rate": x.rate.values, "mat": x.maturity_date.values,
                         "frn": (x.kind == "frn").values, "spread": np.where(x.kind == "frn", x.rate, 0.0)})
    mix = issuance_mix(auc, t_year)
    h = h15.set_index("month")
    cohorts = []                                              # [par, rate, maturity, frn, spread]
    out = []
    wam = (x.par * x.tau).sum() / x.par.sum()
    rb_scalar = None
    for m in range(1, months + 1):
        d = t0 + pd.offsets.MonthEnd(m)
        key = d.strftime("%Y-%m")
        if key not in h.index:
            break
        y = h.loc[key]
        yrs = m / 12
        y0, y1 = t_year + int(np.floor((m - 1) / 12)), t_year + int(np.floor((m - 1) / 12)) + 1
        if y1 not in totals.index and not beyond_last_year:      # trend borrowing can run past the data
            break
        frac = (m - 12 * (y0 - t_year)) / 12
        target = (totals[y0] * (totals[y1] / totals[y0]) ** frac if realized_totals
                  else totals[t_year] * np.exp(G_BASELINE * m / 12))    # ex ante: trend growth only
        alive = orig[orig.mat > d]
        cohorts = [c for c in cohorts if c[2] > d]
        need = target - alive.par.sum() - sum(c[0] for c in cohorts)
        if need > 0:
            for r in mix.itertuples():
                rate = y["n0.25"] if r.frn else y[r.col]
                if np.isnan(rate):
                    rate = y["n10"]
                cohorts.append([need * r.share, rate, d + pd.DateOffset(days=int(round(r.tenor * 365.25))),
                                r.frn, 0.1 if r.frn else 0.0])
        par = np.r_[alive.par.values, [c[0] for c in cohorts]]
        rate = np.r_[np.where(alive.frn, y["n0.25"] + alive.spread, alive.rate),
                     [y["n0.25"] + c[4] if c[3] else c[1] for c in cohorts]]
        pred = (par * rate).sum() / par.sum()
        r_new = sum(r.share * (y["n0.25"] if r.frn else (y[r.col] if not np.isnan(y[r.col]) else y["n10"]))
                    for r in mix.itertuples())
        out.append({"t": t_year, "m": m, "date": d.strftime("%Y-%m"), "pred_clock": pred, "r_new": r_new})
    df = pd.DataFrame(out)
    df.attrs["wam"] = wam
    return df


def main() -> None:
    market = pd.read_csv("data/interim/mspd/table3_market_yearend.csv", dtype=str)
    sec = securities(market)
    rates = security_rates(market)
    auc = pd.read_csv(IN / "auctions.csv", dtype=str)
    h15 = pd.read_csv(IN / "h15_monthly.csv")
    totals = sec.groupby(sec.record_date.dt.year).par.sum()
    avg = pd.read_csv(IN / "avg_interest_rates.csv", dtype=str)
    off = avg[avg.security_desc.str.replace(" ", "").eq("TotalMarketable")].copy()
    off["date"] = pd.to_datetime(off.record_date).dt.strftime("%Y-%m")
    off = off.assign(official=pd.to_numeric(off.avg_interest_rate_amt)).groupby("date").official.first()

    res = []
    for t in range(2001, 2025):
        p = project(t, sec, rates, auc, h15, totals)
        p_ex = project(t, sec, rates, auc, h15, totals, realized_totals=False)
        p["pred_clock_exante"] = p_ex.pred_clock.values[:len(p)]
        if p.empty:
            continue
        base = off.get(f"{t}-12")
        if base is None:                                      # official Total Marketable missing (2004-12)
            continue
        # engine level at t (m=0) for the level check
        x0 = sec[sec.record_date == pd.Timestamp(f"{t}-12-31")].merge(
            rates[rates.record_date == pd.Timestamp(f"{t}-12-31")], on="cusip")
        h0 = h15.set_index("month").loc[f"{t}-12", "n0.25"]
        r0 = np.where(x0.kind == "frn", h0 + x0.rate, x0.rate)
        engine0 = (x0.par * r0).sum() / x0.par.sum()
        lam = 1 / p.attrs["wam"] + G_BASELINE
        rb = base
        sc = []
        for r in p.r_new:
            rb = rb + lam / 12 * (r - rb)
            sc.append(rb)
        p["pred_scalar"] = sc
        p["official"] = p.date.map(off)
        p["base"], p["engine0"] = base, engine0
        res.append(p)
    r = pd.concat(res, ignore_index=True).dropna(subset=["official"])
    r["d_actual"] = r.official - r.base
    r["d_clock"] = r.pred_clock - r.engine0
    r["d_clock_exante"] = r.pred_clock_exante - r.engine0
    r["d_scalar"] = r.pred_scalar - r.base
    r["d_nochange"] = 0.0
    OUT.mkdir(parents=True, exist_ok=True)
    r.to_csv(OUT / "backtest_paths.csv", index=False)

    lvl = r.groupby("t").agg(official=("base", "first"), eng=("engine0", "first"))
    lvl["err"] = lvl["eng"] - lvl["official"]
    print("Level check at t (pp): mean err %.3f, max |err| %.3f" % (lvl.err.mean(), lvl.err.abs().max()))
    rows = []
    for H in (12, 24, 36):
        s = r[r.m == H]
        for k in ("clock", "clock_exante", "scalar", "nochange"):
            e = s[f"d_{k}"] - s.d_actual
            rows.append({"horizon_m": H, "model": k, "n": len(s), "MAE": e.abs().mean(),
                         "RMSE": np.sqrt((e ** 2).mean()), "bias": e.mean()})
    score = pd.DataFrame(rows)
    score.to_csv(OUT / "backtest_scores.csv", index=False)
    print(score.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
