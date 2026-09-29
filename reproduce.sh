#!/usr/bin/env bash
# Reproduce every number, table and figure in the paper from public sources.
#   bash reproduce.sh            # download inputs, then run the pipeline
#   bash reproduce.sh --no-fetch # skip the bulk-file downloads (reuse data/raw/)
# Hand-transcribed or hand-collected inputs are committed in data/manual/.
set -euo pipefail
cd "$(dirname "$0")"

if [[ "${1:-}" != "--no-fetch" ]]; then
  mkdir -p data/raw/fed/soma data/raw/bea
  # Federal Reserve Data Download Program bulk files (H.4.1 balance sheet, H.15 yields)
  curl -fsSL -o data/raw/fed/h41.zip "https://www.federalreserve.gov/datadownload/Output.aspx?rel=H41&filetype=zip"
  curl -fsSL -o data/raw/fed/h15.zip "https://www.federalreserve.gov/datadownload/Output.aspx?rel=H15&filetype=zip"
  (cd data/raw/fed && unzip -oq h41.zip && unzip -oq h15.zip)
  # New York Fed: effective federal funds rate and the end-2021 SOMA MBS book
  curl -fsSL -o data/raw/fed/effr_2021_2025.json \
    "https://markets.newyorkfed.org/api/rates/unsecured/effr/search.json?startDate=2021-12-01&endDate=2025-12-31"
  curl -fsSL -o data/raw/fed/soma/mbs_2021-12-29.json \
    "https://markets.newyorkfed.org/api/soma/mbs/get/asof/2021-12-29.json"
  # BEA NIPA annual tables (nominal GDP, primary surplus)
  curl -fsSL -o data/raw/bea/NipaDataA.txt "https://apps.bea.gov/national/Release/TXT/NipaDataA.txt"
  # Currency in circulation and reserve balances (monthly, $bn), 1980-2002: the zero-interest base
  mkdir -p data/raw/fred
  curl -fsSL -o data/raw/fred/CURRCIR.csv "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CURRCIR"
  curl -fsSL -o data/raw/fred/RESBALNS.csv "https://fred.stlouisfed.org/graph/fredgraph.csv?id=RESBALNS"
fi

# Treasury MSPD, auctions and average rates (FiscalData API) and SOMA by CUSIP (NY Fed API);
# API pages are cached under data/raw/, so reruns do not download them again.
python3 -m src.clock.fetch_mspd
python3 -m src.clock.fetch_fed
python3 -m src.clock.fetch_backtest

# Section 3 / Appendix B: model checks
python3 -m src.model.derive_stability
python3 -m src.model.check_repricing_law
python3 -m src.model.scan_stability

# Section 4: the rollover clock and its validation
python3 -m src.clock.treasury_clock
python3 -m src.clock.consolidated_clock
python3 -m src.clock.inflation_layer
python3 -m src.clock.backtest
python3 -m src.clock.freeze_2021
python3 -m src.clock.fd5_clock

# Sections 5-6: the two-layer limit, identification attempt, counterfactuals
python3 -m src.limit.limit_map
python3 -m src.limit.limit_map_long
python3 -m src.fiscal.identify_phi
python3 -m src.limit.counterfactuals

# Figures 1-3
python3 -m src.limit.plot_limit_map_long
python3 -m src.paper.figures
echo "Done. Outputs in data/processed/, figures in paper/figures/."
