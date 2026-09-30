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
  # Financial Accounts of the United States (Z.1): U.S. currency held abroad
  mkdir -p data/raw/fed/z1
  curl -fsSL -o data/raw/fed/z1/z1.zip "https://www.federalreserve.gov/datadownload/Output.aspx?rel=Z1&filetype=zip"
  (cd data/raw/fed/z1 && unzip -oq z1.zip Z1_data.xml)
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
  # Debt held by the public, real and potential GDP: fiscal-response regressions (Section 5.3)
  for s in FYGFDPUN FYPUGDA188S GDPC1 GDPPOT CPIAUCSL EXPINF10YR; do
    curl -fsSL -o data/raw/fred/$s.csv "https://fred.stlouisfed.org/graph/fredgraph.csv?id=$s"
  done
  # Section 6: nominal and real GDP for the United Kingdom and Japan; Japan CPI before 2020
  for s in UKNGDP NGDPRSAXDCGBQ JPNNGDP JPNRGDPEXP JPNCPIALLMINMEI; do
    curl -fsSL -o data/raw/fred/$s.csv "https://fred.stlouisfed.org/graph/fredgraph.csv?id=$s"
  done
  # Section 6: Bank of England, ONS, Ministry of Finance, Bank of Japan
  # (the DMO's gilts-in-issue reports are committed in data/manual/uk_dmo/)
  python3 -m src.intl.uk_fetch
  python3 -m src.intl.jp_fetch
  # Section 5.3, Appendix C: OBR and CBO forecast revisions; OECD and BIS panel
  python3 -m src.fiscal.fetch_phi
  python3 -m src.fiscal.panel_fetch
fi

# Treasury MSPD, auctions and average rates (FiscalData API) and SOMA by CUSIP (NY Fed API);
# API pages are cached under data/raw/, so reruns do not download them again.
python3 -m src.clock.fetch_mspd
python3 -m src.clock.fetch_fed
python3 -m src.clock.fetch_backtest
python3 -m src.clock.fetch_z1

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
python3 -m src.clock.inflation_test

# Sections 5 and 7: the two-layer limit, identification attempt, counterfactuals
python3 -m src.limit.limit_map
python3 -m src.limit.limit_map_long
python3 -m src.fiscal.fiscal_response
python3 -m src.fiscal.identify_phi
python3 -m src.limit.counterfactuals
python3 -m src.limit.decompose
python3 -m src.limit.level_metric
python3 -m src.limit.time_to_limit
python3 -m src.limit.robustness
python3 -m src.limit.psi_regimes
python3 -m src.fiscal.breaks
python3 -m src.fiscal.phi_obr
python3 -m src.fiscal.phi_cbo
python3 -m src.fiscal.phi_panel

# Section 6: the United Kingdom and Japan
python3 -m src.intl.uk_stock
python3 -m src.intl.uk_apf
python3 -m src.intl.uk_clock
python3 -m src.intl.jp_stock
python3 -m src.intl.jp_boj
python3 -m src.intl.jp_clock
python3 -m src.intl.phi_star
python3 -m src.intl.uk_inflation_test
python3 -m src.intl.jp_inflation_test

# Figures 1-5
python3 -m src.limit.plot_limit_map_long
python3 -m src.limit.plot_time_to_limit
python3 -m src.paper.figures
python3 -m src.intl.comparison
echo "Done. Outputs in data/processed/, figures in paper/figures/."
