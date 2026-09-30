"""Step 4: out-of-sample test of the 2022-25 tightening from the end-2021 balance sheets.

A. Treasury: average interest rate on marketable debt, 48 months from end-2021
   (engine of backtest.py), vs official.
B. Fed: weekly net interest income with the asset book frozen at end-2021
   (Treasuries by CUSIP at their coupons, MBS at the end-2021 book coupon, TIPS
   inflation compensation as realized) and liabilities repricing overnight
   (reserves at IORB ~ EFFR + 0.07; reverse repos at ~ EFFR - 0.03). Realized
   balance-sheet quantities and rates. Net losses accumulate as a deferred asset,
   compared with the H.4.1 'earnings remittances due' line. Premium amortization
   (net of discount accretion) is the weekly decline in H.4.1 unamortized premiums
   plus discounts; increases (purchases) are ignored.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .backtest import IN, project, security_rates
from .treasury_clock import securities

OUT = Path("data/processed/clock")
T0_SOMA = "2021-12-29"
IORB_SPREAD, RRP_SPREAD = 0.07, -0.03          # fallback EFFR-spread proxies (earlier version)
RRP_AT_BOTTOM_FROM = "2024-12-19"              # ON RRP set at the bottom of the range from this date


def policy_rates() -> pd.DataFrame:
    """Daily IORB and ON RRP rates from the FOMC target range (NY Fed EFFR API):
    IORB = top - 0.10; ON RRP = bottom + 0.05 (bottom from 2024-12-19)."""
    files = [f for f in ("data/raw/fed/effr_2021_2025.json", "data/raw/fed/effr_2026.json") if Path(f).exists()]
    d = pd.DataFrame([r for f in files for r in json.load(open(f))["refRates"]]).drop_duplicates("effectiveDate")
    d["date"] = pd.to_datetime(d.effectiveDate)
    d = d.sort_values("date").set_index("date")
    out = pd.DataFrame({"iorb": d.targetRateTo - 0.10,
                        "rrp": np.where(d.index >= RRP_AT_BOTTOM_FROM, d.targetRateFrom, d.targetRateFrom + 0.05)},
                       index=d.index)
    return out


def other_expenses_by_year() -> dict[int, float]:
    """Operating expenses + dividends - other income ($mn), Fed combined financial statements."""
    f = pd.read_csv("data/manual/fed_income_2022_2025.csv")
    return {r.year: r.operating_expenses + r.dividends - r.total_other_income for r in f.itertuples()}


def treasury_path() -> pd.DataFrame:
    market = pd.read_csv("data/interim/mspd/table3_market_yearend.csv", dtype=str)
    sec, rates = securities(market), security_rates(market)
    auc = pd.read_csv(IN / "auctions.csv", dtype=str)
    h15 = pd.read_csv(IN / "h15_monthly.csv")
    totals = sec.groupby(sec.record_date.dt.year).par.sum()
    avg = pd.read_csv(IN / "avg_interest_rates.csv", dtype=str)
    off = avg[avg.security_desc.str.replace(" ", "").eq("TotalMarketable")].copy()
    off["date"] = pd.to_datetime(off.record_date).dt.strftime("%Y-%m")
    off = off.assign(o=pd.to_numeric(off.avg_interest_rate_amt)).groupby("date").o.first()
    p = project(2021, sec, rates, auc, h15, totals, months=48)
    pe = project(2021, sec, rates, auc, h15, totals, months=48, realized_totals=False)
    p["pred_exante"] = pe.pred_clock.values[:len(p)]
    x0 = sec[sec.record_date == "2021-12-31"].merge(rates[rates.record_date == "2021-12-31"], on="cusip")
    h0 = h15.set_index("month").loc["2021-12", "n0.25"]
    eng0 = (x0.par * np.where(x0.kind == "frn", h0 + x0.rate, x0.rate)).sum() / x0.par.sum()
    base = off["2021-12"]
    wam = p.attrs["wam"]
    rb, sc = base, []
    for r in p.r_new:
        rb += (1 / wam + 0.04) / 12 * (r - rb)
        sc.append(rb)
    p["official"] = p.date.map(off)
    p["d_actual"] = p.official - base
    p["d_clock"] = p.pred_clock - eng0
    p["d_clock_exante"] = p.pred_exante - eng0
    p["d_scalar"] = np.array(sc) - base
    return p


def fed_path(other_exp_bn: float | None = None) -> pd.DataFrame:
    """other_exp_bn=None: actual annual other expenses and rule-based IORB/ON RRP rates."""
    h41 = pd.read_csv("data/interim/fed/h41_wednesday_levels.csv")
    h41 = h41[(h41.date > T0_SOMA) & (h41.date <= "2025-12-31")].reset_index(drop=True)
    h15 = pd.read_csv(IN / "h15_monthly.csv").set_index("month")
    soma = pd.read_csv("data/interim/fed/soma_tsy_yearend.csv", dtype=str)
    s0 = soma[soma.asOfDate == T0_SOMA].copy()
    s0["par"] = pd.to_numeric(s0.parValue) / 1e6
    s0["cpn"] = pd.to_numeric(s0.coupon, errors="coerce").fillna(0.05)      # bills: ~0.05% at end-2021
    s0["mat"] = pd.to_datetime(s0.maturityDate)
    mbs = pd.DataFrame(json.load(open("data/raw/fed/soma/mbs_2021-12-29.json"))["soma"]["holdings"])
    mbs_cpn = (pd.to_numeric(mbs.currentFaceValue) * pd.to_numeric(mbs.securityDescription.str.extract(r"(\d+\.?\d*)%")[0], errors="coerce")).sum() \
        / pd.to_numeric(mbs.currentFaceValue)[mbs.securityDescription.str.contains("%")].sum()
    rows, da = [], 0.0
    rates = policy_rates()
    other_actual = other_expenses_by_year()
    prev_ic = h41.soma_tips_infl_comp.iloc[0]
    prev_prem = h41.unamort_premium.iloc[0] + h41.unamort_discount.iloc[0]
    for w in h41.itertuples():
        d = pd.Timestamp(w.date)
        effr = h15.loc[d.strftime("%Y-%m"), "effr"]
        alive = s0[s0.mat > d]
        resid = max(w.soma_tsy_outright - w.soma_tips_infl_comp - alive.par.sum(), 0.0)
        r_resid = h15.loc[d.strftime("%Y-%m"), "n2"]
        income = (alive.par * alive.cpn).sum() / 100 + resid * r_resid / 100 + w.soma_mbs * mbs_cpn / 100
        income_week = income / 52 + max(w.soma_tips_infl_comp - prev_ic, 0.0)
        prev_ic = w.soma_tips_infl_comp
        prem = w.unamort_premium + w.unamort_discount
        amort_week = max(prev_prem - prem, 0.0)
        prev_prem = prem
        if other_exp_bn is None:
            pr = rates.loc[:d].iloc[-1]
            iorb, rrp = pr.iorb, pr.rrp
            other_week = other_actual[d.year] / 52
        else:
            iorb, rrp = effr + IORB_SPREAD, max(effr + RRP_SPREAD, 0.0)
            other_week = other_exp_bn * 1e3 / 52
        res_exp = w.reserves * iorb / 100 / 52
        rrp_exp = w.reverse_repo * rrp / 100 / 52
        expense_week = res_exp + rrp_exp + other_week
        ni = income_week - amort_week - expense_week
        da = max(da - ni, 0.0)
        rows.append({"date": w.date, "net_income_week": ni, "income_week": income_week - amort_week,
                     "res_exp_week": res_exp, "rrp_exp_week": rrp_exp, "pred_deferred_asset": -da,
                     "actual_deferred_asset": min(w.remittances_due, 0.0), "resid_tsy": resid})
    out = pd.DataFrame(rows)
    out.attrs["mbs_cpn"] = mbs_cpn
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    t = treasury_path()
    t.to_csv(OUT / "freeze2021_treasury.csv", index=False)
    print("A. Treasury average rate, change from end-2021 (pp)")
    print(t[t.m % 6 == 0][["date", "d_actual", "d_clock", "d_clock_exante", "d_scalar"]].round(3).to_string(index=False))
    for other in (5.0, 8.0, 11.0):
        f = fed_path(other)
        f.to_csv(OUT / f"freeze2021_fed_other{int(other)}.csv", index=False)
    f = fed_path(None)
    f.to_csv(OUT / "freeze2021_fed_actual.csv", index=False)
    ye = f.groupby(f.date.str[:4]).tail(1)
    print("\nB. Fed deferred asset ($bn), rule-based IORB/ON RRP, actual other expenses")
    print((ye.set_index("date")[["pred_deferred_asset", "actual_deferred_asset"]] / 1e3).round(1).to_string())
    act = pd.read_csv("data/manual/fed_income_2022_2025.csv").set_index("year")
    f["year"] = f.date.str[:4].astype(int)
    comp = f.groupby("year")[["income_week", "res_exp_week", "rrp_exp_week"]].sum() / 1e3
    comp.columns = ["model_interest_income_net_amort", "model_reserves_exp", "model_rrp_exp"]
    comp["actual_interest_income"] = act.interest_income / 1e3
    comp["actual_depository_exp"] = act.int_exp_depository_and_others / 1e3
    comp["actual_rrp_exp"] = act.int_exp_reverse_repo / 1e3
    comp.to_csv(OUT / "freeze2021_fed_components.csv")
    print("\nAnnual components ($bn): model (frozen end-2021 book, H.4.1 balances) vs combined financial statements")
    print(comp.round(1).to_string())


if __name__ == "__main__":
    main()
