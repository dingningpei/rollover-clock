# The Rollover Clock

Replication package for

> Ningpei Ding (2026). **"The Rollover Clock: Debt Maturity, the Central-Bank Balance Sheet, and the Debt Limit of a Reserve-Currency Sovereign."** Working paper.

- Paper: [`paper/rollover_clock.pdf`](paper/rollover_clock.pdf), with source text in [`paper/manuscript.md`](paper/manuscript.md)
- Contact: dingningpei@gmail.com

## What the paper does

The debt limit of a reserve-currency sovereign has two layers.

- **Fiscal layer.** Debt is stable if and only if the primary surplus offsets at least a share φ\* = 1 − g/(r + ψb) of the marginal interest cost of debt. This threshold does not depend on maturity, for any repricing kernel.
- **Inflation layer.** If the fiscal response falls short, the inflation needed to fill the gap depends on the *rollover clock* P(h): how fast the consolidated Treasury + Federal Reserve liabilities reprice.

We measure the clock security by security for the United States, 1980–2025, and validate it:
- in a 2001–2024 backtest of the official average interest rate;
- out of sample on the 2022–25 tightening, frozen at end-2021, for both Treasury interest costs and the Fed's deferred asset.

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
| Table 2, Figure 3 (two-layer limit) | `data/processed/limit/`, `paper/figures/fig3_*` |
| Section 5.3 (φ identification) | `data/processed/fiscal/phi_*.csv` |
| Table 3 (counterfactuals) | `data/processed/limit/counterfactuals_2025.csv` |

To rebuild the PDF you also need Chromium or Chrome. Run `CHROME=/path/to/chrome python3 paper/pdf/build_pdf.py`.

## Data

**Downloaded by `reproduce.sh`:**

| Source | Content |
|---|---|
| U.S. Treasury, FiscalData API | Monthly Statement of the Public Debt (security level), auction results, average interest rates |
| Federal Reserve Board, Data Download Program | H.4.1 (reserves, reverse repos, SOMA totals) and H.15 (yields) bulk files |
| Federal Reserve Bank of New York API | SOMA holdings by CUSIP, SOMA MBS at end-2021, effective federal funds rate |
| BEA | NIPA annual tables (GDP, primary balance) |

**Hand-collected, committed in `data/manual/`:**

| File | Content |
|---|---|
| `fd5_december.csv` | Treasury Bulletin FD-5 (FD-7 before 1983): privately held marketable debt by maturity bucket, December 1980–2003. Transcribed from FRASER scans; each row's buckets sum to its total. |
| `fed_income_2022_2025.csv` | Federal Reserve Banks' combined statements of income, 2022–2025 |
| `sep_longrun.csv` | FOMC Summary of Economic Projections, December longer-run real GDP growth, 2013–2025 |

`src/clock/fd5_locate.py` and `src/clock/fd5_parse.py` are the helpers used to find the FD-5 pages in the FRASER PDFs. They are not needed to reproduce the results.

## Code layout

```
src/model/    model checks: symbolic Jacobian, repricing-law simulation, stability scan
src/clock/    data fetchers; Treasury-only and consolidated clocks; backtest; 2022-25 test; FD-5 era
src/limit/    two-layer limit map 1980-2025; counterfactuals; Figure 3
src/fiscal/   attempt to identify the fiscal-offset coefficient (a negative result)
src/paper/    Figures 1-2
```

## License

MIT (see `LICENSE`). If you use the data or code, please cite the paper.
