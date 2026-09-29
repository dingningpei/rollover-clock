"""Identify the fiscal offset phi from predetermined repricing exposure x rate changes.

Annual, calendar years 1981-2025.
  S_t    : federal primary surplus / GDP, NIPA table 3.2, EXCLUDING Federal Reserve
           remittances (those are part of the consolidated interest channel):
           S = [W005RC - LA000248 - (W013RC - A091RC)] / GDP
  IC_t   : federal interest payments / GDP (A091RC / GDP)
  Exposure at end t: b_t * P_t(1)  (consolidated clock; FD-5 buckets before 2003)
  PIC_{t+1} = b_t * P_t(1) * (r1_{t+1} - r1_t) : predicted change in interest/GDP next year
              from repricing of the predetermined portfolio (r1 = 1-year CMT, annual avg)
Identification: variation in the predetermined exposure b_t*P_t(1) conditional on the
rate change itself (dr enters as a control), debt, growth and the lagged surplus.
Estimates: first stage (dIC on PIC), reduced form (S_{t+k}-S_t on PIC), IV (dS on dIC
instrumented by PIC). phi_hat = -(response of S) / (response of IC) sign-adjusted:
a positive coefficient of dS on dIC means the surplus rises to offset interest.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

OUT = Path("data/processed/fiscal")


def nipa() -> pd.DataFrame:
    d = pd.read_csv("data/raw/bea/NipaDataA.txt", dtype=str)
    d.columns = [c.strip() for c in d.columns]
    c0, c1, c2 = d.columns[:3]
    s = {}
    for code in ["W005RC", "W013RC", "A091RC", "LA000248", "A191RC", "A191RL"]:
        x = d[d[c0] == code]
        s[code] = pd.Series(pd.to_numeric(x[c2].str.replace(",", "")).values, index=x[c1].astype(int).values)
    f = pd.DataFrame(s)
    f["S"] = 100 * (f.W005RC - f.LA000248 - (f.W013RC - f.A091RC)) / f.A191RC
    f["S_incl_fed"] = 100 * (f.W005RC - (f.W013RC - f.A091RC)) / f.A191RC
    f["IC"] = 100 * f.A091RC / f.A191RC
    f["growth"] = f.A191RL
    return f


def exposure() -> pd.DataFrame:
    fd5 = pd.read_csv("data/processed/clock/fd5_clock_1980_2003.csv")
    fd5 = fd5[fd5.year <= 2002].assign(P1=lambda x: 1 - (1 - x.F1) * np.exp(-0.04))
    con = pd.read_csv("data/processed/clock/consolidated_clock_yearend.csv")
    lm = pd.read_csv("data/processed/limit/limit_map_1980_2025.csv").set_index("year")
    e = pd.concat([fd5[["year", "P1"]], con[["year", "P_1"]].rename(columns={"P_1": "P1"})]).set_index("year")
    e["b"] = lm.b
    return e


def build() -> pd.DataFrame:
    f, e = nipa(), exposure()
    h = pd.read_csv("data/interim/backtest/h15_monthly.csv")
    r1 = h.assign(year=h.month.str[:4].astype(int)).groupby("year").n1.mean()
    d = e.join(f, how="left")
    d["r1"] = r1
    d["dr"] = d.r1.shift(-1) - d.r1                       # rate change t -> t+1 (pp)
    d["expo"] = d.b * d.P1                               # predetermined at end t
    d["PIC"] = d.expo * d.dr                             # predicted d(interest/GDP), pp of GDP
    d["dIC"] = d.IC.shift(-1) - d.IC
    for k in (1, 2, 3):
        d[f"dS{k}"] = d.S.shift(-k) - d.S
    d["growth1"] = d.growth.shift(-1)
    d["post2004"] = (d.index >= 2004).astype(float)
    return d


def ols(y, X, lags=2):
    m = sm.OLS(y, sm.add_constant(X), missing="drop").fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return m


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = build()
    d.to_csv(OUT / "phi_dataset.csv")
    ctrl = ["dr", "b", "growth1", "S"]
    rows = []
    fs = ols(d.dIC, d[["PIC"] + ctrl])
    rows.append({"spec": "first stage: dIC on PIC", "coef": fs.params["PIC"], "se": fs.bse["PIC"], "n": int(fs.nobs),
                 "F_PIC": (fs.params["PIC"] / fs.bse["PIC"]) ** 2})
    for k in (1, 2, 3):
        rf = ols(d[f"dS{k}"], d[["PIC"] + ctrl])
        rows.append({"spec": f"reduced form: dS(t,t+{k}) on PIC", "coef": rf.params["PIC"], "se": rf.bse["PIC"], "n": int(rf.nobs)})
        # interaction with post-2004 regime
        X = d[["PIC"] + ctrl].copy()
        X["PICxPost"] = d.PIC * d.post2004
        X["post2004"] = d.post2004
        ri = ols(d[f"dS{k}"], X)
        rows.append({"spec": f"  pre-2004 PIC (k={k})", "coef": ri.params["PIC"], "se": ri.bse["PIC"], "n": int(ri.nobs)})
        rows.append({"spec": f"  post-2004 shift (k={k})", "coef": ri.params["PICxPost"], "se": ri.bse["PICxPost"], "n": int(ri.nobs)})
        # IV (Wald ratio via 2SLS by hand): dS_k on dIC_hat
        sub = d[[f"dS{k}", "dIC", "PIC"] + ctrl].dropna()
        Z = sm.add_constant(sub[["PIC"] + ctrl])
        dIC_hat = sm.OLS(sub.dIC, Z).fit().fittedvalues
        iv = sm.OLS(sub[f"dS{k}"], sm.add_constant(pd.concat([dIC_hat.rename("dIC_hat"), sub[ctrl]], axis=1))).fit(
            cov_type="HAC", cov_kwds={"maxlags": 2})
        rows.append({"spec": f"IV phi: dS(t,t+{k}) on dIC (instr. PIC)", "coef": iv.params["dIC_hat"], "se": iv.bse["dIC_hat"],
                     "n": int(iv.nobs), "note": "2SLS point estimate; HAC SE from second stage (not corrected for generated regressor)"})
    r = pd.DataFrame(rows)
    r["t"] = r.coef / r.se
    r.to_csv(OUT / "phi_estimates.csv", index=False)
    print(r[["spec", "coef", "se", "t", "n"]].round(3).to_string(index=False))
    print("\nsample years:", int(d.dropna(subset=["PIC", "dS1"]).index.min()), "-", int(d.dropna(subset=["PIC", "dS1"]).index.max()))


if __name__ == "__main__":
    main()
