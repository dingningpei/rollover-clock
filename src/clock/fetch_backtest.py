"""Inputs for the interest-rate backtest.

- FiscalData average interest rates (monthly, by security class), 2001-.
- FiscalData auctions (issue dates 2000-), for the issuance mix by term.
- H.15 monthly yields (nominal CMT, TIPS real CMT, bill rates) from the DDP bulk file
  data/raw/fed/H15_data.xml (https://www.federalreserve.gov/datadownload/Output.aspx?rel=H15&filetype=zip).
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

from .fiscaldata import fetch_all

CACHE = Path("data/raw/fiscaldata")
OUT = Path("data/interim/backtest")
H15 = {"RIFLGFCM01_N.M": "n0.0833", "RIFLGFCM03_N.M": "n0.25", "RIFLGFCM06_N.M": "n0.5",
       "RIFLGFCY01_N.M": "n1", "RIFLGFCY02_N.M": "n2", "RIFLGFCY03_N.M": "n3", "RIFLGFCY05_N.M": "n5",
       "RIFLGFCY07_N.M": "n7", "RIFLGFCY10_N.M": "n10", "RIFLGFCY20_N.M": "n20", "RIFLGFCY30_N.M": "n30",
       "RIFLGFCY05_XII_N.M": "r5", "RIFLGFCY07_XII_N.M": "r7", "RIFLGFCY10_XII_N.M": "r10",
       "RIFLGFCY20_XII_N.M": "r20", "RIFLGFCY30_XII_N.M": "r30", "RIFSPFF_N.M": "effr"}


def h15_monthly() -> pd.DataFrame:
    rows, keep = [], None
    for ev, el in ET.iterparse("data/raw/fed/H15_data.xml", events=("start", "end")):
        tag = el.tag.split("}")[-1]
        if ev == "start" and tag == "Series":
            keep = H15.get(el.attrib.get("SERIES_NAME"))
        elif ev == "end" and tag == "Obs" and keep:
            rows.append((keep, el.attrib["TIME_PERIOD"], el.attrib.get("OBS_VALUE")))
        elif ev == "end" and tag == "Series":
            keep = None
            el.clear()
    df = pd.DataFrame(rows, columns=["tenor", "month", "value"])
    df["value"] = pd.to_numeric(df.value, errors="coerce")
    df.loc[df.value <= -9000, "value"] = float("nan")              # H.15 missing-value sentinel (-9999)
    df["month"] = df.month.str[:7]                                  # YYYY-MM
    return df.pivot(index="month", columns="tenor", values="value").reset_index()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    avg = pd.DataFrame(fetch_all("/v2/accounting/od/avg_interest_rates", {"sort": "record_date"},
                                 CACHE / "avg_interest_rates"))
    avg.to_csv(OUT / "avg_interest_rates.csv", index=False)
    auc = pd.DataFrame(fetch_all("/v1/accounting/od/auctions_query",
                                 {"filter": "issue_date:gte:2000-01-01", "sort": "issue_date"},
                                 CACHE / "auctions_2000"))
    auc.to_csv(OUT / "auctions.csv", index=False)
    h = h15_monthly()
    h.to_csv(OUT / "h15_monthly.csv", index=False)
    print("avg rates", len(avg), avg.record_date.min(), avg.record_date.max())
    print("auctions", len(auc), auc.issue_date.min(), auc.issue_date.max())
    print("h15", h.month.min(), h.month.max(), h.columns.tolist())


if __name__ == "__main__":
    main()
