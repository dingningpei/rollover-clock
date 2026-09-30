"""U.S. currency held abroad, from the Financial Accounts of the United States (Z.1).

Reads the DDP bulk file data/raw/fed/z1/Z1_data.xml
(https://www.federalreserve.gov/datadownload/Output.aspx?rel=Z1&filetype=zip) and keeps
  FL263025003.Q  rest of the world; U.S. currency; asset ($mn, end of quarter).
Output: data/interim/fed/z1_currency_abroad.csv
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

SERIES = {"FL263025003.Q": "currency_abroad"}
OUT = Path("data/interim/fed")


def main() -> None:
    rows, keep = [], None
    for ev, el in ET.iterparse("data/raw/fed/z1/Z1_data.xml", events=("start", "end")):
        tag = el.tag.split("}")[-1]
        if ev == "start" and tag == "Series":
            keep = SERIES.get(el.attrib.get("SERIES_NAME"))
        elif ev == "end" and tag == "Obs" and keep:
            rows.append((keep, el.attrib["TIME_PERIOD"], el.attrib.get("OBS_VALUE")))
        elif ev == "end" and tag == "Series":
            keep = None
            el.clear()
    d = pd.DataFrame(rows, columns=["series", "date", "value"])
    d["value"] = pd.to_numeric(d.value, errors="coerce")
    d = d.pivot(index="date", columns="series", values="value").reset_index()
    OUT.mkdir(parents=True, exist_ok=True)
    d.to_csv(OUT / "z1_currency_abroad.csv", index=False)
    print(d.tail(3).to_string(index=False))


if __name__ == "__main__":
    main()
