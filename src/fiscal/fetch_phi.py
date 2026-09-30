"""Inputs for the fiscal-response evidence (Section 5.3, Appendix C).

OBR (obr.uk/data): fiscal forecast revisions database and historical official forecasts database.
CBO (github.com/US-CBO/eval-projections, input_data): baselines, baseline changes, actual GDP.
Outputs: data/raw/uk/obr/, data/raw/us/cbo_eval/
"""
from __future__ import annotations

from pathlib import Path

import requests

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
OBR = Path("data/raw/uk/obr")
CBO = Path("data/raw/us/cbo_eval")
OBR_FILES = ["forecast-revisions-database-march-2025", "historical-official-forecasts-database"]
CBO_URL = "https://raw.githubusercontent.com/US-CBO/eval-projections/main/input_data/{f}.csv"


def main() -> None:
    OBR.mkdir(parents=True, exist_ok=True)
    CBO.mkdir(parents=True, exist_ok=True)
    for f in OBR_FILES:
        r = requests.get(f"https://obr.uk/download/{f}/", headers=UA, timeout=120)
        r.raise_for_status()
        (OBR / f"{f}.xlsx").write_bytes(r.content)
    for f in ("baseline_changes", "baselines", "actual_GDP"):
        r = requests.get(CBO_URL.format(f=f), timeout=120)
        r.raise_for_status()
        (CBO / f"{f}.csv").write_text(r.text)
    print("saved OBR and CBO inputs")


if __name__ == "__main__":
    main()
