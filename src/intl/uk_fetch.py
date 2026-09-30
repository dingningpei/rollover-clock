"""United Kingdom: Bank of England database series and ONS price indices.

  boe_series.csv  LPMBL22 reserve balances, LPMAVAA notes and coin (£mn, month-end), IUDBEDR Bank Rate
  boe_yields.csv  IUDSOIA SONIA; nominal par yields 5/10/20y (IUDSNPY, IUDMNPY, IUDLNPY)
  boe_curves.csv  zero-coupon nominal (IUD?NZC), real (IUD?RZC) and implied RPI inflation (IUD?IZC)
                  at 5 (S), 10 (M) and 20 (L) years, daily
  ons_prices.csv  CPI (D7BT, 2015=100) and RPI (CHAW, Jan 1987=100), monthly
  data/raw/uk/boe/  APF gilt purchase and sale results, 2022 financial-stability operations,
                    and the Bank's table of current APF holdings (src/intl/uk_apf.py)
"""
from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import requests

BOE = Path("data/raw/uk/boe_db")
ONS = Path("data/raw/uk/ons")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
BOE_URL = ("https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp?csv.x=yes"
           "&Datefrom=01/Jan/2006&Dateto=31/Dec/2026&SeriesCodes={codes}&CSVF=TN&UsingCodes=Y&VPD=Y&VFD=N")
REQUESTS = {"boe_series": ["LPMBL22", "LPMAVAA", "IUDBEDR"],
            "boe_yields": ["IUDSOIA", "IUDSNPY", "IUDMNPY", "IUDLNPY"],
            "boe_curves": [f"IUD{t}{k}ZC" for k in "NRI" for t in "SML"]}
APF = Path("data/raw/uk/boe")
APF_FILES = {"asset-purchase-facility": ["gilt-purchase-operational-results", "gilt-sales-time-series",
                                         "finanical-stability-gilt-sales-time-series", "table-for-website"],
             "other-market-operations": ["long-dated-uk-government-bond-purchase-time-series",
                                         "index-linked-gilt-purchase-results"]}
ONS_URL = "https://www.ons.gov.uk/generator?format=csv&uri=/economy/inflationandpriceindices/timeseries/{s}/mm23"


def main() -> None:
    BOE.mkdir(parents=True, exist_ok=True)
    ONS.mkdir(parents=True, exist_ok=True)
    for name, codes in REQUESTS.items():
        r = requests.get(BOE_URL.format(codes=",".join(codes)), headers=UA, timeout=60)
        r.raise_for_status()
        (BOE / f"{name}.csv").write_text(r.text)
        print(name, len(r.text.splitlines()), "rows")
    out = {}
    for s in ("D7BT", "CHAW"):
        r = requests.get(ONS_URL.format(s=s.lower()), headers=UA, timeout=60)
        r.raise_for_status()
        d = pd.read_csv(io.StringIO(r.text), header=None, names=["period", "value"])
        d = d[d.period.str.fullmatch(r"\d{4} [A-Z]{3}")]
        out[s] = pd.Series(pd.to_numeric(d.value).values, index=pd.to_datetime(d.period, format="%Y %b"))
    p = pd.DataFrame(out).rename_axis("month")
    p.index = p.index.strftime("%Y-%m")
    p.to_csv(ONS / "ons_prices.csv")
    print("ons_prices", p.index.min(), p.index.max())
    APF.mkdir(parents=True, exist_ok=True)
    for folder, names in APF_FILES.items():
        for f in names:
            r = requests.get(f"https://www.bankofengland.co.uk/-/media/boe/files/markets/{folder}/{f}.xlsx",
                             headers=UA, timeout=60)
            r.raise_for_status()
            (APF / f"{f}.xlsx").write_bytes(r.content)
    print("APF files saved")


if __name__ == "__main__":
    main()
