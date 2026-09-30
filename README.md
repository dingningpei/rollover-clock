# The Rollover Clock

Replication package for

> Ningpei Ding (2026). **"The Rollover Clock: Debt Maturity, the Central-Bank Balance Sheet, and the Debt Limit of a Reserve-Currency Sovereign."** Working paper.

- Paper: [`paper/rollover_clock.pdf`](paper/rollover_clock.pdf), with source text in [`paper/manuscript.md`](paper/manuscript.md)
- Contact: dingningpei@gmail.com

## What the paper does

The debt limit of a reserve-currency sovereign has two layers.

- **Fiscal layer.** Debt is stable if and only if the primary surplus offsets at least a share φ\* = 1 − g/(r + ψb) of the marginal interest cost of debt. This threshold does not depend on maturity, for any repricing kernel.
- **Inflation layer.** If the fiscal response falls short, the inflation needed to fill the gap depends on two things:
  - the *rollover clock* P(h), how fast the consolidated Treasury + Federal Reserve liabilities reprice;
  - how much of those liabilities inflation can erode: nominal debt not yet repriced, and currency.

We measure the clock security by security for the United States, 1980–2025, and validate it:
- in a 2001–2024 backtest of the official average interest rate;
- out of sample on the 2022–25 tightening, frozen at end-2021, for both Treasury interest costs and the Fed's deferred asset.

Section 6 builds the same measures for the United Kingdom (2007–2025, gilt by gilt, net of the Bank of England's Asset Purchase Facility) and Japan (fiscal years 2020–2024, JGB by issue, net of the Bank of Japan).

## Reproducing the results

Requirements:
- Python ≥ 3.10;
- `pip install -r requirements.txt`;
- `curl` and `unzip`;
- about 1 GB of disk space.

```
bash reproduce.sh              # download all public inputs, then run everything
bash reproduce.sh --no-fetch   # rerun on inputs already in data/raw/
```

A full run takes about 10–20 minutes, mostly downloads. Outputs:

| Paper | Output |
|---|---|
| Section 3, Appendix B (stability, repricing law) | printed by `src/model/*` |
| Figure 1, Section 4.2 (the clock) | `data/processed/clock/*_clock_yearend.csv`, `paper/figures/fig1_*` |
| Table 1 (backtest) | `data/processed/clock/backtest_scores.csv` |
| Section 4.4, Figure 2 (2022–25 test) | `data/processed/clock/freeze2021_*.csv`, `paper/figures/fig2_*` |
| Section 4.5, Table 2 (inflation layer, 2021–25) | `data/processed/clock/inflation_test_*.csv` |
| Section 5.2, Table 3, Figure 3, Appendix F (two-layer limit) | `data/processed/limit/`, `paper/figures/fig3_*` |
| Appendix D.1, Table D1 (fiscal response regressions) | `data/processed/fiscal/fiscal_response_*.csv` |
| Appendix D.2–D.4, Table D2 (break dates), Table D3 (UK fiscal events), panel and CBO designs | `data/processed/fiscal/breaks*.csv`, `phi_obr*.csv`, `phi_cbo*.csv`, `phi_panel.csv` |
| Table 5, regime-specific ψ | `data/processed/limit/psi_regimes_*.csv` |
| Sections 3.3, 5.3 (Table 4), 6.2: monetary tolerance threshold κ* | `data/processed/limit/monetary_reaction_*.csv` |
| Appendix D.4 (φ identification with the clock) | `data/processed/fiscal/phi_*.csv` |
| Section 7, Table 11 (counterfactuals) | `data/processed/limit/counterfactuals_2025.csv` |
| Section 5.2 (decomposition, 2007–2025) | `data/processed/limit/decomposition_2007_2025.csv` |
| Section 5.4, Table 5 (robustness, Monte Carlo) | `data/processed/limit/robustness*.csv` |
| Section 5.5, Table 6 (inflation to hold debt/GDP constant) | `data/processed/limit/level_metric.csv` |
| Appendix C.2, Table C1, Figure C1 (time to the limit) | `data/processed/limit/time_to_limit.csv`, `paper/figures/fig4_*` |
| Section 6, Tables 7–10, Figure 4 (United Kingdom and Japan: clocks, fiscal threshold, UK 2021–25 and Japan 2022–25 inflation tests) | `data/processed/uk/`, `data/processed/jp/`, `data/processed/intl_*.csv`, `paper/figures/fig5_*` |

A LaTeX version of the paper is in `paper/latex/` (`bash paper/latex/build.sh`; needs pdflatex and bibtex). Its tables are generated from `paper/manuscript.md` by `paper/latex/md_tables.py`, and its figures are the vector PDFs in `paper/figures/`.

To rebuild the PDF you also need Chromium or Chrome. Run `CHROME=/path/to/chrome python3 paper/pdf/build_pdf.py`.

## Data

**Downloaded by `reproduce.sh`:**

| Source | Content |
|---|---|
| U.S. Treasury, FiscalData API | Monthly Statement of the Public Debt (security level), auction results, average interest rates |
| Federal Reserve Board, Data Download Program | H.4.1 (reserves, reverse repos, currency, SOMA totals), H.15 (yields) and Z.1 (U.S. currency held abroad) bulk files |
| Federal Reserve Bank of New York API | SOMA holdings by CUSIP, SOMA MBS at end-2021, effective federal funds rate |
| BEA | NIPA annual tables (GDP, primary balance) |
| Bank of England | APF gilt purchase and sale results and holdings table; statistical database (reserves, notes and coin, Bank Rate, SONIA, gilt yield curves) |
| ONS | CPI (D7BT) and RPI (CHAW) |
| Ministry of Finance, Japan | Debt yearbook, Table 34 (JGBs by issue), FY2020–2024; constant-maturity JGB yields |
| Bank of Japan | JGB holdings by issue; Time-Series Data Search API (balance sheet, current-account tiers, required reserves, government debt by holder) |
| Statistics Bureau of Japan | CPI, 2020 base, monthly |
| Office for Budget Responsibility | Fiscal forecast revisions database; historical official forecasts database |
| CBO (github.com/US-CBO/eval-projections) | Baselines and baseline changes by source, 1983–2026 |
| OECD Economic Outlook; BIS debt securities statistics | Fiscal and maturity panel for 23 advanced economies (Appendix D.4) |
| FRED (Federal Reserve Bank of St. Louis) | UK and Japan nominal and real GDP (UKNGDP, NGDPRSAXDCGBQ, JPNNGDP, JPNRGDPEXP); Japan CPI before 2020 (JPNCPIALLMINMEI); currency in circulation and reserve balances, 1980–2002 (CURRCIR, RESBALNS); debt held by the public, real and potential GDP (FYGFDPUN, FYPUGDA188S, GDPC1, GDPPOT); CPI (CPIAUCSL); Cleveland Fed 10-year expected inflation (EXPINF10YR) |

**Hand-collected, committed in `data/manual/`:**

| File | Content |
|---|---|
| `fd5_december.csv` | Treasury Bulletin FD-5 (FD-7 before 1983): privately held marketable debt by maturity bucket, December 1980–2003. Transcribed from FRASER scans; each row's buckets sum to its total. |
| `fed_income_2022_2025.csv` | Federal Reserve Banks' combined statements of income, 2022–2025 |
| `sep_longrun.csv` | FOMC Summary of Economic Projections, December longer-run real GDP growth, 2013–2025 |
| `tips_fd2_december.csv` | Treasury Bulletin FD-2: TIPS outstanding, December 1997–2002 |
| `uk_dmo/D1A_{year}-12-31.xls` | UK Debt Management Office, report D1A (gilts in issue by ISIN) for the last business day of 2007–2025. Committed because the DMO site blocks scripted downloads. |
| `cbo_automatic_stabilizers_2026-08.xlsx` | CBO, *Effects of Automatic Stabilizers on the Federal Budget: 2026 to 2036* (publication 62568), supplemental data: deficits with and without automatic stabilizers, FY1966–2036. Committed because cbo.gov blocks scripted downloads. |

`src/clock/fd5_locate.py` and `src/clock/fd5_parse.py` are the helpers used to find the FD-5 pages in the FRASER PDFs. They are not needed to reproduce the results.

## Code layout

```
src/model/    model checks: symbolic Jacobian, repricing-law simulation, stability scan
src/clock/    data fetchers; Treasury-only and consolidated clocks; backtest; 2022-25 test; FD-5 era
src/limit/    two-layer limit map 1980-2025; counterfactuals; Figure 3
src/fiscal/   evidence on the fiscal response: Bohn regressions, break tests, UK fiscal events, CBO, panel
src/intl/     United Kingdom and Japan: fetchers, security-level stocks, central-bank holdings, clocks,
              cross-country fiscal threshold, UK and Japan inflation tests, Figure 5
src/paper/    Figures 1-2
```

## License

MIT (see `LICENSE`). If you use the data or code, please cite the paper.
