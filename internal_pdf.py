"""
Interner Detail-PDF-Generator fuer den Kritikalitaets-Lead (nur fuer das Team).
Kompakt, ohne Kunden-Deko: zeigt pro Lieferant alle 8 Antworten mit Werten
sowie Impact/Wahrscheinlichkeit - als Gespraechsgrundlage fuer den Vertrieb.
"""
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

INK      = HexColor("#0f1e33")
INK_SOFT = HexColor("#475569")
INK_DIM  = HexColor("#94a3b8")
LINE     = HexColor("#e2e8f0")
PANEL    = HexColor("#f5f8fc")
CYAN     = HexColor("#0fb5a6")
WHITE    = HexColor("#ffffff")
GRADE_COLORS = {"A": HexColor("#e0483f"), "B": HexColor("#d9931a"),
                "C": HexColor("#2f7fd6"), "D": HexColor("#1f9e6e")}
VALUE_COLORS = {4: HexColor("#e0483f"), 3: HexColor("#d9931a"),
                2: HexColor("#2f7fd6"), 1: HexColor("#1f9e6e")}


def _styles():
    ss = getSampleStyleSheet()
    st = {}
    st["h1"]  = ParagraphStyle("h1", parent=ss["Normal"], fontName="Helvetica-Bold",
                                fontSize=18, leading=22, textColor=INK, spaceAfter=2)
    st["sub"] = ParagraphStyle("sub", parent=ss["Normal"], fontName="Helvetica",
                               fontSize=9, leading=12, textColor=CYAN, spaceAfter=12)
    st["tag"] = ParagraphStyle("tag", parent=ss["Normal"], fontName="Helvetica-Bold",
                               fontSize=8, leading=11, textColor=INK_DIM, spaceAfter=4)
    st["k"]   = ParagraphStyle("k", parent=ss["Normal"], fontName="Helvetica",
                               fontSize=9, leading=12, textColor=INK_SOFT)
    st["v"]   = ParagraphStyle("v", parent=ss["Normal"], fontName="Helvetica-Bold",
                               fontSize=9, leading=12, textColor=INK)
    st["sname"] = ParagraphStyle("sname", parent=ss["Normal"], fontName="Helvetica-Bold",
                                 fontSize=12, leading=15, textColor=INK)
    st["smeta"] = ParagraphStyle("smeta", parent=ss["Normal"], fontName="Helvetica",
                                 fontSize=8, leading=11, textColor=INK_DIM)
    st["cat"]  = ParagraphStyle("cat", parent=ss["Normal"], fontName="Helvetica",
                                fontSize=8, leading=11, textColor=INK_DIM)
    st["ans"]  = ParagraphStyle("ans", parent=ss["Normal"], fontName="Helvetica",
                                fontSize=9, leading=12, textColor=INK)
    st["foot"] = ParagraphStyle("foot", parent=ss["Normal"], fontName="Helvetica",
                                fontSize=7.5, leading=11, textColor=INK_DIM)
    return st


def _header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(WHITE)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    canvas.setStrokeColor(CYAN)
    canvas.setLineWidth(2)
    canvas.line(0, A4[1] - 4, A4[0], A4[1] - 4)
    canvas.setFillColor(INK_DIM)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(18 * mm, 12 * mm, "INTERN - Lead-Detailauswertung - Software Technologies")
    canvas.drawRightString(A4[0] - 18 * mm, 12 * mm, "Vertraulich")
    canvas.restoreState()


def _grade_badge(grade):
    col = GRADE_COLORS.get(grade, CYAN)
    t = Table([[grade]], colWidths=[10 * mm], rowHeights=[10 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), col),
        ("TEXTCOLOR", (0, 0), (-1, -1), WHITE),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 15),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def _value_badge(v):
    col = VALUE_COLORS.get(v, INK_DIM)
    t = Table([[str(v)]], colWidths=[7 * mm], rowHeights=[6 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), col),
        ("TEXTCOLOR", (0, 0), (-1, -1), WHITE),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def generate_internal_pdf(lead: dict, suppliers: list, summary: str = "") -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=18 * mm, bottomMargin=18 * mm)
    st = _styles()
    story = []
    n = len(suppliers)
    plural = "en" if n != 1 else ""

    # Kopf
    story.append(Paragraph("Lead-Detailauswertung", st["h1"]))
    story.append(Paragraph(f"Kritikalitäts-Einstufung · {n} Lieferant{plural}", st["sub"]))

    # Kontaktdaten
    contact_rows = [
        [Paragraph("Name", st["k"]), Paragraph(lead.get("name", "-") or "-", st["v"])],
        [Paragraph("Unternehmen", st["k"]), Paragraph(lead.get("company", "-") or "-", st["v"])],
        [Paragraph("E-Mail", st["k"]), Paragraph(lead.get("email", "-") or "-", st["v"])],
        [Paragraph("Telefon", st["k"]), Paragraph(lead.get("phone", "-") or "-", st["v"])],
    ]
    ct = Table(contact_rows, colWidths=[35 * mm, None])
    ct.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(ct)

    if summary:
        story.append(Spacer(1, 8))
        story.append(Paragraph("KI-GESAMTEINSCHÄTZUNG", st["tag"]))
        story.append(Paragraph(summary, st["ans"]))

    story.append(HRFlowable(width="100%", thickness=0.6, color=LINE, spaceBefore=10, spaceAfter=12))

    # Pro Lieferant: Kopf + alle Antworten
    for s in suppliers:
        grade = s.get("grade", "-")
        gname = s.get("gradeName", "")
        name = s.get("name", "-")
        url = s.get("url", "")
        plz = s.get("plz", "")
        impact = s.get("impact", "")
        likelihood = s.get("likelihood", "")
        meta = " · ".join([x for x in [url, plz] if x])
        meta_line = f"Stufe {grade} · {gname}" + (f" · {meta}" if meta else "")

        head = Table(
            [[_grade_badge(grade),
              [Paragraph(name, st["sname"]), Paragraph(meta_line, st["smeta"])],
              [Paragraph("Schaden / Wahrsch.", st["smeta"]),
               Paragraph(f"{impact} / {likelihood}", st["v"])]]],
            colWidths=[13 * mm, None, 32 * mm])
        head.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("ALIGN", (2, 0), (2, 0), "RIGHT"),
        ]))

        ans_data = []
        for a in s.get("answers", []):
            v = a.get("value", 0)
            ans_data.append([
                Paragraph(a.get("cat", ""), st["cat"]),
                Paragraph(a.get("answer", ""), st["ans"]),
                _value_badge(v),
            ])
        ans_tbl = Table(ans_data, colWidths=[38 * mm, None, 10 * mm])
        ans_tbl.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LINEBELOW", (0, 0), (-1, -2), 0.4, LINE),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ]))

        block = Table([[head], [ans_tbl]], colWidths=[None])
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

    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Wert 4 = höchstes Risiko (rot), 1 = niedrigstes (grün). Diese Auswertung dient der internen "
        "Gesprächsvorbereitung und ist vertraulich.", st["foot"]))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buf.getvalue()


if __name__ == "__main__":
    lead = {"name": "Max Mustermann", "company": "Muster Kosmetik GmbH",
            "email": "max@firma.de", "phone": "+43 660 1234567"}
    sups = [{"name": "Nord Specialty Chemicals GmbH", "url": "www.nord.com", "plz": "1220",
             "grade": "A", "gradeName": "Sehr kritisch", "impact": 92, "likelihood": 78,
             "answers": [
                 {"cat": "Ersetzbarkeit", "answer": "Single-Source - kein Ersatz", "value": 4},
                 {"cat": "Schadenspotenzial", "answer": "Produktionsstopp", "value": 4},
                 {"cat": "Materialkritikalität", "answer": "Wirkstoff / GMP", "value": 4},
                 {"cat": "Abhängigkeit", "answer": "Mittel", "value": 2},
                 {"cat": "Region / Compliance", "answer": "EU / gering", "value": 1},
                 {"cat": "Datenlage", "answer": "Langjährig", "value": 1},
                 {"cat": "Ersetzbarkeit", "answer": "Über 6 Monate", "value": 4},
                 {"cat": "Schadenspotenzial", "answer": "Hoch sichtbar", "value": 3},
             ]}]
    pdf = generate_internal_pdf(lead, sups, "Nord Specialty Chemicals ist der kritischste Lieferant.")
    open("test_internal.pdf", "wb").write(pdf)
    print("Internes PDF erzeugt:", len(pdf), "Bytes")
