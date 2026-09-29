"""Parse the December row of Treasury Bulletin table FD-5 from OCR (300 dpi).

Row: total, within 1y, 1-5y, 5-10y, 10-20y, 20y+, average length (years, months).
A row is accepted only if the buckets sum to the total within 0.05%.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

RAW = Path("data/raw/tbulletin")
NUM = r"(\d{1,3}(?:[,.]\d{3})+|\d{4,7})"


def ocr_table(pdf: Path, page: int, dpi: int = 300) -> str:
    cache = RAW / "ocr" / f"{pdf.stem}_p{page:03d}_{dpi}_psm6.txt"
    if cache.exists():
        return cache.read_text()
    png = RAW / "ocr" / f"tbl_{pdf.stem}_{page}"
    subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-r", str(dpi), "-gray", "-png", "-singlefile",
                    str(pdf), str(png)], check=True)
    txt = subprocess.run(["tesseract", f"{png}.png", "-", "--psm", "6"], capture_output=True, text=True).stdout
    cache.write_text(txt)
    return txt


def to_int(s: str) -> int:
    return int(re.sub(r"[,.]", "", s))


def parse_rows(txt: str) -> list[dict]:
    """All FD-5 data rows on the page (FD-5 block only: stops at FD-6)."""
    block = re.split(r"FD-?\s*6", txt)[0]
    rows = []
    for line in block.splitlines():
        nums = re.findall(NUM, line)
        if len(nums) < 6:
            continue
        v = [to_int(x) for x in nums[:6]]
        m = re.search(r"(\d{1,2})\s*yrs?\.?\s*(\d{1,2})\s*mos?", line)
        label = re.match(r"\s*([A-Za-z0-9\- ]{2,12}?)[\s.]", line)
        rows.append({"label": label.group(1).strip() if label else "", "total": v[0], "b1": v[1], "b1_5": v[2],
                     "b5_10": v[3], "b10_20": v[4], "b20": v[5],
                     "avg_years": int(m.group(1)) + int(m.group(2)) / 12 if m else None,
                     "sum_ok": abs(sum(v[1:]) - v[0]) <= 0.0005 * v[0], "line": line.strip()})
    return rows


if __name__ == "__main__":
    import sys
    pdf, page = Path(sys.argv[1]), int(sys.argv[2])
    for r in parse_rows(ocr_table(pdf, page)):
        print(r["sum_ok"], r["label"], r["total"], r["b1"], r["b20"], r["avg_years"])
