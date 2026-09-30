"""Cross-country panel for identifying the fiscal response phi (advanced economies, annual).

OECD Economic Outlook (SDMX, dataflow DSD_EO@DF_EO), general government:
  NLGXQ   primary balance, % of GDP;  NLGXQU underlying primary balance, % of potential GDP
  NLGXQA  cyclically adjusted primary balance, % of potential GDP
  GGINTP  gross interest payments;  GNINTQ net interest payments, % of GDP;  GDP nominal GDP
  GGFLQ   gross financial liabilities, % of GDP;  GAP output gap, % of potential GDP
  IRS / IRL  short- and long-term interest rates, %
  RFSH    share of outstanding marketable debt to refinance within the coming year (from 2013)
BIS debt securities statistics (WS_NA_SEC_DSS): general government debt securities outstanding,
  all and short-term original maturity (bills), quarterly -> year-end bills share.
Outputs: data/raw/panel/oecd_eo.csv, data/raw/panel/bis_dss_gg.csv
"""
from __future__ import annotations

from pathlib import Path

import requests

OUT = Path("data/raw/panel")
UA = {"User-Agent": "Mozilla/5.0"}
COUNTRIES = ["AUS", "AUT", "BEL", "CAN", "CHE", "DEU", "DNK", "ESP", "FIN", "FRA", "GBR", "GRC", "IRL", "ISL",
             "ITA", "JPN", "KOR", "NLD", "NOR", "NZL", "PRT", "SWE", "USA"]
MEASURES = ["NLGXQ", "NLGXQU", "NLGXQA", "GGINTP", "GNINTQ", "GDP", "GGFLQ", "GAP", "IRS", "IRL", "RFSH"]
EO = ("https://sdmx.oecd.org/public/rest/data/OECD.ECO.MAD,DSD_EO@DF_EO,/{c}.{m}.A"
      "?startPeriod=1970&format=csvfilewithlabels")
BIS = ("https://stats.bis.org/api/v2/data/dataflow/BIS/WS_NA_SEC_DSS/1.0/"
       "Q.N.*.*.S13.S1.N.L.LE.F3.*.*.*.*.*.*.*.*?format=csv")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    r = requests.get(EO.format(c="+".join(COUNTRIES), m="+".join(MEASURES)), headers=UA, timeout=300)
    r.raise_for_status()
    (OUT / "oecd_eo.csv").write_text(r.text)
    r = requests.get(BIS, headers={**UA, "Accept": "text/csv"}, timeout=600)
    r.raise_for_status()
    (OUT / "bis_dss_gg.csv").write_text(r.text)
    print("saved", [p.name for p in OUT.iterdir()])


if __name__ == "__main__":
    main()
