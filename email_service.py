# -*- coding: utf-8 -*-
import os
import base64
import httpx
from typing import Optional

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL     = os.getenv("FROM_EMAIL", "onboarding@resend.dev")
FROM_NAME      = os.getenv("FROM_NAME", "YNHALD Supplier Risk")
ALERT_EMAIL    = os.getenv("ALERT_EMAIL", "azajic@sw-tech.net")

# Software Technologies Links
CAL_URL      = "https://cal.com/alexander-zajic/riskmanagement"
WHATSAPP_URL = "https://wa.me/4367764118066?text=Anfrage-YLB9"
WEBSITE_URL  = "https://sw-tech.net"

SCORE_LABELS = {"green": "Gut gesichert", "yellow": "Handlungsbedarf", "red": "Kritisches Risiko"}


def _send(to: str, subject: str, html: str, pdf_bytes: Optional[bytes] = None,
          pdf_name: str = "Report.pdf") -> bool:
    """Sendet eine E-Mail via Resend REST API (optional mit PDF-Anhang)."""
    if not RESEND_API_KEY:
        print(f"[EMAIL] Kein API-Key - wuerde senden an {to}: {subject}")
        return True

    payload: dict = {
        "from":    f"{FROM_NAME} <{FROM_EMAIL}>",
        "to":      [to],
        "subject": subject,
        "html":    html,
    }
    if pdf_bytes:
        payload["attachments"] = [{
            "filename":     pdf_name,
            "content":      base64.b64encode(pdf_bytes).decode("utf-8"),
            "content_type": "application/pdf",
        }]

    try:
        r = httpx.post(
            "https://api.resend.com/emails",
            json=payload,
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            timeout=20,
        )
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False


# ==============================================================
#  BESTEHEND: Risikobewertung
# ==============================================================

def send_lead_email(lead: dict, scores: dict, analysis: dict, pdf_bytes: bytes) -> bool:
    name      = lead.get("name", "")
    company   = lead.get("company", "")
    final     = int(scores.get("final", 0))
    color     = scores.get("color", "red")
    score_lbl = SCORE_LABELS.get(color, "")
    pkg       = analysis.get("pkg", "Guided Remediation")
    num_color = '#059669' if color == 'green' else '#D97706' if color == 'yellow' else '#DC2626'
    exec_txt  = analysis.get('exec', '')
    pkg_why   = analysis.get('pkgWhy', '')

    html = f"""
<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"><style>
  body {{ font-family: -apple-system, system-ui, sans-serif; color: #0A1940; margin: 0; padding: 0; background: #f4f6fb; }}
  .wrap {{ max-width: 600px; margin: 0 auto; background: #fff; }}
  .header {{ background: #0A1940; padding: 28px 32px; }}
  .header h1 {{ color: #fff; margin: 0; font-size: 22px; }}
  .header p {{ color: #93C5FD; margin: 4px 0 0; font-size: 13px; }}
  .score-box {{ background: #0A1940; margin: 0; padding: 24px 32px; text-align: center; }}
  .score-num {{ font-size: 64px; font-weight: 900; color: {num_color}; line-height: 1; }}
  .score-label {{ font-size: 15px; color: #CBD5E1; margin-top: 4px; }}
  .body {{ padding: 28px 32px; }}
  .section {{ margin-bottom: 24px; }}
  .section-title {{ font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: #1E3FA0; margin-bottom: 8px; }}
  .text {{ font-size: 14px; line-height: 1.6; color: #475569; }}
  .cta-box {{ background: #FFF7ED; border: 1px solid #E8960C; border-radius: 8px; padding: 20px; text-align: center; margin: 24px 0; }}
  .cta-title {{ font-size: 16px; font-weight: 700; color: #0A1940; margin-bottom: 8px; }}
  .cta-btn {{ display: inline-block; background: #E8960C; color: #fff; padding: 12px 28px; border-radius: 8px; font-weight: 700; text-decoration: none; font-size: 15px; }}
  .footer {{ background: #F8FAFC; padding: 20px 32px; text-align: center; font-size: 12px; color: #94A3B8; }}
</style></head>
<body>
<div class="wrap">
  <div class="header">
    <h1>YNHALD Supplier Risk</h1>
    <p>Ihr Assessment-Report ist bereit</p>
  </div>
  <div class="score-box">
    <div class="score-num">{final}</div>
    <div class="score-label">/100 Punkte &nbsp;&middot;&nbsp; {score_lbl}</div>
  </div>
  <div class="body">
    <p>Guten Tag {name},</p>
    <p class="text">vielen Dank fuer die Teilnahme am YNHALD Supplier Risk Check. Anbei Ihr vollstaendiger PDF-Report fuer <strong>{company}</strong>.</p>
    <div class="section"><div class="section-title">Executive Summary</div><p class="text">{exec_txt}</p></div>
    <div class="section"><div class="section-title">Empfohlenes Paket</div><p class="text"><strong>{pkg}</strong> &mdash; {pkg_why}</p></div>
    <div class="cta-box">
      <div class="cta-title">Kostenloses 30-min Erstgespraech buchen</div>
      <a href="{CAL_URL}" class="cta-btn">Termin buchen</a>
    </div>
    <p class="text">Mit freundlichen Gruessen,<br><strong>Das YNHALD Team</strong></p>
  </div>
  <div class="footer">YNHALD &middot; azajic@sw-tech.net &middot; Vertraulich</div>
</div>
</body></html>
"""
    return _send(lead["email"], f"Ihr YNHALD Supplier Risk Report - Score: {final}/100",
                 html, pdf_bytes=pdf_bytes, pdf_name="YNHALD_Supplier_Risk_Report.pdf")


def send_sales_alert(lead: dict, scores: dict, analysis: dict, assessment_id: str) -> bool:
    name    = lead.get("name", "")
    company = lead.get("company", "")
    supplier= lead.get("supplier", "-")
    email   = lead.get("email", "")
    phone   = lead.get("phone", "-")
    final   = int(scores.get("final", 0))
    color   = scores.get("color", "red")
    pkg     = analysis.get("pkg", "-")
    score_lbl = SCORE_LABELS.get(color, "")
    flag_col  = '#DC2626' if color == 'red' else '#D97706'
    exec_txt  = analysis.get('exec', '')

    html = f"""
<!DOCTYPE html>
<html lang="de"><head><meta charset="UTF-8"></head>
<body style="font-family:-apple-system,system-ui,sans-serif;background:#f4f6fb;margin:0">
<div style="max-width:580px;margin:0 auto;background:#fff">
  <div style="background:{flag_col};padding:20px 28px"><h1 style="color:#fff;margin:0;font-size:18px">Neuer Lead - {score_lbl}</h1></div>
  <div style="padding:24px 28px">
    <div style="font-size:48px;font-weight:900;color:{flag_col}">{final}<span style="font-size:16px;font-weight:400;color:#94A3B8">/100</span></div>
    <p style="margin:4px 0 20px;color:#64748B;font-size:13px">Assessment-ID: {assessment_id}</p>
    <table style="border-collapse:collapse;width:100%;font-size:13px">
      <tr><td style="padding:6px 0;color:#64748B;width:130px">Name</td><td style="padding:6px 0;font-weight:600">{name}</td></tr>
      <tr><td style="padding:6px 0;color:#64748B">Unternehmen</td><td style="padding:6px 0;font-weight:600">{company}</td></tr>
      <tr><td style="padding:6px 0;color:#64748B">Lieferant</td><td style="padding:6px 0;font-weight:600">{supplier}</td></tr>
      <tr><td style="padding:6px 0;color:#64748B">E-Mail</td><td style="padding:6px 0;font-weight:600"><a href="mailto:{email}">{email}</a></td></tr>
      <tr><td style="padding:6px 0;color:#64748B">Telefon</td><td style="padding:6px 0;font-weight:600">{phone}</td></tr>
      <tr><td style="padding:6px 0;color:#64748B">Paket</td><td style="padding:6px 0;font-weight:600;color:#E8960C">{pkg}</td></tr>
    </table>
    <p style="font-size:13px;color:#475569;line-height:1.5;margin-top:14px">{exec_txt}</p>
  </div>
</div>
</body></html>
"""
    return _send(ALERT_EMAIL, f"[YNHALD Lead] {company} - Score {final}/100 - {score_lbl}", html)


# ==============================================================
#  KRITIKALITAET (Software Technologies Design)
# ==============================================================

ST_BG    = "#ffffff"   # heller Hintergrund
ST_PANEL = "#f5f8fc"   # sehr helles Panel
ST_LINE  = "#e2e8f0"   # helle Trennlinien
ST_INK   = "#0f1e33"   # dunkler Text (Haupttext)
ST_SOFT  = "#475569"   # gedaempfter Text
ST_DIM   = "#94a3b8"   # sehr heller Text (Fusszeilen)
ST_CYAN  = "#0fb5a6"   # kraeftigeres Cyan (auf Weiss besser lesbar)
GRADE_COLORS = {"A": "#e0483f", "B": "#d9931a", "C": "#2f7fd6", "D": "#1f9e6e"}


def _btn(href, label, bg=ST_CYAN, color="#ffffff"):
    return (f'<a href="{href}" target="_blank" '
            f'style="display:inline-block;background:{bg};color:{color};'
            f'padding:12px 22px;border-radius:8px;font-weight:700;text-decoration:none;'
            f'font-size:14px;margin:4px 6px">{label}</a>')


def _supplier_block_email(s: dict) -> str:
    grade = s.get("grade", "-")
    gcol  = GRADE_COLORS.get(grade, ST_CYAN)
    rec   = s.get("recommendation", {})
    name  = s.get("name", "-")
    url   = s.get("url", "")
    plz   = s.get("plz", "")
    gname = s.get("gradeName", "")
    meta  = " &middot; ".join([x for x in [url, plz] if x])
    meta_html = (" &middot; " + meta) if meta else ""
    tiefe = rec.get("tiefe", "")
    reass = rec.get("reass", "")
    mon   = rec.get("monitoring", "")
    frei  = rec.get("freigabe", "")

    return f"""
    <div style="border:1px solid {ST_LINE};border-radius:12px;margin-bottom:16px;overflow:hidden;background:{ST_PANEL}">
      <div style="padding:16px 18px;border-bottom:1px solid {ST_LINE}">
        <table style="border-collapse:collapse"><tr>
          <td style="width:40px;vertical-align:middle"><div style="width:40px;height:40px;border-radius:8px;background:{gcol};color:#fff;font-weight:900;font-size:19px;text-align:center;line-height:40px">{grade}</div></td>
          <td style="padding-left:12px;vertical-align:middle">
            <div style="font-weight:700;font-size:15px;color:{ST_INK}">{name}</div>
            <div style="font-size:12px;color:{ST_DIM};font-family:'Courier New',monospace">Stufe {grade} &middot; {gname}{meta_html}</div>
          </td>
        </tr></table>
      </div>
      <table style="width:100%;border-collapse:collapse;font-size:13px">
        <tr><td style="padding:9px 18px;color:{ST_SOFT};width:150px;border-bottom:1px solid {ST_LINE}">Pr&uuml;ftiefe</td><td style="padding:9px 18px;color:{ST_INK};border-bottom:1px solid {ST_LINE}">{tiefe}</td></tr>
        <tr><td style="padding:9px 18px;color:{ST_SOFT};border-bottom:1px solid {ST_LINE}">Re-Assessment</td><td style="padding:9px 18px;color:{ST_INK};border-bottom:1px solid {ST_LINE}">{reass}</td></tr>
        <tr><td style="padding:9px 18px;color:{ST_SOFT};border-bottom:1px solid {ST_LINE}">Monitoring</td><td style="padding:9px 18px;color:{ST_INK};border-bottom:1px solid {ST_LINE}">{mon}</td></tr>
        <tr><td style="padding:9px 18px;color:{ST_SOFT}">Freigabe</td><td style="padding:9px 18px;color:{ST_INK}">{frei}</td></tr>
      </table>
    </div>"""


def send_criticality_lead_email(lead: dict, suppliers: list, summary: str = "",
                                pdf_bytes: Optional[bytes] = None) -> bool:
    """Kritikalitaets-Report an den Kunden - SW-Tech-Design, mit Buttons + PDF."""
    name = lead.get("name", "")
    first = name.split(" ")[0] if name else ""
    n    = len(suppliers)
    plural = "en" if n != 1 else ""
    blocks = "".join(_supplier_block_email(s) for s in suppliers)

    summary_html = ""
    if summary:
        summary_html = f"""
      <div style="background:rgba(15,181,166,0.08);border:1px solid {ST_LINE};border-radius:10px;padding:16px 18px;margin-bottom:22px">
        <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:{ST_CYAN};margin-bottom:6px;font-family:'Courier New',monospace">Gesamteinsch&auml;tzung</div>
        <p style="font-size:14px;line-height:1.6;color:{ST_INK};margin:0">{summary}</p>
      </div>"""

    buttons = f"""
      <div style="text-align:center;margin:8px 0 4px">
        {_btn(CAL_URL, "Beratungsgespr&auml;ch buchen")}
        {_btn(WHATSAPP_URL, "Per WhatsApp chatten", bg="#25D366", color="#04140f")}
      </div>"""

    html = f"""
<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"></head>
<body style="font-family:-apple-system,system-ui,'Segoe UI',sans-serif;background:{ST_BG};margin:0;padding:0">
<div style="max-width:640px;margin:0 auto;background:{ST_BG}">

  <div style="padding:30px 32px 22px 32px;border-bottom:1px solid {ST_LINE}">
    <div style="font-size:19px;font-weight:700;color:{ST_INK};letter-spacing:-.01em">Software<span style="color:{ST_CYAN}">&middot;</span>Technologies</div>
    <div style="font-size:11px;color:{ST_DIM};font-family:'Courier New',monospace;letter-spacing:.05em;margin-top:2px">SSOT &middot; Lieferanten-Kritikalit&auml;t</div>
  </div>

  <div style="padding:28px 32px">
    <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.14em;color:{ST_CYAN};font-family:'Courier New',monospace;margin-bottom:10px">Kritikalit&auml;ts-Report</div>
    <h1 style="font-size:23px;color:{ST_INK};margin:0 0 14px 0;font-weight:700">Ihre Einstufung &uuml;ber {n} Lieferant{plural}</h1>
    <p style="font-size:14px;line-height:1.6;color:{ST_SOFT};margin:0 0 22px 0">
      Guten Tag {first}, vielen Dank f&uuml;r Ihre Einstufung. Nachfolgend finden Sie f&uuml;r jeden Lieferanten die Kritikalit&auml;tsstufe A&ndash;D und die daraus abgeleitete Empfehlung f&uuml;r Ihr Risikomanagement. Den vollst&auml;ndigen Report finden Sie zus&auml;tzlich im PDF-Anhang.
    </p>

    {summary_html}
    {blocks}

    <div style="border:1px solid {ST_LINE};border-radius:12px;padding:22px;margin-top:24px;text-align:center;background:{ST_PANEL}">
      <div style="font-size:15px;font-weight:700;color:{ST_INK};margin-bottom:4px">N&auml;chster Schritt: das vollst&auml;ndige Assessment</div>
      <p style="font-size:13px;color:{ST_SOFT};margin:0 0 14px 0">Wir erstellen f&uuml;r Ihre kritischen Lieferanten das detaillierte, quellenbasierte Assessment (OSINT, Fragenkatalog, Expertenbewertung).</p>
      {buttons}
    </div>

    <p style="font-size:13px;line-height:1.6;color:{ST_SOFT};margin-top:24px">Mit freundlichen Gr&uuml;&szlig;en,<br><strong style="color:{ST_INK}">Ihr Software-Technologies-Team</strong></p>
  </div>

  <div style="padding:20px 32px;border-top:1px solid {ST_LINE};text-align:center">
    <div style="font-size:11px;color:{ST_DIM};font-family:'Courier New',monospace;line-height:1.7">
      <a href="{WEBSITE_URL}" style="color:{ST_CYAN};text-decoration:none">sw-tech.net</a> &middot;
      <a href="mailto:office@sw-tech.net" style="color:{ST_SOFT};text-decoration:none">office@sw-tech.net</a><br>
      Software Technologies-Development-Service GesmbH &middot; Wien &middot; powered by Ynhald
    </div>
  </div>

</div>
</body></html>
"""
    return _send(lead["email"], f"Ihr Kritikalit\u00e4ts-Report - {n} Lieferant{plural}",
                 html, pdf_bytes=pdf_bytes, pdf_name="Kritikalitaets-Report.pdf")


def send_criticality_alert(lead: dict, suppliers: list, crit_id: str, summary: str = "",
                           pdf_bytes=None) -> bool:
    """Kompakter interner Alert - nur Uebersicht. Details im angehaengten PDF."""
    name    = lead.get("name", "")
    company = lead.get("company", "")
    email   = lead.get("email", "")
    phone   = lead.get("phone", "-")
    n       = len(suppliers)
    plural  = "en" if n != 1 else ""

    rows = ""
    for s in suppliers:
        gcol = GRADE_COLORS.get(s.get("grade"), ST_CYAN)
        imp  = s.get("impact", "")
        lik  = s.get("likelihood", "")
        rows += (
            f'<tr>'
            f'<td style="padding:8px 8px;border-bottom:1px solid {ST_LINE}">'
            f'<span style="display:inline-block;width:24px;height:24px;border-radius:6px;background:{gcol};color:#fff;font-weight:700;font-size:12px;text-align:center;line-height:24px">{s.get("grade","")}</span></td>'
            f'<td style="padding:8px 8px;border-bottom:1px solid {ST_LINE};font-weight:600;color:{ST_INK}">{s.get("name","")}</td>'
            f'<td style="padding:8px 8px;border-bottom:1px solid {ST_LINE};color:{ST_SOFT}">{s.get("gradeName","")}</td>'
            f'<td style="padding:8px 8px;border-bottom:1px solid {ST_LINE};color:{ST_DIM};font-family:\'Courier New\',monospace;text-align:right;white-space:nowrap">{imp}/{lik}</td>'
            f'</tr>'
        )

    summary_html = ""
    if summary:
        summary_html = f'<p style="font-size:13px;color:{ST_SOFT};line-height:1.5;margin-top:16px">{summary}</p>'

    html = f"""
<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"></head>
<body style="font-family:-apple-system,system-ui,'Segoe UI',sans-serif;background:{ST_BG};margin:0;padding:0">
<div style="max-width:580px;margin:0 auto;background:{ST_BG}">
  <div style="padding:22px 28px;border-bottom:1px solid {ST_LINE}">
    <div style="font-size:11px;color:{ST_CYAN};font-family:'Courier New',monospace;letter-spacing:.1em;text-transform:uppercase">Neuer Kritikalit&auml;ts-Lead</div>
    <h1 style="color:{ST_INK};margin:6px 0 0 0;font-size:18px">{n} Lieferant{plural} eingestuft</h1>
  </div>
  <div style="padding:24px 28px">
    <p style="margin:0 0 16px;color:{ST_DIM};font-size:12px;font-family:'Courier New',monospace">ID: {crit_id}</p>
    <table style="border-collapse:collapse;width:100%;font-size:13px">
      <tr><td style="padding:7px 0;color:{ST_SOFT};width:130px;border-bottom:1px solid {ST_LINE}">Name</td><td style="padding:7px 0;font-weight:600;color:{ST_INK};border-bottom:1px solid {ST_LINE}">{name}</td></tr>
      <tr><td style="padding:7px 0;color:{ST_SOFT};border-bottom:1px solid {ST_LINE}">Unternehmen</td><td style="padding:7px 0;font-weight:600;color:{ST_INK};border-bottom:1px solid {ST_LINE}">{company}</td></tr>
      <tr><td style="padding:7px 0;color:{ST_SOFT};border-bottom:1px solid {ST_LINE}">E-Mail</td><td style="padding:7px 0;font-weight:600;border-bottom:1px solid {ST_LINE}"><a href="mailto:{email}" style="color:{ST_CYAN};text-decoration:none">{email}</a></td></tr>
      <tr><td style="padding:7px 0;color:{ST_SOFT}">Telefon</td><td style="padding:7px 0;font-weight:600;color:{ST_INK}">{phone}</td></tr>
    </table>

    <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:{ST_SOFT};font-family:'Courier New',monospace;margin:22px 0 8px">Eingestufte Lieferanten <span style="color:{ST_DIM};font-weight:400">(Schaden/Wahrsch.)</span></div>
    <table style="border-collapse:collapse;width:100%;font-size:13px">{rows}</table>
    {summary_html}

    <p style="font-size:12px;color:{ST_DIM};margin-top:20px;padding-top:14px;border-top:1px solid {ST_LINE}">
      &#128206; Die vollst&auml;ndige Detailauswertung (alle Antworten je Lieferant) finden Sie im angeh&auml;ngten PDF.
    </p>
  </div>
  <div style="padding:16px 28px;border-top:1px solid {ST_LINE};text-align:center;font-size:11px;color:{ST_DIM};font-family:'Courier New',monospace">
    Software Technologies &middot; Interner Lead-Alert &middot; Vertraulich
  </div>
</div>
</body></html>
"""
    return _send(ALERT_EMAIL, f"[Kritikalit\u00e4t] {company or name} - {n} Lieferant{plural}",
                 html, pdf_bytes=pdf_bytes, pdf_name="Lead-Detailauswertung.pdf")


# ==============================================================
#  KRITIKALITAET REPORT DOUBLE-OPT-IN
# ==============================================================

def send_criticality_confirm_email(email: str, name: str, n_suppliers: int, confirm_url: str,
                                   with_newsletter: bool = False) -> bool:
    """Bestaetigungsmail (Double-Opt-in) fuer den Kritikalitaets-Report.
    Wenn with_newsletter=True, wird der Newsletter beim selben Klick mitbestaetigt."""
    first = name.split(" ")[0] if name else ""
    plural = "en" if n_suppliers != 1 else ""
    nl_note = ""
    if with_newsletter:
        nl_note = f"""
    <div style="background:rgba(15,181,166,0.08);border:1px solid {ST_LINE};border-radius:10px;padding:14px 16px;margin:0 0 22px 0">
      <p style="font-size:13px;line-height:1.6;color:{ST_SOFT};margin:0">
        Mit diesem Klick best&auml;tigen Sie zugleich Ihre Anmeldung zu unseren Updates rund um Supplier Risk Management (NIS2, LkSG, MoCRA). Jederzeit abbestellbar.
      </p>
    </div>"""
    html = f"""
<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"></head>
<body style="font-family:-apple-system,system-ui,'Segoe UI',sans-serif;background:{ST_BG};margin:0;padding:0">
<div style="max-width:560px;margin:0 auto;background:{ST_BG}">
  <div style="padding:30px 32px 22px 32px;border-bottom:1px solid {ST_LINE}">
    <div style="font-size:19px;font-weight:700;color:{ST_INK};letter-spacing:-.01em">Software<span style="color:{ST_CYAN}">&middot;</span>Technologies</div>
    <div style="font-size:11px;color:{ST_DIM};font-family:'Courier New',monospace;letter-spacing:.05em;margin-top:2px">SSOT &middot; Lieferanten-Kritikalit&auml;t</div>
  </div>
  <div style="padding:28px 32px">
    <h1 style="font-size:21px;color:{ST_INK};margin:0 0 14px 0;font-weight:700">Nur noch ein Klick zu Ihrem Report</h1>
    <p style="font-size:14px;line-height:1.6;color:{ST_SOFT};margin:0 0 22px 0">
      Guten Tag {first}, Sie haben einen Kritikalit&auml;ts-Report &uuml;ber {n_suppliers} Lieferant{plural} angefordert. Bitte best&auml;tigen Sie kurz, dass diese Anfrage von Ihnen stammt &ndash; danach senden wir Ihnen den vollst&auml;ndigen Report inklusive PDF sofort zu.
    </p>
    {nl_note}
    <div style="text-align:center;margin:26px 0">
      <a href="{confirm_url}" target="_blank" style="display:inline-block;background:{ST_CYAN};color:#ffffff;padding:14px 30px;border-radius:8px;font-weight:700;text-decoration:none;font-size:15px">Report jetzt anfordern</a>
    </div>
    <p style="font-size:12px;line-height:1.6;color:{ST_DIM};margin:22px 0 0 0">
      Falls der Button nicht funktioniert, kopieren Sie diesen Link in Ihren Browser:<br>
      <a href="{confirm_url}" style="color:{ST_CYAN};text-decoration:none;word-break:break-all">{confirm_url}</a>
    </p>
    <p style="font-size:12px;line-height:1.6;color:{ST_DIM};margin:18px 0 0 0">
      Wenn Sie diese Anfrage nicht gestellt haben, ignorieren Sie diese E-Mail einfach &ndash; es wird dann kein Report versendet.
    </p>
  </div>
  <div style="padding:20px 32px;border-top:1px solid {ST_LINE};text-align:center">
    <div style="font-size:11px;color:{ST_DIM};font-family:'Courier New',monospace;line-height:1.7">
      <a href="{WEBSITE_URL}" style="color:{ST_CYAN};text-decoration:none">sw-tech.net</a> &middot;
      <a href="mailto:office@sw-tech.net" style="color:{ST_SOFT};text-decoration:none">office@sw-tech.net</a><br>
      Software Technologies-Development-Service GesmbH &middot; Wien
    </div>
  </div>
</div>
</body></html>
"""
    return _send(email, "Bitte best\u00e4tigen Sie Ihre Report-Anfrage", html)


def criticality_confirmed_page(email: str = "", n_suppliers: int = 0, already: bool = False) -> str:
    """Seite nach Bestaetigung des Kritikalitaets-Reports."""
    plural = "en" if n_suppliers != 1 else ""
    if already or not email:
        headline = "Link ung&uuml;ltig oder bereits best&auml;tigt"
        text = "Dieser Best&auml;tigungslink ist nicht mehr g&uuml;ltig. M&ouml;glicherweise wurde Ihr Report bereits versendet."
    else:
        headline = "Report ist unterwegs"
        text = f'Vielen Dank! Ihre Anfrage ist best&auml;tigt. Ihr Kritikalit&auml;ts-Report &uuml;ber {n_suppliers} Lieferant{plural} wird jetzt an <strong style="color:{ST_INK}">{email}</strong> gesendet.'
    return f"""<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Report best\u00e4tigt \u2013 Software Technologies</title>
<style>
  body{{font-family:-apple-system,system-ui,'Segoe UI',sans-serif;background:{ST_BG};color:{ST_INK};margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px}}
  .card{{max-width:460px;text-align:center;background:{ST_PANEL};border:1px solid {ST_LINE};border-radius:18px;padding:44px 36px}}
  .brand{{font-size:17px;font-weight:700;margin-bottom:4px}}
  .brand .ac{{color:{ST_CYAN}}}
  .sub{{font-size:11px;color:{ST_DIM};font-family:'Courier New',monospace;letter-spacing:.05em;margin-bottom:28px}}
  .check{{width:76px;height:76px;border-radius:50%;background:rgba(15,181,166,.12);display:flex;align-items:center;justify-content:center;margin:0 auto 22px}}
  .check svg{{width:36px;height:36px;stroke:{ST_CYAN};fill:none;stroke-width:2.5}}
  h1{{font-size:22px;margin:0 0 12px 0}}
  p{{font-size:14px;line-height:1.6;color:{ST_SOFT};margin:0 0 8px 0}}
  .btn{{display:inline-block;margin-top:22px;background:{ST_CYAN};color:#ffffff;padding:12px 26px;border-radius:9px;font-weight:700;text-decoration:none;font-size:14px}}
</style></head>
<body>
  <div class="card">
    <div class="brand">Software<span class="ac">&middot;</span>Technologies</div>
    <div class="sub">SSOT Supplier Risk Management</div>
    <div class="check"><svg viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg></div>
    <h1>{headline}</h1>
    <p>{text}</p>
    <p>Pr&uuml;fen Sie ggf. Ihren Spam-Ordner.</p>
    <a class="btn" href="{WEBSITE_URL}">Zur Website</a>
  </div>
</body></html>"""


# ==============================================================
#  NEWSLETTER DOUBLE-OPT-IN (Software Technologies Design)
# ==============================================================

def send_newsletter_confirm_email(email: str, confirm_url: str) -> bool:
    """Bestaetigungsmail (Double-Opt-in) an einen neuen Newsletter-Abonnenten."""
    html = f"""
<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"></head>
<body style="font-family:-apple-system,system-ui,'Segoe UI',sans-serif;background:{ST_BG};margin:0;padding:0">
<div style="max-width:560px;margin:0 auto;background:{ST_BG}">
  <div style="padding:30px 32px 22px 32px;border-bottom:1px solid {ST_LINE}">
    <div style="font-size:19px;font-weight:700;color:{ST_INK};letter-spacing:-.01em">Software<span style="color:{ST_CYAN}">&middot;</span>Technologies</div>
    <div style="font-size:11px;color:{ST_DIM};font-family:'Courier New',monospace;letter-spacing:.05em;margin-top:2px">Newsletter-Anmeldung best&auml;tigen</div>
  </div>
  <div style="padding:28px 32px">
    <h1 style="font-size:21px;color:{ST_INK};margin:0 0 14px 0;font-weight:700">Nur noch ein Klick</h1>
    <p style="font-size:14px;line-height:1.6;color:{ST_SOFT};margin:0 0 22px 0">
      Bitte best&auml;tigen Sie Ihre Anmeldung zu unseren Updates rund um Supplier Risk Management und regulatorische Neuerungen (NIS2, LkSG, MoCRA). Erst nach Ihrer Best&auml;tigung nehmen wir Sie in den Verteiler auf.
    </p>
    <div style="text-align:center;margin:26px 0">
      <a href="{confirm_url}" target="_blank" style="display:inline-block;background:{ST_CYAN};color:#ffffff;padding:14px 30px;border-radius:8px;font-weight:700;text-decoration:none;font-size:15px">Anmeldung best&auml;tigen</a>
    </div>
    <p style="font-size:12px;line-height:1.6;color:{ST_DIM};margin:22px 0 0 0">
      Falls der Button nicht funktioniert, kopieren Sie diesen Link in Ihren Browser:<br>
      <a href="{confirm_url}" style="color:{ST_CYAN};text-decoration:none;word-break:break-all">{confirm_url}</a>
    </p>
    <p style="font-size:12px;line-height:1.6;color:{ST_DIM};margin:18px 0 0 0">
      Wenn Sie sich nicht angemeldet haben, ignorieren Sie diese E-Mail einfach &ndash; ohne Best&auml;tigung erfolgt keine Aufnahme in den Verteiler.
    </p>
  </div>
  <div style="padding:20px 32px;border-top:1px solid {ST_LINE};text-align:center">
    <div style="font-size:11px;color:{ST_DIM};font-family:'Courier New',monospace;line-height:1.7">
      <a href="{WEBSITE_URL}" style="color:{ST_CYAN};text-decoration:none">sw-tech.net</a> &middot;
      <a href="mailto:office@sw-tech.net" style="color:{ST_SOFT};text-decoration:none">office@sw-tech.net</a><br>
      Software Technologies-Development-Service GesmbH &middot; Wien
    </div>
  </div>
</div>
</body></html>
"""
    return _send(email, "Bitte best\u00e4tigen Sie Ihre Newsletter-Anmeldung", html)


def newsletter_confirmed_page(email: str = "") -> str:
    """HTML-Seite, die nach erfolgreicher Bestaetigung angezeigt wird."""
    return f"""<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Anmeldung best\u00e4tigt \u2013 Software Technologies</title>
<style>
  body{{font-family:-apple-system,system-ui,'Segoe UI',sans-serif;background:{ST_BG};color:{ST_INK};margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px}}
  .card{{max-width:460px;text-align:center;background:{ST_PANEL};border:1px solid {ST_LINE};border-radius:18px;padding:44px 36px}}
  .brand{{font-size:17px;font-weight:700;margin-bottom:4px}}
  .brand .ac{{color:{ST_CYAN}}}
  .sub{{font-size:11px;color:{ST_DIM};font-family:'Courier New',monospace;letter-spacing:.05em;margin-bottom:28px}}
  .check{{width:76px;height:76px;border-radius:50%;background:rgba(15,181,166,.12);display:flex;align-items:center;justify-content:center;margin:0 auto 22px}}
  .check svg{{width:36px;height:36px;stroke:{ST_CYAN};fill:none;stroke-width:2.5}}
  h1{{font-size:22px;margin:0 0 12px 0}}
  p{{font-size:14px;line-height:1.6;color:{ST_SOFT};margin:0 0 8px 0}}
  .btn{{display:inline-block;margin-top:22px;background:{ST_CYAN};color:#ffffff;padding:12px 26px;border-radius:9px;font-weight:700;text-decoration:none;font-size:14px}}
</style></head>
<body>
  <div class="card">
    <div class="brand">Software<span class="ac">&middot;</span>Technologies</div>
    <div class="sub">SSOT Supplier Risk Management</div>
    <div class="check"><svg viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg></div>
    <h1>Anmeldung best\u00e4tigt</h1>
    <p>Vielen Dank! Ihre Anmeldung f\u00fcr <strong style="color:{ST_INK}">{email}</strong> ist best\u00e4tigt.</p>
    <p>Sie erhalten k\u00fcnftig unsere Updates zu Supplier Risk Management und regulatorischen Neuerungen.</p>
    <a class="btn" href="{WEBSITE_URL}">Zur Website</a>
  </div>
</body></html>"""


# ==============================================================
#  RISIKOANALYSE / ASSESSMENT (Software Technologies Design, hell)
# ==============================================================

DIM_LABELS = {
    "legal":       "Rechtliche Absicherung",
    "cyber":       "IT-Sicherheit & Datenschutz",
    "operational": "Operative Risiken",
    "financial":   "Finanzielle Stabilität",
}
DIM_EMOJI = {"legal": "&#9878;", "cyber": "&#128272;", "operational": "&#9881;", "financial": "&#128202;"}

SCORE_COLOR = {"green": "#1f9e6e", "yellow": "#d9931a", "red": "#e0483f"}
SCORE_TEXT  = {"green": "Gut gesichert", "yellow": "Handlungsbedarf", "red": "Kritisches Risiko"}
SCORE_ICON  = {"green": "&#9989;", "yellow": "&#9888;&#65039;", "red": "&#128680;"}


def _dim_bar(dim, val):
    try:
        v = int(round(float(val)))
    except Exception:
        v = 0
    col = "#1f9e6e" if v >= 80 else "#d9931a" if v >= 60 else "#e0483f"
    label = DIM_LABELS.get(dim, dim)
    emoji = DIM_EMOJI.get(dim, "")
    return f"""
      <div style="margin-bottom:16px">
        <div style="display:flex;justify-content:space-between;margin-bottom:7px">
          <span style="font-size:14px;color:{ST_INK};font-weight:500">{emoji} {label}</span>
          <span style="font-size:14px;font-weight:800;color:{col}">{v}%</span>
        </div>
        <div style="background:#eef2f7;border-radius:99px;height:9px">
          <div style="background:{col};border-radius:99px;height:9px;width:{v}%"></div>
        </div>
      </div>"""


def _assessment_result_html(scores: dict, analysis: dict, company: str = "") -> str:
    """Der innere Ergebnis-Block (wird in Seite UND Report-Mail genutzt)."""
    final = int(round(float(scores.get("final", 0))))
    color = scores.get("color", "red")
    scol  = SCORE_COLOR.get(color, "#e0483f")
    stext = SCORE_TEXT.get(color, "")
    sicon = SCORE_ICON.get(color, "")
    ds    = scores.get("ds", {}) or {}
    top   = scores.get("top", []) or []

    exec_txt = analysis.get("exec", "")
    impact   = analysis.get("impact", "")
    pkg      = analysis.get("pkg", "")
    pkg_why  = analysis.get("pkgWhy", "")

    dims_html = "".join(_dim_bar(d, v) for d, v in ds.items())

    top_html = ""
    if top:
        items = ""
        for i, q in enumerate(top):
            label = q.get("label", "") if isinstance(q, dict) else str(q)
            fix   = q.get("fix", "") if isinstance(q, dict) else ""
            border = "border-bottom:1px solid #eef2f7;" if i < len(top) - 1 else ""
            items += f"""
            <div style="display:flex;gap:12px;padding:12px 0;{border}">
              <div style="width:28px;height:28px;border-radius:50%;background:#e0483f;color:#fff;display:inline-flex;align-items:center;justify-content:center;font-weight:800;font-size:13px;flex:none">{i+1}</div>
              <div><div style="font-weight:700;color:{ST_INK};font-size:14px;margin-bottom:2px">{label}</div><div style="font-size:13px;color:{ST_SOFT}">{fix}</div></div>
            </div>"""
        top_html = f"""
        <div style="background:{ST_PANEL};border:1px solid {ST_LINE};border-radius:14px;padding:20px 22px;margin-bottom:16px">
          <div style="font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:{ST_SOFT};font-weight:700;margin-bottom:8px;font-family:'Courier New',monospace">Wichtigste Risiken</div>
          {items}
        </div>"""

    prios = [analysis.get("p1"), analysis.get("p2"), analysis.get("p3")]
    prio_colors = ["#0fb5a6", "#2f7fd6", "#7C3AED"]
    prio_items = ""
    real = [p for p in prios if p]
    for i, p in enumerate(real):
        title = p.get("title", "") if isinstance(p, dict) else ""
        text  = p.get("text", "") if isinstance(p, dict) else ""
        border = "border-bottom:1px solid #eef2f7;" if i < len(real) - 1 else ""
        prio_items += f"""
        <div style="display:flex;gap:12px;padding:12px 0;{border}">
          <div style="width:28px;height:28px;border-radius:50%;background:{prio_colors[i%3]};color:#fff;display:inline-flex;align-items:center;justify-content:center;font-weight:800;font-size:13px;flex:none">{i+1}</div>
          <div><div style="font-weight:700;color:{ST_INK};font-size:14px;margin-bottom:2px">Priorit&auml;t {i+1}: {title}</div><div style="font-size:13px;color:{ST_SOFT};line-height:1.5">{text}</div></div>
        </div>"""

    return f"""
    <div style="border:1px solid {ST_LINE};border-radius:16px;text-align:center;padding:30px 24px;margin-bottom:16px;background:{ST_PANEL}">
      <div style="font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:{ST_CYAN};margin-bottom:8px;font-family:'Courier New',monospace">Ihr Supplier-Risk-Score</div>
      <div style="font-size:70px;font-weight:900;color:{scol};line-height:1">{final}</div>
      <div style="font-size:15px;color:{ST_SOFT};margin-bottom:16px">von 100 Punkten</div>
      <div style="display:inline-block;padding:9px 22px;border-radius:99px;background:{scol}1a;color:{scol};font-weight:700;font-size:15px">{sicon} {stext}</div>
    </div>

    <div style="border:1px solid {ST_LINE};border-left:4px solid {ST_CYAN};border-radius:12px;padding:20px 22px;margin-bottom:16px">
      <div style="font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:{ST_CYAN};font-weight:700;margin-bottom:8px;font-family:'Courier New',monospace">Zusammenfassung</div>
      <p style="font-size:14px;line-height:1.6;color:{ST_INK};margin:0">{exec_txt}</p>
    </div>

    <div style="border:1px solid {ST_LINE};border-radius:14px;padding:20px 22px;margin-bottom:16px">
      <div style="font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:{ST_SOFT};font-weight:700;margin-bottom:16px;font-family:'Courier New',monospace">Dimensionen</div>
      {dims_html}
    </div>

    <div style="border:1px solid {ST_LINE};border-left:4px solid #e0483f;border-radius:12px;padding:20px 22px;margin-bottom:16px">
      <div style="font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:#e0483f;font-weight:700;margin-bottom:8px;font-family:'Courier New',monospace">Auswirkung</div>
      <p style="font-size:14px;line-height:1.6;color:{ST_INK};margin:0">{impact}</p>
    </div>

    {top_html}

    <div style="border:1px solid {ST_LINE};border-radius:14px;padding:20px 22px;margin-bottom:16px">
      <div style="font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:{ST_SOFT};font-weight:700;margin-bottom:8px;font-family:'Courier New',monospace">Empfohlene Ma&szlig;nahmen</div>
      {prio_items}
    </div>

    <div style="border:1px solid {ST_CYAN};border-radius:16px;text-align:center;padding:28px 24px;background:rgba(15,181,166,0.06)">
      <div style="font-size:15px;font-weight:700;color:{ST_INK};margin-bottom:6px">Empfohlenes Paket: {pkg}</div>
      <p style="font-size:13px;color:{ST_SOFT};margin:0 0 16px 0">{pkg_why}</p>
      <a href="{CAL_URL}" target="_blank" style="display:inline-block;background:{ST_CYAN};color:#fff;padding:13px 30px;border-radius:10px;font-weight:700;text-decoration:none;font-size:15px;margin:0 5px 8px">Beratungsgespr&auml;ch buchen</a>
      <a href="{WHATSAPP_URL}" target="_blank" style="display:inline-block;background:#25D366;color:#04140f;padding:13px 26px;border-radius:10px;font-weight:700;text-decoration:none;font-size:15px;margin:0 5px 8px">Per WhatsApp chatten</a>
    </div>"""


def assessment_result_page(scores: dict, analysis: dict, lead: dict, already: bool = False) -> str:
    """Vollstaendige Ergebnisseite nach Bestaetigung (Double-Opt-in)."""
    if already or not scores:
        return f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Link ung&uuml;ltig</title>
<style>body{{font-family:-apple-system,system-ui,'Segoe UI',sans-serif;background:{ST_BG};color:{ST_INK};margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px}}
.card{{max-width:440px;text-align:center;background:{ST_PANEL};border:1px solid {ST_LINE};border-radius:18px;padding:44px 36px}}</style></head>
<body><div class="card"><h1 style="font-size:20px;color:{ST_INK}">Link ung&uuml;ltig oder bereits verwendet</h1>
<p style="color:{ST_SOFT};font-size:14px">Dieser Best&auml;tigungslink ist nicht mehr g&uuml;ltig. M&ouml;glicherweise wurde Ihr Report bereits freigeschaltet.</p>
<a href="{WEBSITE_URL}" style="display:inline-block;margin-top:18px;background:{ST_CYAN};color:#fff;padding:11px 24px;border-radius:9px;font-weight:700;text-decoration:none">Zur Website</a></div></body></html>"""

    company = lead.get("company", "")
    name = lead.get("name", "")
    inner = _assessment_result_html(scores, analysis, company)
    return f"""<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ihr Supplier-Risk-Report &ndash; Software Technologies</title>
<style>body{{font-family:-apple-system,system-ui,'Segoe UI',sans-serif;background:{ST_BG};color:{ST_INK};margin:0;padding:0}}</style>
</head>
<body>
  <div style="max-width:640px;margin:0 auto;padding:0 16px 60px">
    <div style="padding:26px 4px 22px;border-bottom:1px solid {ST_LINE};margin-bottom:24px">
      <div style="font-size:19px;font-weight:700;color:{ST_INK}">Software<span style="color:{ST_CYAN}">&middot;</span>Technologies</div>
      <div style="font-size:11px;color:{ST_DIM};font-family:'Courier New',monospace;letter-spacing:.05em;margin-top:2px">SSOT &middot; Supplier Risk Assessment</div>
    </div>
    <div style="margin-bottom:20px">
      <div style="display:inline-block;background:rgba(31,158,110,.12);color:#1f9e6e;font-size:12px;font-weight:700;padding:6px 14px;border-radius:99px">&#10003; E-Mail best&auml;tigt</div>
      <p style="font-size:14px;color:{ST_SOFT};margin:12px 0 0">Guten Tag {name.split(' ')[0] if name else ''}, hier ist Ihr vollst&auml;ndiges Ergebnis f&uuml;r <strong style="color:{ST_INK}">{company}</strong>. Der PDF-Report ist zus&auml;tzlich in Ihrem Postfach.</p>
    </div>
    {inner}
  </div>
</body></html>"""


def send_assessment_confirm_email(email: str, name: str, confirm_url: str) -> bool:
    """Bestaetigungsmail (Double-Opt-in) fuer das Risiko-Assessment."""
    first = name.split(" ")[0] if name else ""
    html = f"""
<!DOCTYPE html>
<html lang="de"><head><meta charset="UTF-8"></head>
<body style="font-family:-apple-system,system-ui,'Segoe UI',sans-serif;background:{ST_BG};margin:0;padding:0">
<div style="max-width:560px;margin:0 auto;background:{ST_BG}">
  <div style="padding:30px 32px 22px 32px;border-bottom:1px solid {ST_LINE}">
    <div style="font-size:19px;font-weight:700;color:{ST_INK}">Software<span style="color:{ST_CYAN}">&middot;</span>Technologies</div>
    <div style="font-size:11px;color:{ST_DIM};font-family:'Courier New',monospace;letter-spacing:.05em;margin-top:2px">SSOT &middot; Supplier Risk Assessment</div>
  </div>
  <div style="padding:28px 32px">
    <h1 style="font-size:21px;color:{ST_INK};margin:0 0 14px 0;font-weight:700">Nur noch ein Klick zu Ihrem Ergebnis</h1>
    <p style="font-size:14px;line-height:1.6;color:{ST_SOFT};margin:0 0 22px 0">
      Guten Tag {first}, Sie haben ein Supplier-Risk-Assessment durchgef&uuml;hrt. Bitte best&auml;tigen Sie kurz, dass diese Anfrage von Ihnen stammt &ndash; danach sehen Sie Ihren vollst&auml;ndigen Score mit Analyse und erhalten den PDF-Report per E-Mail.
    </p>
    <div style="text-align:center;margin:26px 0">
      <a href="{confirm_url}" target="_blank" style="display:inline-block;background:{ST_CYAN};color:#fff;padding:14px 30px;border-radius:8px;font-weight:700;text-decoration:none;font-size:15px">Ergebnis freischalten</a>
    </div>
    <p style="font-size:12px;line-height:1.6;color:{ST_DIM};margin:22px 0 0 0">
      Falls der Button nicht funktioniert, kopieren Sie diesen Link in Ihren Browser:<br>
      <a href="{confirm_url}" style="color:{ST_CYAN};text-decoration:none;word-break:break-all">{confirm_url}</a>
    </p>
    <p style="font-size:12px;line-height:1.6;color:{ST_DIM};margin:18px 0 0 0">
      Wenn Sie diese Anfrage nicht gestellt haben, ignorieren Sie diese E-Mail einfach.
    </p>
  </div>
  <div style="padding:20px 32px;border-top:1px solid {ST_LINE};text-align:center">
    <div style="font-size:11px;color:{ST_DIM};font-family:'Courier New',monospace;line-height:1.7">
      <a href="{WEBSITE_URL}" style="color:{ST_CYAN};text-decoration:none">sw-tech.net</a> &middot;
      <a href="mailto:office@sw-tech.net" style="color:{ST_SOFT};text-decoration:none">office@sw-tech.net</a><br>
      Software Technologies-Development-Service GesmbH &middot; Wien
    </div>
  </div>
</div>
</body></html>
"""
    return _send(email, "Bitte best\u00e4tigen Sie Ihr Assessment", html)


def send_assessment_report_email(lead: dict, scores: dict, analysis: dict, pdf_bytes=None) -> bool:
    """Report-Mail (nach Bestaetigung) im hellen SW-Tech-Design, mit PDF."""
    name = lead.get("name", "")
    first = name.split(" ")[0] if name else ""
    company = lead.get("company", "")
    final = int(round(float(scores.get("final", 0))))
    inner = _assessment_result_html(scores, analysis, company)
    html = f"""
<!DOCTYPE html>
<html lang="de"><head><meta charset="UTF-8"></head>
<body style="font-family:-apple-system,system-ui,'Segoe UI',sans-serif;background:{ST_BG};margin:0;padding:0">
<div style="max-width:640px;margin:0 auto;background:{ST_BG}">
  <div style="padding:30px 32px 22px 32px;border-bottom:1px solid {ST_LINE}">
    <div style="font-size:19px;font-weight:700;color:{ST_INK}">Software<span style="color:{ST_CYAN}">&middot;</span>Technologies</div>
    <div style="font-size:11px;color:{ST_DIM};font-family:'Courier New',monospace;letter-spacing:.05em;margin-top:2px">SSOT &middot; Supplier Risk Assessment</div>
  </div>
  <div style="padding:28px 32px">
    <p style="font-size:14px;line-height:1.6;color:{ST_SOFT};margin:0 0 22px 0">Guten Tag {first}, hier ist Ihr vollst&auml;ndiger Supplier-Risk-Report f&uuml;r <strong style="color:{ST_INK}">{company}</strong>. Den Report finden Sie zus&auml;tzlich als PDF im Anhang.</p>
    {inner}
    <p style="font-size:13px;line-height:1.6;color:{ST_SOFT};margin-top:24px">Mit freundlichen Gr&uuml;&szlig;en,<br><strong style="color:{ST_INK}">Ihr Software-Technologies-Team</strong></p>
  </div>
  <div style="padding:20px 32px;border-top:1px solid {ST_LINE};text-align:center">
    <div style="font-size:11px;color:{ST_DIM};font-family:'Courier New',monospace;line-height:1.7">
      <a href="{WEBSITE_URL}" style="color:{ST_CYAN};text-decoration:none">sw-tech.net</a> &middot; office@sw-tech.net<br>
      Software Technologies-Development-Service GesmbH &middot; Wien &middot; powered by Ynhald
    </div>
  </div>
</div>
</body></html>
"""
    return _send(lead["email"], f"Ihr Supplier-Risk-Report - Score {final}/100",
                 html, pdf_bytes=pdf_bytes, pdf_name="Supplier-Risk-Report.pdf")


def send_assessment_alert(lead: dict, scores: dict, analysis: dict, assessment_id: str) -> bool:
    """Kompakter interner Alert fuer ein Assessment (SW-Tech, hell)."""
    name    = lead.get("name", "")
    company = lead.get("company", "")
    email   = lead.get("email", "")
    phone   = lead.get("phone", "-")
    final   = int(round(float(scores.get("final", 0))))
    color   = scores.get("color", "red")
    scol    = SCORE_COLOR.get(color, "#e0483f")
    stext   = SCORE_TEXT.get(color, "")
    pkg     = analysis.get("pkg", "-")
    ds      = scores.get("ds", {}) or {}
    exec_txt = analysis.get("exec", "")

    dim_rows = ""
    for d, v in ds.items():
        try:
            vi = int(round(float(v)))
        except Exception:
            vi = 0
        c = "#1f9e6e" if vi >= 80 else "#d9931a" if vi >= 60 else "#e0483f"
        dim_rows += f'<tr><td style="padding:5px 8px;color:{ST_SOFT};font-size:13px">{DIM_LABELS.get(d, d)}</td><td style="padding:5px 8px;text-align:right;font-weight:700;color:{c};font-size:13px">{vi}%</td></tr>'

    html = f"""
<!DOCTYPE html>
<html lang="de"><head><meta charset="UTF-8"></head>
<body style="font-family:-apple-system,system-ui,'Segoe UI',sans-serif;background:{ST_BG};margin:0;padding:0">
<div style="max-width:560px;margin:0 auto;background:{ST_BG}">
  <div style="padding:22px 28px;border-bottom:1px solid {ST_LINE}">
    <div style="font-size:11px;color:{ST_CYAN};font-family:'Courier New',monospace;letter-spacing:.1em;text-transform:uppercase">Neuer Assessment-Lead</div>
    <h1 style="color:{ST_INK};margin:6px 0 0 0;font-size:18px">Score {final}/100 &middot; {stext}</h1>
  </div>
  <div style="padding:24px 28px">
    <div style="font-size:44px;font-weight:900;color:{scol};line-height:1;margin-bottom:6px">{final}<span style="font-size:15px;color:{ST_DIM};font-weight:400">/100</span></div>
    <p style="margin:0 0 16px;color:{ST_DIM};font-size:12px;font-family:'Courier New',monospace">ID: {assessment_id}</p>
    <table style="border-collapse:collapse;width:100%;font-size:13px">
      <tr><td style="padding:7px 0;color:{ST_SOFT};width:130px;border-bottom:1px solid {ST_LINE}">Name</td><td style="padding:7px 0;font-weight:600;color:{ST_INK};border-bottom:1px solid {ST_LINE}">{name}</td></tr>
      <tr><td style="padding:7px 0;color:{ST_SOFT};border-bottom:1px solid {ST_LINE}">Unternehmen</td><td style="padding:7px 0;font-weight:600;color:{ST_INK};border-bottom:1px solid {ST_LINE}">{company}</td></tr>
      <tr><td style="padding:7px 0;color:{ST_SOFT};border-bottom:1px solid {ST_LINE}">E-Mail</td><td style="padding:7px 0;font-weight:600;border-bottom:1px solid {ST_LINE}"><a href="mailto:{email}" style="color:{ST_CYAN};text-decoration:none">{email}</a></td></tr>
      <tr><td style="padding:7px 0;color:{ST_SOFT};border-bottom:1px solid {ST_LINE}">Telefon</td><td style="padding:7px 0;font-weight:600;color:{ST_INK};border-bottom:1px solid {ST_LINE}">{phone}</td></tr>
      <tr><td style="padding:7px 0;color:{ST_SOFT}">Paket</td><td style="padding:7px 0;font-weight:600;color:#0fb5a6">{pkg}</td></tr>
    </table>
    <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:{ST_SOFT};font-family:'Courier New',monospace;margin:20px 0 6px">Dimensionen</div>
    <table style="border-collapse:collapse;width:100%">{dim_rows}</table>
    <p style="font-size:13px;color:{ST_SOFT};line-height:1.5;margin-top:16px">{exec_txt}</p>
  </div>
  <div style="padding:16px 28px;border-top:1px solid {ST_LINE};text-align:center;font-size:11px;color:{ST_DIM};font-family:'Courier New',monospace">
    Software Technologies &middot; Interner Lead-Alert &middot; Vertraulich
  </div>
</div>
</body></html>
"""
    return _send(ALERT_EMAIL, f"[Assessment] {company or name} - Score {final}/100 - {stext}", html)
