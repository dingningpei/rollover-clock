"""Japan: test of the inflation layer on the 2022-25 inflation surprise, on the design of the
U.S. and UK tests (src/clock/inflation_test.py, src/intl/uk_inflation_test.py).

End-FY2021 (31 March 2022) consolidated balance sheet (MOF + Bank of Japan, src/intl/jp_clock.py),
held as a closed portfolio for 48 months (April 2022 - March 2026):
  - privately held nominal JGBs and bills by issue; each is rolled at redemption into a new
    security of the same original tenor, and amounts stay at their end-FY2021 levels;
    floating-rate JGBs reset every six months at the 10-year yield;
  - interest-bearing BoJ current accounts (the positive and negative tiers);
  - the zero-interest base: banknotes and current accounts in the 0% tier (incl. required reserves).
Index-linked JGBs (0.6% of the stock) carry no nominal claim to erode and are left out.

Expected inflation = average CPI inflation over the ten years to March 2022 (market breakeven
inflation is not available in a public series); surprise s_t = realized CPI inflation
(monthly, annualized) - expected. Sensitivity: expected = 1%.

Transfer to the consolidated government, relative to the no-surprise baseline, monthly:
    transfer_t = s_t * N  -  (interest_t - interest_t^A),     N = nominal liabilities.
Yields at which securities and current accounts reprice:
  A  no surprise: forwards from the March 2022 JGB curve (MOF constant-maturity yields, call rate at
     zero maturity); interest-bearing current accounts at their March 2022 tier-weighted rate plus the
     forward change in the short rate;
  B  full Fisher repricing (the model): A plus the surprise realized over the new security's life;
  C  actual: realized JGB yields; current accounts at the tier-weighted rate (+0.1% basic balance,
     -0.1% policy-rate balance) until the March 2024 reform and at the call rate after it.
Under C, the reform also started paying the call rate on the 0% tier above required reserves;
that cost is part of C and is reported separately. No series of breakeven inflation is used, so
there is no run D.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

from src.clock.consolidated_clock import OVERNIGHT
from src.clock.inflation_layer import GRID, exact_F
from src.intl.jp_clock import gdp_fy, monthly, portfolio
from src.intl.phi_star import JP_TENOR, jp_yields

OUT = Path("data/processed/jp")
FY0, MONTHS = 2021, 48
T0 = "2022-03"
REFORM = "2024-04"                      # first full month after the 19 March 2024 reform
TIER_RATES = {"MACAB3202": 0.1, "MACAB3203": 0.0, "MACAB3204": -0.1}


def cpi() -> pd.Series:
    """Monthly CPI (all items), chained: OECD series (FRED) before 2020, Statistics Bureau from 2020."""
    s = pd.read_csv("data/raw/jp/stat/zmi2020aa.csv", encoding="shift_jis", header=None, dtype=str)
    s = s[s[0].str.fullmatch(r"\d{6}", na=False)]
    new = pd.Series(pd.to_numeric(s[1]).values, index=pd.to_datetime(s[0], format="%Y%m").dt.strftime("%Y-%m"))
    f = pd.read_csv("data/raw/fred/JPNCPIALLMINMEI.csv")
    old = pd.Series(pd.to_numeric(f.iloc[:, 1], errors="coerce").values,
                    index=pd.to_datetime(f.observation_date).dt.strftime("%Y-%m"))
    old = old.loc[:"2020-01"] * new.loc["2020-01"] / old.loc["2020-01"]
    return pd.concat([old.loc[:"2019-12"], new])


def monthly_curves() -> pd.DataFrame:
    d = pd.read_csv("data/raw/jp/mof/jgbcm_all.csv", encoding="shift_jis", skiprows=1)
    from src.intl.jp_stock import era_date
    d["month"] = d["基準日"].map(era_date).dt.strftime("%Y-%m")
    d = d.drop(columns="基準日").set_index("month").apply(pd.to_numeric, errors="coerce").groupby(level=0).mean()
    d.columns = [int(re.sub(r"\D", "", c)) for c in d.columns]
    c = pd.read_csv("data/raw/jp/boj_api/FM01.csv", dtype={"date": str}).dropna(subset=["value"])
    c["month"] = pd.to_datetime(c.date, format="%Y%m%d").dt.strftime("%Y-%m")
    d[0] = c.groupby("month").value.mean().reindex(d.index)
    return d[sorted(d.columns)]


def curve(row: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    ok = row.notna()
    return np.array(row.index[ok], float), row[ok].values.astype(float)


def forward(t: float, tau: float, tt: np.ndarray, yy: np.ndarray) -> float:
    Y = lambda x: np.interp(x, tt, yy)
    return float((Y(t + tau) * (t + tau) - Y(t) * t) / tau)


def tenor(name: str, kind: str) -> tuple[float, float]:
    """(months held between repricings, tenor of the yield it reprices at)."""
    n = unicodedata.normalize("NFKC", name)
    if kind == "floating":
        return 0.5, 10.0
    if kind == "bill":
        if "FB" in n:
            return 0.25, 0.25
        m = re.search(r"\((\d+)(年|ヶ月|か月|カ月)\)", n)
        t = (float(m.group(1)) if m.group(2) == "年" else float(m.group(1)) / 12) if m else 1.0
        return t, t
    for k, v in JP_TENOR.items():
        if k in n:
            return float(v), float(v)
    raise ValueError(n)


def main() -> None:
    cv = monthly_curves()
    p = cpi()
    pi = 1200 * np.log(p / p.shift(1))
    exp = float(100 * np.log(p.loc[T0] / p.loc["2012-03"]) / 10)
    months = pd.period_range("2022-04", periods=MONTHS, freq="M").strftime("%Y-%m")
    issues = pd.read_csv("data/interim/jp/jgb_by_issue.csv")
    boj = pd.read_csv("data/interim/jp/boj_holdings.csv")
    pf, bs, md, rr = monthly("PF02"), monthly("BS01"), monthly("MD08"), monthly("MD07")
    pt = portfolio(FY0, issues, boj, pf, bs, md, rr)
    sec = pt["sec"][pt["sec"].kind != "indexed"].copy()
    ca_ib, ca_zero, notes = pt["ca_ib"], pt["ca_zero"], pt["banknotes"]
    req0 = rr.loc[202203, "MAREM3"]
    # rate paid on interest-bearing current accounts (tier-weighted), monthly
    t = md[list(TIER_RATES)]
    ib = t["MACAB3202"] + t["MACAB3204"]
    paid = (t["MACAB3202"] * 0.1 - t["MACAB3204"] * 0.1) / ib
    paid.index = pd.to_datetime(paid.index.astype(str), format="%Y%m").strftime("%Y-%m")
    tn, yn = curve(cv.loc[T0])
    out = {}
    for label, e in (("base", exp), ("exp1", 1.0)):
        s = (pi - e).dropna()
        diff = {k: np.zeros(MONTHS) for k in "BC"}
        for r in sec.itertuples():
            hold, ten = tenor(r.name, r.kind)
            roll = max(0, int(np.ceil(r.tau * 12)))
            while roll < MONTHS:
                m = max(roll, 1)
                key = months[m - 1]
                a = forward(m / 12, ten, tn, yn)
                n = max(1, int(round(ten * 12)))
                y = {"B": a + s.loc[key:].iloc[:n].mean(), "C": float(np.interp(ten, *curve(cv.loc[key])))}
                nxt = roll + max(1, int(round(hold * 12)))
                for k in "BC":
                    diff[k][roll:min(nxt, MONTHS)] += r.private * (y[k] - a) / 100 / 12
                roll = nxt
        on_a = np.array([paid.loc[T0] + forward(m / 12, 1 / 12, tn, yn) - forward(0, 1 / 12, tn, yn)
                         for m in range(1, MONTHS + 1)])
        on_c = np.where(months < REFORM, paid.reindex(months).values, cv[0].reindex(months).values)
        reform = np.where(months < REFORM, 0.0, cv[0].reindex(months).values) * (ca_zero - req0) / 100 / 12
        diff["B"] += ca_ib * s.reindex(months).values / 100 / 12
        diff["C"] += ca_ib * (on_c - on_a) / 100 / 12 + reform
        N = sec.private.sum() + ca_ib + ca_zero + notes
        d = pd.DataFrame({"s": s.reindex(months).values}, index=months)
        d["gross"] = d.s / 100 / 12 * N
        for k in "BC":
            d[f"transfer_{k}"] = d.gross - diff[k]
        d["reform_cost_C"] = reform
        tau = np.r_[sec.tau.clip(lower=0).values, OVERNIGHT]
        w = np.r_[sec.private.values, ca_ib]
        g = float(pd.read_csv(OUT / "jp_clock.csv").set_index("fy").loc[FY0, "g_trailing10"])
        Pn = 1 - (1 - exact_F(tau, w, GRID)) * np.exp(-g * GRID)
        E = np.interp(np.arange(1, MONTHS + 1) / 12, GRID, w.sum() * (1 - Pn) + ca_zero + notes)
        d["transfer_analytic"] = d.s / 100 / 12 * E
        out[label] = d
    gdp = gdp_fy()[FY0]
    rows = []
    for label, d in out.items():
        d = d.copy()
        d["fy"] = [int(m[:4]) - (int(m[5:]) < 4) for m in d.index]
        y = d.groupby("fy")[["gross", "transfer_B", "transfer_analytic", "transfer_C", "reform_cost_C"]].sum().cumsum()
        y = 100 * y / gdp
        y["cum_surprise_pp"] = d.groupby("fy").s.sum().cumsum() / 12
        y["expected"] = exp if label == "base" else 1.0
        y["case"] = label
        rows.append(y.reset_index())
    res = pd.concat(rows, ignore_index=True)
    res.to_csv(OUT / "jp_inflation_test_summary.csv", index=False)
    out["base"].to_csv(OUT / "jp_inflation_test_monthly.csv")
    print(f"expected CPI inflation {exp:.2f}% (10 years to March 2022)")
    print(f"end-FY2021, trillion yen: private nominal JGBs and bills {sec.private.sum() / 1e9:.0f}, "
          f"interest-bearing current accounts {ca_ib / 1e9:.0f}, 0% tier {ca_zero / 1e9:.0f}, "
          f"banknotes {notes / 1e9:.0f}; GDP FY2021 {gdp / 1e9:.0f}")
    pd.set_option("display.width", 220)
    print(res.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
