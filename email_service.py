import os
import base64
import httpx
from typing import Optional

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL     = os.getenv("FROM_EMAIL", "onboarding@resend.dev")
FROM_NAME      = os.getenv("FROM_NAME", "YNHALD Supplier Risk")
ALERT_EMAIL    = os.getenv("ALERT_EMAIL", "azajic@sw-tech.net")

SCORE_LABELS = {"green": "Gut gesichert \u2705", "yellow": "Handlungsbedarf \u26a0\ufe0f", "red": "Kritisches Risiko \U0001f6a8"}


def _send(to: str, subject: str, html: str, pdf_bytes: Optional[bytes] = None) -> bool:
    """Sendet eine E-Mail via Resend REST API."""
    if not RESEND_API_KEY:
        print(f"[EMAIL] Kein API-Key \u2013 w\u00fcrde senden an {to}: {subject}")
        return True  # Kein Fehler im Dev-Modus

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
  .score-num {{ font-size: 64px; font-weight: 900; color: {'#059669' if color=='green' else '#D97706' if color=='yellow' else '#DC2626'}; line-height: 1; }}
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
    <div class="score-label">/100 Punkte &nbsp;\u00b7&nbsp; {score_lbl}</div>
  </div>
  <div class="body">
    <p>Guten Tag {name},</p>
    <p class="text">vielen Dank f\u00fcr die Teilnahme am YNHALD Supplier Risk Check. Anbei finden Sie Ihren vollst\u00e4ndigen PDF-Report f\u00fcr <strong>{company}</strong>.</p>

    <div class="section">
      <div class="section-title">Executive Summary</div>
      <p class="text">{analysis.get('exec', '')}</p>
    </div>

    <div class="section">
      <div class="section-title">Empfohlenes Paket</div>
      <p class="text"><strong>{pkg}</strong> \u2014 {analysis.get('pkgWhy', '')}</p>
    </div>

    <div class="cta-box">
      <div class="cta-title">Kostenloses 30-min Erstgespr\u00e4ch buchen</div>
      <p style="font-size:13px;color:#64748B;margin:0 0 14px">Sprechen Sie mit einem unserer Experten \u00fcber Ihre Ergebnisse.</p>
      <a href="mailto:azajic@sw-tech.net?subject=Erstgespr\u00e4ch \u2013 {company}" class="cta-btn">Termin anfragen \u2192</a>
    </div>

    <p class="text">Den vollst\u00e4ndigen Report mit allen Details und Handlungsempfehlungen finden Sie im Anhang.</p>
    <p class="text">Mit freundlichen Gr\u00fc\u00dfen,<br><strong>Das YNHALD Team</strong></p>
  </div>
  <div class="footer">YNHALD \u00b7 azajic@sw-tech.net \u00b7 Vertraulich</div>
</div>
</body></html>
"""
    return _send(
        to=lead["email"],
        subject=f"Ihr YNHALD Supplier Risk Report \u2013 Score: {final}/100",
        html=html,
        pdf_bytes=pdf_bytes,
    )


def send_sales_alert(lead: dict, scores: dict, analysis: dict, assessment_id: str) -> bool:
    """Sales-Alert an das YNHALD-Team."""
    name    = lead.get("name", "")
    company = lead.get("company", "")
    supplier= lead.get("supplier", "\u2014")
    email   = lead.get("email", "")
    phone   = lead.get("phone", "\u2014")
    final   = int(scores.get("final", 0))
    color   = scores.get("color", "red")
    ds      = scores.get("ds", {})
    crits   = scores.get("crits", [])
    pkg     = analysis.get("pkg", "\u2014")
    score_lbl = SCORE_LABELS.get(color, "")
    flag_col  = '#DC2626' if color == 'red' else '#D97706'

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
    <h1>\U0001f514 Neuer Lead \u2013 {score_lbl}</h1>
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

    <h3 style="margin:16px 0 8px;font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:#DC2626">Kritische L\u00fccken</h3>
    <ul style="margin:0;padding-left:20px;font-size:13px">{crit_html}</ul>

    <h3 style="margin:16px 0 6px;font-size:13px;color:#64748B">KI-Einsch\u00e4tzung</h3>
    <p style="font-size:13px;color:#475569;line-height:1.5">{analysis.get('exec', '')}</p>

    <div style="margin-top:24px;padding:16px;background:#FFF7ED;border-radius:8px;text-align:center">
      <a href="mailto:{email}?subject=YNHALD Supplier Risk \u2013 Follow-up&body=Guten Tag {name},%0A%0A"
         style="background:#E8960C;color:#fff;padding:10px 24px;border-radius:6px;font-weight:700;text-decoration:none;font-size:14px">
        Jetzt {name} kontaktieren \u2192
      </a>
    </div>
  </div>
</div>
</body></html>
"""
    return _send(
        to=ALERT_EMAIL,
        subject=f"[YNHALD Lead] {company} \u2013 Score {final}/100 \u2013 {score_lbl}",
        html=html,
    )


# ==============================================================
#  KRITIKALITAeTS-EINSTUFUNG  (Software Technologies)
#  Multi-Lieferanten: ein Report ueber mehrere Lieferanten
# ==============================================================

GRADE_COLORS = {"A": "#DC2626", "B": "#D97706", "C": "#2563EB", "D": "#059669"}


def _supplier_block(s: dict) -> str:
    """HTML-Block fuer einen einzelnen Lieferanten im Report."""
    grade = s.get("grade", "\u2014")
    gcol  = GRADE_COLORS.get(grade, "#0A1940")
    rec   = s.get("recommendation", {})
    name  = s.get("name", "\u2014")
    url   = s.get("url", "")
    plz   = s.get("plz", "")
    meta  = " \u00b7 ".join([x for x in [url, plz] if x])

    return f"""
    <div style="border:1px solid #E9EDF2;border-radius:10px;margin-bottom:16px;overflow:hidden">
      <div style="display:flex;align-items:center;gap:12px;padding:14px 16px;background:#F8FAFC;border-bottom:1px solid #E9EDF2">
        <div style="width:38px;height:38px;border-radius:8px;background:{gcol};color:#fff;font-weight:900;font-size:18px;text-align:center;line-height:38px">{grade}</div>
        <div>
          <div style="font-weight:700;font-size:15px;color:#0A1940">{name}</div>
          <div style="font-size:12px;color:#94A3B8">Stufe {grade} \u00b7 {s.get('gradeName','')}{(' \u00b7 ' + meta) if meta else ''}</div>
        </div>
      </div>
      <table style="width:100%;border-collapse:collapse;font-size:13px">
        <tr><td style="padding:8px 16px;color:#64748B;width:150px;border-bottom:1px solid #F1F5F9">Pr\u00fcftiefe</td><td style="padding:8px 16px;border-bottom:1px solid #F1F5F9">{rec.get('tiefe','')}</td></tr>
        <tr><td style="padding:8px 16px;color:#64748B;border-bottom:1px solid #F1F5F9">Re-Assessment</td><td style="padding:8px 16px;border-bottom:1px solid #F1F5F9">{rec.get('reass','')}</td></tr>
        <tr><td style="padding:8px 16px;color:#64748B;border-bottom:1px solid #F1F5F9">Monitoring</td><td style="padding:8px 16px;border-bottom:1px solid #F1F5F9">{rec.get('monitoring','')}</td></tr>
        <tr><td style="padding:8px 16px;color:#64748B">Freigabe</td><td style="padding:8px 16px">{rec.get('freigabe','')}</td></tr>
      </table>
    </div>"""


def send_criticality_lead_email(lead: dict, suppliers: list, summary: str = "") -> bool:
    """Kritikalitaets-Report (mehrere Lieferanten) an den Kunden."""
    name = lead.get("name", "")
    n    = len(suppliers)
    blocks = "".join(_supplier_block(s) for s in suppliers)
    summary_html = f"""
      <div style="background:#F1F6FE;border-radius:8px;padding:16px 18px;margin-bottom:22px">
        <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#1E3FA0;margin-bottom:6px">Gesamteinsch\u00e4tzung</div>
        <p style="font-size:14px;line-height:1.6;color:#334155;margin:0">{summary}</p>
      </div>""" if summary else ""

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
    <p>Ihr Kritikalit\u00e4ts-Report ist bereit</p>
  </div>
  <div class="body">
    <p>Guten Tag {name},</p>
    <p class="text">vielen Dank f\u00fcr Ihre Einstufung. Nachfolgend finden Sie den Kritikalit\u00e4ts-Report \u00fcber <strong>{n} Lieferant{'en' if n != 1 else ''}</strong> \u2014 jeweils mit Stufe A\u2013D und Empfehlung f\u00fcr Ihr Risikomanagement.</p>
    {summary_html}
    {blocks}
    <p class="text" style="margin-top:20px">Diese Einstufung priorisiert Ihr Risikomanagement. F\u00fcr ein vollst\u00e4ndiges, quellenbasiertes Assessment einzelner Lieferanten (OSINT, Fragenkatalog, Expertenbewertung) stehen wir gern bereit.</p>
    <p class="text">Mit freundlichen Gr\u00fc\u00dfen,<br><strong>Ihr Software-Technologies-Team</strong></p>
  </div>
  <div class="footer">Software Technologies \u00b7 azajic@sw-tech.net \u00b7 Vertraulich</div>
</div>
</body></html>
"""
    return _send(
        to=lead["email"],
        subject=f"Ihr Kritikalit\u00e4ts-Report \u2013 {n} Lieferant{'en' if n != 1 else ''}",
        html=html,
    )


def send_criticality_alert(lead: dict, suppliers: list, crit_id: str, summary: str = "") -> bool:
    """Alert an das Team: neuer Kritikalitaets-Lead (mehrere Lieferanten)."""
    name    = lead.get("name", "")
    company = lead.get("company", "")
    email   = lead.get("email", "")
    phone   = lead.get("phone", "\u2014")
    n       = len(suppliers)

    rows = "".join(
        f"<tr><td style='padding:7px 8px;border-bottom:1px solid #F1F5F9'>"
        f"<span style='display:inline-block;width:22px;height:22px;border-radius:5px;background:{GRADE_COLORS.get(s.get('grade'),'#0A1940')};color:#fff;font-weight:700;font-size:12px;text-align:center;line-height:22px'>{s.get('grade','')}</span></td>"
        f"<td style='padding:7px 8px;border-bottom:1px solid #F1F5F9;font-weight:600'>{s.get('name','')}</td>"
        f"<td style='padding:7px 8px;border-bottom:1px solid #F1F5F9;color:#64748B'>{s.get('gradeName','')}</td></tr>"
        for s in suppliers
    )

    summary_html = f"<p style='font-size:13px;color:#475569;line-height:1.5;margin-top:14px'>{summary}</p>" if summary else ""

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
    <h1>\U0001f514 Neuer Kritikalit\u00e4ts-Lead \u2013 {n} Lieferant{'en' if n != 1 else ''}</h1>
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
      <a href="mailto:{email}?subject=Software Technologies \u2013 Ihre Lieferanten-Einstufung&body=Guten Tag {name},%0A%0A"
         style="background:#E8960C;color:#fff;padding:10px 24px;border-radius:6px;font-weight:700;text-decoration:none;font-size:14px">
        Jetzt {name} kontaktieren \u2192
      </a>
    </div>
  </div>
</div>
</body></html>
"""
    return _send(
        to=ALERT_EMAIL,
        subject=f"[Kritikalit\u00e4t] {company or name} \u2013 {n} Lieferant{'en' if n != 1 else ''}",
        html=html,
    )
