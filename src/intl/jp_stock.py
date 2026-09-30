"""Japan: outstanding JGBs by issue at each fiscal-year end (31 March), from MOF's
JGB Statistics Yearbook (国債統計年報), Table 34 "現存国債の名称別発行要項
普通国債及び財政投融資特別会計": every existing issue of general and FILP bonds with its
amount issued, its fiscal-year-end amount outstanding, coupon and redemption date.
Files: data/raw/jp/mof/nenpou/{FY}nenpou09.xlsx (MOF, FY2020 on) or the one-file edition
from e-Stat. Amounts in thousand yen. Redemption dates are in Japanese era format
(R = Reiwa 2019+, H = Heisei 1989+, S = Showa 1926+).

Output: data/interim/jp/jgb_by_issue.csv (one row per fiscal year and issue).
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd

RAW = Path("data/raw/jp/mof/nenpou")
OUT = Path("data/interim/jp")
ERA = {"R": 2018, "H": 1988, "S": 1925}


def era_date(s) -> pd.Timestamp:
    if isinstance(s, (pd.Timestamp,)) or hasattr(s, "year"):     # some editions store real dates
        return pd.Timestamp(s)
    s = unicodedata.normalize("NFKC", str(s)).replace(" ", "")
    m = re.match(r"([RHS])(\d+|元)\.(\d+)\.(\d+)", s)
    if not m:
        return pd.NaT
    y = ERA[m.group(1)] + (1 if m.group(2) == "元" else int(m.group(2)))
    return pd.Timestamp(year=y, month=int(m.group(3)), day=int(m.group(4)))


def kind(name: str) -> str:
    n = unicodedata.normalize("NFKC", name)
    if "物価連動" in n:
        return "indexed"
    if "変動" in n:
        return "floating"                       # 15-year floaters, retail floating 10-year
    if "割引" in n:
        return "bill"
    return "fixed"


def table34(path: Path, fy: int) -> pd.DataFrame:
    x = pd.ExcelFile(path)
    sheet = [s for s in x.sheet_names if s.startswith("34") and "普通国債" in s][0]
    d = pd.read_excel(x, sheet, header=None)
    # locate the header row and columns by their labels (layouts differ across editions)
    hdr = next(i for i in range(15) if any(str(v).strip() == "回記号" for v in d.iloc[i]))
    lab = {j: unicodedata.normalize("NFKC", str(v)).replace(" ", "") for j, v in d.iloc[hdr].items()}
    col = {"name": next(j for j, v in lab.items() if v == "名称"),
           "no": next(j for j, v in lab.items() if v == "回記号"),
           "issued": next(j for j, v in lab.items() if v == "発行額"),
           "outstanding": next(j for j, v in lab.items() if v.endswith("年度末現在額")),
           "coupon": next(j for j, v in lab.items() if v == "利率"),
           "maturity_era": next(j for j, v in lab.items() if v == "償還期限")}
    d = d.iloc[hdr + 1:, list(col.values())]
    d.columns = list(col.keys())
    d["name"] = d.name.ffill()
    d = d[d.no.astype(str).str.contains("第", na=False)].copy()
    d["name"] = d.name.map(lambda s: unicodedata.normalize("NFKC", str(s)).strip())
    d["issue_no"] = d.no.astype(str).str.extract(r"(\d+)")[0].astype(int)
    for c in ("issued", "outstanding"):
        d[c] = pd.to_numeric(d[c].astype(str).str.replace(",", ""), errors="coerce")
    d["coupon"] = pd.to_numeric(d.coupon, errors="coerce")
    d["maturity"] = d.maturity_era.map(era_date)
    d["kind"] = d.name.map(kind)
    d["fy"] = fy
    d["as_of"] = pd.Timestamp(year=fy + 1, month=3, day=31)
    return d[["fy", "as_of", "name", "issue_no", "kind", "coupon", "maturity", "issued", "outstanding"]]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frames = []
    for f in sorted(RAW.glob("*nenpou09.xlsx")):
        fy = int(f.name[:4])
        frames.append(table34(f, fy))
    d = pd.concat(frames, ignore_index=True)
    d = d[d.outstanding > 0]
    d.to_csv(OUT / "jgb_by_issue.csv", index=False)
    s = d.groupby(["fy", "kind"]).outstanding.sum().unstack() / 1e9      # trillion yen
    s["total"] = s.sum(axis=1)
    print("Outstanding by kind, trillion yen"); print(s.round(1).to_string())
    print("missing maturities:", d.maturity.isna().sum())


if __name__ == "__main__":
    main()
