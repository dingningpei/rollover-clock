#!/usr/bin/env bash
# Build paper/latex/rollover_clock.pdf: regenerate the tables from paper/manuscript.md, then pdflatex + bibtex.
set -euo pipefail
cd "$(dirname "$0")"
export PATH="/Library/TeX/texbin:$PATH"
python3 md_tables.py
pdflatex -interaction=nonstopmode -halt-on-error rollover_clock.tex >/dev/null
bibtex rollover_clock >/dev/null
pdflatex -interaction=nonstopmode -halt-on-error rollover_clock.tex >/dev/null
pdflatex -interaction=nonstopmode -halt-on-error rollover_clock.tex >/dev/null
grep -E "Warning|Error" rollover_clock.log | grep -v "Font shape" | sort | uniq -c | head -30 || true
echo "built rollover_clock.pdf"
