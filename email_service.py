import os
import base64
import httpx
from typing import Optional

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL     = os.getenv("FROM_EMAIL", "onboarding@resend.dev")
FROM_NAME      = os.getenv("FROM_NAME", "YNHALD Supplier Risk")
ALERT_EMAIL    = os.getenv("ALERT_EMAIL", "azajic@sw-tech.net")

SCORE_LABELS = {"green": "Gut gesichert ✅", "yellow": "Handlungsbedarf ⚠️", "red": "Kritisches Risiko 🚨"}


def _send(to: str, subject: str, html: str, pdf_bytes: Optional[bytes] = None) -> bool:
    """Sendet eine E-Mail via Resend REST API."""
    if not RESEND_API_KEY:
        print(f"[EMAIL] Kein API-Key – würde senden an {to}: {subject}")
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
    <div class="score-label">/100 Punkte &nbsp;·&nbsp; {score_lbl}</div>
  </div>
  <div class="body">
    <p>Guten Tag {name},</p>
    <p class="text">vielen Dank für die Teilnahme am YNHALD Supplier Risk Check. Anbei finden Sie Ihren vollständigen PDF-Report für <strong>{company}</strong>.</p>

    <div class="section">
      <div class="section-title">Executive Summary</div>
      <p class="text">{analysis.get('exec', '')}</p>
    </div>

    <div class="section">
      <div class="section-title">Empfohlenes Paket</div>
      <p class="text"><strong>{pkg}</strong> — {analysis.get('pkgWhy', '')}</p>
    </div>

    <div class="cta-box">
      <div class="cta-title">Kostenloses 30-min Erstgespräch buchen</div>
      <p style="font-size:13px;color:#64748B;margin:0 0 14px">Sprechen Sie mit einem unserer Experten über Ihre Ergebnisse.</p>
      <a href="mailto:azajic@sw-tech.net?subject=Erstgespräch – {company}" class="cta-btn">Termin anfragen →</a>
    </div>

    <p class="text">Den vollständigen Report mit allen Details und Handlungsempfehlungen finden Sie im Anhang.</p>
    <p class="text">Mit freundlichen Grüßen,<br><strong>Das YNHALD Team</strong></p>
  </div>
  <div class="footer">YNHALD · azajic@sw-tech.net · Vertraulich</div>
</div>
</body></html>
"""
    return _send(
        to=lead["email"],
        subject=f"Ihr YNHALD Supplier Risk Report – Score: {final}/100",
        html=html,
        pdf_bytes=pdf_bytes,
    )


def send_sales_alert(lead: dict, scores: dict, analysis: dict, assessment_id: str) -> bool:
    """Sales-Alert an das YNHALD-Team."""
    name    = lead.get("name", "")
    company = lead.get("company", "")
    supplier= lead.get("supplier", "—")
    email   = lead.get("email", "")
    phone   = lead.get("phone", "—")
    final   = int(scores.get("final", 0))
    color   = scores.get("color", "red")
    ds      = scores.get("ds", {})
    crits   = scores.get("crits", [])
    pkg     = analysis.get("pkg", "—")
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
    <h1>🔔 Neuer Lead – {score_lbl}</h1>
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

    <h3 style="margin:16px 0 8px;font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:#DC2626">Kritische Lücken</h3>
    <ul style="margin:0;padding-left:20px;font-size:13px">{crit_html}</ul>

    <h3 style="margin:16px 0 6px;font-size:13px;color:#64748B">KI-Einschätzung</h3>
    <p style="font-size:13px;color:#475569;line-height:1.5">{analysis.get('exec', '')}</p>

    <div style="margin-top:24px;padding:16px;background:#FFF7ED;border-radius:8px;text-align:center">
      <a href="mailto:{email}?subject=YNHALD Supplier Risk – Follow-up&body=Guten Tag {name},%0A%0A"
         style="background:#E8960C;color:#fff;padding:10px 24px;border-radius:6px;font-weight:700;text-decoration:none;font-size:14px">
        Jetzt {name} kontaktieren →
      </a>
    </div>
  </div>
</div>
</body></html>
"""
    return _send(
        to=ALERT_EMAIL,
        subject=f"[YNHALD Lead] {company} – Score {final}/100 – {score_lbl}",
        html=html,
    )


# ══════════════════════════════════════════════════════════════
#  KRITIKALITÄTS-EINSTUFUNG  (Software Technologies)
# ══════════════════════════════════════════════════════════════

GRADE_COLORS = {"A": "#DC2626", "B": "#D97706", "C": "#2563EB", "D": "#059669"}


def send_criticality_lead_email(lead: dict, crit: dict, analysis: dict) -> bool:
    """Kritikalitäts-Report an den Kunden."""
    name      = lead.get("name", "")
    supplier  = lead.get("supplier", "—")
    grade     = crit.get("grade", "—")
    grade_name = crit.get("gradeName", "")
    rec       = crit.get("recommendation", {})
    gcol      = GRADE_COLORS.get(grade, "#0A1940")

    p1 = analysis.get("p1", {})
    p2 = analysis.get("p2", {})
    p3 = analysis.get("p3", {})

    html = f"""
<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"><style>
  body {{ font-family: -apple-system, system-ui, sans-serif; color: #0A1940; background: #f4f6fb; margin: 0; padding: 0; }}
  .wrap {{ max-width: 600px; margin: 0 auto; background: #fff; }}
  .header {{ background: #0A1940; padding: 28px 32px; }}
  .header h1 {{ color: #fff; margin: 0; font-size: 22px; }}
  .header p {{ color: #93C5FD; margin: 4px 0 0; font-size: 13px; }}
  .grade-box {{ background: #0A1940; padding: 24px 32px; text-align: center; }}
  .grade-num {{ font-size: 64px; font-weight: 900; color: {gcol}; line-height: 1; }}
  .grade-label {{ font-size: 15px; color: #CBD5E1; margin-top: 4px; }}
  .body {{ padding: 28px 32px; }}
  .section {{ margin-bottom: 22px; }}
  .section-title {{ font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: #1E3FA0; margin-bottom: 8px; }}
  .text {{ font-size: 14px; line-height: 1.6; color: #475569; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
  td {{ padding: 7px 8px; border-bottom: 1px solid #F1F5F9; }}
  td:first-child {{ color: #64748B; width: 150px; }}
  .footer {{ background: #F8FAFC; padding: 20px 32px; text-align: center; font-size: 12px; color: #94A3B8; }}
</style></head>
<body>
<div class="wrap">
  <div class="header">
    <h1>Software Technologies</h1>
    <p>Ihr Kritikalitäts-Report ist bereit</p>
  </div>
  <div class="grade-box">
    <div class="grade-num">{grade}</div>
    <div class="grade-label">Kritikalität · {grade_name}</div>
  </div>
  <div class="body">
    <p>Guten Tag {name},</p>
    <p class="text">vielen Dank für die Einstufung von <strong>{supplier}</strong>. Nachfolgend Ihr individueller Kritikalitäts-Report.</p>

    <div class="section">
      <div class="section-title">Executive Summary</div>
      <p class="text">{analysis.get('exec', '')}</p>
    </div>

    <div class="section">
      <div class="section-title">Was das für Sie bedeutet</div>
      <p class="text">{analysis.get('impact', '')}</p>
    </div>

    <div class="section">
      <div class="section-title">Empfohlenes Risikomanagement</div>
      <table>
        <tr><td>Prüftiefe</td><td>{rec.get('tiefe', '')}</td></tr>
        <tr><td>Re-Assessment</td><td>{rec.get('reass', '')}</td></tr>
        <tr><td>Monitoring</td><td>{rec.get('monitoring', '')}</td></tr>
        <tr><td>Freigabe</td><td>{rec.get('freigabe', '')}</td></tr>
      </table>
    </div>

    <div class="section">
      <div class="section-title">Empfohlene nächste Schritte</div>
      <p class="text"><strong>{p1.get('title', '')}</strong> — {p1.get('text', '')}</p>
      <p class="text"><strong>{p2.get('title', '')}</strong> — {p2.get('text', '')}</p>
      <p class="text"><strong>{p3.get('title', '')}</strong> — {p3.get('text', '')}</p>
    </div>

    <p class="text">Diese Einstufung priorisiert Ihr Risikomanagement. Für ein vollständiges, quellenbasiertes Assessment dieses Lieferanten (OSINT, Fragenkatalog, Expertenbewertung) stehen wir gern bereit.</p>
    <p class="text">Mit freundlichen Grüßen,<br><strong>Ihr Software-Technologies-Team</strong></p>
  </div>
  <div class="footer">Software Technologies · azajic@sw-tech.net · Vertraulich</div>
</div>
</body></html>
"""
    return _send(
        to=lead["email"],
        subject=f"Ihr Kritikalitäts-Report – {supplier} (Stufe {grade})",
        html=html,
    )


def send_criticality_alert(lead: dict, crit: dict, analysis: dict, crit_id: str) -> bool:
    """Alert an das Team: neuer Kritikalitäts-Lead."""
    name      = lead.get("name", "")
    company   = lead.get("company", "")
    supplier  = lead.get("supplier", "—")
    email     = lead.get("email", "")
    phone     = lead.get("phone", "—")
    grade     = crit.get("grade", "—")
    grade_name = crit.get("gradeName", "")
    gcol      = GRADE_COLORS.get(grade, "#0A1940")

    html = f"""
<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"><style>
  body {{ font-family: -apple-system, system-ui, sans-serif; color: #0A1940; background: #f4f6fb; margin:0; }}
  .wrap {{ max-width: 580px; margin: 0 auto; background: #fff; }}
  .header {{ background: {gcol}; padding: 20px 28px; }}
  .header h1 {{ color: #fff; margin: 0; font-size: 18px; }}
  .body {{ padding: 24px 28px; }}
  table {{ border-collapse: collapse; width: 100%; }}
  .meta td {{ padding: 6px 0; font-size: 13px; border-bottom: 1px solid #F1F5F9; }}
  .meta td:first-child {{ color: #64748B; width: 150px; }}
  .meta td:last-child {{ font-weight: 600; }}
  .grade-big {{ font-size: 48px; font-weight: 900; color: {gcol}; }}
</style></head>
<body>
<div class="wrap">
  <div class="header">
    <h1>🔔 Neuer Kritikalitäts-Lead – Stufe {grade}</h1>
  </div>
  <div class="body">
    <div class="grade-big">{grade}<span style="font-size:16px;font-weight:400;color:#94A3B8"> · {grade_name}</span></div>
    <p style="margin:4px 0 20px;color:#64748B;font-size:13px">ID: {crit_id}</p>

    <table class="meta">
      <tr><td>Name</td><td>{name}</td></tr>
      <tr><td>Unternehmen</td><td>{company}</td></tr>
      <tr><td>Eingestufter Lieferant</td><td>{supplier}</td></tr>
      <tr><td>E-Mail</td><td><a href="mailto:{email}">{email}</a></td></tr>
      <tr><td>Telefon</td><td>{phone}</td></tr>
    </table>

    <h3 style="margin:18px 0 6px;font-size:13px;color:#64748B">KI-Einschätzung</h3>
    <p style="font-size:13px;color:#475569;line-height:1.5">{analysis.get('exec', '')}</p>

    <div style="margin-top:24px;padding:16px;background:#FFF7ED;border-radius:8px;text-align:center">
      <a href="mailto:{email}?subject=Software Technologies – Assessment {supplier}&body=Guten Tag {name},%0A%0A"
         style="background:#E8960C;color:#fff;padding:10px 24px;border-radius:6px;font-weight:700;text-decoration:none;font-size:14px">
        Jetzt {name} kontaktieren →
      </a>
    </div>
  </div>
</div>
</body></html>
"""
    return _send(
        to=ALERT_EMAIL,
        subject=f"[Kritikalität] {company or supplier} – Stufe {grade}",
        html=html,
    )
