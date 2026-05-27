from fpdf import FPDF, XPos, YPos
from datetime import datetime
from typing import Dict, Any

# Brand Colors (RGB)
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

ANSWER_SCORES = {"Ja": 100, "Teilweise": 50, "Nein": 0, "Weiss nicht": 0, "Weiß nicht": 0}

QUESTIONS = [
    {"id":"Q1.1","dim":"legal",       "label":"Versicherungsnachweis",
     "q":"Haftpflicht-/Cyber-Versicherung liegt vor und deckt Zusammenarbeit explizit ab?",
     "fix":"Verlange jaehrlich eine aktuelle Versicherungsbestaetigung."},
    {"id":"Q1.2","dim":"legal",       "label":"Right-to-Audit",
     "q":"Lieferantenvertrag enthaelt Right-to-Audit-Klauseln?",
     "fix":"Right-to-Audit-Klauseln bei naechster Vertragsverlaengerung einfuegen."},
    {"id":"Q1.3","dim":"legal",       "label":"72h-Meldepflicht",
     "q":"Vertraglich vereinbarte 72h-Meldepflicht fuer Sicherheitsvorfaelle?",
     "fix":"72h-Meldepflicht verankern; bei laufenden Vertraegen als Addendum."},
    {"id":"Q1.4","dim":"legal",       "label":"UBO/PEP-Check",
     "q":"UBO und Key-Management inkl. Sanktions-/PEP-Check geprueft?",
     "fix":"KYB-Dienste fuer jaehrliche UBO/PEP-Screenings nutzen."},
    {"id":"Q1.5","dim":"legal",       "label":"Jaehrl. Rezertifizierung",
     "q":"Jaehrliche Vertrags-Rezertifizierung durchgefuehrt?",
     "fix":"Jaehrlichen Rezertifizierungskalender etablieren."},
    {"id":"Q2.1","dim":"cyber",       "label":"Datenspeicherort",
     "q":"Datenspeicherort (Land/Rechenzentrum) bekannt?",
     "fix":"Schriftliche Bestaetigung des Datenspeicherorts in der DPA verankern."},
    {"id":"Q2.2","dim":"cyber",       "label":"Externe Pruefberichte",
     "q":"Aktuelle SOC2/ISO27001/PenTest-Berichte (max. 12 Monate)?",
     "fix":"SOC2 Typ II oder ISO 27001 als Onboarding-Voraussetzung verlangen."},
    {"id":"Q2.3","dim":"cyber",       "label":"Datenverschluesselung",
     "q":"Sensible Daten verschluesselt (at-rest und in-transit)?",
     "fix":"Schriftliche Bestaetigung der Verschluesselungsstandards verlangen."},
    {"id":"Q2.4","dim":"cyber",       "label":"Incident-Monitoring",
     "q":"Automatisierter Alert-Prozess bei Sicherheitsvorfaellen?",
     "fix":"Threat-Intelligence-Feeds (SecurityScorecard, BitSight) abonnieren."},
    {"id":"Q2.5","dim":"cyber",       "label":"Vendor-Onboarding",
     "q":"Dokumentiertes jaehrliches Vendor-Onboarding + Remediation-Routine?",
     "fix":"Standardisiertes Vendor-Assessment-Framework implementieren."},
    {"id":"Q3.1","dim":"operational", "label":"BC/DR-Plan",
     "q":"Getesteter BC/DR-Plan inkl. Sub-Tier-Ausfaelle vorhanden?",
     "fix":"Jaehrliche BC/DR-Testnachweise inkl. Sub-Tier-Abdeckung verlangen."},
    {"id":"Q3.2","dim":"operational", "label":"Sub-Tier-Transparenz",
     "q":"Wichtigste Sub-Tier-Lieferanten fuer kritische Komponenten bekannt?",
     "fix":"Tier-2/3-Lieferanten-Mapping fuer kritische Komponenten erstellen."},
    {"id":"Q3.3","dim":"operational", "label":"Zweite Bezugsquelle",
     "q":"Mindestens eine validierte Zweitquelle fuer Schluesselkomponenten?",
     "fix":"Alternative Quelle fuer kritische Teile qualifizieren und regelmaessig testen."},
    {"id":"Q3.4","dim":"operational", "label":"Lieferueberwachung",
     "q":"Lieferzeiten/Kapazitaeten/Bestaende regelmaessig ueberwacht?",
     "fix":"KPI-Dashboards mit automatischen Alerts implementieren."},
    {"id":"Q3.5","dim":"operational", "label":"Vor-Ort-Audit",
     "q":"Jaehrliches Vor-Ort- oder Remote-Audit durchgefuehrt?",
     "fix":"Jaehrliche Audits fuer Tier-1-Lieferanten planen und dokumentieren."},
    {"id":"Q4.1","dim":"financial",   "label":"Finanzmonitoring",
     "q":"Automatisierte Bonitaets-Alerts oder regelmaessige Finanz-Updates?",
     "fix":"Creditsafe oder D&B fuer automatisierte Bonitaets-Alerts nutzen."},
    {"id":"Q4.2","dim":"financial",   "label":"Finanzsicherheiten",
     "q":"Mindest-Liquiditaetskennzahlen oder Parent-Guarantees vereinbart?",
     "fix":"Mindest-Finanzkennzahlen bei strategischen Lieferanten verankern."},
    {"id":"Q4.3","dim":"financial",   "label":"Jahresabschluss-Pruefung",
     "q":"Jaehrlich geprueft: Bilanz/GuV oder Finanzkennzahlen?",
     "fix":"Testierte Jahresabschluesse als Standard fordern."},
    {"id":"Q4.4","dim":"financial",   "label":"Concentration-Risk",
     "q":"Ausgaben pro Lieferant limitiert und Concentration-Risk getrackt?",
     "fix":"Spend-Analysen durchfuehren und Obergrenzen setzen."},
    {"id":"Q4.5","dim":"financial",   "label":"Business-Interruption",
     "q":"Lieferant hat BII mit Drittschadendeckung?",
     "fix":"BII-Nachweis mit Drittschadendeckung als Vertragsstandard verlangen."},
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
    def __init__(self, data: Dict[str, Any]):
        super().__init__()
        self.data = data
        self.set_margins(16, 22, 16)
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        # Full-width navy header
        self.set_fill_color(*NAVY)
        self.rect(0, 0, 210, 24, "F")
        # Orange accent bar
        self.set_fill_color(*ORANGE)
        self.rect(0, 22, 210, 3, "F")
        # Logo text
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*WHITE)
        self.set_xy(16, 5)
        self.cell(40, 12, "YNHALD")
        # Subtitle
        self.set_font("Helvetica", "", 9)
        self.set_text_color(180, 200, 230)
        self.set_xy(56, 8)
        self.cell(80, 7, "Supplier Risk Assessment Report")
        # Date
        self.set_font("Helvetica", "", 8)
        self.set_text_color(150, 170, 210)
        self.set_xy(140, 8)
        self.cell(54, 7, datetime.now().strftime("%d.%m.%Y"), align="R")
        self.ln(16)

    def footer(self):
        self.set_fill_color(*NAVY)
        self.rect(0, 287, 210, 10, "F")
        self.set_y(-10)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(150, 170, 210)
        self.cell(0, 8, f"YNHALD Supplier Risk Management as a Service  -  {datetime.now().strftime('%d.%m.%Y')}  -  Vertraulich  -  Seite {self.page_no()}", align="C")

    def colored_section_header(self, title: str, color=BLUE):
        self.set_fill_color(*color)
        self.rect(16, self.get_y(), 4, 8, "F")
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*color)
        self.set_x(22)
        self.cell(0, 8, title.upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def score_bar_colored(self, label: str, value: float, dim_color=BLUE, bar_width: float = 95):
        val = int(value)
        bar_color = GREEN if val >= 80 else (YELLOW if val >= 60 else RED)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*NAVY)
        self.cell(58, 7, label)
        x = self.get_x()
        y = self.get_y() + 1
        # Background
        self.set_fill_color(225, 232, 240)
        self.rect(x, y, bar_width, 5, "F")
        # Value fill
        self.set_fill_color(*bar_color)
        filled = bar_width * val / 100
        if filled > 0:
            self.rect(x, y, filled, 5, "F")
        # Percentage
        self.set_xy(x + bar_width + 3, self.get_y())
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*bar_color)
        self.cell(12, 7, f"{val}%", new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def generate_pdf(data: Dict[str, Any]) -> bytes:
    lead      = data["lead"]
    scores    = data["scores"]
    analysis  = data["analysis"]
    answers   = data["answers"]
    ind_label = data.get("industryLabel", "-")

    sc_color  = scores["color"]
    sc_final  = int(scores["final"])
    sc_ds     = scores["ds"]
    sc_col    = SCORE_COLORS.get(sc_color, MGRAY)
    sc_bg     = SCORE_BG.get(sc_color, (248,250,252))

    pdf = YnhaldPDF(data)
    pdf.add_page()

    # ---- PAGE 1: EXECUTIVE SUMMARY --------------------------------

    # Title
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 10, "Supplier Risk Assessment", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*MGRAY)
    pdf.cell(0, 6, safe(f"{lead['company']}   -   {datetime.now().strftime('%d.%m.%Y')}   -   Branche: {ind_label}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)

    # Score Hero - colored box
    pdf.set_fill_color(*sc_bg)
    pdf.set_draw_color(*sc_col)
    pdf.set_line_width(0.5)
    hero_y = pdf.get_y()
    pdf.rect(16, hero_y, 178, 36, "FD")
    # Left accent bar
    pdf.set_fill_color(*sc_col)
    pdf.rect(16, hero_y, 5, 36, "F")
    # Score number
    pdf.set_font("Helvetica", "B", 42)
    pdf.set_text_color(*sc_col)
    pdf.set_xy(26, hero_y + 4)
    pdf.cell(30, 20, str(sc_final))
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*MGRAY)
    pdf.set_xy(56, hero_y + 10)
    pdf.cell(20, 8, "/100")
    # Status label
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*sc_col)
    pdf.set_xy(82, hero_y + 5)
    pdf.cell(100, 10, safe(SCORE_LABELS.get(sc_color, "-")))
    # Industry
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*MGRAY)
    pdf.set_xy(82, hero_y + 17)
    pdf.cell(100, 7, safe(f"Branche: {ind_label}"))
    pdf.set_line_width(0.2)
    pdf.ln(38)

    # Meta grid - 4 colored boxes
    meta = [
        ("Kontaktperson", safe(lead["name"]), BLUE),
        ("Unternehmen",   safe(lead["company"]), NAVY),
        ("E-Mail",        safe(lead["email"]), MGRAY),
        ("Erstellt am",   datetime.now().strftime("%d.%m.%Y"), ORANGE),
    ]
    grid_y = pdf.get_y()
    for i, (lbl, val, col) in enumerate(meta):
        x = 16 + (i % 2) * 90
        y = grid_y + (i // 2) * 18
        pdf.set_fill_color(*LGRAY)
        pdf.rect(x, y, 87, 15, "F")
        pdf.set_fill_color(*col)
        pdf.rect(x, y, 3, 15, "F")
        pdf.set_xy(x + 6, y + 2)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*MGRAY)
        pdf.cell(78, 4, lbl)
        pdf.set_xy(x + 6, y + 7)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*NAVY)
        pdf.cell(78, 5, val[:35] if val else "-")
    pdf.ln(40)

    # Executive Summary
    pdf.colored_section_header("Executive Summary", BLUE)
    pdf.set_fill_color(240, 244, 255)
    summ_y = pdf.get_y()
    pdf.rect(16, summ_y, 178, 20, "F")
    pdf.set_xy(20, summ_y + 2)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*NAVY)
    pdf.multi_cell(170, 5, safe(analysis.get("exec", "")), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # Dimension Scores - colored bars
    pdf.colored_section_header("Risikodimensionen", BLUE)
    for dim, label in DIM_LABELS.items():
        val = sc_ds.get(dim, 0)
        dim_col = DIM_COLORS.get(dim, BLUE)
        # Dim color dot
        pdf.set_fill_color(*dim_col)
        pdf.rect(16, pdf.get_y() + 2, 3, 3, "F")
        pdf.set_x(21)
        pdf.score_bar_colored(label, val, dim_col)
    pdf.ln(4)

    # Business Impact - red box
    pdf.colored_section_header("Geschaeftsauswirkung", RED)
    impact_y = pdf.get_y()
    pdf.set_fill_color(254, 242, 242)
    pdf.rect(16, impact_y, 178, 18, "F")
    pdf.set_fill_color(*RED)
    pdf.rect(16, impact_y, 4, 18, "F")
    pdf.set_xy(24, impact_y + 2)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(127, 29, 29)
    pdf.multi_cell(166, 5, safe(analysis.get("impact", "")), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # Priority Actions - colored numbered boxes
    pdf.colored_section_header("Sofortmassnahmen", NAVY)
    prio_colors = [ORANGE, BLUE, LBLUE]
    prio_bgs    = [(255,247,237), (240,244,255), (236,247,255)]
    priorities  = [analysis.get("p1",{}), analysis.get("p2",{}), analysis.get("p3",{})]
    for i, (p, col, bg) in enumerate(zip(priorities, prio_colors, prio_bgs)):
        if not p: continue
        py = pdf.get_y()
        pdf.set_fill_color(*bg)
        pdf.rect(16, py, 178, 16, "F")
        # Number badge
        pdf.set_fill_color(*col)
        pdf.rect(16, py, 14, 16, "F")
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*WHITE)
        pdf.set_xy(16, py + 4)
        pdf.cell(14, 8, str(i+1), align="C")
        # Content
        pdf.set_xy(34, py + 2)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*NAVY)
        pdf.cell(0, 5, safe(p.get("title", "")), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_x(34)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*MGRAY)
        pdf.multi_cell(156, 4, safe(p.get("text", "")), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)
    pdf.ln(2)

    # CTA Box
    cta_y = pdf.get_y()
    if cta_y > 240:
        pdf.add_page()
        cta_y = pdf.get_y()
    pdf.set_fill_color(*NAVY)
    pdf.rect(16, cta_y, 178, 26, "F")
    pdf.set_fill_color(*ORANGE)
    pdf.rect(16, cta_y + 23, 178, 3, "F")
    pdf.set_xy(24, cta_y + 4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*ORANGE)
    pdf.cell(0, 7, safe(f"Empfehlung: {analysis.get('pkg','Guided Remediation')}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(24)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(180, 200, 230)
    pdf.cell(0, 5, "Kostenloses 30-min Erstgespraech: azajic@sw-tech.net", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(12)

    # ---- PAGE 2: DETAILED Q&A ------------------------------------
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 10, "Detaillierter Fragebogen", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    for dim, dim_label in DIM_LABELS.items():
        dim_col = DIM_COLORS.get(dim, BLUE)
        dim_qs  = [q for q in QUESTIONS if q["dim"] == dim]

        # Dimension header - colored
        dh_y = pdf.get_y()
        pdf.set_fill_color(*dim_col)
        pdf.rect(16, dh_y, 178, 10, "F")
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*WHITE)
        pdf.set_xy(20, dh_y + 1)
        pdf.cell(0, 8, dim_label.upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)

        for q in dim_qs:
            ans   = answers.get(q["id"], "-")
            # Handle special chars in answer
            ans_clean = ans.replace("Weiß nicht", "Weiss nicht")
            sc_val = ANSWER_SCORES.get(ans, ANSWER_SCORES.get(ans_clean, 0))
            col   = GREEN if sc_val == 100 else (YELLOW if sc_val == 50 else RED)
            bg    = (236,253,245) if sc_val == 100 else ((255,251,235) if sc_val == 50 else (254,242,242))

            if pdf.get_y() > 258: pdf.add_page()

            row_y = pdf.get_y()
            # Background
            pdf.set_fill_color(*bg)
            pdf.rect(16, row_y, 178, 20, "F")
            # Left color bar
            pdf.set_fill_color(*col)
            pdf.rect(16, row_y, 4, 20, "F")
            # Question ID + Label
            pdf.set_xy(22, row_y + 2)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*NAVY)
            pdf.cell(100, 4, safe(f"{q['id']} - {q['label']}"))
            # Answer badge
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*col)
            pdf.set_x(140)
            pdf.cell(50, 4, safe(f"{ans}  ({sc_val}%)"), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            # Question text
            pdf.set_x(22)
            pdf.set_font("Helvetica", "", 7.5)
            pdf.set_text_color(*MGRAY)
            pdf.multi_cell(170, 4, safe(q["q"]), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            if sc_val < 100:
                pdf.set_x(22)
                pdf.set_font("Helvetica", "I", 7)
                pdf.set_text_color(71, 85, 105)
                pdf.multi_cell(170, 3.5, safe(f">> {q['fix']}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(3)
        pdf.ln(3)

    # ---- PAGE 3: METHOD + CTA ------------------------------------
    pdf.add_page()
    pdf.colored_section_header("Methodik & Bewertungslogik", MGRAY)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*NAVY)
    pdf.multi_cell(0, 5, "Ja = 100 Pkt | Teilweise = 50 Pkt | Nein/Weiss nicht = 0 Pkt. Die vier Dimensionen werden jeweils als gewichteter Durchschnitt berechnet und dann mit branchenspezifischen Gewichten zum Gesamtscore aggregiert. Ampel-Schwellenwerte: Gruen >= 80 | Gelb 60-79 | Rot < 60. High-Trigger-Fragen mit 0 Punkten setzen den Sales-Flag.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*MGRAY)
    pdf.cell(0, 5, safe(f"Assessment: {datetime.now().strftime('%d.%m.%Y %H:%M')} UTC  |  {lead['company']}  |  {lead['email']}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)

    # Package recommendation
    pkg_name = safe(analysis.get("pkg", "Guided Remediation"))
    pdf.colored_section_header("Paketempfehlung", ORANGE)
    pr_y = pdf.get_y()
    pdf.set_fill_color(255, 247, 237)
    pdf.set_fill_color(*ORANGE)
    pdf.rect(16, pr_y, 178, 8, "F")
    pdf.set_fill_color(255, 247, 237)
    pdf.rect(16, pr_y + 8, 178, 25, "F")
    pdf.set_xy(20, pr_y + 1)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 6, pkg_name)
    pdf.set_xy(20, pr_y + 10)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*NAVY)
    pdf.multi_cell(170, 5, safe(analysis.get("pkgWhy", "")), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)

    # Final CTA
    fta_y = pdf.get_y()
    pdf.set_fill_color(*NAVY)
    pdf.rect(16, fta_y, 178, 32, "F")
    pdf.set_fill_color(*ORANGE)
    pdf.rect(16, fta_y + 29, 178, 3, "F")
    pdf.set_xy(24, fta_y + 5)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 8, "Kostenloses 30-min Erstgespraech buchen", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(24)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*ORANGE)
    pdf.cell(0, 6, "azajic@sw-tech.net", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(24)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(150, 170, 210)
    pdf.cell(0, 6, "YNHALD - Supplier Risk Management as a Service")

    return bytes(pdf.output())
