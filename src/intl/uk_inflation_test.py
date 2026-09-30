"""United Kingdom: test of the inflation layer on the 2021-25 inflation surprise, on the design
of the U.S. test (src/clock/inflation_test.py, paper Section 4.5).

End-2020 consolidated balance sheet (HM Treasury + Bank of England), held as a closed
portfolio: privately held conventional gilts by ISIN (DMO minus APF), reserves (repricing
at Bank Rate), notes and coin (zero rate). Each gilt, at redemption, is rolled into a new
gilt of the same original tenor; amounts are held at their end-2020 levels. Index-linked
gilts (RPI-linked, a quarter of the private stock) carry no nominal claim to erode and are
reported separately. Treasury bills (about 3% of the stock) are not included.

Expected CPI inflation = end-2020 five-year implied RPI inflation (Bank of England,
December average) minus the average RPI-CPI wedge of 2011-20; surprise s_t = realized
CPI inflation (monthly, annualized) - expected.

Transfer to the consolidated government, relative to the no-surprise baseline, monthly:
    transfer_t = s_t * N  -  (interest_t - interest_t^A),     N = nominal liabilities.
Yields at which each rolled gilt and the reserves reprice:
  A  no surprise: forwards from the end-2020 nominal zero-coupon curve;
  B  full Fisher repricing (the model): A plus the surprise realized over the new gilt's life;
  C  actual: realized nominal zero-coupon yields and Bank Rate;
  D  inflation compensation as priced: A plus the change in implied inflation (actual minus
     the end-2020 forward, at max(tenor, 5 years)).
D - B is the inflation-layer test; C - D the real-rate increase (rate layer). The analytic
layer s_t * b * E(t) on the end-2020 portfolio is reported alongside B.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.clock.consolidated_clock import OVERNIGHT
from src.clock.inflation_layer import GRID, exact_F

OUT = Path("data/processed/uk")
T0, MONTHS = 2020, 60
KNOTS = {5.0: "S", 10.0: "M", 20.0: "L"}


def monthly_curves() -> pd.DataFrame:
    c = pd.read_csv("data/raw/uk/boe_db/boe_curves.csv")
    s = pd.read_csv("data/raw/uk/boe_db/boe_series.csv")[["DATE", "IUDBEDR"]]
    d = c.merge(s, on="DATE", how="left")
    d["month"] = pd.to_datetime(d.DATE, format="%d %b %Y").dt.strftime("%Y-%m")
    return d.drop(columns="DATE").apply(pd.to_numeric, errors="coerce").assign(month=d.month).groupby("month").mean()


def nominal(row: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    return np.r_[0.0, list(KNOTS)], np.r_[row.IUDBEDR, [row[f"IUD{k}NZC"] for k in KNOTS.values()]]


def real(row: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    y = [row[f"IUD{k}RZC"] for k in KNOTS.values()]
    return np.r_[0.0, list(KNOTS)], np.r_[y[0], y]                   # flat below 5 years


def implied(row: pd.Series, tau: float) -> float:
    return float(np.interp(tau, list(KNOTS), [row[f"IUD{k}IZC"] for k in KNOTS.values()]))


def forward(t: float, tau: float, tt: np.ndarray, yy: np.ndarray) -> float:
    Y = lambda x: np.interp(x, tt, yy)                               # flat beyond 20 years
    return float((Y(t + tau) * (t + tau) - Y(t) * t) / tau)


def surprise(cv: pd.DataFrame) -> tuple[pd.Series, pd.Series, float, float]:
    p = pd.read_csv("data/raw/uk/ons/ons_prices.csv").set_index("month")
    cpi, rpi = 1200 * np.log(p.D7BT / p.D7BT.shift(1)), 1200 * np.log(p.CHAW / p.CHAW.shift(1))
    dec = p[p.index.str.endswith("-12")]
    wedge = float((100 * np.log(dec.CHAW / dec.D7BT).diff()).loc[f"{T0 - 9}-12":f"{T0}-12"].mean())
    exp_rpi = float(cv.loc[f"{T0}-12", "IUDSIZC"])
    return (cpi - (exp_rpi - wedge)).dropna(), (rpi - exp_rpi).dropna(), exp_rpi - wedge, wedge


def rates(cv: pd.DataFrame, s: pd.Series, m: int, tau: float) -> dict:
    """Yield (%) under A-D for a gilt of tenor tau issued in month m (1 = January 2021)."""
    t, key = m / 12, (pd.Period(f"{T0}-12", "M") + m).strftime("%Y-%m")
    base, now = cv.loc[f"{T0}-12"], cv.loc[key]
    tn, yn = nominal(base)
    a = forward(t, tau, tn, yn)
    n = max(1, int(round(tau * 12)))
    tb = max(tau, 5.0)
    be_fwd = forward(t, tb, tn, yn) - forward(t, tb, *real(base))
    return {"A": a, "B": a + s.loc[key:].iloc[:n].mean(), "C": float(np.interp(tau, *nominal(now))),
            "D": a + implied(now, tb) - be_fwd}


def balance_sheet() -> tuple[pd.DataFrame, float, float, float]:
    g = pd.read_csv("data/interim/uk/gilts_by_isin.csv", parse_dates=["as_of", "maturity", "first_issue"])
    apf = pd.read_csv("data/interim/uk/apf_by_isin.csv")
    x = g[g.as_of.dt.year == T0].merge(apf[apf.year == T0][["isin", "apf_nominal"]], on="isin", how="left")
    x = x.fillna({"apf_nominal": 0.0})
    x["private"] = (x.amount - x.apf_nominal * x.amount / x.nominal).clip(lower=0)
    x["tenor"] = ((x.maturity - x.first_issue).dt.days / 365.25).clip(lower=1.0)
    x["roll"] = (x.maturity.dt.year - T0 - 1) * 12 + x.maturity.dt.month          # month of redemption
    x["tau"] = (x.maturity - x.as_of).dt.days / 365.25
    b = pd.read_csv("data/raw/uk/boe_db/boe_series.csv")
    b["DATE"] = pd.to_datetime(b.DATE, format="%d %b %Y")
    dec = b[b.DATE.dt.strftime("%Y-%m") == f"{T0}-12"]
    reserves, notes = dec.LPMBL22.dropna().iloc[-1], dec.LPMAVAA.dropna().iloc[-1]
    il = x.loc[x.kind == "indexed", "private"].sum()
    return x[x.kind != "indexed"], reserves, notes, il


def main() -> None:
    cv = monthly_curves()
    s, s_rpi, exp, wedge = surprise(cv)
    gilts, reserves, notes, il = balance_sheet()
    months = pd.period_range(f"{T0 + 1}-01", periods=MONTHS, freq="M").strftime("%Y-%m")
    diff = {k: np.zeros(MONTHS) for k in "BCD"}
    rate_dec = {k: [] for k in "ABCD"}
    for r in gilts.itertuples():                   # interest difference vs A after each rollover
        roll = r.roll
        while roll < MONTHS:
            y = rates(cv, s, max(roll, 1), r.tenor)
            nxt = roll + max(1, int(round(r.tenor * 12)))
            for k in "BCD":
                diff[k][roll:min(nxt, MONTHS)] += r.private * (y[k] - y["A"]) / 100 / 12
            roll = nxt
    on = pd.DataFrame([rates(cv, s, m, 1 / 12) for m in range(1, MONTHS + 1)], index=months)
    on["C"] = cv.IUDBEDR.reindex(months).values                         # reserves paid Bank Rate
    on["B"] = on.A + s.reindex(months).values
    for k in "BCD":
        diff[k] += reserves * (on[k] - on.A).values / 100 / 12
    N = gilts.private.sum() + reserves + notes
    d = pd.DataFrame({"s": s.reindex(months).values, "s_rpi": s_rpi.reindex(months).values}, index=months)
    d["gross"] = d.s / 100 / 12 * N
    for k in "BCD":
        d[f"transfer_{k}"] = d.gross - diff[k]
    # analytic layer on the end-2020 portfolio
    clk = pd.read_csv(OUT / "uk_clock.csv").set_index("year")
    g = float(clk.loc[T0, "g_trailing10"])
    tau = np.r_[gilts.tau.values, OVERNIGHT]
    w = np.r_[gilts.private.values, reserves]
    Pn = 1 - (1 - exact_F(tau, w, GRID)) * np.exp(-g * GRID)
    E = np.interp(np.arange(1, MONTHS + 1) / 12, GRID, w.sum() * (1 - Pn) + notes)
    d["transfer_analytic"] = d.s / 100 / 12 * E
    d["il_uplift_surprise"] = d.s_rpi / 100 / 12 * il            # RPI above expectations on index-linked
    d["on_A"], d["on_C"] = on.A.values, on.C.values
    d["reserves_cost_C"] = reserves * (on.C - on.A).values / 100 / 12   # part of C's extra interest on reserves
    d.to_csv(OUT / "uk_inflation_test_monthly.csv")
    gdp = pd.read_csv("data/raw/fred/UKNGDP.csv")
    gdp20 = gdp[gdp.observation_date.str.startswith(str(T0))].UKNGDP.sum()
    d["year"] = d.index.str[:4].astype(int)
    cols = ["gross", "transfer_B", "transfer_analytic", "transfer_D", "transfer_C", "reserves_cost_C", "il_uplift_surprise"]
    y = d.groupby("year")[cols].sum().cumsum()
    y = pd.concat([(y / 1e3).add_suffix("_bn"), (100 * y / gdp20).add_suffix("_pct_gdp20")], axis=1)
    y["cum_surprise_pp"] = d.groupby("year").s.sum().cumsum() / 12
    y["cum_rpi_surprise_pp"] = d.groupby("year").s_rpi.sum().cumsum() / 12
    y.to_csv(OUT / "uk_inflation_test_summary.csv")
    print(f"expected CPI inflation {exp:.2f}% (5y implied RPI {exp + wedge:.2f} - wedge {wedge:.2f})")
    print(f"end-2020 private stock £bn: conventional {gilts.private.sum() / 1e3:.0f}, reserves {reserves / 1e3:.0f}, "
          f"notes {notes / 1e3:.0f}, index-linked {il / 1e3:.0f}; GDP 2020 {gdp20 / 1e3:.0f}; g {g:.3f}")
    pd.set_option("display.width", 250)
    print(y.round(2).to_string())


if __name__ == "__main__":
    main()
