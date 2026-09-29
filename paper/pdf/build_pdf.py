"""Build the paper PDF from paper/manuscript.md.

    python3 paper/pdf/build_pdf.py --author "Name" --affil "Affiliation" --email "x@y"

Needs `pip install markdown latex2mathml` and Chromium (headless print to PDF).
Display math ($$...$$) is converted to MathML; figures are embedded from paper/figures/.
"""
import argparse
import os
import base64
import html
import re
import subprocess
from pathlib import Path

import markdown
from latex2mathml.converter import convert

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "paper" / "manuscript.md"
OUT = ROOT / "paper"
CHROME = os.environ.get("CHROME", "chromium")   # any Chromium/Chrome binary

CSS = """
@page { size: Letter; margin: 1in 1in 1in 1in;
        @bottom-center { content: counter(page); } }
body { font-family: 'Liberation Serif', 'Times New Roman', serif; font-size: 11.5pt;
       line-height: 1.45; color: #111; background: #fff; }
h1 { font-size: 17pt; text-align: center; line-height: 1.25; margin: 0 0 .6em; }
h2 { font-size: 13pt; margin: 1.4em 0 .4em; page-break-after: avoid; }
h3 { font-size: 11.5pt; font-style: italic; margin: 1.1em 0 .3em; page-break-after: avoid; }
p { margin: .45em 0; text-align: justify; }
.author { text-align: center; margin: .2em 0 1.2em; }
.author .name { font-size: 12.5pt; }
.meta { text-align: center; font-size: 10pt; color: #333; }
.abstract { margin: 1em 2.2em; font-size: 10.5pt; }
.front { font-size: 10pt; margin: .6em 2.2em; }
table { border-collapse: collapse; margin: .8em auto; font-size: 9.5pt; page-break-inside: avoid; }
th, td { border-top: 1px solid #999; border-bottom: 1px solid #999; padding: 3px 7px; }
th { border-top: 1.5px solid #000; border-bottom: 1px solid #000; }
img { display: block; max-width: 100%; max-height: 5.6in; margin: .8em auto; page-break-inside: avoid; }
.eq { text-align: center; margin: .6em 0; font-size: 110%; page-break-inside: avoid; }
pre { font-size: 8.5pt; background: #f4f4f4; padding: 6px; white-space: pre-wrap; }
code { font-size: 9.5pt; }
li { margin: .15em 0; }
hr { border: 0; }
.fig { page-break-inside: avoid; }
"""


def tidy(md: str) -> str:
    """Python-Markdown needs a blank line before a list and 4-space nesting; plain-text
    super/subscripts (e^{-gh}, pi^req, int_0^H, P_t) become <sup>/<sub>."""
    out, prev, fence = [], "", False
    for line in md.split("\n"):
        if line.startswith("```"):
            fence = not fence
        if not fence:
            item = re.match(r"^( *)([-*]|\d+\.) ", line)
            if item:
                if prev.strip() and not re.match(r"^ *([-*]|\d+\.) ", prev):
                    out.append("")
                line = " " * (2 * len(item.group(1))) + line.lstrip(" ")
            line = re.sub(r"\^\{([^}]*)\}", r"<sup>\1</sup>", line)
            line = re.sub(r"\^(req|gap|∞|H|h)", r"<sup>\1</sup>", line)
            line = re.sub(r"_\{([^}]*)\}", r"<sub>\1</sub>", line)
            line = re.sub(r"(?<=[A-Za-z])_([A-Za-z])\b", r"<sub>\1</sub>", line)     # P_t, P_N, F_N
            line = re.sub(r"(?<![A-Za-z\\*])([rbsφgψ])\*(?!\*)", r"\1\\*", line)   # r*, b*, φ* are not emphasis
        out.append(line)
        prev = line
    return "\n".join(out)


def build(author: str, affil: str, email: str, jel: str, keywords: str) -> Path:
    md = SRC.read_text()
    maths = []

    def stash(m):
        maths.append('<div class="eq">' + convert(m.group(1).strip(), display="inline") + "</div>")
        return f"\n\nMATHBLOCK{len(maths) - 1}\n\n"

    md = re.sub(r"\$\$(.+?)\$\$", stash, md, flags=re.S)

    def embed(m):
        data = base64.b64encode((ROOT / "paper" / m.group(2)).read_bytes()).decode()
        return f"![{m.group(1)}](data:image/png;base64,{data})"

    md = re.sub(r"!\[([^\]]*)\]\((figures/[^)]+\.png)\)", embed, md)

    md = tidy(md)
    title, rest = md.split("\n", 1)
    title = title.lstrip("# ").strip()
    rest = re.sub(r"^\s*\*Preliminary[^\n]*\*\s*\n", "", rest)       # replaced by the title block
    body = markdown.markdown(rest, extensions=["tables", "fenced_code"])
    for k, m in enumerate(maths):
        body = body.replace(f"<p>MATHBLOCK{k}</p>", m)

    # keep each figure with its caption
    body = re.sub(r"(<p><img [^>]+></p>\s*<p><em>Figure.*?</p>)", r'<div class="fig">\1</div>', body, flags=re.S)
    # abstract block + JEL/keywords line
    body = body.replace("<h2>Abstract</h2>", '<div class="abstract"><h2 style="text-align:center">Abstract</h2>', 1)
    front = (f'<p class="front"><b>JEL:</b> {html.escape(jel)}<br><b>Keywords:</b> {html.escape(keywords)}</p></div>')
    body = body.replace("<hr />", front, 1)

    head = (f"<h1>{html.escape(title)}</h1>"
            f'<div class="author"><div class="name">{html.escape(author)}</div>'
            f"<div>{html.escape(affil)}</div><div>{html.escape(email)}</div></div>"
            f'<p class="meta">Preliminary working paper, September 2026. Comments welcome.</p>')
    doc = (f"<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(title)}</title>"
           f"<style>{CSS}</style></head><body>{head}{body}</body></html>")
    page = OUT / "rollover_clock.html"
    page.write_text(doc)
    pdf = OUT / "rollover_clock.pdf"
    subprocess.run([CHROME, "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", page.as_uri()], check=True, capture_output=True)
    page.unlink()
    return pdf


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--author", default="Ningpei Ding")
    a.add_argument("--affil", default="Independent Researcher")
    a.add_argument("--email", default="dingningpei@gmail.com")
    a.add_argument("--jel", default="E52, E58, E62, E63, H62, H63")
    a.add_argument("--keywords", default="rollover risk; debt maturity; consolidated government balance sheet; "
                   "quantitative easing; fiscal limits; inflation tax; debt sustainability")
    x = a.parse_args()
    print(build(x.author, x.affil, x.email, x.jel, x.keywords))
