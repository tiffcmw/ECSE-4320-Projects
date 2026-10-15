#!/usr/bin/env python3
"""Markdown report -> DOCX (pandoc, with a reference document styled for readable tables) -> PDF (LibreOffice).
  scripts/make_docx.py   (run scripts/build_report.py first)"""
import os, re, shutil, subprocess, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(ROOT, "report")
B = os.path.join(REP, "build")
os.makedirs(B, exist_ok=True)
MD = os.path.join(REP, "ECSE4320_Project2_Report.md")
DOCX = os.path.join(REP, "ECSE4320_Project2_Report.docx")
SOFFICE = "/Applications/LibreOffice.app/Contents/MacOS/soffice"


def reference():
    ref = os.path.join(B, "ref.docx")
    with open(ref, "wb") as f:
        f.write(subprocess.run(["pandoc", "--print-default-data-file", "reference.docx"], capture_output=True, check=True).stdout)
    z = zipfile.ZipFile(ref); items = {n: z.read(n) for n in z.namelist()}; z.close()
    st = items["word/styles.xml"].decode()
    # base font and sizes
    st = st.replace("<w:rPrDefault>", "<w:rPrDefault>", 1)
    st = re.sub(r'(<w:docDefaults>.*?<w:rPr>)', r'\1<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri" w:eastAsia="Calibri"/><w:sz w:val="19"/><w:szCs w:val="19"/>', st, count=1, flags=re.S)
    def style_patch(sid, add_rpr="", add_ppr=""):
        nonlocal st
        m = re.search(rf'(<w:style [^>]*w:styleId="{sid}".*?)(</w:style>)', st, flags=re.S)
        if not m:
            return
        blk = m.group(1)
        if add_ppr:
            blk = blk + f"<w:pPr>{add_ppr}</w:pPr>" if "<w:pPr>" not in blk else blk.replace("<w:pPr>", f"<w:pPr>{add_ppr}", 1)
        if add_rpr:
            blk = re.sub(r'<w:sz w:val="\d+"\s*/>|<w:szCs w:val="\d+"\s*/>', '', blk) if '<w:sz ' in add_rpr else blk
            blk = blk + f"<w:rPr>{add_rpr}</w:rPr>" if "<w:rPr>" not in blk else blk.replace("<w:rPr>", f"<w:rPr>{add_rpr}", 1)
        st = st[:m.start()] + blk + m.group(2) + st[m.end():]
    style_patch("Compact", '<w:sz w:val="16"/><w:szCs w:val="16"/>', '<w:spacing w:before="20" w:after="20"/>')
    style_patch("VerbatimChar", '<w:sz w:val="15"/><w:szCs w:val="15"/>')
    style_patch("ImageCaption", '<w:sz w:val="17"/><w:szCs w:val="17"/><w:i w:val="0"/>')
    style_patch("TableCaption", '<w:sz w:val="17"/><w:szCs w:val="17"/><w:i w:val="0"/>')
    style_patch("BodyText", "", '<w:spacing w:before="60" w:after="100"/>')
    style_patch("FirstParagraph", "", '<w:spacing w:before="60" w:after="100"/>')
    # table style: light grid and tight margins
    st = st.replace('''<w:tblCellMar>
        <w:top w:w="0" w:type="dxa" />
        <w:left w:w="108" w:type="dxa" />
        <w:bottom w:w="0" w:type="dxa" />
        <w:right w:w="108" w:type="dxa" />
      </w:tblCellMar>''', '''<w:tblBorders><w:top w:val="single" w:sz="4" w:color="999999"/><w:left w:val="single" w:sz="4" w:color="999999"/><w:bottom w:val="single" w:sz="4" w:color="999999"/><w:right w:val="single" w:sz="4" w:color="999999"/><w:insideH w:val="single" w:sz="4" w:color="BBBBBB"/><w:insideV w:val="single" w:sz="4" w:color="BBBBBB"/></w:tblBorders>
      <w:tblCellMar><w:top w:w="20" w:type="dxa" /><w:left w:w="60" w:type="dxa" /><w:bottom w:w="20" w:type="dxa" /><w:right w:w="60" w:type="dxa" /></w:tblCellMar>''')
    items["word/styles.xml"] = st.encode()
    doc = items["word/document.xml"].decode()
    doc = re.sub(r"<w:pgMar [^>]*/>", '<w:pgMar w:top="1080" w:right="1080" w:bottom="1080" w:left="1080" w:header="500" w:footer="500" w:gutter="0"/>', doc)
    items["word/document.xml"] = doc.encode()
    with zipfile.ZipFile(ref, "w", zipfile.ZIP_DEFLATED) as zo:
        for n, d in items.items():
            zo.writestr(n, d)
    return ref


def main():
    ref = reference()
    subprocess.run(["pandoc", MD, "-f", "markdown+pipe_tables+table_captions+implicit_figures+backtick_code_blocks-smart", "-o", DOCX, "--reference-doc", ref,
                    "--resource-path", REP, "--columns=80"], check=True)
    out = subprocess.run([SOFFICE, "--headless", "--convert-to", "pdf", "--outdir", REP, DOCX], capture_output=True, text=True)
    print(out.stdout.strip(), out.stderr.strip()[:200])


if __name__ == "__main__":
    main()
