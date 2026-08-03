import os
import base64
import httpx
from typing import Optional

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL     = os.getenv("FROM_EMAIL", "onboarding@resend.dev")
FROM_NAME      = os.getenv("FROM_NAME", "YNHALD Supplier Risk")
ALERT_EMAIL    = os.getenv("ALERT_EMAIL", "azajic@sw-tech.net")

SCORE_LABELS = {"green": "Gut gesichert", "yellow": "Handlungsbedarf", "red": "Kritisches Risiko"}


def _send(to: str, subject: str, html: str, pdf_bytes: Optional[bytes] = None) -> bool:
    """Sendet eine E-Mail via Resend REST API."""
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
            "filename":    "YNHALD_Supplier_Risk_Report.pdf",
            "content":     base64.b64encode(pdf_bytes).decode("utf-8"),
            "content_type": "application/pdf",
        }]

    try:
        r = httpx.post(
            "https://api.resend.com/emails",
            json=payload,
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            timeout=15,
        )
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False


def send_lead_email(lead: dict, scores: dict, analysis: dict, pdf_bytes: bytes) -> bool:
    """E-Mail an den Lead mit PDF-Anhang."""
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
    <p class="text">vielen Dank fuer die Teilnahme am YNHALD Supplier Risk Check. Anbei finden Sie Ihren vollstaendigen PDF-Report fuer <strong>{company}</strong>.</p>
    <div class="section">
      <div class="section-title">Executive Summary</div>
      <p class="text">{exec_txt}</p>
    </div>
    <div class="section">
      <div class="section-title">Empfohlenes Paket</div>
      <p class="text"><strong>{pkg}</strong> &mdash; {pkg_why}</p>
    </div>
    <div class="cta-box">
      <div class="cta-title">Kostenloses 30-min Erstgespraech buchen</div>
      <p style="font-size:13px;color:#64748B;margin:0 0 14px">Sprechen Sie mit einem unserer Experten ueber Ihre Ergebnisse.</p>
      <a href="mailto:azajic@sw-tech.net" class="cta-btn">Termin anfragen</a>
    </div>
    <p class="text">Den vollstaendigen Report mit allen Details und Handlungsempfehlungen finden Sie im Anhang.</p>
    <p class="text">Mit freundlichen Gruessen,<br><strong>Das YNHALD Team</strong></p>
  </div>
  <div class="footer">YNHALD &middot; azajic@sw-tech.net &middot; Vertraulich</div>
</div>
</body></html>
"""
    return _send(
        to=lead["email"],
        subject=f"Ihr YNHALD Supplier Risk Report - Score: {final}/100",
        html=html,
        pdf_bytes=pdf_bytes,
    )


def send_sales_alert(lead: dict, scores: dict, analysis: dict, assessment_id: str) -> bool:
    """Sales-Alert an das YNHALD-Team."""
    name    = lead.get("name", "")
    company = lead.get("company", "")
    supplier= lead.get("supplier", "-")
    email   = lead.get("email", "")
    phone   = lead.get("phone", "-")
    final   = int(scores.get("final", 0))
    color   = scores.get("color", "red")
    ds      = scores.get("ds", {})
    crits   = scores.get("crits", [])
    pkg     = analysis.get("pkg", "-")
    score_lbl = SCORE_LABELS.get(color, "")
    flag_col  = '#DC2626' if color == 'red' else '#D97706'
    exec_txt  = analysis.get('exec', '')

    crit_html = "".join(
        f"<li style='color:#DC2626'>{c.get('label', c.get('id', ''))}</li>"
        for c in crits
    ) or "<li>Keine</li>"

    dim_html = "".join(
        f"<tr><td style='padding:4px 8px;color:#64748B'>{k.title()}</td>"
        f"<td style='padding:4px 8px;font-weight:700;color:{'#059669' if v>=80 else '#D97706' if v>=60 else '#DC2626'}'>{int(v)}%</td></tr>"
        for k, v in ds.items()
    )

    html = f"""
<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"><style>
  body {{ font-family: -apple-system, system-ui, sans-serif; color: #0A1940; background: #f4f6fb; margin:0; }}
  .wrap {{ max-width: 580px; margin: 0 auto; background: #fff; }}
  .header {{ background: {flag_col}; padding: 20px 28px; }}
  .header h1 {{ color: #fff; margin: 0; font-size: 18px; }}
  .body {{ padding: 24px 28px; }}
  table {{ border-collapse: collapse; width: 100%; }}
  .meta td {{ padding: 6px 0; font-size: 13px; border-bottom: 1px solid #F1F5F9; }}
  .meta td:first-child {{ color: #64748B; width: 130px; }}
  .meta td:last-child {{ font-weight: 600; }}
  .score-big {{ font-size: 48px; font-weight: 900; color: {flag_col}; }}
</style></head>
<body>
<div class="wrap">
  <div class="header">
    <h1>Neuer Lead - {score_lbl}</h1>
  </div>
  <div class="body">
    <div class="score-big">{final}<span style="font-size:16px;font-weight:400;color:#94A3B8">/100</span></div>
    <p style="margin:4px 0 20px;color:#64748B;font-size:13px">Assessment-ID: {assessment_id}</p>
    <table class="meta">
      <tr><td>Name</td><td>{name}</td></tr>
      <tr><td>Unternehmen</td><td>{company}</td></tr>
      <tr><td>Lieferant</td><td>{supplier}</td></tr>
      <tr><td>E-Mail</td><td><a href="mailto:{email}">{email}</a></td></tr>
      <tr><td>Telefon</td><td>{phone}</td></tr>
      <tr><td>Paket-Empfehlung</td><td><strong style="color:#E8960C">{pkg}</strong></td></tr>
    </table>
    <h3 style="margin:20px 0 8px;font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:#64748B">Dimensionen</h3>
    <table>{dim_html}</table>
    <h3 style="margin:16px 0 8px;font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:#DC2626">Kritische Luecken</h3>
    <ul style="margin:0;padding-left:20px;font-size:13px">{crit_html}</ul>
    <h3 style="margin:16px 0 6px;font-size:13px;color:#64748B">KI-Einschaetzung</h3>
    <p style="font-size:13px;color:#475569;line-height:1.5">{exec_txt}</p>
    <div style="margin-top:24px;padding:16px;background:#FFF7ED;border-radius:8px;text-align:center">
      <a href="mailto:{email}" style="background:#E8960C;color:#fff;padding:10px 24px;border-radius:6px;font-weight:700;text-decoration:none;font-size:14px">
        Jetzt {name} kontaktieren
      </a>
    </div>
  </div>
</div>
</body></html>
"""
    return _send(
        to=ALERT_EMAIL,
        subject=f"[YNHALD Lead] {company} - Score {final}/100 - {score_lbl}",
        html=html,
    )


# ==============================================================
#  KRITIKALITAETS-EINSTUFUNG  (Software Technologies)
#  Multi-Lieferanten: ein Report ueber mehrere Lieferanten
# ==============================================================

GRADE_COLORS = {"A": "#DC2626", "B": "#D97706", "C": "#2563EB", "D": "#059669"}


def _supplier_block(s: dict) -> str:
    """HTML-Block fuer einen einzelnen Lieferanten im Report."""
    grade = s.get("grade", "-")
    gcol  = GRADE_COLORS.get(grade, "#0A1940")
    rec   = s.get("recommendation", {})
    name  = s.get("name", "-")
    url   = s.get("url", "")
    plz   = s.get("plz", "")
    grade_name = s.get('gradeName', '')
    meta  = " &middot; ".join([x for x in [url, plz] if x])
    meta_html = (" &middot; " + meta) if meta else ""
    tiefe = rec.get('tiefe', '')
    reass = rec.get('reass', '')
    monitoring = rec.get('monitoring', '')
    freigabe = rec.get('freigabe', '')

    return f"""
    <div style="border:1px solid #E9EDF2;border-radius:10px;margin-bottom:16px;overflow:hidden">
      <div style="display:flex;align-items:center;gap:12px;padding:14px 16px;background:#F8FAFC;border-bottom:1px solid #E9EDF2">
        <div style="width:38px;height:38px;border-radius:8px;background:{gcol};color:#fff;font-weight:900;font-size:18px;text-align:center;line-height:38px">{grade}</div>
        <div>
          <div style="font-weight:700;font-size:15px;color:#0A1940">{name}</div>
          <div style="font-size:12px;color:#94A3B8">Stufe {grade} &middot; {grade_name}{meta_html}</div>
        </div>
      </div>
      <table style="width:100%;border-collapse:collapse;font-size:13px">
        <tr><td style="padding:8px 16px;color:#64748B;width:150px;border-bottom:1px solid #F1F5F9">Prueftiefe</td><td style="padding:8px 16px;border-bottom:1px solid #F1F5F9">{tiefe}</td></tr>
        <tr><td style="padding:8px 16px;color:#64748B;border-bottom:1px solid #F1F5F9">Re-Assessment</td><td style="padding:8px 16px;border-bottom:1px solid #F1F5F9">{reass}</td></tr>
        <tr><td style="padding:8px 16px;color:#64748B;border-bottom:1px solid #F1F5F9">Monitoring</td><td style="padding:8px 16px;border-bottom:1px solid #F1F5F9">{monitoring}</td></tr>
        <tr><td style="padding:8px 16px;color:#64748B">Freigabe</td><td style="padding:8px 16px">{freigabe}</td></tr>
      </table>
    </div>"""


def send_criticality_lead_email(lead: dict, suppliers: list, summary: str = "") -> bool:
    """Kritikalitaets-Report (mehrere Lieferanten) an den Kunden."""
    name = lead.get("name", "")
    n    = len(suppliers)
    plural = "en" if n != 1 else ""
    blocks = "".join(_supplier_block(s) for s in suppliers)
    summary_html = ""
    if summary:
        summary_html = f"""
      <div style="background:#F1F6FE;border-radius:8px;padding:16px 18px;margin-bottom:22px">
        <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#1E3FA0;margin-bottom:6px">Gesamteinschaetzung</div>
        <p style="font-size:14px;line-height:1.6;color:#334155;margin:0">{summary}</p>
      </div>"""

    html = f"""
<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"><style>
  body {{ font-family: -apple-system, system-ui, sans-serif; color: #0A1940; background: #f4f6fb; margin: 0; padding: 0; }}
  .wrap {{ max-width: 640px; margin: 0 auto; background: #fff; }}
  .header {{ background: #0A1940; padding: 28px 32px; }}
  .header h1 {{ color: #fff; margin: 0; font-size: 22px; }}
  .header p {{ color: #93C5FD; margin: 4px 0 0; font-size: 13px; }}
  .body {{ padding: 28px 32px; }}
  .text {{ font-size: 14px; line-height: 1.6; color: #475569; }}
  .footer {{ background: #F8FAFC; padding: 20px 32px; text-align: center; font-size: 12px; color: #94A3B8; }}
</style></head>
<body>
<div class="wrap">
  <div class="header">
    <h1>Software Technologies</h1>
    <p>Ihr Kritikalitaets-Report ist bereit</p>
  </div>
  <div class="body">
    <p>Guten Tag {name},</p>
    <p class="text">vielen Dank fuer Ihre Einstufung. Nachfolgend finden Sie den Kritikalitaets-Report ueber <strong>{n} Lieferant{plural}</strong> - jeweils mit Stufe A-D und Empfehlung fuer Ihr Risikomanagement.</p>
    {summary_html}
    {blocks}
    <p class="text" style="margin-top:20px">Diese Einstufung priorisiert Ihr Risikomanagement. Fuer ein vollstaendiges, quellenbasiertes Assessment einzelner Lieferanten (OSINT, Fragenkatalog, Expertenbewertung) stehen wir gern bereit.</p>
    <p class="text">Mit freundlichen Gruessen,<br><strong>Ihr Software-Technologies-Team</strong></p>
  </div>
  <div class="footer">Software Technologies &middot; azajic@sw-tech.net &middot; Vertraulich</div>
</div>
</body></html>
"""
    return _send(
        to=lead["email"],
        subject=f"Ihr Kritikalitaets-Report - {n} Lieferant{plural}",
        html=html,
    )


def send_criticality_alert(lead: dict, suppliers: list, crit_id: str, summary: str = "") -> bool:
    """Alert an das Team: neuer Kritikalitaets-Lead (mehrere Lieferanten)."""
    name    = lead.get("name", "")
    company = lead.get("company", "")
    email   = lead.get("email", "")
    phone   = lead.get("phone", "-")
    n       = len(suppliers)
    plural  = "en" if n != 1 else ""

    rows = ""
    for s in suppliers:
        gcol = GRADE_COLORS.get(s.get('grade'), '#0A1940')
        rows += (
            f"<tr><td style='padding:7px 8px;border-bottom:1px solid #F1F5F9'>"
            f"<span style='display:inline-block;width:22px;height:22px;border-radius:5px;background:{gcol};color:#fff;font-weight:700;font-size:12px;text-align:center;line-height:22px'>{s.get('grade','')}</span></td>"
            f"<td style='padding:7px 8px;border-bottom:1px solid #F1F5F9;font-weight:600'>{s.get('name','')}</td>"
            f"<td style='padding:7px 8px;border-bottom:1px solid #F1F5F9;color:#64748B'>{s.get('gradeName','')}</td></tr>"
        )

    summary_html = ""
    if summary:
        summary_html = f"<p style='font-size:13px;color:#475569;line-height:1.5;margin-top:14px'>{summary}</p>"

    html = f"""
<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"><style>
  body {{ font-family: -apple-system, system-ui, sans-serif; color: #0A1940; background: #f4f6fb; margin:0; }}
  .wrap {{ max-width: 580px; margin: 0 auto; background: #fff; }}
  .header {{ background: #0A1940; padding: 20px 28px; }}
  .header h1 {{ color: #fff; margin: 0; font-size: 18px; }}
  .body {{ padding: 24px 28px; }}
  table {{ border-collapse: collapse; width: 100%; }}
  .meta td {{ padding: 6px 0; font-size: 13px; border-bottom: 1px solid #F1F5F9; }}
  .meta td:first-child {{ color: #64748B; width: 130px; }}
  .meta td:last-child {{ font-weight: 600; }}
</style></head>
<body>
<div class="wrap">
  <div class="header">
    <h1>Neuer Kritikalitaets-Lead - {n} Lieferant{plural}</h1>
  </div>
  <div class="body">
    <p style="margin:0 0 16px;color:#64748B;font-size:13px">ID: {crit_id}</p>
    <table class="meta">
      <tr><td>Name</td><td>{name}</td></tr>
      <tr><td>Unternehmen</td><td>{company}</td></tr>
      <tr><td>E-Mail</td><td><a href="mailto:{email}">{email}</a></td></tr>
      <tr><td>Telefon</td><td>{phone}</td></tr>
    </table>
    <h3 style="margin:20px 0 8px;font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:#64748B">Eingestufte Lieferanten</h3>
    <table>{rows}</table>
    {summary_html}
    <div style="margin-top:24px;padding:16px;background:#FFF7ED;border-radius:8px;text-align:center">
      <a href="mailto:{email}" style="background:#E8960C;color:#fff;padding:10px 24px;border-radius:6px;font-weight:700;text-decoration:none;font-size:14px">
        Jetzt {name} kontaktieren
      </a>
    </div>
  </div>
</div>
</body></html>
"""
    return _send(
        to=ALERT_EMAIL,
        subject=f"[Kritikalitaet] {company or name} - {n} Lieferant{plural}",
        html=html,
    )
