"""Fed inputs for the consolidated clock.

1. H.4.1 Wednesday levels (reserves, reverse repos, Federal Reserve notes) from the
   DDP bulk file data/raw/fed/H41_data.xml (downloaded from
   https://www.federalreserve.gov/datadownload/Output.aspx?rel=H41&filetype=zip).
2. SOMA Treasury holdings by CUSIP (NY Fed API) at the last as-of date of each year.
"""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.request import urlopen

import pandas as pd

RAW = Path("data/raw/fed")
OUT = Path("data/interim/fed")
H41_SERIES = {"RESH4R_N.WW": "reserves", "RESPPLLR_N.WW": "reverse_repo", "RESPPLLN_N.WW": "fr_notes",
              "RESTBC_N.WW": "currency",               # currency in circulation (incl. Treasury coin)
              "RESPPALGUO_N.WW": "soma_tsy_outright",
              "RESPPALGASMO_N.WW": "soma_mbs", "RESPPLLOP_N.WW": "remittances_due",
              "RESPPALGUOMI_N.WW": "soma_tips_infl_comp",
              "RESPPALSP_N.WW": "unamort_premium", "RESPPALSD_N.WW": "unamort_discount"}
SOMA = "https://markets.newyorkfed.org/api/soma"


def h41_levels() -> pd.DataFrame:
    rows, keep = [], None
    for ev, el in ET.iterparse(RAW / "H41_data.xml", events=("start", "end")):
        tag = el.tag.split("}")[-1]
        if ev == "start" and tag == "Series":
            keep = H41_SERIES.get(el.attrib.get("SERIES_NAME"))
        elif ev == "end" and tag == "Obs" and keep:
            rows.append((keep, el.attrib["TIME_PERIOD"], el.attrib.get("OBS_VALUE")))
        elif ev == "end" and tag == "Series":
            keep = None
            el.clear()
    df = pd.DataFrame(rows, columns=["series", "date", "value"])
    df["value"] = pd.to_numeric(df.value, errors="coerce")          # millions of dollars
    return df.pivot(index="date", columns="series", values="value").reset_index()


def soma_year_end(start: int, end: int) -> pd.DataFrame:
    dates = sorted(json.load(urlopen(f"{SOMA}/asofdates/list.json", timeout=120))["soma"]["asOfDates"])
    out = []
    for y in range(start, end + 1):
        d = max(x for x in dates if x <= f"{y}-12-31")
        cache = RAW / "soma" / f"{d}.json"
        if not cache.exists():
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(urlopen(f"{SOMA}/tsy/get/asof/{d}.json", timeout=120).read().decode())
        h = pd.DataFrame(json.loads(cache.read_text())["soma"]["holdings"])
        h["year"] = y
        out.append(h)
    return pd.concat(out, ignore_index=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    h41 = h41_levels()
    h41.to_csv(OUT / "h41_wednesday_levels.csv", index=False)
    print("H.4.1:", h41.date.min(), "to", h41.date.max(), len(h41), "weeks")
    soma = soma_year_end(2003, 2025)
    soma.to_csv(OUT / "soma_tsy_yearend.csv", index=False)
    print("SOMA:", soma.groupby("year").asOfDate.first().to_dict())


if __name__ == "__main__":
    main()
