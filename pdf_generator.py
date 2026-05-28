from fpdf import FPDF, XPos, YPos
from datetime import datetime
from typing import Dict, Any

NAVY   = (10,  25,  64)
BLUE   = (30,  63,  160)
ORANGE = (232, 150, 12)
LBLUE  = (75,  156, 211)
GREEN  = (5,   150, 105)
YELLOW = (217, 119, 6)
RED    = (220, 38,  38)
LGRAY  = (241, 245, 249)
MGRAY  = (100, 116, 139)
WHITE  = (255, 255, 255)
PURPLE = (124, 58,  237)

DIM_LABELS = {
    "legal":       "Rechtliche Absicherung",
    "cyber":       "IT-Sicherheit & Datenschutz",
    "operational": "Operative Risiken",
    "financial":   "Finanzielle Stabilitaet",
}

DIM_COLORS = {
    "legal":       BLUE,
    "cyber":       PURPLE,
    "operational": ORANGE,
    "financial":   GREEN,
}

SCORE_COLORS = {"green": GREEN, "yellow": YELLOW, "red": RED}
SCORE_LABELS = {"green": "GUT GESICHERT", "yellow": "HANDLUNGSBEDARF", "red": "KRITISCHES RISIKO"}
SCORE_BG     = {"green": (236,253,245), "yellow": (255,251,235), "red": (254,242,242)}
ANSWER_SCORES = {"Ja": 100, "Teilweise": 50, "Nein": 0, "Weiss nicht": 0, "Weiß nicht": 0,
                 "Yes": 100, "Partially": 50, "No": 0, "Don't know": 0,
                 "Si": 100, "Parcialmente": 50, "Oui": 100, "Partiellement": 50, "Non": 0}

QUESTIONS = [
    {"id":"Q1.1","dim":"legal","label":"Versicherungsnachweis","q":"Haftpflicht-/Cyber-Versicherung explizit abgedeckt?","fix":"Jaehrlich aktuelle Versicherungsbestaetigung verlangen."},
    {"id":"Q1.2","dim":"legal","label":"Right-to-Audit","q":"Lieferantenvertrag enthaelt Right-to-Audit-Klauseln?","fix":"Right-to-Audit-Klauseln bei naechster Verlaengerung einfuegen."},
    {"id":"Q1.3","dim":"legal","label":"72h-Meldepflicht","q":"Vertraglich vereinbarte 72h-Meldepflicht fuer Sicherheitsvorfaelle?","fix":"72h-Meldepflicht verankern; bei laufenden Vertraegen als Addendum."},
    {"id":"Q1.4","dim":"legal","label":"UBO/PEP-Check","q":"UBO und Key-Management inkl. Sanktions-/PEP-Check geprueft?","fix":"KYB-Dienste fuer jaehrliche UBO/PEP-Screenings nutzen."},
    {"id":"Q1.5","dim":"legal","label":"Jaehrl. Rezertifizierung","q":"Jaehrliche Vertrags-Rezertifizierung durchgefuehrt?","fix":"Jaehrlichen Rezertifizierungskalender etablieren."},
    {"id":"Q2.1","dim":"cyber","label":"Datenspeicherort","q":"Datenspeicherort (Land/Rechenzentrum) bekannt?","fix":"Schriftliche Bestaetigung des Datenspeicherorts in der DPA verankern."},
    {"id":"Q2.2","dim":"cyber","label":"Externe Pruefberichte","q":"Aktuelle SOC2/ISO27001/PenTest-Berichte (max. 12 Monate)?","fix":"SOC2 Typ II oder ISO 27001 als Onboarding-Voraussetzung verlangen."},
    {"id":"Q2.3","dim":"cyber","label":"Datenverschluesselung","q":"Sensible Daten verschluesselt (at-rest und in-transit)?","fix":"Schriftliche Bestaetigung der Verschluesselungsstandards verlangen."},
    {"id":"Q2.4","dim":"cyber","label":"Incident-Monitoring","q":"Automatisierter Alert-Prozess bei Sicherheitsvorfaellen?","fix":"Threat-Intelligence-Feeds (SecurityScorecard, BitSight) abonnieren."},
    {"id":"Q2.5","dim":"cyber","label":"Vendor-Onboarding","q":"Dokumentiertes jaehrliches Vendor-Onboarding + Remediation-Routine?","fix":"Standardisiertes Vendor-Assessment-Framework implementieren."},
    {"id":"Q3.1","dim":"operational","label":"BC/DR-Plan","q":"Getesteter BC/DR-Plan inkl. Sub-Tier-Ausfaelle vorhanden?","fix":"Jaehrliche BC/DR-Testnachweise inkl. Sub-Tier-Abdeckung verlangen."},
    {"id":"Q3.2","dim":"operational","label":"Sub-Tier-Transparenz","q":"Wichtigste Sub-Tier-Lieferanten fuer kritische Komponenten bekannt?","fix":"Tier-2/3-Lieferanten-Mapping fuer kritische Komponenten erstellen."},
    {"id":"Q3.3","dim":"operational","label":"Zweite Bezugsquelle","q":"Mindestens eine validierte Zweitquelle fuer Schluesselkomponenten?","fix":"Alternative Quelle fuer kritische Teile qualifizieren und regelmaessig testen."},
    {"id":"Q3.4","dim":"operational","label":"Lieferueberwachung","q":"Lieferzeiten/Kapazitaeten/Bestaende regelmaessig ueberwacht?","fix":"KPI-Dashboards mit automatischen Alerts implementieren."},
    {"id":"Q3.5","dim":"operational","label":"Vor-Ort-Audit","q":"Jaehrliches Vor-Ort- oder Remote-Audit durchgefuehrt?","fix":"Jaehrliche Audits fuer Tier-1-Lieferanten planen und dokumentieren."},
    {"id":"Q4.1","dim":"financial","label":"Finanzmonitoring","q":"Automatisierte Bonitaets-Alerts oder regelmaessige Finanz-Updates?","fix":"Creditsafe oder D&B fuer automatisierte Bonitaets-Alerts nutzen."},
    {"id":"Q4.2","dim":"financial","label":"Finanzsicherheiten","q":"Mindest-Liquiditaetskennzahlen oder Parent-Guarantees vereinbart?","fix":"Mindest-Finanzkennzahlen bei strategischen Lieferanten verankern."},
    {"id":"Q4.3","dim":"financial","label":"Jahresabschluss-Pruefung","q":"Jaehrlich geprueft: Bilanz/GuV oder Finanzkennzahlen?","fix":"Testierte Jahresabschluesse als Standard fordern."},
    {"id":"Q4.4","dim":"financial","label":"Concentration-Risk","q":"Ausgaben pro Lieferant limitiert und Concentration-Risk getrackt?","fix":"Spend-Analysen durchfuehren und Obergrenzen setzen."},
    {"id":"Q4.5","dim":"financial","label":"Business-Interruption","q":"Lieferant hat BII mit Drittschadendeckung?","fix":"BII-Nachweis mit Drittschadendeckung als Vertragsstandard verlangen."},
]


def safe(text: str) -> str:
    return (str(text)
        .replace("\u2014", "-").replace("\u2013", "-")
        .replace("\u2019", "'").replace("\u2018", "'")
        .replace("\u201C", '"').replace("\u201D", '"')
        .replace("\u2026", "...").replace("\u2192", ">>")
        .replace("\u00e4", "ae").replace("\u00f6", "oe").replace("\u00fc", "ue")
        .replace("\u00c4", "Ae").replace("\u00d6", "Oe").replace("\u00dc", "Ue")
        .replace("\u00df", "ss")
    )


class YnhaldPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_margins(16, 26, 16)
        self.set_auto_page_break(auto=True, margin=18)

    def header(self):
        self.set_fill_color(*NAVY)
        self.rect(0, 0, 210, 22, "F")
        self.set_fill_color(*ORANGE)
        self.rect(0, 20, 210, 2, "F")
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*WHITE)
        self.set_xy(16, 5)
        self.cell(40, 10, "YNHALD")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(180, 200, 230)
        self.set_xy(56, 7)
        self.cell(80, 7, "Supplier Risk Assessment Report")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(150, 170, 210)
        self.set_xy(140, 7)
        self.cell(54, 7, datetime.now().strftime("%d.%m.%Y"), align="R")
        self.ln(14)

    def footer(self):
        self.set_fill_color(*NAVY)
        self.rect(0, 287, 210, 10, "F")
        self.set_y(-10)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(150, 170, 210)
        self.cell(0, 8, f"YNHALD Supplier Risk Management as a Service  -  {datetime.now().strftime('%d.%m.%Y')}  -  Vertraulich  -  Seite {self.page_no()}", align="C")

    def section_title(self, title, color=BLUE):
        self.set_fill_color(*color)
        self.rect(16, self.get_y(), 4, 7, "F")
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*color)
        self.set_x(22)
        self.cell(0, 7, title.upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def score_bar(self, label, value, bar_width=95):
        val = int(value)
        bar_color = GREEN if val >= 80 else (YELLOW if val >= 60 else RED)
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(*NAVY)
        self.cell(58, 6, label)
        x = self.get_x()
        y = self.get_y() + 0.5
        self.set_fill_color(220, 228, 240)
        self.rect(x, y, bar_width, 5, "F")
        self.set_fill_color(*bar_color)
        if val > 0:
            self.rect(x, y, bar_width * val / 100, 5, "F")
        self.set_xy(x + bar_width + 3, self.get_y())
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*bar_color)
        self.cell(14, 6, f"{val}%", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def check_page_break(self, needed_height=25):
        if self.get_y() + needed_height > 265:
            self.add_page()


def generate_pdf(data: Dict[str, Any]) -> bytes:
    lead      = data["lead"]
    scores    = data["scores"]
    analysis  = data["analysis"]
    answers   = data["answers"]
    ind_label = safe(data.get("industryLabel", "-"))

    sc_color = scores["color"]
    sc_final = int(scores["final"])
    sc_ds    = scores["ds"]
    sc_col   = SCORE_COLORS.get(sc_color, MGRAY)
    sc_bg    = SCORE_BG.get(sc_color, (248,250,252))

    pdf = YnhaldPDF()
    pdf.add_page()

    # ── PAGE 1: EXECUTIVE SUMMARY ─────────────────────────────────

    # Title
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 9, "Supplier Risk Assessment", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*MGRAY)
    pdf.cell(0, 5, safe(f"{lead['company']}   -   {datetime.now().strftime('%d.%m.%Y')}   -   {ind_label}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)

    # Score hero
    hero_y = pdf.get_y()
    pdf.set_fill_color(*sc_bg)
    pdf.set_draw_color(*sc_col)
    pdf.set_line_width(0.4)
    pdf.rect(16, hero_y, 178, 30, "FD")
    pdf.set_fill_color(*sc_col)
    pdf.rect(16, hero_y, 5, 30, "F")
    pdf.set_line_width(0.2)
    # Score number
    pdf.set_font("Helvetica", "B", 36)
    pdf.set_text_color(*sc_col)
    pdf.set_xy(26, hero_y + 3)
    pdf.cell(28, 16, str(sc_final))
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*MGRAY)
    pdf.set_xy(54, hero_y + 9)
    pdf.cell(15, 7, "/100")
    # Status
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*sc_col)
    pdf.set_xy(76, hero_y + 5)
    pdf.cell(110, 8, safe(SCORE_LABELS.get(sc_color, "")))
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*MGRAY)
    pdf.set_xy(76, hero_y + 15)
    pdf.cell(110, 6, f"Branche: {ind_label}")
    pdf.ln(34)

    # Meta boxes
    meta = [
        ("Kontaktperson", safe(lead.get("name",""))),
        ("Unternehmen",   safe(lead.get("company",""))),
        ("E-Mail",        safe(lead.get("email",""))),
        ("Erstellt am",   datetime.now().strftime("%d.%m.%Y")),
    ]
    my = pdf.get_y()
    for i, (lbl, val) in enumerate(meta):
        x = 16 + (i % 2) * 90
        y = my + (i // 2) * 14
        pdf.set_fill_color(*LGRAY)
        pdf.rect(x, y, 87, 12, "F")
        pdf.set_fill_color(*BLUE if i < 2 else ORANGE)
        pdf.rect(x, y, 3, 12, "F")
        pdf.set_xy(x + 5, y + 1)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*MGRAY)
        pdf.cell(79, 4, lbl)
        pdf.set_xy(x + 5, y + 5)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*NAVY)
        pdf.cell(79, 5, val[:38] if val else "-")
    pdf.ln(32)

    # Executive Summary
    pdf.section_title("Executive Summary", BLUE)
    exec_text = safe(analysis.get("exec", ""))
    pdf.set_fill_color(240, 244, 255)
    ey = pdf.get_y()
    pdf.set_font("Helvetica", "", 8.5)
    # Calculate height needed
    lines = pdf.multi_cell(170, 4.5, exec_text, dry_run=True, output="LINES")
    box_h = max(14, len(lines) * 4.5 + 6)
    pdf.rect(16, ey, 178, box_h, "F")
    pdf.set_xy(20, ey + 3)
    pdf.set_text_color(*NAVY)
    pdf.multi_cell(170, 4.5, exec_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # Dimensions
    pdf.section_title("Risikodimensionen", BLUE)
    for dim, label in DIM_LABELS.items():
        val = sc_ds.get(dim, 0)
        dc = DIM_COLORS.get(dim, BLUE)
        pdf.set_fill_color(*dc)
        pdf.rect(16, pdf.get_y() + 1.5, 3, 3, "F")
        pdf.set_x(21)
        pdf.score_bar(label, val)
    pdf.ln(3)

    # Business Impact
    pdf.section_title("Geschaeftsauswirkung", RED)
    impact_text = safe(analysis.get("impact", ""))
    iy = pdf.get_y()
    pdf.set_fill_color(254, 242, 242)
    i_lines = pdf.multi_cell(168, 4.5, impact_text, dry_run=True, output="LINES")
    i_box_h = max(12, len(i_lines) * 4.5 + 6)
    pdf.rect(16, iy, 178, i_box_h, "F")
    pdf.set_fill_color(*RED)
    pdf.rect(16, iy, 4, i_box_h, "F")
    pdf.set_xy(24, iy + 3)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(127, 29, 29)
    pdf.multi_cell(166, 4.5, impact_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # Priority Actions - all 3 together, no page breaks between them
    pdf.section_title("Sofortmassnahmen", NAVY)
    prio_colors = [ORANGE, BLUE, LBLUE]
    prio_bgs    = [(255,247,237), (240,244,255), (236,247,255)]
    priorities  = [analysis.get("p1",{}), analysis.get("p2",{}), analysis.get("p3",{})]

    for i, (p, col, bg) in enumerate(zip(priorities, prio_colors, prio_bgs)):
        if not p or not p.get("title"):
            continue
        title_text = safe(p.get("title", ""))
        body_text  = safe(p.get("text", ""))
        # Estimate height needed
        t_lines = pdf.multi_cell(150, 4, title_text, dry_run=True, output="LINES")
        b_lines = pdf.multi_cell(150, 4, body_text, dry_run=True, output="LINES")
        needed = (len(t_lines) + len(b_lines)) * 4 + 10
        pdf.check_page_break(needed)

        py = pdf.get_y()
        pdf.set_fill_color(*bg)
        pdf.rect(16, py, 178, needed, "F")
        # Number badge
        pdf.set_fill_color(*col)
        pdf.rect(16, py, 14, needed, "F")
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*WHITE)
        pdf.set_xy(16, py + needed/2 - 5)
        pdf.cell(14, 8, str(i+1), align="C")
        # Title
        pdf.set_xy(33, py + 3)
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*NAVY)
        pdf.multi_cell(157, 4, title_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        # Body
        pdf.set_x(33)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*MGRAY)
        pdf.multi_cell(157, 4, body_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)
    pdf.ln(3)

    # CTA Box
    pdf.check_page_break(28)
    cta_y = pdf.get_y()
    pdf.set_fill_color(*NAVY)
    pdf.rect(16, cta_y, 178, 24, "F")
    pdf.set_fill_color(*ORANGE)
    pdf.rect(16, cta_y + 22, 178, 2, "F")
    pdf.set_xy(24, cta_y + 4)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*ORANGE)
    pkg_text = safe(analysis.get("pkg", "Guided Remediation"))
    pdf.cell(0, 7, f"Empfehlung: {pkg_text}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(24)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(180, 200, 230)
    pdf.cell(0, 6, "Kostenloses Erstgespraech: office@ynhald.com  |  cal.com/alexander-zajic/riskmanagement")
    pdf.ln(14)

    # ── PAGE 2+: DETAILED Q&A ──────────────────────────────────────
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 9, "Detaillierter Fragebogen", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    for dim, dim_label in DIM_LABELS.items():
        dim_col = DIM_COLORS.get(dim, BLUE)
        dim_qs  = [q for q in QUESTIONS if q["dim"] == dim]

        pdf.check_page_break(16)
        dh_y = pdf.get_y()
        pdf.set_fill_color(*dim_col)
        pdf.rect(16, dh_y, 178, 9, "F")
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*WHITE)
        pdf.set_xy(20, dh_y + 1)
        pdf.cell(0, 7, dim_label.upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)

        for q in dim_qs:
            ans = answers.get(q["id"], "-")
            ans_clean = (ans.replace("Weiß nicht","Weiss nicht")
                           .replace("Don't know","Weiss nicht"))
            sc_val = ANSWER_SCORES.get(ans, ANSWER_SCORES.get(ans_clean, 0))
            col   = GREEN if sc_val == 100 else (YELLOW if sc_val == 50 else RED)
            bg    = (236,253,245) if sc_val == 100 else ((255,251,235) if sc_val == 50 else (254,242,242))

            # Calculate height needed for this row
            q_lines = pdf.multi_cell(158, 4, safe(q["q"]), dry_run=True, output="LINES")
            f_lines = pdf.multi_cell(158, 3.5, safe(q.get("fix","")), dry_run=True, output="LINES") if sc_val < 100 else []
            row_h = (len(q_lines) + len(f_lines)) * 4 + 12
            pdf.check_page_break(row_h)

            row_y = pdf.get_y()
            pdf.set_fill_color(*bg)
            pdf.rect(16, row_y, 178, row_h, "F")
            pdf.set_fill_color(*col)
            pdf.rect(16, row_y, 4, row_h, "F")

            # Header row
            pdf.set_xy(22, row_y + 2)
            pdf.set_font("Helvetica", "B", 7.5)
            pdf.set_text_color(*NAVY)
            pdf.cell(120, 4, safe(f"{q['id']} - {q['label']}"))
            pdf.set_font("Helvetica", "B", 7.5)
            pdf.set_text_color(*col)
            pdf.set_x(22 + 120)
            pdf.cell(50, 4, safe(f"{ans}  ({sc_val}%)"), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            # Question text
            pdf.set_x(22)
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(*MGRAY)
            pdf.multi_cell(168, 4, safe(q["q"]), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            # Fix text
            if sc_val < 100 and q.get("fix"):
                pdf.set_x(22)
                pdf.set_font("Helvetica", "I", 7)
                pdf.set_text_color(71, 85, 105)
                pdf.multi_cell(168, 3.5, safe(f">> {q['fix']}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(2)
        pdf.ln(3)

    # ── LAST PAGE: METHOD + CTA ────────────────────────────────────
    pdf.check_page_break(80)
    pdf.section_title("Methodik & Bewertungslogik", MGRAY)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*NAVY)
    pdf.multi_cell(0, 4.5, "Ja = 100 Pkt | Teilweise = 50 Pkt | Nein/Weiss nicht = 0 Pkt. Die vier Dimensionen werden als gewichteter Durchschnitt berechnet und mit branchenspezifischen Gewichten zum Gesamtscore aggregiert. Ampel: Gruen >= 80 | Gelb 60-79 | Rot < 60. High-Trigger-Fragen mit 0 Punkten setzen den Sales-Flag.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(*MGRAY)
    pdf.cell(0, 5, safe(f"Assessment: {datetime.now().strftime('%d.%m.%Y %H:%M')} UTC  |  {lead.get('company','')}  |  {lead.get('email','')}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)

    # Package box
    pdf.check_page_break(45)
    pdf.section_title("Paketempfehlung", ORANGE)
    pr_y = pdf.get_y()
    pkg_name = safe(analysis.get("pkg", "Guided Remediation"))
    pkg_why  = safe(analysis.get("pkgWhy", ""))
    why_lines = pdf.multi_cell(168, 4.5, pkg_why, dry_run=True, output="LINES")
    pr_h = len(why_lines) * 4.5 + 20
    pdf.set_fill_color(*ORANGE)
    pdf.rect(16, pr_y, 178, 10, "F")
    pdf.set_fill_color(255, 247, 237)
    pdf.rect(16, pr_y + 10, 178, pr_h - 10, "F")
    pdf.set_xy(20, pr_y + 2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 6, pkg_name)
    pdf.set_xy(20, pr_y + 13)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*NAVY)
    pdf.multi_cell(170, 4.5, pkg_why, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)

    # Final CTA
    pdf.check_page_break(30)
    fta_y = pdf.get_y()
    pdf.set_fill_color(*NAVY)
    pdf.rect(16, fta_y, 178, 28, "F")
    pdf.set_fill_color(*ORANGE)
    pdf.rect(16, fta_y + 26, 178, 2, "F")
    pdf.set_xy(24, fta_y + 5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 7, "Kostenloses Erstgespraech buchen", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(24)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*ORANGE)
    pdf.cell(0, 5, "office@ynhald.com", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(24)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(150, 170, 210)
    pdf.cell(0, 5, "cal.com/alexander-zajic/riskmanagement  |  YNHALD - Supplier Risk Management as a Service")

    return bytes(pdf.output())
