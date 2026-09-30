"""United Kingdom: Bank of England Asset Purchase Facility gilt holdings by ISIN at any date,
rebuilt from the Bank's operation-level results (nominal £mn, by settlement date):
  + APF gilt purchases (2009-2021, incl. reinvestments)
  + 2022 financial-stability purchases (long-dated conventional and index-linked)
  - APF gilt sales (active QT, from November 2022)
  - financial-stability portfolio sales (November 2022 - January 2023)
A gilt's holding falls to zero at its redemption. Validated against the Bank's table of the
current stock by gilt (table-for-website.xlsx).
Output: data/interim/uk/apf_by_isin.csv (year-end holdings, nominal £mn).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

RAW = Path("data/raw/uk/boe")
OUT = Path("data/interim/uk")
FILES = [("gilt-purchase-operational-results.xlsx", +1), ("long-dated-uk-government-bond-purchase-time-series.xlsx", +1),
         ("index-linked-gilt-purchase-results.xlsx", +1), ("gilt-sales-time-series.xlsx", -1),
         ("finanical-stability-gilt-sales-time-series.xlsx", -1)]


def operations() -> pd.DataFrame:
    frames = []
    for f, sign in FILES:
        d = pd.read_excel(RAW / f, header=None)
        hdr = next(i for i in range(8) if any("ISIN" in str(v) for v in d.iloc[i]))
        cols = {str(v).replace("\n", " ").strip(): j for j, v in d.iloc[hdr].items()}
        x = pd.DataFrame({"settle": pd.to_datetime(d.iloc[hdr + 1:, cols["Settlement date"]], errors="coerce"),
                          "isin": d.iloc[hdr + 1:, cols["ISIN"]].astype(str).str.strip(),
                          "bond": d.iloc[hdr + 1:, cols["Bond"]].astype(str).str.strip(),
                          "nominal": pd.to_numeric(d.iloc[hdr + 1:, cols["Total allocation (nominal £mn)"]],
                                                   errors="coerce")})
        x = x.dropna(subset=["settle", "nominal"])
        x = x[x["isin"].str.match(r"GB[0-9A-Z]{10}")]
        x["nominal"] *= sign
        x["source"] = f
        frames.append(x)
    return pd.concat(frames, ignore_index=True)


def bond_maturity(code: str) -> pd.Timestamp:
    """Maturity from the Bank's bond code, e.g. UKT_4.5_070313 or UKTI_0.125_22032026 (ddmmyy[yy])."""
    tail = code.split("_")[-1]
    if len(tail) == 6:                  # two-digit year: every gilt the APF has held matures after 2000
        tail = tail[:4] + "20" + tail[4:]
    return pd.to_datetime(tail, format="%d%m%Y", errors="coerce")


def holdings(ops: pd.DataFrame, date: pd.Timestamp) -> pd.Series:
    x = ops[ops.settle <= date].copy()
    mat = x.groupby("isin").bond.first().map(bond_maturity)
    h = x.groupby("isin").nominal.sum()
    return h[(mat.reindex(h.index) > date) & (h.abs() > 1e-6)]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ops = operations()
    rows = []
    for y in range(2008, 2026):
        h = holdings(ops, pd.Timestamp(f"{y}-12-31"))
        rows += [{"year": y, "isin": i, "apf_nominal": v} for i, v in h.items()]
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "apf_by_isin.csv", index=False)
    print("APF gilt holdings, nominal £bn, year-end:", (d.groupby("year").apf_nominal.sum() / 1e3).round(1).to_dict())
    # validation against the Bank's current table
    t = pd.read_excel(RAW / "table-for-website.xlsx", header=None)
    t = t[pd.to_datetime(t[1], errors="coerce").notna()]
    stated = pd.to_numeric(t[2], errors="coerce").sum()
    latest = holdings(ops, ops.settle.max())
    print(f"current stock: rebuilt {latest.sum() / 1e3:.2f}bn nominal vs Bank table {stated:.2f}bn; "
          f"{len(latest)} gilts vs {len(t)}")


if __name__ == "__main__":
    main()
