"""United Kingdom: gilts in issue by gilt at each year-end (DMO report D1A).

Files: data/manual/uk_dmo/D1A_{year}-12-31.xls (the report for the last business day of the
year, downloaded by hand: the DMO site blocks scripted access). Conventional gilts carry
the nominal amount in issue; index-linked gilts (3-month and 8-month lag) also carry the
amount including the inflation uplift, which is the amount used here. Each file states
its total including uplift, which the parsed sum must reproduce. Undated gilts (perpetuals,
until their redemption in 2014-15) have no redemption date unless one has been announced.
Output: data/interim/uk/gilts_by_isin.csv
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

RAW = Path("data/manual/uk_dmo")
OUT = Path("data/interim/uk")


def parse(path: Path) -> tuple[pd.DataFrame, float, pd.Timestamp]:
    d = pd.read_excel(path, header=None)
    as_of = pd.to_datetime(re.search(r"ISSUE ON (\d{1,2} [A-Z]+ \d{4})", str(d.iloc[0, 2])).group(1),
                           format="%d %B %Y")
    line = next(str(v) for v in d.iloc[:12, 0] if "Total Amount Outstanding" in str(v))
    total = float(re.search(r"= £([\d,\.]+) billion", line).group(1).replace(",", "")) * 1e3
    rows, section = [], None
    for _, r in d.iterrows():
        first = str(r[0])
        if first.startswith("Conventional Gilts") or first.startswith('"Rump" Gilts'):
            section = "conventional"
        elif first.startswith("Index-linked Gilts"):
            section = "indexed"
        elif first.startswith("Undated Gilts"):
            section = "undated"                      # perpetuals (War Loan, Consols), redeemed 2014-15
        if not re.fullmatch(r"GB[0-9A-Z]{10}", str(r[1]).strip()):
            continue
        nominal = float(r[6])
        amount = float(r[8]) if section == "indexed" else nominal
        rows.append({"as_of": as_of, "name": first.strip(), "isin": str(r[1]).strip(), "kind": section,
                     # undated gilts have no redemption date until one is announced
                     "maturity": pd.to_datetime(r[2], errors="coerce"),
                     "first_issue": pd.to_datetime(r[3], errors="coerce"),
                     "nominal": nominal, "amount": amount})
    return pd.DataFrame(rows), total, as_of


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frames = []
    for f in sorted(RAW.glob("D1A_*.xls")):
        x, total, as_of = parse(f)
        frames.append(x)
        print(f"{as_of.date()}: {len(x)} gilts, sum {x.amount.sum() / 1e3:,.2f}bn vs stated {total / 1e3:,.2f}bn "
              f"(diff {(x.amount.sum() - total) / 1e3:+.2f}); index-linked share {x.loc[x.kind == 'indexed', 'amount'].sum() / x.amount.sum():.3f}")
    pd.concat(frames, ignore_index=True).to_csv(OUT / "gilts_by_isin.csv", index=False)


if __name__ == "__main__":
    main()
