"""Download year-end MSPD snapshots (Table 3 Market: security level; Table 1: totals).

Raw pages are cached under data/raw/fiscaldata/ (git-ignored).
Usage: python -m src.clock.fetch_mspd --start 2001 --end 2025
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .fiscaldata import fetch_all

MARKET = "/v1/debt/mspd/mspd_table_3_market"
SUMMARY = "/v1/debt/mspd/mspd_table_1"
CACHE = Path("data/raw/fiscaldata")
OUT = Path("data/interim/mspd")


def year_end_dates(start: int, end: int) -> list[str]:
    return [f"{y}-12-31" for y in range(start, end + 1)]


def fetch(endpoint: str, dates: list[str], name: str) -> pd.DataFrame:
    rows = fetch_all(endpoint, {"filter": "record_date:in:(" + ",".join(dates) + ")",
                                "sort": "record_date"}, CACHE / name / f"{dates[0]}_{dates[-1]}")
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=2001)
    ap.add_argument("--end", type=int, default=2025)
    a = ap.parse_args()
    dates = year_end_dates(a.start, a.end)
    OUT.mkdir(parents=True, exist_ok=True)
    mkt = fetch(MARKET, dates, "mspd_table_3_market")
    summ = fetch(SUMMARY, dates, "mspd_table_1")
    mkt.to_csv(OUT / "table3_market_yearend.csv", index=False)
    summ.to_csv(OUT / "table1_yearend.csv", index=False)
    print("table3 rows", len(mkt), "dates", mkt.record_date.nunique())
    print("table1 rows", len(summ), "dates", summ.record_date.nunique())


if __name__ == "__main__":
    main()
