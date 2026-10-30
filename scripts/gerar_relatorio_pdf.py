"""Gera PDF a partir do relatório versionado (biblioteca ReportLab)."""
from pathlib import Path
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from xml.sax.saxutils import escape

source = Path("RELATORIO_FINAL.md").read_text(encoding="utf-8")
target = Path("Relatorio_Final_TP2_P2P_2026.pdf")
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TextAcademic", parent=styles["BodyText"], fontSize=9, leading=13, alignment=TA_JUSTIFY, spaceAfter=8))
styles.add(ParagraphStyle(name="SmallAcademic", parent=styles["BodyText"], fontSize=7.5, leading=10, spaceAfter=6))
styles.add(ParagraphStyle(name="HeadAcademic", parent=styles["Heading2"], fontSize=11, leading=14, spaceBefore=12, spaceAfter=6))
doc = SimpleDocTemplate(str(target), pagesize=A4, leftMargin=45, rightMargin=45, topMargin=44, bottomMargin=44)
flow = []
lines = source.splitlines()
i = 0
def rich(value):
    value = escape(value)
    value = re.sub(r"\\*\\*(.+?)\\*\\*", r"<b>\\1</b>", value)
    value = re.sub(r"`([^`]+)`", r"<font name='Courier'>\\1</font>", value)
    value = re.sub(r"\\[([^]]+)\\]\\((https?://[^)]+)\\)", r"\\1 (\\2)", value)
    return value
while i < len(lines):
    line = lines[i].strip()
    if not line:
        i += 1
        continue
    if line.startswith("|") and i + 1 < len(lines):
        rows = []
        while i < len(lines) and lines[i].startswith("|"):
            cells = [x.strip() for x in lines[i].strip("|").split("|")]
            if not all(re.fullmatch(r":?-{2,}:?", x) for x in cells):
                rows.append([Paragraph(rich(c), styles["SmallAcademic"]) for c in cells])
            i += 1
        if rows:
            table = Table(rows, repeatRows=1, hAlign="LEFT", colWidths=[100]+[99]*(len(rows[0])-1))
            table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#e7edf3")),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f5f7fa")]),
                ("VALIGN",(0,0),(-1,-1),"TOP"),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
            flow.append(table)
        continue
    if line.startswith("# "):
        flow.append(Paragraph(rich(line[2:]),styles["Title"]))
    elif line.startswith("## "):
        flow.append(Paragraph(rich(line[3:]),styles["HeadAcademic"]))
    else:
        flow.append(Paragraph(rich(line),styles["TextAcademic"]))
    i += 1
def footer(canvas,doc):
    canvas.setFont("Helvetica",8)
    canvas.drawRightString(A4[0]-45,26,f"Página {doc.page}")
doc.build(flow,onFirstPage=footer,onLaterPages=footer)
print(f"Gerado: {target} ({target.stat().st_size} bytes)")
