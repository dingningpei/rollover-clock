"""Test of the inflation layer on the 2021-25 inflation surprise (paper, Section 4.5).

End-2020 balance sheet; expected inflation = end-2020 five-year breakeven (H.15 n5 - r5,
1.87%); surprise s_t = realized CPI inflation (monthly, annualized) - 1.87.

The real transfer from holders of nominal government liabilities to the consolidated
government, relative to the no-surprise baseline, accrues monthly as

    transfer_t = s_t * N_t  -  (interest_t - interest_t^A),

N_t = privately held nominal (non-TIPS) marketable debt + reserves + reverse repos +
currency; interest_t = average rate on marketable debt x privately held marketable debt
+ overnight rate x (reserves + reverse repos). Three runs of the rollover-clock projection
(backtest.project, realized borrowing), differing only in the yields at which debt
reprices:

  A  no surprise: the end-2020 forward curve (nominal and real);
  B  the model's assumption (Section 3.3), full Fisher repricing: forwards plus the
     surprise realized over each new security's life (perfect foresight within the data),
     overnight rates plus the current surprise; TIPS real yields unchanged;
  C  actual: realized H.15 yields; interest on reserves and ON RRP from the target range.

  D  inflation compensation as actually priced: forwards plus the change in breakeven
     inflation (actual breakeven minus the end-2020 forward breakeven for the tenor;
     five-year breakeven below five years), real yields at their forwards.

B is the inflation layer's prediction; C is what happened. D - B measures how far the
market's repricing for inflation fell short of full Fisher repricing (the inflation-layer
test); C - D is the cost of the real-rate increase of 2022-25, which belongs to the rate
layer. The analytic version, s_t * b * E(t) from inflation_layer.layer on the end-2020
portfolio, is reported alongside B.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .backtest import IN, project, security_rates
from .consolidated_clock import OVERNIGHT, soma_by_cusip
from .freeze_2021 import policy_rates
from .inflation_layer import GRID, exact_F
from .treasury_clock import G_BASELINE, securities

OUT = Path("data/processed/clock")
T0, MONTHS = 2020, 60
N_TENORS = {"n0.0833": 1 / 12, "n0.25": 0.25, "n0.5": 0.5, "n1": 1, "n2": 2, "n3": 3, "n5": 5, "n7": 7,
            "n10": 10, "n20": 20, "n30": 30}
R_TENORS = {"r5": 5, "r7": 7, "r10": 10, "r20": 20, "r30": 30}


def surprise(t0: int = T0) -> tuple[pd.Series, float]:
    h = pd.read_csv(IN / "h15_monthly.csv").set_index("month")
    exp = float(h.loc[f"{t0}-12", "n5"] - h.loc[f"{t0}-12", "r5"])
    c = pd.read_csv("data/raw/fred/CPIAUCSL.csv")
    c.index = pd.to_datetime(c.observation_date)
    # October 2025 CPI was not published (federal shutdown): log level interpolated
    full = pd.date_range(c.index.min(), c.index.max(), freq="MS")
    lvl = np.exp(np.log(pd.to_numeric(c.CPIAUCSL, errors="coerce")).reindex(full).interpolate())
    lvl.index = lvl.index.strftime("%Y-%m")
    pi = 1200 * np.log(lvl / lvl.shift(1))
    return (pi - exp).dropna(), exp


def curve(row: pd.Series, tenors: dict, short_flat: bool) -> tuple[np.ndarray, np.ndarray]:
    t = np.array(list(tenors.values()), float)
    y = np.array([row[k] for k in tenors], float)
    ok = ~np.isnan(y)
    t, y = t[ok], y[ok]
    if short_flat:                                  # real curve: flat below 5 years
        t, y = np.r_[0.0, t], np.r_[y[0], y]
    return t, y


def forward(t: float, tau: float, tt: np.ndarray, yy: np.ndarray) -> float:
    """Forward yield from t to t+tau, treating par yields as zero yields."""
    Y = lambda x: np.interp(x, tt, yy)
    return (Y(t + tau) * (t + tau) - Y(t) * t) / tau if t > 0 else float(Y(tau))


def breakeven_tenor(tau: float) -> str:
    return min(R_TENORS, key=lambda k: abs(R_TENORS[k] - max(tau, 5)))


def scenario_h15(s: pd.Series, fisher: bool, breakeven: bool = False, t0: int = T0,
                 months_n: int = MONTHS) -> pd.DataFrame:
    h = pd.read_csv(IN / "h15_monthly.csv").set_index("month")
    base = h.loc[f"{t0}-12"]
    tn, yn = curve(base, N_TENORS, False)
    tr, yr = curve(base, R_TENORS, True)
    months = pd.period_range(f"{t0 + 1}-01", periods=months_n, freq="M").strftime("%Y-%m")
    rows = []
    for m, key in enumerate(months, start=1):
        t = m / 12
        row = {"month": key}
        for c, tau in N_TENORS.items():
            v = forward(t, tau, tn, yn)
            if fisher:                              # surprise realized over the security's life
                win = s.loc[key:].iloc[: max(1, int(round(tau * 12)))]
                v += win.sum() / max(1, int(round(tau * 12)))
            if breakeven:                           # actual minus forward breakeven for the tenor
                rk = breakeven_tenor(tau)
                tb = max(tau, 5.0)
                be_act = h.loc[key, "n" + rk[1:]] - h.loc[key, rk]
                be_fwd = forward(t, tb, tn, yn) - forward(t, tb, tr, yr)
                v += be_act - be_fwd
            row[c] = v
        for c, tau in R_TENORS.items():
            row[c] = forward(t, tau, tr, yr)
        row["effr"] = row["n0.0833"]
        rows.append(row)
    return pd.DataFrame(rows)


def monthly_quantities(t0: int = T0, months_n: int = MONTHS) -> pd.DataFrame:
    """Privately held marketable (total, TIPS), overnight liabilities, currency by month ($mn)."""
    sec = securities(pd.read_csv("data/interim/mspd/table3_market_yearend.csv", dtype=str))
    soma = soma_by_cusip(pd.read_csv("data/interim/fed/soma_tsy_yearend.csv", dtype=str))
    soma["year"] = soma.year.astype(int)
    ye = []
    for y in range(t0, t0 + months_n // 12 + 1):
        if not (sec.record_date.dt.year == y).any():
            continue
        x = sec[sec.record_date.dt.year == y].merge(soma[soma.year == y][["cusip", "soma_par"]], on="cusip",
                                                    how="left").fillna({"soma_par": 0})
        p = x.par - x.soma_par
        ye.append({"date": pd.Timestamp(f"{y}-12-31"), "priv": p.sum(), "priv_tips": p[x.kind == "tips"].sum()})
    ye = pd.DataFrame(ye).set_index("date")
    h41 = pd.read_csv("data/interim/fed/h41_wednesday_levels.csv")
    h41["month"] = pd.to_datetime(h41.date).dt.strftime("%Y-%m")
    h41 = h41.groupby("month")[["reserves", "reverse_repo", "currency"]].mean()
    idx = pd.date_range(f"{t0 + 1}-01-31", periods=months_n, freq="ME")
    q = ye.reindex(ye.index.union(idx)).interpolate(method="time").ffill().loc[idx]   # held after the last year-end
    q.index = q.index.strftime("%Y-%m")
    return q.join(h41)


def overnight_rates(s: pd.Series, h_a: pd.DataFrame, h_d: pd.DataFrame) -> pd.DataFrame:
    """The target-range series starts in December 2021. Before that the range was 0-0.25:
    IOER 0.10 and ON RRP 0.00 until the FOMC's technical adjustment of 16 June 2021, then
    0.15 and 0.05."""
    p = policy_rates()
    p["month"] = p.index.strftime("%Y-%m")
    act = p.groupby("month")[["iorb", "rrp"]].mean()
    a = h_a.set_index("month")["n0.0833"]
    idx = a.index
    act = act.reindex(idx)
    early = idx < "2021-12"
    h1 = idx <= "2021-06"
    act.loc[early, "iorb"] = np.where(h1[early], 0.10, 0.15)
    act.loc[early, "rrp"] = np.where(h1[early], 0.00, 0.05)
    return pd.DataFrame({"A": a, "B": a + s.reindex(idx), "D": h_d.set_index("month")["n0.0833"],
                         "C_iorb": act.iorb, "C_rrp": act.rrp})


def analytic_E(s: pd.Series, t0: int = T0, months_n: int = MONTHS) -> pd.Series:
    """Erosion per $ of end-2020 interest-bearing debt, model layer: s_t * E(t)."""
    sec = securities(pd.read_csv("data/interim/mspd/table3_market_yearend.csv", dtype=str))
    x = sec[sec.record_date.dt.year == t0]
    soma = soma_by_cusip(pd.read_csv("data/interim/fed/soma_tsy_yearend.csv", dtype=str))
    x = x.merge(soma[soma.year.astype(int) == t0][["cusip", "soma_par"]], on="cusip", how="left").fillna({"soma_par": 0})
    h41 = pd.read_csv("data/interim/fed/h41_wednesday_levels.csv")
    lev = h41.loc[h41.date <= f"{t0}-12-31"].iloc[-1]
    tau = np.r_[x.tau.values, OVERNIGHT]
    w = np.r_[(x.par - x.soma_par).values, lev.reserves + lev.reverse_repo]
    ix = np.r_[(x.kind == "tips").values, False]
    Pn = 1 - (1 - exact_F(tau[~ix], w[~ix], GRID)) * np.exp(-G_BASELINE * GRID)
    E = w[~ix].sum() / w.sum() * (1 - Pn) + lev.currency / w.sum()
    months = pd.period_range(f"{t0 + 1}-01", periods=months_n, freq="M").strftime("%Y-%m")
    e = np.interp(np.arange(1, months_n + 1) / 12, GRID, E)
    return pd.Series(e, index=months), w.sum()


def run(t0: int, months_n: int, realized_totals: bool, tag: str = "") -> pd.DataFrame:
    """One run of the test from the end-t0 balance sheet; writes inflation_test{tag}_*.csv."""
    s, exp = surprise(t0)
    market = pd.read_csv("data/interim/mspd/table3_market_yearend.csv", dtype=str)
    sec, rates = securities(market), security_rates(market)
    auc = pd.read_csv(IN / "auctions.csv", dtype=str)
    totals = sec.groupby(sec.record_date.dt.year).par.sum()
    hA, hB, hD = (scenario_h15(s, False, t0=t0, months_n=months_n), scenario_h15(s, True, t0=t0, months_n=months_n),
                  scenario_h15(s, False, breakeven=True, t0=t0, months_n=months_n))
    hC = pd.read_csv(IN / "h15_monthly.csv")
    runs = {k: project(t0, sec, rates, auc, h, totals, months=months_n, realized_totals=realized_totals,
                       beyond_last_year=not realized_totals).set_index("date").pred_clock
            for k, h in (("A", hA), ("B", hB), ("C", hC), ("D", hD))}
    q = monthly_quantities(t0, months_n)
    on = overnight_rates(s, hA, hD)
    d = q.copy()
    d["s"] = s.reindex(d.index)
    d["N"] = d.priv - d.priv_tips + d.reserves + d.reverse_repo + d.currency
    for k in "ABCD":
        d[f"rate_{k}"] = runs[k].reindex(d.index)
    d["int_A"] = d.rate_A / 100 * d.priv + on.A.reindex(d.index) / 100 * (d.reserves + d.reverse_repo)
    d["int_B"] = d.rate_B / 100 * d.priv + on.B.reindex(d.index) / 100 * (d.reserves + d.reverse_repo)
    d["int_D"] = d.rate_D / 100 * d.priv + on.D.reindex(d.index) / 100 * (d.reserves + d.reverse_repo)
    d["int_C"] = (d.rate_C / 100 * d.priv + on.C_iorb.reindex(d.index) / 100 * d.reserves
                  + on.C_rrp.reindex(d.index) / 100 * d.reverse_repo)
    d["gross"] = d.s / 100 / 12 * d.N                         # erosion of all nominal liabilities
    assert d[["int_A", "int_B", "int_C", "int_D", "s"]].notna().all().all(), "missing monthly inputs"
    for k in "BCD":
        d[f"transfer_{k}"] = d.gross - (d[f"int_{k}"] - d.int_A) / 12
    E, W0 = analytic_E(s, t0, months_n)
    d["transfer_analytic"] = d.s / 100 / 12 * E.reindex(d.index) * W0
    gdp = pd.read_csv("data/raw/bea/NipaDataA.txt", dtype=str)
    gdp.columns = [c.strip() for c in gdp.columns]
    gdp = gdp[gdp.iloc[:, 0] == "A191RC"]
    gdp20 = float(pd.to_numeric(gdp[gdp.iloc[:, 1].astype(int) == t0].iloc[0, 2].replace(",", "")))
    d.to_csv(OUT / f"inflation_test{tag}_monthly.csv")
    d["year"] = d.index.str[:4].astype(int)
    cols = ["gross", "transfer_B", "transfer_analytic", "transfer_D", "transfer_C"]
    y = d.groupby("year")[cols].sum().cumsum()
    y = pd.concat([(y / 1e3).add_suffix("_bn"), (100 * y / gdp20).add_suffix("_pct_gdp20")], axis=1)
    y["cum_surprise_pp"] = d.groupby("year").s.sum().cumsum() / 12
    y["rate_A_dec"] = d.groupby("year").rate_A.last()
    y["rate_B_dec"] = d.groupby("year").rate_B.last()
    y["rate_C_dec"] = d.groupby("year").rate_C.last()
    y["rate_D_dec"] = d.groupby("year").rate_D.last()
    y.to_csv(OUT / f"inflation_test{tag}_summary.csv")
    print(f"expected inflation (end-{t0} 5y breakeven): {exp:.2f}%")
    pd.set_option("display.width", 220)
    print(y.round(2).to_string())
    return y



def main() -> None:
    run(T0, MONTHS, realized_totals=True)

if __name__ == "__main__":
    main()
