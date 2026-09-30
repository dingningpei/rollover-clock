"""Japan: Bank of Japan time series via the BOJ Time-Series Data Search API
(https://www.stat-search.boj.or.jp/api/v1/getDataCode), and JGB yields from MOF.

Series (monthly unless noted; 100 million yen):
  BS01  MABJMA5A  BoJ assets: financing bills, T-bills and treasury discount bills
        MABJMA5B  BoJ assets: JGBs
        MABJML1   BoJ liabilities: banknotes
        MABJML11  BoJ liabilities: current deposits
        MABJML3   BoJ liabilities: deposits of the government
  MD08  MACAB3202 / 3203 / 3204  current-account balances of institutions under the
        complementary deposit facility at a positive / zero / negative rate (average
        outstanding; through February 2024, when the three tiers ended)
  MD07  MAREM3    required reserves (average outstanding)
  PF02  PFGD11    national government debt: internal JGBs;  PFGD@01 treasury discount bills
        PFGD211 / PFGD@02  held by the government;  PFGD221 / PFGD@04  held by the BoJ;
        PFGD231 / PFGD@05  held by others
  FM01  STRDCLUCON  uncollateralized overnight call rate, daily average (%)
MOF: JGB constant-maturity yields, daily (jgbcm_all.csv); debt yearbook part 09 (Table 34,
JGBs by issue), FY2020-2024.
BoJ: JGB holdings by issue at fiscal year-ends (mei*.xlsx).
Outputs: data/raw/jp/boj_api/<db>.csv (long: series, date, value), data/raw/jp/mof/jgbcm_all.csv,
data/raw/jp/mof/nenpou/, data/raw/jp/boj/
"""
from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

import pandas as pd

from src.intl.jp_boj import FILES as BOJ_FILES

API = "https://www.stat-search.boj.or.jp/api/v1/getDataCode"
OUT = Path("data/raw/jp/boj_api")
REQUESTS = {  # start and end are YYYYMM for every frequency
    "BS01": (["MABJMA5A", "MABJMA5B", "MABJML1", "MABJML11", "MABJML3"], "200001", "202612"),
    "MD08": (["MACAB3202", "MACAB3203", "MACAB3204"], "201601", "202612"),
    "MD07": (["MAREM3"], "200001", "202612"),
    "PF02": (["PFGD11", "PFGD@01", "PFGD211", "PFGD@02", "PFGD221", "PFGD@04", "PFGD231", "PFGD@05"],
             "200001", "202612"),
    "FM01": (["STRDCLUCON"], "200001", "202612"),              # daily data, requested by month
}


def get(db: str, codes: list[str], start: str, end: str) -> pd.DataFrame:
    rows, pos = [], ""
    while True:
        url = (f"{API}?format=json&lang=en&db={db}&startDate={start}&endDate={end}&code={','.join(codes)}"
               + (f"&startPosition={pos}" if pos else ""))
        with urllib.request.urlopen(url, timeout=120) as r:
            js = json.loads(r.read().decode("utf-8"))
        for s in js.get("RESULTSET", []):
            v = s["VALUES"]
            rows += [(s["SERIES_CODE"], d, x) for d, x in zip(v["SURVEY_DATES"], v["VALUES"])]
        pos = js.get("NEXTPOSITION")
        if not pos:
            break
        time.sleep(1)
    return pd.DataFrame(rows, columns=["series", "date", "value"])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for db, (codes, start, end) in REQUESTS.items():
        d = get(db, codes, start, end)
        d.to_csv(OUT / f"{db}.csv", index=False)
        print(db, len(d), d.groupby("series").date.agg(["min", "max"]).to_dict("index"))
        time.sleep(2)                                   # the API asks users to avoid rapid requests
    mof = Path("data/raw/jp/mof")
    mof.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve("https://www.mof.go.jp/jgbs/reference/interest_rate/data/jgbcm_all.csv",
                               mof / "jgbcm_all.csv")
    print("MOF yields saved")
    (mof / "nenpou").mkdir(exist_ok=True)
    for fy in range(2020, 2025):
        f = f"{fy}nenpou09.xlsx"
        urllib.request.urlretrieve(f"https://www.mof.go.jp/jgbs/publication/annual_report/{fy}/{f}", mof / "nenpou" / f)
        time.sleep(1)
    boj = Path("data/raw/jp/boj")
    boj.mkdir(parents=True, exist_ok=True)
    for f in BOJ_FILES.values():
        urllib.request.urlretrieve(f"https://www.boj.or.jp/en/statistics/boj/other/mei/release/20{f[3:5]}/{f}", boj / f)
        time.sleep(1)
    print("MOF yearbooks and BoJ holdings saved")


if __name__ == "__main__":
    main()
