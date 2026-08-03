"""
PDF-Generator fuer den Kritikalitaets-Report (Software Technologies Design).
Erzeugt ein PDF ueber einen oder mehrere Lieferanten mit Stufe A-D und
Risikomanagement-Empfehlung. Nutzt reportlab (bereits im Projekt vorhanden).
"""
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

# --- Farben (Software Technologies) ---
BG      = HexColor("#0a0e14")
PANEL   = HexColor("#121a26")
LINE    = HexColor("#27384d")
INK     = HexColor("#e7eef7")
INK_SOFT= HexColor("#8da2bb")
INK_DIM = HexColor("#5d748f")
CYAN    = HexColor("#28d3c4")
GRADE_COLORS = {"A": HexColor("#ef5c57"), "B": HexColor("#f5b942"),
                "C": HexColor("#3b9df5"), "D": HexColor("#27c08a")}
WHITE   = HexColor("#ffffff")


def _styles():
    ss = getSampleStyleSheet()
    styles = {}
    styles["h1"] = ParagraphStyle("h1", parent=ss["Normal"], fontName="Helvetica-Bold",
                                   fontSize=22, leading=26, textColor=INK, spaceAfter=2)
    styles["sub"] = ParagraphStyle("sub", parent=ss["Normal"], fontName="Helvetica",
                                    fontSize=9, leading=12, textColor=CYAN, spaceAfter=14)
    styles["tag"] = ParagraphStyle("tag", parent=ss["Normal"], fontName="Helvetica-Bold",
                                    fontSize=8, leading=11, textColor=CYAN, spaceAfter=4)
    styles["body"] = ParagraphStyle("body", parent=ss["Normal"], fontName="Helvetica",
                                     fontSize=10, leading=15, textColor=INK_SOFT, spaceAfter=10)
    styles["sname"] = ParagraphStyle("sname", parent=ss["Normal"], fontName="Helvetica-Bold",
                                      fontSize=13, leading=16, textColor=INK)
    styles["smeta"] = ParagraphStyle("smeta", parent=ss["Normal"], fontName="Helvetica",
                                      fontSize=8, leading=11, textColor=INK_DIM)
    styles["k"] = ParagraphStyle("k", parent=ss["Normal"], fontName="Helvetica",
                                 fontSize=9, leading=13, textColor=INK_DIM)
    styles["v"] = ParagraphStyle("v", parent=ss["Normal"], fontName="Helvetica",
                                 fontSize=9, leading=13, textColor=INK)
    styles["foot"] = ParagraphStyle("foot", parent=ss["Normal"], fontName="Helvetica",
                                     fontSize=8, leading=12, textColor=INK_DIM)
    return styles


def _bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(BG)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    # top accent line
    canvas.setStrokeColor(CYAN)
    canvas.setLineWidth(2)
    canvas.line(0, A4[1] - 4, A4[0], A4[1] - 4)
    # footer
    canvas.setFillColor(INK_DIM)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(18 * mm, 12 * mm,
                      "Software Technologies-Development-Service GesmbH  |  Wien  |  office@sw-tech.net  |  sw-tech.net")
    canvas.drawRightString(A4[0] - 18 * mm, 12 * mm, "powered by Ynhald")
    canvas.restoreState()


def _grade_badge(grade):
    col = GRADE_COLORS.get(grade, CYAN)
    t = Table([[grade]], colWidths=[11 * mm], rowHeights=[11 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), col),
        ("TEXTCOLOR", (0, 0), (-1, -1), WHITE),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 16),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    return t


def generate_criticality_pdf(lead: dict, suppliers: list, summary: str = "") -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=20 * mm, bottomMargin=20 * mm)
    st = _styles()
    story = []
    n = len(suppliers)
    plural = "en" if n != 1 else ""

    # Header
    story.append(Paragraph("Kritikalitäts-Report", st["h1"]))
    story.append(Paragraph("Software Technologies · Lieferanten-Kritikalität", st["sub"]))

    who = lead.get("company") or lead.get("name") or ""
    intro = f"Einstufung für {who} über {n} Lieferant{plural}. " \
            f"Jeder Lieferant ist einer Kritikalitätsstufe A–D zugeordnet, aus der sich " \
            f"Prüftiefe, Re-Assessment-Intervall und Monitoring ableiten."
    story.append(Paragraph(intro, st["body"]))

    if summary:
        story.append(Spacer(1, 2))
        story.append(Paragraph("GESAMTEINSCHÄTZUNG", st["tag"]))
        story.append(Paragraph(summary, st["body"]))

    story.append(HRFlowable(width="100%", thickness=0.6, color=LINE, spaceBefore=6, spaceAfter=14))

    # Supplier blocks
    for s in suppliers:
        grade = s.get("grade", "-")
        gname = s.get("gradeName", "")
        name = s.get("name", "-")
        url = s.get("url", "")
        plz = s.get("plz", "")
        rec = s.get("recommendation", {})
        meta = " · ".join([x for x in [url, plz] if x])
        meta_line = f"Stufe {grade} · {gname}" + (f" · {meta}" if meta else "")

        header_tbl = Table(
            [[_grade_badge(grade),
              [Paragraph(name, st["sname"]), Paragraph(meta_line, st["smeta"])]]],
            colWidths=[15 * mm, None])
        header_tbl.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))

        rec_rows = [
            [Paragraph("Prüftiefe", st["k"]), Paragraph(rec.get("tiefe", ""), st["v"])],
            [Paragraph("Re-Assessment", st["k"]), Paragraph(rec.get("reass", ""), st["v"])],
            [Paragraph("Monitoring", st["k"]), Paragraph(rec.get("monitoring", ""), st["v"])],
            [Paragraph("Freigabe", st["k"]), Paragraph(rec.get("freigabe", ""), st["v"])],
        ]
        rec_tbl = Table(rec_rows, colWidths=[38 * mm, None])
        rec_tbl.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LINEBELOW", (0, 0), (-1, -2), 0.4, LINE),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ]))

        block = Table([[header_tbl], [rec_tbl]], colWidths=[None])
        block.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PANEL),
            ("BOX", (0, 0), (-1, -1), 0.6, LINE),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(block)
        story.append(Spacer(1, 10))

    # Disclaimer
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.6, color=LINE, spaceBefore=4, spaceAfter=10))
    story.append(Paragraph(
        "Diese Einstufung ist eine strukturierte Selbsteinschätzung zur Priorisierung Ihres "
        "Risikomanagements und ersetzt kein vollständiges Lieferanten-Assessment. Software Technologies "
        "erstellt auf Wunsch das detaillierte, quellenbasierte Assessment (OSINT, Fragenkatalog, "
        "Expertenbewertung) und bildet Lieferant, Abhängigkeiten, Assets und Maßnahmen in der "
        "SSOT-Plattform ab.", st["foot"]))

    doc.build(story, onFirstPage=_bg, onLaterPages=_bg)
    return buf.getvalue()


if __name__ == "__main__":
    # Test
    lead = {"name": "Max Mustermann", "company": "Muster Kosmetik GmbH", "email": "max@firma.de"}
    sups = [
        {"name": "Nord Specialty Chemicals GmbH", "url": "www.nord.com", "plz": "1220",
         "grade": "A", "gradeName": "Sehr kritisch",
         "recommendation": {"tiefe": "Vollständiges Assessment, alle Module, ggf. Vor-Ort-Audit",
                            "reass": "Jährlich oder häufiger", "monitoring": "Laufend, mit aktiven Alerts",
                            "freigabe": "Nur mit dokumentierter Freigabe der Geschäftsführung"}},
        {"name": "Verpackung Süd AG", "url": "", "plz": "",
         "grade": "D", "gradeName": "Unkritisch",
         "recommendation": {"tiefe": "Minimal-Check / Selbstauskunft", "reass": "Nur bei Anlass",
                            "monitoring": "Keins / stichprobenartig", "freigabe": "Standardprozess"}},
    ]
    pdf = generate_criticality_pdf(lead, sups, "Nord Specialty Chemicals ist der kritischste Lieferant und sollte prioritär betrachtet werden.")
    open("test_criticality.pdf", "wb").write(pdf)
    print("PDF erzeugt:", len(pdf), "Bytes")
