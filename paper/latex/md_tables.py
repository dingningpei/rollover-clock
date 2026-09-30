"""Generate the LaTeX tables of the paper from paper/manuscript.md, so that no number is
transcribed by hand. Each Markdown table is identified by the caption line or the text
just above it; the output goes to paper/latex/tables/<name>.tex.

    python3 paper/latex/md_tables.py
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "paper" / "manuscript.md"
OUT = ROOT / "paper" / "latex" / "tables"

# name, anchor (start of the caption line or of the text before the table), label, float or not
TABLES = [
    ("reliability", "| Result | Basis | Depends on | Reliability |", None, "inlinewide"),
    ("tab1", "**Table 1. Backtest", "tab:backtest", "num"),
    ("fedloss", "| | 2022 | 2023 | 2024 | 2025 |", None, "inline"),
    ("tab2", "**Table 2. Real transfer", "tab:inflationtest", "num"),
    ("tab3", "**Table 3. Two-layer limit by period", "tab:limitperiod", "num"),
    ("tab4", "**Table 4. Monetary tolerance threshold", "tab:kappa", "num"),
    ("tab5", "**Table 5. Robustness", "tab:robust", "num"),
    ("tab6", "**Table 6. Inflation needed to hold", "tab:level", "num"),
    ("tab7", "**Table 7. Three sovereigns", "tab:threesov", "num"),
    ("tab8", "**Table 8. Fiscal threshold and inflation requirement", "tab:threshold3", "num"),
    ("tab9", "**Table 9. United Kingdom", "tab:uktest", "num"),
    ("tab10", "**Table 10. Japan", "tab:jptest", "num"),
    ("tab11", "**Table 11. End-2025 counterfactuals", "tab:counterfactuals", "num"),
    ("tab12", "**Table 12. Who bears a fiscal gap", "tab:whopays", "wide"),
    ("tabC0", "| Price-level path | Erosion (debt + currency) | Effect of shorter maturity |", None, "inlinewide"),
    ("tabC1", "**Table C1. Years until", "tab:timetolimit", "num"),
    ("tabD1", "**Table D1. Implied fiscal response", "tab:bohn", "num"),
    ("tabD2", "**Table D2. Data-determined breaks", "tab:breaks", "num"),
    ("tabD3", "**Table D3. UK: policy response", "tab:obr", "num"),
    ("tabF1", "**Table F1. Two-layer limit by year", "tab:annual", "long"),
]

SYM = [
    ("κ\\*", "KAPPASTAR"), ("κ*", "KAPPASTAR"), ("φ̂", "PHIHAT"), ("φ*", "PHISTAR"), ("r̄₀", "RBARZERO"),
    ("∫P/∫E", "INTPE"), ("∫", "INTEG"),
]
MATH = {
    "KAPPASTAR": r"$\kappa^*$", "PHIHAT": r"$\hat\varphi$", "PHISTAR": r"$\varphi^*$", "RBARZERO": r"$\bar r_0$",
    "INTPE": r"$\int P/\int E$", "INTEG": r"$\int$",
}
CHARS = {
    "φ": r"$\varphi$", "ψ": r"$\psi$", "κ": r"$\kappa$", "Δ": r"$\Delta$", "π": r"$\pi$", "λ": r"$\lambda$",
    "τ": r"$\tau$", "ρ": r"$\rho$", "−": r"$-$", "≈": r"$\approx$", "≤": r"$\le$", "≥": r"$\ge$", "×": r"$\times$",
    "·": r"$\cdot$", "⁺": r"$^+$", "±": r"$\pm$", "→": r"$\to$", "£": r"\pounds{}", "r̄": r"$\bar r$",
}


def tex(s: str) -> str:
    s = s.strip()
    for a, b in SYM:
        s = s.replace(a, b)
    s = s.replace("\\", "")
    s = re.sub(r"([&%$#{}])", r"\\\1", s)
    s = re.sub(r"_([A-Za-z0-9]+)", r"$_{\1}$", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", s)
    s = re.sub(r"(?<![A-Za-z0-9])\*(.+?)\*(?![A-Za-z0-9])", r"\\emph{\1}", s)
    s = re.sub(r'"(.+?)"', r"``\1''", s)
    for a, b in CHARS.items():
        s = s.replace(a, b)
    for a, b in MATH.items():
        s = s.replace(a, b)
    s = s.replace("$$", "")                               # merge adjacent math
    return s


def rows(block: list[str]) -> list[list[str]]:
    out = []
    for line in block:
        cells = [c for c in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r"\s*:?-+:?\s*", c) for c in cells):
            continue
        out.append([tex(c) for c in cells])
    return out


def find(md: list[str], anchor: str) -> tuple[str | None, str | None, list[str], str | None]:
    """Caption line, subtitle, table lines, notes for the table at `anchor`."""
    i = next(k for k, l in enumerate(md) if l.startswith(anchor))
    caption = None
    if md[i].startswith("**Table"):
        caption = md[i]
        i += 1
        while not md[i].startswith("|"):
            i += 1
    block = []
    while i < len(md) and md[i].startswith("|"):
        block.append(md[i])
        i += 1
    notes = None
    j = i
    while j < len(md) and md[j].strip() == "":
        j += 1
    if j < len(md) and (md[j].startswith("*Notes.*") or md[j].startswith("Newey–West") or md[j].startswith("r is the stock")):
        notes = md[j]
    return caption, block, notes


def split_caption(c: str) -> tuple[str, str]:
    m = re.match(r"\*\*Table [A-Z]?\d+\. (.+?)\*\*\s*(.*)$", c)
    title, sub = m.group(1), m.group(2).strip()
    sub = sub[1:-1] if sub.startswith("(") and sub.endswith(")") else sub
    return tex(title), tex(sub)


def colspec(n: int, kind: str, first: list[str]) -> str:
    if kind in ("wide", "inlinewide"):
        return r">{\raggedright\arraybackslash}X" * n
    plain = [re.sub(r"\\[a-z]+|[${}^_]", "", c) for c in first]
    L = max(len(c) for c in plain)
    if L <= 14:
        head = "l"
    elif L <= 34:
        head = r">{\raggedright\arraybackslash}p{0.2\textwidth}"
    else:
        head = r">{\raggedright\arraybackslash}p{0.3\textwidth}"
    return head + r">{\centering\arraybackslash}X" * (n - 1)


def build(name: str, anchor: str, label: str | None, kind: str, md: list[str]) -> str:
    caption, block, notes = find(md, anchor)
    r = rows(block)
    n = len(r[0])
    size = r"\footnotesize" if n >= 6 or kind in ("wide", "inlinewide") else r"\small"
    body = []
    head, data = r[0], r[1:]
    if name == "tabF1":                                        # short headers for the 12-column annual table
        head = ["Year", "Source", "$r$ (\\%)", "$g$ (\\%)", "$b$", "$\\varphi^*$", "$\\hat\\varphi$", "Gap",
                "$R$ cons.", "$R$ Treas.", "$\\Delta\\pi$ (pp/yr)", "Jump (\\%)"]
    if kind == "long":
        spec = "l" * n
        lines = [r"{\scriptsize\setlength{\tabcolsep}{3pt}", r"\begin{longtable}{" + spec + "}"]
        t, sub = split_caption(caption)
        lines += [r"\caption{" + t + r"}\label{" + label + r"}\\", r"\multicolumn{" + str(n) + r"}{l}{" + sub + r"}\\",
                  r"\toprule", " & ".join(head) + r" \\", r"\midrule", r"\endfirsthead", r"\toprule",
                  " & ".join(head) + r" \\", r"\midrule", r"\endhead"]
        lines += [" & ".join(x) + r" \\" for x in data]
        lines += [r"\bottomrule", r"\end{longtable}}"]
        if notes:
            lines.append(r"{\footnotesize " + tex(re.sub(r"^\*Notes\.\*\s*", r"\\emph{Notes.} ", notes)) + "}")
        return "\n".join(lines) + "\n"
    tab = [size, r"\begin{tabularx}{\textwidth}{" + colspec(n, kind, [x[0] for x in data] or [head[0]]) + "}", r"\toprule",
           " & ".join(head) + r" \\", r"\midrule"] + [" & ".join(x) + r" \\" for x in data] + [r"\bottomrule",
                                                                                           r"\end{tabularx}"]
    if kind in ("inline", "inlinewide"):
        return "\\begin{center}\n" + "\n".join(tab) + "\n\\end{center}\n"
    out = [r"\begin{table}[htbp]", r"\centering"]
    if caption:
        t, sub = split_caption(caption)
        out.append(r"\caption{" + t + r"}\label{" + label + "}")
        if sub:
            out.append(r"{\small " + sub + r"\par}\smallskip")
    elif label:
        pass
    out += tab
    if notes:
        n_ = notes.replace("*Notes.*", "NOTESMARK")
        out.append(r"\par\smallskip{\footnotesize\raggedright " + tex(n_).replace("NOTESMARK", r"\emph{Notes.}") + r"\par}")
    out.append(r"\end{table}")
    return "\n".join(out) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    md = MD.read_text().split("\n")
    for name, anchor, label, kind in TABLES:
        (OUT / f"{name}.tex").write_text(build(name, anchor, label, kind, md))
    print("wrote", len(TABLES), "tables")


if __name__ == "__main__":
    main()
