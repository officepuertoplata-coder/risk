from fpdf import FPDF, XPos, YPos
from datetime import datetime
from typing import Dict, Any

# --- Brand Colors (RGB) ----------------------------------------
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

DIM_LABELS = {
    "legal":       "Rechtliche Absicherung",
    "cyber":       "IT-Sicherheit & Datenschutz",
    "operational": "Operative Risiken",
    "financial":   "Finanzielle Stabilitaet",
}

SCORE_COLORS = {
    "green":  GREEN,
    "yellow": YELLOW,
    "red":    RED,
}

SCORE_LABELS = {
    "green":  "GUT GESICHERT",
    "yellow": "HANDLUNGSBEDARF",
    "red":    "KRITISCHES RISIKO",
}

ANSWER_SCORES = {"Ja": 100, "Teilweise": 50, "Nein": 0, "Weiss nicht": 0}

QUESTIONS = [
    {"id": "Q1.1", "dim": "legal",       "label": "Versicherungsnachweis",
     "q": "Liegt eine aktuelle Kopie der Haftpflicht-/Cyber-Versicherung vor?",
     "fix": "Verlange jaehrlich eine aktuelle Versicherungsbestaetigung."},
    {"id": "Q1.2", "dim": "legal",       "label": "Right-to-Audit",
     "q": "Enthaelt der Vertrag Right-to-Audit-Klauseln?",
     "fix": "Fuege Right-to-Audit-Klauseln bei der naechsten Verlaengerung ein."},
    {"id": "Q1.3", "dim": "legal",       "label": "72h-Meldepflicht",
     "q": "Ist eine 72h-Meldepflicht fuer Vorfaelle vertraglich geregelt?",
     "fix": "Verankere eine 72h-Meldepflicht; bei laufenden Vertraegen als Addendum."},
    {"id": "Q1.4", "dim": "legal",       "label": "UBO/PEP-Check",
     "q": "Wurden UBO und Key-Management inkl. Sanktions-/PEP-Check geprueft?",
     "fix": "Nutze KYB-Dienste fuer jaehrliche UBO/PEP-Screenings."},
    {"id": "Q1.5", "dim": "legal",       "label": "Jaehrl. Rezertifizierung",
     "q": "Fuehrst du mindestens jaehrlich eine Vertrags-Rezertifizierung durch?",
     "fix": "Etabliere einen jaehrlichen Rezertifizierungskalender."},
    {"id": "Q2.1", "dim": "cyber",       "label": "Datenspeicherort",
     "q": "Weisst du, in welchem Land/Rechenzentrum die Daten liegen?",
     "fix": "Fordere schriftliche Bestaetigung und verankere ihn in der DPA."},
    {"id": "Q2.2", "dim": "cyber",       "label": "Externe Pruefberichte",
     "q": "Legt der Lieferant aktuelle SOC2/ISO27001/PenTest-Berichte vor?",
     "fix": "Verlange SOC2 Typ II oder ISO 27001 als Onboarding-Voraussetzung."},
    {"id": "Q2.3", "dim": "cyber",       "label": "Datenverschluesselung",
     "q": "Werden sensible Daten standardmaessig verschluesselt (at-rest/in-transit)?",
     "fix": "Verlange schriftliche Bestaetigung der Verschluesselungsstandards."},
    {"id": "Q2.4", "dim": "cyber",       "label": "Incident-Monitoring",
     "q": "Gibt es einen automatisierten Alert-Prozess bei Sicherheitsvorfaellen?",
     "fix": "Abonniere Threat-Intelligence-Feeds (SecurityScorecard, BitSight)."},
    {"id": "Q2.5", "dim": "cyber",       "label": "Vendor-Onboarding-Routine",
     "q": "Gibt es ein dokumentiertes jaehrliches Vendor-Onboarding?",
     "fix": "Implementiere ein standardisiertes Assessment-Framework."},
    {"id": "Q3.1", "dim": "operational", "label": "BC/DR-Plan",
     "q": "Existiert ein getesteter BC/DR-Plan inkl. Sub-Tier-Ausfaelle?",
     "fix": "Verlange jaehrliche BC/DR-Testnachweise inklusive Sub-Tier-Abdeckung."},
    {"id": "Q3.2", "dim": "operational", "label": "Sub-Tier-Transparenz",
     "q": "Kennst du die wichtigsten Sub-Tier-Lieferanten?",
     "fix": "Erstelle ein Tier-2/3-Lieferanten-Mapping fuer kritische Komponenten."},
    {"id": "Q3.3", "dim": "operational", "label": "Zweite Bezugsquelle",
     "q": "Existiert mindestens eine validierte Zweitquelle fuer Schluesselkomponenten?",
     "fix": "Qualifiziere eine alternative Quelle fuer alle kritischen Teile."},
    {"id": "Q3.4", "dim": "operational", "label": "Lieferueberwachung",
     "q": "Werden Lieferzeiten/Kapazitaeten/Bestaende regelmaessig ueberwacht?",
     "fix": "Implementiere KPI-Dashboards mit automatischen Alerts."},
    {"id": "Q3.5", "dim": "operational", "label": "Vor-Ort-Audit",
     "q": "Findet jaehrlich ein Vor-Ort- oder Remote-Audit statt?",
     "fix": "Plane jaehrliche Audits fuer Tier-1-Lieferanten."},
    {"id": "Q4.1", "dim": "financial",   "label": "Finanzmonitoring",
     "q": "Erhaeltst du automatisierte Bonitaets-Alerts zum Lieferanten?",
     "fix": "Nutze Creditsafe oder D&B fuer automatisierte Bonitaets-Alerts."},
    {"id": "Q4.2", "dim": "financial",   "label": "Finanzsicherheiten",
     "q": "Verlangst du Mindest-Liquiditaetskennzahlen oder Parent-Guarantees?",
     "fix": "Verankere Mindest-Finanzkennzahlen bei strategischen Lieferanten."},
    {"id": "Q4.3", "dim": "financial",   "label": "Jahresabschluss-Pruefung",
     "q": "Pruefst du jaehrlich gepruefte Bilanzen/GuV?",
     "fix": "Fordere testierte Jahresabschluesse als Standard."},
    {"id": "Q4.4", "dim": "financial",   "label": "Concentration-Risk",
     "q": "Limitiert ihr Ausgaben pro Lieferant und trackt ihr Concentration-Risk?",
     "fix": "Fuehre Spend-Analysen durch und setze Obergrenzen."},
    {"id": "Q4.5", "dim": "financial",   "label": "Business-Interruption",
     "q": "Hat der Lieferant eine BII mit Drittschadendeckung?",
     "fix": "Verlange BII-Nachweis mit Drittschadendeckung."},
]


def safe(text: str) -> str:
    """Ersetzt Zeichen ausserhalb Latin-1 durch sichere Alternativen."""
    return (
        text.replace("\u2014", "-")   # em dash
            .replace("\u2013", "-")   # en dash
            .replace("\u2019", "'")   # right single quote
            .replace("\u2018", "'")   # left single quote
            .replace("\u201C", '"')   # left double quote
            .replace("\u201D", '"')   # right double quote
            .replace("\u2026", "...") # ellipsis
            .replace("\u00e4", "ae").replace("\u00f6", "oe").replace("\u00fc", "ue")
            .replace("\u00c4", "Ae").replace("\u00d6", "Oe").replace("\u00dc", "Ue")
            .replace("\u00df", "ss")
    )


class YnhaldPDF(FPDF):
    def __init__(self, data: Dict[str, Any]):
        super().__init__()
        self.data = data
        self.set_margins(18, 18, 18)
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        # Navy header bar
        self.set_fill_color(*NAVY)
        self.rect(0, 0, 210, 22, "F")
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*WHITE)
        self.set_xy(18, 6)
        self.cell(80, 10, "YNHALD", new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(180, 200, 230)
        self.cell(60, 10, "Supplier Risk Assessment Report")
        # Date right-aligned
        self.set_font("Helvetica", "", 9)
        self.set_text_color(180, 200, 230)
        self.set_xy(140, 6)
        self.cell(52, 10, datetime.now().strftime("%d.%m.%Y"), align="R")
        self.ln(14)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MGRAY)
        self.cell(0, 8, f"YNHALD Supplier Risk Bot  -  {datetime.now().strftime('%d.%m.%Y')}  -  Vertraulich  -  Seite {self.page_no()}", align="C")

    def section_title(self, title: str, color=BLUE):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*color)
        self.set_fill_color(*LGRAY)
        self.cell(0, 8, title.upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
        self.ln(2)

    def score_bar(self, label: str, value: float, bar_width: float = 100):
        val = int(value)
        color = GREEN if val >= 80 else (YELLOW if val >= 60 else RED)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*NAVY)
        self.cell(55, 7, label)
        # Background bar
        self.set_fill_color(*LGRAY)
        x = self.get_x()
        y = self.get_y() + 1
        self.rect(x, y, bar_width, 5, "F")
        # Value bar
        self.set_fill_color(*color)
        filled = bar_width * val / 100
        if filled > 0:
            self.rect(x, y, filled, 5, "F")
        # Percentage label
        self.set_xy(x + bar_width + 3, self.get_y())
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*color)
        self.cell(12, 7, f"{val}%", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def colored_box(self, text: str, color, bg_color=None):
        if bg_color is None:
            bg_color = tuple(min(255, c + 200) for c in color)
        self.set_fill_color(*bg_color)
        self.set_text_color(*color)
        self.set_font("Helvetica", "B", 8)
        self.cell(0, 6, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True, border="L")
        self.ln(1)


def generate_pdf(data: Dict[str, Any]) -> bytes:
    """
    Generiert den vollstaendigen PDF-Report.
    data enthaelt: lead, industry_label, answers, scores, analysis
    """
    lead      = data["lead"]
    scores    = data["scores"]
    analysis  = data["analysis"]
    answers   = data["answers"]
    ind_label = data.get("industryLabel", "-")

    sc_color  = scores["color"]
    sc_final  = int(scores["final"])
    sc_ds     = scores["ds"]
    sc_col    = SCORE_COLORS.get(sc_color, MGRAY)

    pdf = YnhaldPDF(data)
    pdf.add_page()

    # -- PAGE 1: EXECUTIVE SUMMARY ------------------------------
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 10, "Supplier Risk Assessment", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*MGRAY)
    pdf.cell(0, 7, f"{lead['company']}  -  Lieferant: {lead.get('supplier') or '-'}  -  {datetime.now().strftime('%d.%m.%Y')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)

    # Score Hero Box
    pdf.set_fill_color(*NAVY)
    pdf.rect(18, pdf.get_y(), 174, 38, "F")
    # Score number
    pdf.set_font("Helvetica", "B", 38)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(28, pdf.get_y() + 4)
    pdf.cell(35, 20, str(sc_final))
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(180, 200, 230)
    pdf.set_xy(63, pdf.get_y() + 8)
    pdf.cell(20, 8, "/100")
    # Label
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*sc_col)
    pdf.set_xy(90, pdf.get_y() - 4)
    pdf.cell(90, 10, safe(SCORE_LABELS.get(sc_color, "-")))
    # Branche
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(150, 170, 210)
    pdf.set_xy(90, pdf.get_y() + 8)
    pdf.cell(90, 7, f"Branche: {safe(ind_label)}")
    pdf.ln(34)
    pdf.ln(4)

    # Meta grid
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*MGRAY)
    cols = [("Kontaktperson", safe(lead["name"])), ("Unternehmen", safe(lead["company"])),
            ("Lieferant", safe(lead.get("supplier") or "-")), ("E-Mail", safe(lead["email"]))]
    for i, (lbl, val) in enumerate(cols):
        if i % 2 == 0:
            pdf.set_x(18)
        else:
            pdf.set_x(109)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*MGRAY)
        pdf.cell(87, 5, lbl)
        if i % 2 == 1:
            pdf.ln(0)
        pdf.set_x(18 if i % 2 == 0 else 109)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*NAVY)
        pdf.cell(87, 6, val[:45] if val else "-")
        if i % 2 == 1:
            pdf.ln(3)
    pdf.ln(6)

    # Executive Summary
    pdf.section_title("Executive Summary", BLUE)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*NAVY)
    pdf.multi_cell(0, 5, safe(analysis.get("exec", "")), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # Dimension Scores
    pdf.section_title("Risikodimensionen", BLUE)
    for dim, label in DIM_LABELS.items():
        val = sc_ds.get(dim, 0)
        pdf.score_bar(label, val)
    pdf.ln(4)

    # Business Impact
    pdf.section_title("Geschaeftsauswirkung", RED)
    pdf.set_fill_color(254, 242, 242)
    pdf.set_text_color(*RED)
    pdf.set_font("Helvetica", "B", 8)
    x, y = pdf.get_x(), pdf.get_y()
    pdf.set_fill_color(254, 242, 242)
    pdf.set_draw_color(*RED)
    h_est = 18
    pdf.rect(18, y, 174, h_est, "F")
    pdf.set_line_width(1.2)
    pdf.line(18, y, 18, y + h_est)
    pdf.set_line_width(0.2)
    pdf.set_xy(23, y + 2)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(127, 29, 29)
    pdf.multi_cell(165, 5, safe(analysis.get("impact", "")), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # Priority Actions
    pdf.section_title("Sofortmassnahmen", NAVY)
    priorities = [
        (analysis.get("p1", {}), ORANGE),
        (analysis.get("p2", {}), BLUE),
        (analysis.get("p3", {}), LBLUE),
    ]
    for i, (p, col) in enumerate(priorities):
        if not p:
            continue
        pdf.set_fill_color(*col)
        pdf.set_text_color(*WHITE)
        pdf.set_font("Helvetica", "B", 8)
        px, py = pdf.get_x(), pdf.get_y()
        pdf.rect(px, py, 7, 7, "F")
        pdf.set_xy(px + 1, py + 0.5)
        pdf.cell(5, 6, str(i + 1))
        pdf.set_xy(px + 9, py)
        pdf.set_text_color(*NAVY)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 7, safe(p.get("title", "")), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_x(px + 9)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*MGRAY)
        pdf.multi_cell(163, 4.5, safe(p.get("text", "")), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)
    pdf.ln(2)

    # CTA Box
    pdf.set_fill_color(*NAVY)
    cta_y = pdf.get_y()
    pdf.rect(18, cta_y, 174, 22, "F")
    pdf.set_xy(28, cta_y + 3)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*ORANGE)
    pdf.cell(0, 7, f"Empfehlung: {analysis.get('pkg', 'Guided Remediation')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(28)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(180, 200, 230)
    pdf.cell(0, 6, "Kostenloses 30-min Erstgesprach: azajic@sw-tech.net", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)

    # -- PAGE 2: DETAILED Q&A --------------------------------------
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 10, "Detaillierter Fragebogen", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    for dim, dim_label in DIM_LABELS.items():
        dim_qs = [q for q in QUESTIONS if q["dim"] == dim]
        # Dimension header
        pdf.set_fill_color(*LGRAY)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*NAVY)
        pdf.cell(0, 8, f"  {dim_label}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
        pdf.ln(2)

        for q in dim_qs:
            ans = answers.get(q["id"], "-")
            sc_val = ANSWER_SCORES.get(ans, 0)
            col = GREEN if sc_val == 100 else (YELLOW if sc_val == 50 else RED)

            # Check if we need a page break
            if pdf.get_y() > 255:
                pdf.add_page()

            row_y = pdf.get_y()
            # Left accent bar
            pdf.set_fill_color(*col)
            pdf.rect(18, row_y, 2.5, 18, "F")

            # Content
            pdf.set_xy(23, row_y)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*NAVY)
            pdf.cell(90, 5, f"{q['id']} - {q['label']}")
            # Answer badge
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*col)
            pdf.set_x(23 + 90)
            pdf.cell(40, 5, f"{ans}  ({sc_val}%)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.set_x(23)
            pdf.set_font("Helvetica", "", 7.5)
            pdf.set_text_color(*MGRAY)
            pdf.multi_cell(169, 4, safe(q["q"]), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            if sc_val < 100:
                pdf.set_x(23)
                pdf.set_font("Helvetica", "I", 7.5)
                pdf.set_text_color(71, 85, 105)
                pdf.multi_cell(169, 4, f">> {q['fix']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.ln(3)
        pdf.ln(2)

    # -- PAGE 3: METHODIK & KONTAKT --------------------------------
    pdf.add_page()
    pdf.section_title("Methodik & Audit-Trail", MGRAY)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*NAVY)
    method_text = (
        "Bewertungslogik: Ja = 100 Pkt | Teilweise = 50 Pkt | Nein/Weiss nicht = 0 Pkt. "
        "Die Dimensionen Rechtliche Absicherung, IT-Sicherheit & Datenschutz, Operative Risiken "
        "und Finanzielle Stabilitaet werden jeweils als gewichteter Durchschnitt der Fragewerte berechnet. "
        "Der Gesamtscore ergibt sich aus der branchenspezifischen Gewichtung der vier Dimensionen. "
        "Ampel-Schwellenwerte: Gruen - 80 | Gelb 60-79 | Rot < 60. "
        "High-Trigger-Fragen mit Score 0 setzen automatisch den Sales-Flag."
    )
    pdf.multi_cell(0, 5, method_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # Timestamp
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*MGRAY)
    pdf.cell(0, 6, f"Assessment erstellt: {datetime.now().strftime('%d.%m.%Y %H:%M:%S UTC')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6, f"Unternehmen: {lead['company']}  |  E-Mail: {lead['email']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)

    # Package recommendation
    pdf.section_title("Paketempfehlung & naechste Schritte", BLUE)
    pkg_texts = {
        "Guided Remediation": (
            "Das Guided-Remediation-Paket eignet sich fuer Unternehmen, die einen klaren Fahrplan "
            "benoetigen, die Umsetzung aber intern steuern moechten. YNHALD liefert priorisierte "
            "Handlungsempfehlungen, Vertragsvorlagen und begleitet monatliche Review-Calls."
        ),
        "Managed Remediation": (
            "Das Managed-Remediation-Paket ist fuer Unternehmen mit kritischem Risikoniveau gedacht. "
            "YNHALD uebernimmt die aktive Steuerung der Remediation: Lieferanten-Kommunikation, "
            "Nachweis-Einholung, Monitoring-Aufbau und laufendes Reporting."
        ),
    }
    pkg_name = safe(analysis.get("pkg", "Guided Remediation"))
    pkg_desc = pkg_texts.get(pkg_name, "")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*ORANGE)
    pdf.cell(0, 7, pkg_name, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*NAVY)
    pdf.multi_cell(0, 5, pkg_desc, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*MGRAY)
    reason = safe(analysis.get("pkgWhy", ""))
    if reason:
        pdf.multi_cell(0, 5, reason, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)

    # Final CTA
    pdf.set_fill_color(*NAVY)
    pdf.rect(18, pdf.get_y(), 174, 32, "F")
    pdf.set_xy(28, pdf.get_y() + 5)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 8, "Kostenloses 30-min Erstgespraech buchen", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(28)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*ORANGE)
    pdf.cell(0, 6, "azajic@sw-tech.net", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(28)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(150, 170, 210)
    pdf.cell(0, 6, "www.ynhald.com  -  YNHALD GmbH")

    return bytes(pdf.output())
