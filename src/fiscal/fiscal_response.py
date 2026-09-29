"""Own estimate of the fiscal response (paper, Section 5.3).

Two specifications, annual calendar years, NIPA federal primary surplus S_t (% of GDP,
excluding Fed remittances, as in the consolidated government):

  Bohn:      S_t = c + rho   * b_{t-1}  [+ lam * S_{t-1}] + beta*gap_t + gamma*gvar_t + delta*covid_t + e_t
  Interest:  S_t = c + phi_I * IC_{t-1} [+ lam * S_{t-1}] + beta*gap_t + gamma*gvar_t + delta*covid_t + e_t

Static (no lagged surplus) and partial-adjustment versions; the long-run response in the
latter is coef / (1 - lam).

b      debt held by the public / GDP (FRED FYGFDPUN, Q4, from 1970), in %; the consolidated
       b of the paper (1980-2025) as an alternative
IC     federal interest payments / GDP (NIPA A091RC), in %
gap    output gap, 100*(real GDP / potential - 1), annual mean (CBO via FRED)
gvar   temporary defense spending: defense / GDP (NIPA A824RC) minus its HP trend (Barro, Bohn)
covid  dummy for 2020-2021

Mapping to the paper's phi. In the model s responds to interest cost with slope phi, so
at a steady state ds/db = phi * d(r b)/db = phi * (r + psi b). Hence
    phi = rho / (r + psi b),
and Bohn's condition rho > (r + psi b) - g is exactly (1 - phi)(r + psi b) < g.
The interest specification estimates phi directly (holding debt fixed through the controls).
HAC standard errors (Newey-West, 2 lags).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.filters.hp_filter import hpfilter

from src.fiscal.identify_phi import nipa

OUT = Path("data/processed/fiscal")
PSI = 0.03
CTRL = ["gap", "gvar", "covid"]
BREAK = 2004


def fred_q4(series: str) -> pd.Series:
    d = pd.read_csv(f"data/raw/fred/{series}.csv")
    d["date"] = pd.to_datetime(d.observation_date)
    d = d[d.date.dt.month == 10]
    return pd.Series(d[series].values, index=d.date.dt.year.values)


def fred_annual_mean(series: str) -> pd.Series:
    d = pd.read_csv(f"data/raw/fred/{series}.csv")
    d["year"] = pd.to_datetime(d.observation_date).dt.year
    return d.groupby("year")[series].mean()


def build() -> pd.DataFrame:
    f = nipa()
    n = pd.read_csv("data/raw/bea/NipaDataA.txt", dtype=str)
    n.columns = [c.strip() for c in n.columns]
    x = n[n.iloc[:, 0] == "A824RC"]
    defense = pd.Series(pd.to_numeric(x.iloc[:, 2].str.replace(",", "")).values, index=x.iloc[:, 1].astype(int).values)
    d = pd.DataFrame({"S": f.S, "IC": f.IC, "gdp": f.A191RC})
    d["b"] = 100 * fred_q4("FYGFDPUN") / d.gdp                     # debt held by the public, end of year, % GDP
    d["gap"] = 100 * (fred_annual_mean("GDPC1") / fred_annual_mean("GDPPOT") - 1)
    dshare = (100 * defense / d.gdp).dropna()
    cyc, trend = hpfilter(dshare.loc[1947:], lamb=100)
    d["gvar"] = cyc
    d["covid"] = d.index.isin([2020, 2021]).astype(float)
    lm = pd.read_csv("data/processed/limit/limit_map_1980_2025.csv").set_index("year")
    d["b_consol"] = 100 * lm.b
    d["m"] = lm.r + PSI * lm.b                                       # marginal interest cost r + psi b
    d["b_l"], d["IC_l"], d["b_consol_l"] = d.b.shift(1), d.IC.shift(1), d.b_consol.shift(1)
    d["S_l"] = d.S.shift(1)
    return d.loc[1960:2024]


def fit(d: pd.DataFrame, x: list[str]):
    s = d.dropna(subset=["S"] + x + CTRL)
    ctrl = [c for c in CTRL if s[c].std() > 0]
    return sm.OLS(s.S, sm.add_constant(s[x + ctrl])).fit(cov_type="HAC", cov_kwds={"maxlags": 2}), s


def estimate(d: pd.DataFrame, name: str, var: str, partial: bool) -> dict:
    m, s = fit(d, [var] + (["S_l"] if partial else []))
    lam = m.params.get("S_l", 0.0)
    lr = m.params[var] / (1 - lam)
    if partial:                                              # delta method for coef / (1 - lam)
        grad = np.array([1 / (1 - lam), m.params[var] / (1 - lam) ** 2])
        lr_se = float(np.sqrt(grad @ m.cov_params().loc[[var, "S_l"], [var, "S_l"]].values @ grad))
    else:
        lr_se = m.bse[var]
    scale = 1.0 if var == "IC_l" else s.m.mean()            # rho -> phi = rho / (r + psi b)
    return {"sample": name, "regressor": var, "spec": "partial" if partial else "static",
            "years": f"{s.index.min()}-{s.index.max()}", "n": int(m.nobs), "coef": m.params[var],
            "se": m.bse[var], "lam": lam, "long_run": lr, "m_mean": s.m.mean(),
            "phi_implied": lr / scale, "phi_se": lr_se / scale}


def break_test(d: pd.DataFrame, var: str, partial: bool) -> dict:
    s = d.dropna(subset=["S", "S_l", var] + CTRL).copy()
    s["post"] = (s.index >= BREAK).astype(float)
    s[f"{var}_post"] = s[var] * s.post
    x = [var, f"{var}_post", "post"] + (["S_l"] if partial else []) + CTRL
    m = sm.OLS(s.S, sm.add_constant(s[x])).fit(cov_type="HAC", cov_kwds={"maxlags": 2})
    return {"regressor": var, "spec": "partial" if partial else "static", "pre": m.params[var],
            "change": m.params[f"{var}_post"], "se_change": m.bse[f"{var}_post"],
            "p_change": m.pvalues[f"{var}_post"]}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = build()
    d.to_csv(OUT / "fiscal_response_data.csv")
    samples = {"1971-2003": (1971, 2003), "1984-2003": (1984, 2003), "2004-2024": (2004, 2024),
               "2004-2019": (2004, 2019), "1971-2024": (1971, 2024)}
    rows = []
    for name, (a, z) in samples.items():
        for var in ("b_l", "IC_l", "b_consol_l"):
            if var == "b_consol_l" and a < 1981:
                continue
            for partial in (False, True):
                rows.append(estimate(d.loc[a:z], name, var, partial))
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "fiscal_response_estimates.csv", index=False)
    b = pd.DataFrame([break_test(d.loc[a:2024], v, p) for v, a in (("b_l", 1971), ("IC_l", 1971), ("b_consol_l", 1981))
                      for p in (False, True)])
    b.to_csv(OUT / "fiscal_response_break.csv", index=False)
    # rolling 20-year windows, Bohn specification on debt held by the public
    roll = []
    for end in range(1990, 2025):
        m, s = fit(d.loc[end - 19:end], ["b_l"])
        roll.append({"end": end, "rho": m.params["b_l"], "se": m.bse["b_l"], "m_mean": s.m.mean(),
                     "phi": m.params["b_l"] / s.m.mean() if s.m.notna().any() else np.nan})
    roll = pd.DataFrame(roll)
    roll.to_csv(OUT / "fiscal_response_rolling.csv", index=False)
    pd.set_option("display.width", 200)
    print(t.round(4).to_string(index=False))
    print("\nBreak at", BREAK); print(b.round(4).to_string(index=False))
    print("\nRolling 20-year Bohn rho and implied phi"); print(roll.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
