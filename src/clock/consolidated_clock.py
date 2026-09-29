"""Consolidated (Treasury + Fed) rollover clock, 2003-2025.

Interest-bearing consolidated liabilities to the private sector:
  marketable Treasuries held outside the Fed (MSPD par minus SOMA par, by CUSIP)
  + reserve balances + reverse repos (both reprice overnight).
Currency (zero interest) and the TGA (intragovernmental) are excluded.
SOMA and H.4.1 are Wednesday levels; the Wednesday nearest before each MSPD year-end is used.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .treasury_clock import FRN_RESET_YEARS, G_BASELINE, HORIZONS, securities

OVERNIGHT = 1 / 365.25
OUT = Path("data/processed/clock")


def soma_by_cusip(soma: pd.DataFrame) -> pd.DataFrame:
    s = soma.copy()
    s["soma_par"] = (pd.to_numeric(s.parValue, errors="coerce").fillna(0)
                     + pd.to_numeric(s.inflationCompensation, errors="coerce").fillna(0)) / 1e6
    return s.groupby(["year", "asOfDate", "cusip"], as_index=False).soma_par.sum()


def build() -> tuple[pd.DataFrame, pd.DataFrame]:
    sec = securities(pd.read_csv("data/interim/mspd/table3_market_yearend.csv", dtype=str))
    sec["year"] = sec.record_date.dt.year
    soma = soma_by_cusip(pd.read_csv("data/interim/fed/soma_tsy_yearend.csv", dtype=str))
    h41 = pd.read_csv("data/interim/fed/h41_wednesday_levels.csv")
    rows, checks = [], []
    soma["year"] = soma.year.astype(int)
    for y, s in soma.groupby("year"):
        asof = s.asOfDate.iloc[0]
        lev = h41.loc[h41.date <= asof].iloc[-1]        # H.4.1 Wednesday on or before SOMA as-of
        x = sec[sec.year == y].merge(s[["cusip", "soma_par"]], on="cusip", how="left").fillna({"soma_par": 0})
        unmatched = s.soma_par[~s.cusip.isin(x.cusip)].sum()
        x["private"] = x.par - x.soma_par
        on = lev.reserves + lev.reverse_repo
        tau = np.r_[x.tau.values, OVERNIGHT]
        w = np.r_[x.private.values, on]
        tot = w.sum()
        row = {"year": y, "asof": asof, "private_tsy": x.private.sum(), "overnight_fed": on,
               "consol_total": tot, "overnight_share": (on + x.loc[x.kind == "frn", "private"].sum()) / tot,
               "wam_years": (w * tau).sum() / tot}
        for h in HORIZONS:
            F = w[tau <= h].sum() / tot
            row[f"F_{h}"] = F
            row[f"P_{h}"] = 1 - (1 - F) * np.exp(-G_BASELINE * h)
        rows.append(row)
        checks.append({"year": y, "asof": asof, "h41_date": lev.date, "soma_cusip_sum": s.soma_par.sum(),
                       "h41_outright": lev.soma_tsy_outright, "soma_unmatched_in_mspd": unmatched,
                       "negative_private_cusips": int((x.private < -1).sum())})
    return pd.DataFrame(rows), pd.DataFrame(checks)


def main() -> None:
    c, chk = build()
    chk["err_pct"] = 100 * (chk.soma_cusip_sum / chk.h41_outright - 1)
    OUT.mkdir(parents=True, exist_ok=True)
    c.to_csv(OUT / "consolidated_clock_yearend.csv", index=False)
    chk.to_csv(OUT / "consolidated_checks.csv", index=False)
    print(chk.round(3).to_string())
    print(c[["year", "private_tsy", "overnight_fed", "overnight_share", "wam_years", "F_1", "P_1", "P_2", "P_5", "P_10"]].round(3).to_string())


if __name__ == "__main__":
    main()
