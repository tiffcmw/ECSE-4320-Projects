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
@page { size: Letter; margin: 0.5in 0.55in; }
body { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; font-size: 8.1pt; line-height: 1.24; color: #111; }
h1 { font-size: 14pt; margin: 0 0 4pt 0; } h2 { font-size: 10.5pt; margin: 8pt 0 2pt 0; border-bottom: 0.6pt solid #999; padding-bottom: 1pt; page-break-after: avoid; }
h3 { font-size: 10pt; margin: 6pt 0 2pt 0; page-break-after: avoid; }
p { margin: 2.5pt 0; } ul, ol { margin: 2pt 0 3pt 0; padding-left: 16pt; } li { margin: 1pt 0; }
table { border-collapse: collapse; margin: 3pt 0; font-size: 7.2pt; width: 100%; } tr { page-break-inside: avoid; }
td code { word-break: break-all; font-size: 6.6pt; }
th, td { border: 0.5pt solid #888; padding: 1pt 3pt; text-align: left; vertical-align: top; } th { background: #eee; }
img { max-width: 100%; max-height: 2.4in; display: block; margin: 3pt auto 1pt auto; }
p > img { page-break-inside: avoid; }
img[src*="exp1_sweep_f32"] { max-height: 8.6in; }
img[src*="exp1_sweep_f64"] { max-height: 3.4in; }
img[src*="exp9_chase"] { max-height: 4.2in; }
img[src*="exp4_stride"] { max-height: 3.1in; }
img[src*="exp3_tail"] { max-height: 2.9in; }
img[src*="exp5_dtype"] { max-height: 3.4in; }
img[src*="exp6_roofline"] { max-height: 3.5in; }
em { color: #222; } code { font-family: Menlo, monospace; font-size: 7.2pt; background: #f2f2f2; padding: 0 1pt; }
pre { background: #f6f6f6; border: 0.5pt solid #ccc; padding: 3pt 5pt; font-size: 6.8pt; line-height: 1.2; page-break-inside: avoid; overflow: hidden; }
pre code { background: none; padding: 0; font-size: 6.8pt; }
"""
html = f'<!doctype html><html><head><meta charset="utf-8"><title>SIMD Advantage Profiling</title><style>{CSS}</style></head><body>{body}</body></html>'
with tempfile.TemporaryDirectory() as d:
    h = os.path.join(d, "report.html"); open(h, "w", encoding="utf-8").write(html)
    out = f"{ROOT}/report/REPORT.pdf"
    r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={out}", "--allow-file-access-from-files", "file://" + h], capture_output=True, text=True, timeout=180)
    if r.returncode != 0 or not os.path.exists(out): sys.exit("PDF build failed: " + r.stderr[-500:])
import re as _re
print("wrote", out, "pages:", len(_re.findall(rb"/Type\s*/Page[^s]", open(out, "rb").read())))
