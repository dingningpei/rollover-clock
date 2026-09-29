"""Locate Treasury Bulletin table FD-5 (privately held marketable debt by maturity) in
FRASER PDFs (data/raw/tbulletin/YYYY_03.pdf) by OCR of candidate pages."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

RAW = Path("data/raw/tbulletin")


def page_text(pdf: Path, page: int, dpi: int = 110) -> str:
    cache = RAW / "ocr" / f"{pdf.stem}_p{page:03d}_{dpi}.txt"
    if cache.exists():
        return cache.read_text()
    cache.parent.mkdir(parents=True, exist_ok=True)
    png = RAW / "ocr" / f"tmp_{pdf.stem}_{page}"
    subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-r", str(dpi), "-gray", "-png", "-singlefile",
                    str(pdf), str(png)], check=True)
    txt = subprocess.run(["tesseract", f"{png}.png", "-", "--psm", "4"], capture_output=True, text=True).stdout
    cache.write_text(txt)
    return txt


def locate(pdf: Path, lo: int = 15, hi: int = 80) -> int | None:
    for p in range(lo, hi):
        t = page_text(pdf, p)
        if re.search(r"FD-?\s*5", t) and re.search(r"Average\s+length", t, re.I) and re.search(r"Within", t, re.I):
            return p
    return None


def _job(y: int) -> tuple[int, int | None]:
    return y, locate(RAW / f"{y}_03.pdf")


if __name__ == "__main__":
    from multiprocessing import Pool
    with Pool(4) as pool:
        res = dict(pool.map(_job, range(1981, 2004)))
    (RAW / "fd5_pages.csv").write_text("year,page\n" + "".join(f"{y},{p}\n" for y, p in sorted(res.items())))
    print(res)
