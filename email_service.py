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


def _value_color(v):
    """Farbe je nach Antwort-Wert 1-4 (4 = hohes Risiko = rot)."""
    return {4: "#e0483f", 3: "#d9931a", 2: "#2f7fd6", 1: "#1f9e6e"}.get(v, ST_SOFT)


def _alert_supplier_detail(s: dict) -> str:
    """Detailblock pro Lieferant: Stufe, Impact/Wahrscheinlichkeit, alle Antworten."""
    grade = s.get("grade", "-")
    gcol  = GRADE_COLORS.get(grade, ST_CYAN)
    name  = s.get("name", "-")
    gname = s.get("gradeName", "")
    url   = s.get("url", "")
    plz   = s.get("plz", "")
    impact = s.get("impact", "")
    likelihood = s.get("likelihood", "")
    meta = " &middot; ".join([x for x in [url, plz] if x])
    meta_html = (" &middot; " + meta) if meta else ""

    ans_rows = ""
    for a in s.get("answers", []):
        v = a.get("value", 0)
        vcol = _value_color(v)
        ans_rows += (
            f'<tr>'
            f'<td style="padding:6px 8px;border-bottom:1px solid {ST_LINE};color:{ST_DIM};font-size:11px;width:150px;vertical-align:top">{a.get("cat","")}</td>'
            f'<td style="padding:6px 8px;border-bottom:1px solid {ST_LINE};color:{ST_INK};font-size:12px">{a.get("answer","")}</td>'
            f'<td style="padding:6px 8px;border-bottom:1px solid {ST_LINE};text-align:center;width:34px">'
            f'<span style="display:inline-block;min-width:20px;padding:1px 6px;border-radius:5px;background:{vcol};color:#fff;font-weight:700;font-size:11px">{v}</span></td>'
            f'</tr>'
        )

    return f"""
    <div style="border:1px solid {ST_LINE};border-radius:10px;margin-bottom:14px;overflow:hidden">
      <div style="padding:12px 14px;background:{ST_PANEL};border-bottom:1px solid {ST_LINE}">
        <table style="border-collapse:collapse;width:100%"><tr>
          <td style="width:34px;vertical-align:middle"><div style="width:34px;height:34px;border-radius:7px;background:{gcol};color:#fff;font-weight:900;font-size:16px;text-align:center;line-height:34px">{grade}</div></td>
          <td style="padding-left:10px;vertical-align:middle">
            <div style="font-weight:700;font-size:14px;color:{ST_INK}">{name}</div>
            <div style="font-size:11px;color:{ST_DIM};font-family:'Courier New',monospace">Stufe {grade} &middot; {gname}{meta_html}</div>
          </td>
          <td style="text-align:right;vertical-align:middle;white-space:nowrap">
            <div style="font-size:10px;color:{ST_DIM};font-family:'Courier New',monospace;text-transform:uppercase">Schaden / Wahrsch.</div>
            <div style="font-size:13px;font-weight:700;color:{ST_INK}">{impact} / {likelihood}</div>
          </td>
        </tr></table>
      </div>
      <table style="border-collapse:collapse;width:100%">{ans_rows}</table>
    </div>"""


def send_criticality_alert(lead: dict, suppliers: list, crit_id: str, summary: str = "") -> bool:
    """Alert an das Team - SW-Tech-Design, mit allen Antworten je Lieferant."""
    name    = lead.get("name", "")
    company = lead.get("company", "")
    email   = lead.get("email", "")
    phone   = lead.get("phone", "-")
    n       = len(suppliers)
    plural  = "en" if n != 1 else ""

    details = "".join(_alert_supplier_detail(s) for s in suppliers)

    summary_html = ""
    if summary:
        summary_html = f'<p style="font-size:13px;color:{ST_SOFT};line-height:1.5;margin-top:6px;margin-bottom:18px">{summary}</p>'

    html = f"""
<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"></head>
<body style="font-family:-apple-system,system-ui,'Segoe UI',sans-serif;background:{ST_BG};margin:0;padding:0">
<div style="max-width:600px;margin:0 auto;background:{ST_BG}">
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
    {summary_html}

    <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:{ST_SOFT};font-family:'Courier New',monospace;margin:22px 0 10px">Antworten je Lieferant &middot; Wert 4 = h&ouml;chstes Risiko</div>
    {details}

    <div style="margin-top:22px;text-align:center">
      <a href="mailto:{email}" style="display:inline-block;background:{ST_CYAN};color:#ffffff;padding:11px 24px;border-radius:8px;font-weight:700;text-decoration:none;font-size:14px">{name} kontaktieren</a>
    </div>
  </div>
  <div style="padding:16px 28px;border-top:1px solid {ST_LINE};text-align:center;font-size:11px;color:{ST_DIM};font-family:'Courier New',monospace">
    Software Technologies &middot; Interner Lead-Alert
  </div>
</div>
</body></html>
"""
    return _send(ALERT_EMAIL, f"[Kritikalit\u00e4t] {company or name} - {n} Lieferant{plural}", html)


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
