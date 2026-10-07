#!/usr/bin/env python3
"""Builds report/REPORT.pdf from report/REPORT.md: Markdown -> HTML (python-markdown) -> PDF (headless Google Chrome).
Requirements: `pip install markdown` and Google Chrome (path below). Usage: scripts/make_report_pdf.py"""
import os, re, subprocess, sys, tempfile
import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
src = open(f"{ROOT}/report/REPORT.md", encoding="utf-8").read()
body = markdown.markdown(src, extensions=["tables", "fenced_code", "sane_lists"])
body = re.sub(r'src="\.\./', 'src="file://%s/' % ROOT, body)
CSS = """
@page { size: Letter; margin: 0.55in 0.6in; }
body { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; font-size: 9.3pt; line-height: 1.32; color: #111; }
h1 { font-size: 15pt; margin: 0 0 4pt 0; } h2 { font-size: 11.5pt; margin: 10pt 0 3pt 0; border-bottom: 0.6pt solid #999; padding-bottom: 1pt; page-break-after: avoid; }
h3 { font-size: 10pt; margin: 6pt 0 2pt 0; page-break-after: avoid; }
p { margin: 3pt 0; } ul, ol { margin: 2pt 0 3pt 0; padding-left: 16pt; } li { margin: 1pt 0; }
table { border-collapse: collapse; margin: 4pt 0; font-size: 8.1pt; width: 100%; page-break-inside: avoid; }
th, td { border: 0.5pt solid #888; padding: 1.5pt 4pt; text-align: left; vertical-align: top; } th { background: #eee; }
img { max-width: 100%; max-height: 3.55in; display: block; margin: 3pt auto 1pt auto; }
p > img { page-break-inside: avoid; }
em { color: #222; } code { font-family: Menlo, monospace; font-size: 7.8pt; background: #f2f2f2; padding: 0 1pt; }
pre { background: #f6f6f6; border: 0.5pt solid #ccc; padding: 3pt 5pt; font-size: 7.4pt; line-height: 1.25; page-break-inside: avoid; overflow: hidden; }
pre code { background: none; padding: 0; font-size: 7.4pt; }
"""
html = f'<!doctype html><html><head><meta charset="utf-8"><title>SIMD Advantage Profiling</title><style>{CSS}</style></head><body>{body}</body></html>'
with tempfile.TemporaryDirectory() as d:
    h = os.path.join(d, "report.html"); open(h, "w", encoding="utf-8").write(html)
    out = f"{ROOT}/report/REPORT.pdf"
    r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={out}", "--allow-file-access-from-files", "file://" + h], capture_output=True, text=True, timeout=180)
    if r.returncode != 0 or not os.path.exists(out): sys.exit("PDF build failed: " + r.stderr[-500:])
print("wrote", out)
