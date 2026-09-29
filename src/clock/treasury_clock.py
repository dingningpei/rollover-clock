"""Treasury-only rollover clock from year-end MSPD security-level snapshots.

F_t(h): share of par (incl. TIPS inflation adjustment) repricing within h years.
P_t(h) = 1 - (1 - F_t(h)) * exp(-g h): adds growth-financing issuance at the new rate
(paper, Section 3.1). Repricing: bills/notes/bonds/TIPS at maturity; FRNs weekly.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

IN = Path("data/interim/mspd")
OUT = Path("data/processed/clock")
HORIZONS = [0.25, 0.5, 1, 2, 3, 5, 7, 10]
G_BASELINE = 0.04
FRN_RESET_YEARS = 7 / 365.25
CLASS_MAP = {"Bills Maturity Value": "bill", "Notes": "note", "Bonds": "bond",
             "Inflation-Protected Securities": "tips", "Inflation-Indexed Notes": "tips",
             "Inflation-Indexed Bonds": "tips", "Floating Rate Notes": "frn"}


def securities(market: pd.DataFrame) -> pd.DataFrame:
    """One row per (record_date, CUSIP); the par amount sits on the CUSIP's first line."""
    m = market[market.security_class2_desc.str.match(r"^[0-9A-Z]{9}$", na=False)].copy()
    m["par"] = pd.to_numeric(m.outstanding_amt, errors="coerce")
    m["kind"] = m.security_class1_desc.map(CLASS_MAP)
    agg = (m.groupby(["record_date", "security_class2_desc"], as_index=False)
             .agg(kind=("kind", "first"), maturity_date=("maturity_date", "first"),
                  coupon=("interest_rate_pct", "first"), par=("par", "sum")))
    agg = agg.rename(columns={"security_class2_desc": "cusip"})
    agg["record_date"] = pd.to_datetime(agg.record_date)
    agg["maturity_date"] = pd.to_datetime(agg.maturity_date)
    agg = agg[agg.maturity_date > agg.record_date]           # unmatured only
    agg["tau"] = (agg.maturity_date - agg.record_date).dt.days / 365.25
    agg.loc[agg.kind == "frn", "tau"] = FRN_RESET_YEARS
    return agg


def official_totals(market: pd.DataFrame) -> pd.Series:
    """Official unmatured totals by class. Matched by keyword: MSPD labels vary and
    contain typos (e.g. "Total Tresasury Floating Rate Notes", 2016-12-31)."""
    lab = market.security_class2_desc.fillna("")
    is_total = lab.str.startswith("Total") & ~lab.str.contains("Matured")
    nominal = lab.str.contains("Unmatured")                       # bills, notes, bonds
    other = lab.str.contains("TIPS|Inflation|Floating")           # no matured split published
    t = market[is_total & (nominal | other)].copy()
    t["amt"] = pd.to_numeric(t.outstanding_amt, errors="coerce")
    t["record_date"] = pd.to_datetime(t.record_date)
    return t.groupby("record_date").amt.sum()


def clock(sec: pd.DataFrame, g: float = G_BASELINE) -> pd.DataFrame:
    rows = []
    for d, x in sec.groupby("record_date"):
        tot = x.par.sum()
        row = {"record_date": d, "par_total": tot,
               "wam_years": (x.par * x.tau).sum() / tot}
        for h in HORIZONS:
            F = x.loc[x.tau <= h, "par"].sum() / tot
            row[f"F_{h}"] = F
            row[f"P_{h}"] = 1 - (1 - F) * np.exp(-g * h)
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    market = pd.read_csv(IN / "table3_market_yearend.csv", dtype=str)
    sec = securities(market)
    rec = sec.groupby("record_date").par.sum().to_frame("engine").join(official_totals(market).rename("official"))
    rec["err_pct"] = 100 * (rec.engine / rec.official - 1)
    rec.to_csv(OUT / "treasury_reconciliation.csv")
    print(rec.assign(engine=rec.engine / 1e6, official=rec.official / 1e6).round(4).to_string())
    c = clock(sec)
    c.to_csv(OUT / "treasury_clock_yearend.csv", index=False)
    print(c[["record_date", "wam_years", "F_1", "F_2", "F_5", "P_1", "P_2", "P_5", "P_10"]].round(3).to_string())


if __name__ == "__main__":
    main()
