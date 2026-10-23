#!/usr/bin/env python3
"""Builds report/old/REPORT.pdf (a draft, not the submitted report) from report_src/REPORT.md: Markdown -> HTML (python-markdown) -> PDF (headless Google Chrome).
Requirements: `pip install markdown` and Google Chrome (path below). Usage: scripts/make_report_pdf.py"""
import os, re, subprocess, sys, tempfile
import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
src = open(f"{ROOT}/report_src/REPORT.md", encoding="utf-8").read()
body = markdown.markdown(src, extensions=["tables", "fenced_code", "sane_lists"])
body = re.sub(r'src="\.\./', 'src="file://%s/' % ROOT, body)
body = re.sub(r"<p>((?:(?!</p>).)*)</p>(\s*<table)", lambda m: '<p class="question">' + m.group(1) + "</p>" + m.group(2), body, flags=re.S)
for lab in ("Result.", "Result and explanation."):
    body = body.replace("<p><strong>%s</strong></p>" % lab, '<p class="question"><strong>%s</strong></p>' % lab)
body = re.sub(r"<p><strong>(Question|Expectation|Method)\.</strong>", lambda m: '<p class="kw %s"><strong>%s.</strong>' % (m.group(1).lower(), m.group(1)), body)
CSS = """
@page { size: Letter; margin: 0.45in 0.5in; }
body { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; font-size: 7.8pt; line-height: 1.2; color: #111; }
h1 { font-size: 14pt; margin: 0 0 4pt 0; } h2 { font-size: 10.5pt; margin: 8pt 0 2pt 0; border-bottom: 0.6pt solid #999; padding-bottom: 1pt; page-break-after: avoid; }
h3 { font-size: 10pt; margin: 6pt 0 2pt 0; page-break-after: avoid; }
p { margin: 2.5pt 0; orphans: 3; widows: 3; } p.question { break-after: avoid; page-break-after: avoid; } p.expectation { break-after: avoid; page-break-after: avoid; } ul, ol { margin: 2pt 0 3pt 0; padding-left: 16pt; } li { margin: 1pt 0; }
table { border-collapse: collapse; margin: 3pt 0; font-size: 6.9pt; width: 100%; page-break-inside: avoid; } tr { page-break-inside: avoid; }
td code { word-break: break-all; font-size: 6.6pt; }
th, td { border: 0.5pt solid #888; padding: 1pt 3pt; text-align: left; vertical-align: top; } th { background: #eee; }
img { width: 100%; height: auto; display: block; margin: 3pt auto 1pt auto; }
p > img { page-break-inside: avoid; break-inside: avoid; }
img[src*="exp1_sweep_f32"] { width: 80%; }
img[src*="exp13_stride_jump"] { width: 78%; }
img[src*="exp8_naive"] { width: 88%; }
em { color: #222; } code { font-family: Menlo, monospace; font-size: 7.2pt; background: #f2f2f2; padding: 0 1pt; }
pre { background: #f6f6f6; border: 0.5pt solid #ccc; padding: 3pt 5pt; font-size: 6.8pt; line-height: 1.2; page-break-inside: avoid; overflow: hidden; }
pre code { background: none; padding: 0; font-size: 6.8pt; }
"""
html = f'<!doctype html><html><head><meta charset="utf-8"><title>SIMD Advantage Profiling</title><style>{CSS}</style></head><body>{body}</body></html>'
with tempfile.TemporaryDirectory() as d:
    h = os.path.join(d, "report.html"); open(h, "w", encoding="utf-8").write(html)
    os.makedirs(f"{ROOT}/report/old", exist_ok=True)
    out = f"{ROOT}/report/old/REPORT.pdf"
    r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={out}", "--allow-file-access-from-files", "file://" + h], capture_output=True, text=True, timeout=180)
    if r.returncode != 0 or not os.path.exists(out): sys.exit("PDF build failed: " + r.stderr[-500:])
import re as _re
print("wrote", out, "pages:", len(_re.findall(rb"/Type\s*/Page[^s]", open(out, "rb").read())))
