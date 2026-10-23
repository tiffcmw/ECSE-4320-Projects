#!/usr/bin/env python3
"""Fill {{table:name}} placeholders of report_src/REPORT.template.md from data/processed/tables/*.md and write report_src/REPORT.md."""
import os, re, sys
P3 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = open(P3 + "/report_src/REPORT.template.md").read()
def sub(m):
    path = f"{P3}/data/processed/tables/{m.group(1)}.md"
    if not os.path.exists(path): sys.exit("missing table " + path)
    return open(path).read().rstrip("\n")
s = re.sub(r"\{\{table:([a-z0-9_]+)\}\}", sub, s)
if "—" in s or "–" in s: sys.exit("em/en dash found in report")
open(P3 + "/report_src/REPORT.md", "w").write(s); print("REPORT.md written,", len(s.split()), "words")
