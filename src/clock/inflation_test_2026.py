"""The inflation-layer test of Section 4.5 rerun from the end-2025 balance sheet, January-August 2026.

Same design as src/clock/inflation_test.py, with two differences forced by the data: borrowing
after end-2025 follows 4% trend growth (no 2026 year-end yet), and privately held marketable
debt is held at its end-2025 level. Needs data/raw/fed/effr_2026.json (New York Fed API,
2026-01-01 to 2026-09-30). Not part of the paper.
"""
from .inflation_test import run

if __name__ == "__main__":
    run(2025, 8, realized_totals=False, tag="_2026")
