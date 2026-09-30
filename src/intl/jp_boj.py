"""Japan: Bank of Japan holdings of JGBs by issue at each fiscal-year end.

Source: BoJ, "Japanese Government Bonds Held by the Bank of Japan" (face value, 100 million
yen), release on 31 March or the last business day before it. Coupon-bearing JGBs only;
the BoJ's T-bill holdings come from its accounts (jp_clock.py).
Output: data/interim/jp/boj_holdings.csv (fy, name, issue_no, boj in thousand yen).
"""
from __future__ import annotations

import unicodedata
from pathlib import Path

import pandas as pd

RAW = Path("data/raw/jp/boj")
OUT = Path("data/interim/jp")
FILES = {2020: "mei210331.xlsx", 2021: "mei220331.xlsx", 2022: "mei230331.xlsx",
         2023: "mei240329.xlsx", 2024: "mei250331.xlsx", 2025: "mei260331.xlsx"}
NAME = {"2年債": "利付国庫債券(2年)", "5年債": "利付国庫債券(5年)", "10年債": "利付国庫債券(10年)",
        "20年債": "利付国庫債券(20年)", "30年債": "利付国庫債券(30年)", "40年債": "利付国庫債券(40年)",
        "物価連動債": "利付国庫債券(物価連動・10年)", "変動利付債": "利付国庫債券(変動・15年)",
        "10年クライメート・トランジション国債": "クライメート・トランジション利付国庫債券(10年)",
        "5年クライメート・トランジション国債": "クライメート・トランジション利付国庫債券(5年)"}


def parse(path: Path, fy: int) -> pd.DataFrame:
    d = pd.read_excel(path, header=None)
    lab = d[2].map(lambda v: unicodedata.normalize("NFKC", str(v)).split("\n")[0].strip() if pd.notna(v) else None)
    lab = lab.where(lab.isin(NAME.keys())).ffill()
    no = pd.to_numeric(d[3], errors="coerce")
    amt = pd.to_numeric(d[4], errors="coerce")
    ok = lab.notna() & no.notna() & amt.notna()
    return pd.DataFrame({"fy": fy, "name": lab[ok].map(NAME), "issue_no": no[ok].astype(int),
                         "boj": amt[ok] * 1e5})                     # 100 million yen -> thousand yen


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.concat([parse(RAW / f, fy) for fy, f in FILES.items() if (RAW / f).exists()], ignore_index=True)
    d.to_csv(OUT / "boj_holdings.csv", index=False)
    print((d.groupby(["fy", "name"]).boj.sum().unstack(0) / 1e9).round(1).to_string())
    print("total, trillion yen:", (d.groupby("fy").boj.sum() / 1e9).round(1).to_dict())


if __name__ == "__main__":
    main()
