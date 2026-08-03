import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, HTMLResponse
from sqlalchemy import Column, String, DateTime, Integer, JSON
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from database import get_db, init_db, Base
from models import Assessment
from schemas import AssessmentRequest, AssessmentResponse
from pdf_generator import generate_pdf
from criticality_pdf import generate_criticality_pdf
from email_service import (
    send_lead_email,
    send_sales_alert,
    send_criticality_lead_email,
    send_criticality_alert,
    send_criticality_confirm_email,
    criticality_confirmed_page,
    send_newsletter_confirm_email,
    newsletter_confirmed_page,
)

load_dotenv()

# --- Newsletter Model ---
class NewsletterSubscriber(Base):
    __tablename__ = "newsletter_subscribers"
    id           = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email        = Column(String(255), nullable=False, unique=True)
    company      = Column(String(255))
    source       = Column(String(100))
    confirmed    = Column(Integer, default=0)          # 0 = pending, 1 = bestaetigt (Double-Opt-in)
    token        = Column(String(64))                  # Bestaetigungs-Token
    confirmed_at = Column(DateTime)                    # Zeitpunkt der Bestaetigung
    created_at   = Column(DateTime, default=datetime.utcnow)


# --- Criticality Lead Model (Multi-Lieferant) ---
class CriticalityLead(Base):
    __tablename__ = "criticality_leads"
    id            = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name          = Column(String(255))
    company       = Column(String(255))
    email         = Column(String(255), nullable=False)
    phone         = Column(String(100))
    supplier_count = Column(Integer, default=0)
    top_grade     = Column(String(2))          # kritischste Stufe (A > B > C > D)
    suppliers     = Column(JSON)               # Liste aller Lieferanten mit Einstufung
    summary       = Column(String(2000))       # KI-Gesamteinschaetzung
    confirmed     = Column(Integer, default=0) # 0 = pending (Report noch nicht versendet), 1 = bestaetigt
    token         = Column(String(64))         # Bestaetigungs-Token fuer Report-DOI
    confirmed_at  = Column(DateTime)           # Zeitpunkt der Bestaetigung
    created_at    = Column(DateTime, default=datetime.utcnow)


# --- App Setup ---
app = FastAPI(
    title="YNHALD Supplier Risk Bot API",
    description="Backend fuer den YNHALD Supplier Risk Assessment Bot",
    version="1.0.0",
)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    try:
        init_db()
        from database import engine
        Base.metadata.create_all(bind=engine)
        print("[DB] Tabellen erfolgreich initialisiert.")
    except Exception as e:
        print(f"[DB ERROR] {e}")


# --- Background Tasks ---
def process_assessment_async(assessment_id, data, lead, scores, analysis, db):
    try:
        pdf_bytes = generate_pdf(data)
        print(f"[PDF] Generiert fuer {assessment_id} ({len(pdf_bytes)} Bytes)")

        ok_lead = send_lead_email(lead, scores, analysis, pdf_bytes)
        print(f"[EMAIL] Lead: {'OK' if ok_lead else 'FEHLER'} -> {lead.get('email')}")

        ok_alert = False
        if scores.get("salesFlag") or scores.get("final", 100) < 80:
            ok_alert = send_sales_alert(lead, scores, analysis, assessment_id)
            print(f"[EMAIL] Alert: {'OK' if ok_alert else 'FEHLER'}")

        rec = db.query(Assessment).filter(
            Assessment.id == uuid.UUID(assessment_id)
        ).first()
        if rec:
            rec.email_sent_lead  = ok_lead
            rec.email_sent_alert = ok_alert
            rec.pdf_generated    = True
            db.commit()
    except Exception as e:
        print(f"[BACKGROUND ERROR] {e}")
    finally:
        db.close()


# --- Newsletter Double-Opt-in (zentral, fuer Kritikalitaet + Risikoanalyse) ---

def _public_base_url() -> str:
    """Basis-URL des Backends fuer Bestaetigungslinks."""
    return os.getenv("PUBLIC_BASE_URL", "https://risk-production-5702.up.railway.app").rstrip("/")


import re as _re

_EMAIL_RE = _re.compile(r"^[^@\s]+@([^@\s]+\.[^@\s]+)$")

# einfache Liste bekannter Wegwerf-Domains (erweiterbar)
_DISPOSABLE = {
    "mailinator.com", "10minutemail.com", "guerrillamail.com", "tempmail.com",
    "throwawaymail.com", "yopmail.com", "trashmail.com", "getnada.com",
    "temp-mail.org", "fakeinbox.com", "sharklasers.com", "maildrop.cc",
}


def validate_email_address(email: str) -> tuple:
    """
    Prueft eine E-Mail-Adresse vor dem Versand.
    Rueckgabe: (ok: bool, reason: str)
    Stufe 1: Syntax. Stufe 2: MX-Record der Domain. Stufe 3: keine Wegwerf-Domain.
    Faellt bei fehlender dnspython-Bibliothek sauber auf reine Syntaxpruefung zurueck.
    """
    email = (email or "").strip().lower()
    m = _EMAIL_RE.match(email)
    if not m:
        return False, "syntax"
    domain = m.group(1)

    if domain in _DISPOSABLE:
        return False, "disposable"

    # MX-Record pruefen (wenn dnspython verfuegbar)
    try:
        import dns.resolver  # type: ignore
        try:
            answers = dns.resolver.resolve(domain, "MX", lifetime=4.0)
            if answers and len(answers) > 0:
                return True, "ok"
            return False, "no_mx"
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            return False, "no_mx"
        except Exception:
            # DNS-Timeout o.ae. -> nicht blockieren, Syntax hat gereicht
            return True, "ok_no_dns_check"
    except ImportError:
        # dnspython nicht installiert -> nur Syntaxpruefung
        return True, "ok_syntax_only"


def start_newsletter_doi(db: Session, email: str, company: str = "", source: str = "web") -> str:
    """
    Startet Double-Opt-in: legt (falls noetig) einen unbestaetigten Abonnenten an,
    erzeugt einen Token und verschickt die Bestaetigungsmail.
    Gibt einen Status-String zurueck: 'sent' | 'already_confirmed' | 'resent'.
    Bereits bestaetigte Abonnenten erhalten keine erneute Mail.
    """
    email = (email or "").strip().lower()
    if not email or "@" not in email:
        return "invalid"

    existing = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.email == email
    ).first()

    if existing and existing.confirmed:
        return "already_confirmed"

    token = uuid.uuid4().hex  # 32 Zeichen

    if existing:
        existing.token = token
        existing.source = source or existing.source
        if company:
            existing.company = company
        status = "resent"
    else:
        db.add(NewsletterSubscriber(
            id=str(uuid.uuid4()),
            email=email,
            company=company,
            source=source,
            confirmed=0,
            token=token,
            created_at=datetime.utcnow(),
        ))
        status = "sent"

    db.commit()

    confirm_url = f"{_public_base_url()}/api/newsletter/confirm?token={token}"
    try:
        send_newsletter_confirm_email(email, confirm_url)
        print(f"[NEWSLETTER] Double-Opt-in-Mail an {email} ({status}) via {source}")
    except Exception as e:
        print(f"[NEWSLETTER ERROR] Bestaetigungsmail: {e}")

    return status


# --- Routes ---

@app.get("/health")
def health():
    return {"status": "ok", "service": "YNHALD Supplier Risk Bot", "time": datetime.utcnow().isoformat()}


@app.post("/api/assessment", response_model=AssessmentResponse)
def create_assessment(
    payload: AssessmentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    assessment_id = str(uuid.uuid4())

    rec = Assessment(
        id             = uuid.UUID(assessment_id),
        company_name   = payload.lead.company,
        supplier_name  = payload.lead.supplier or "",
        industry       = payload.industry,
        industry_label = payload.industryLabel,
        submitted_by   = payload.lead.name,
        email          = payload.lead.email,
        phone          = payload.lead.phone or "",
        answers        = payload.answers,
        dimension_scores = payload.scores.ds,
        final_score    = payload.scores.final,
        color          = payload.scores.color,
        top_issues     = [t.model_dump() if hasattr(t,"model_dump") else t for t in payload.scores.top],
        critical_issues= [c.model_dump() if hasattr(c,"model_dump") else c for c in payload.scores.crits],
        sales_flag     = payload.scores.salesFlag,
        analysis       = payload.analysis.model_dump(),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    print(f"[DB] Assessment gespeichert: {assessment_id} | {payload.lead.company} | {int(payload.scores.final)}/100")

    from database import SessionLocal
    bg_db = SessionLocal()

    data_for_pdf = {
        "lead":          payload.lead.model_dump(),
        "industry":      payload.industry,
        "industryLabel": payload.industryLabel,
        "answers":       payload.answers,
        "scores":        payload.scores.model_dump(),
        "analysis":      payload.analysis.model_dump(),
    }

    background_tasks.add_task(
        process_assessment_async,
        assessment_id=assessment_id,
        data=data_for_pdf,
        lead=payload.lead.model_dump(),
        scores=payload.scores.model_dump(),
        analysis=payload.analysis.model_dump(),
        db=bg_db,
    )

    return AssessmentResponse(
        id=assessment_id,
        status="saved",
        email_sent=True,
        message=f"Assessment gespeichert. Report wird an {payload.lead.email} gesendet.",
    )


# --- Criticality Route (Multi-Lieferant) ---

_GRADE_ORDER = {"A": 4, "B": 3, "C": 2, "D": 1}


@app.post("/api/criticality")
def create_criticality(
    payload: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    lead = payload.get("lead", {})
    if not lead.get("email"):
        raise HTTPException(status_code=400, detail="E-Mail fehlt")

    # E-Mail-Vorfilter (Syntax + MX-Domain + keine Wegwerf-Adresse)
    ok, reason = validate_email_address(lead["email"])
    if not ok:
        msg = {
            "syntax": "Bitte eine gueltige E-Mail-Adresse eingeben.",
            "no_mx": "Diese E-Mail-Domain existiert nicht oder kann keine E-Mails empfangen.",
            "disposable": "Bitte eine dauerhafte E-Mail-Adresse verwenden (keine Wegwerf-Adresse).",
        }.get(reason, "Bitte eine gueltige E-Mail-Adresse eingeben.")
        raise HTTPException(status_code=400, detail=msg)

    suppliers = payload.get("suppliers", [])
    if not suppliers:
        raise HTTPException(status_code=400, detail="Keine Lieferanten uebergeben")

    summary = payload.get("summary") or ""
    crit_id = str(uuid.uuid4())
    token   = uuid.uuid4().hex

    # kritischste Stufe bestimmen (A ist am kritischsten)
    top_grade = max(
        (s.get("grade", "D") for s in suppliers),
        key=lambda g: _GRADE_ORDER.get(g, 0),
    )

    rec = CriticalityLead(
        id             = crit_id,
        name           = lead.get("name", ""),
        company        = lead.get("company", ""),
        email          = lead["email"],
        phone          = lead.get("phone", ""),
        supplier_count = len(suppliers),
        top_grade      = top_grade,
        suppliers      = suppliers,
        summary        = summary[:2000],
        confirmed      = 0,        # Report wird erst nach Bestaetigung versendet
        token          = token,
    )
    db.add(rec)
    db.commit()
    print(f"[DB] Criticality gespeichert (pending): {crit_id} | {lead.get('company')} | {len(suppliers)} Lieferanten | Top {top_grade}")

    # Newsletter-Opt-in (eigenes Double-Opt-in)
    if lead.get("newsletter"):
        try:
            start_newsletter_doi(db, lead["email"], lead.get("company", ""), source="kritikalitaet")
        except Exception as e:
            print(f"[NEWSLETTER ERROR] {e}")

    # Lead-Alert an das Team geht SOFORT raus (auch vor Bestaetigung)
    background_tasks.add_task(send_criticality_alert, lead, suppliers, crit_id, summary)

    # Kunde bekommt zunaechst nur die Bestaetigungsmail (Double-Opt-in fuer den Report)
    confirm_url = f"{_public_base_url()}/api/criticality/confirm?token={token}"
    background_tasks.add_task(send_criticality_confirm_email, lead["email"],
                             lead.get("name", ""), len(suppliers), confirm_url)

    return {
        "id": crit_id,
        "status": "pending_confirmation",
        "message": f"Bestaetigungsmail an {lead['email']} gesendet.",
    }


@app.get("/api/criticality/confirm", response_class=HTMLResponse)
def criticality_confirm(token: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Bestaetigt die Report-Anfrage (Double-Opt-in) und versendet dann den Report."""
    rec = db.query(CriticalityLead).filter(CriticalityLead.token == token).first()

    if not rec:
        return HTMLResponse(criticality_confirmed_page("", 0, already=True), status_code=200)

    lead = {
        "name": rec.name, "company": rec.company,
        "email": rec.email, "phone": rec.phone,
    }
    suppliers = rec.suppliers or []
    summary = rec.summary or ""

    if not rec.confirmed:
        rec.confirmed = 1
        rec.confirmed_at = datetime.utcnow()
        rec.token = None
        db.commit()
        print(f"[CRIT] Bestaetigt, Report wird versendet: {rec.id} -> {rec.email}")

        # Jetzt erst PDF erzeugen und Report an den Kunden senden
        pdf_bytes = None
        try:
            pdf_bytes = generate_criticality_pdf(lead, suppliers, summary)
            print(f"[PDF] Kritikalitaets-Report erzeugt ({len(pdf_bytes)} Bytes)")
        except Exception as e:
            print(f"[PDF ERROR] {e}")
        background_tasks.add_task(send_criticality_lead_email, lead, suppliers, summary, pdf_bytes)

    return HTMLResponse(criticality_confirmed_page(rec.email, rec.supplier_count), status_code=200)


@app.get("/api/criticality")
def list_criticality(limit: int = 100, offset: int = 0, db: Session = Depends(get_db)):
    q = db.query(CriticalityLead)
    total = q.count()
    recs = q.order_by(CriticalityLead.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "total": total,
        "items": [
            {
                "id":             r.id,
                "name":           r.name,
                "company":        r.company,
                "email":          r.email,
                "phone":          r.phone,
                "supplier_count": r.supplier_count,
                "top_grade":      r.top_grade,
                "suppliers":      r.suppliers,
                "summary":        r.summary,
                "created_at":     r.created_at.isoformat() if r.created_at else None,
            }
            for r in recs
        ],
    }


@app.delete("/api/criticality/{crit_id}")
def delete_criticality(crit_id: str, db: Session = Depends(get_db)):
    rec = db.query(CriticalityLead).filter(CriticalityLead.id == crit_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Nicht gefunden")
    db.delete(rec)
    db.commit()
    print(f"[DB] Criticality geloescht: {crit_id}")
    return {"status": "deleted", "id": crit_id}


@app.get("/api/assessment/{assessment_id}")
def get_assessment(assessment_id: str, db: Session = Depends(get_db)):
    try:
        rec = db.query(Assessment).filter(
            Assessment.id == uuid.UUID(assessment_id)
        ).first()
    except Exception:
        raise HTTPException(status_code=400, detail="Ungueltige Assessment-ID")

    if not rec:
        raise HTTPException(status_code=404, detail="Assessment nicht gefunden")

    return {
        "id":              str(rec.id),
        "company":         rec.company_name,
        "supplier":        rec.supplier_name,
        "industry":        rec.industry_label,
        "submitted_by":    rec.submitted_by,
        "email":           rec.email,
        "phone":           rec.phone,
        "timestamp":       rec.timestamp.isoformat(),
        "final_score":     rec.final_score,
        "color":           rec.color,
        "sales_flag":      rec.sales_flag,
        "dimension_scores":rec.dimension_scores,
        "top_issues":      rec.top_issues,
        "critical_issues": rec.critical_issues,
        "analysis":        rec.analysis,
        "pdf_generated":   rec.pdf_generated,
        "email_sent_lead": rec.email_sent_lead,
    }


@app.get("/api/assessment/{assessment_id}/pdf")
def download_pdf(assessment_id: str, db: Session = Depends(get_db)):
    try:
        rec = db.query(Assessment).filter(
            Assessment.id == uuid.UUID(assessment_id)
        ).first()
    except Exception:
        raise HTTPException(status_code=400, detail="Ungueltige ID")

    if not rec:
        raise HTTPException(status_code=404, detail="Assessment nicht gefunden")

    data = {
        "lead": {
            "name":     rec.submitted_by,
            "company":  rec.company_name,
            "supplier": rec.supplier_name,
            "email":    rec.email,
            "phone":    rec.phone,
        },
        "industryLabel": rec.industry_label,
        "answers":       rec.answers or {},
        "scores":        {**rec.dimension_scores, "ds": rec.dimension_scores, "final": rec.final_score, "color": rec.color},
        "analysis":      rec.analysis or {},
    }
    pdf_bytes = generate_pdf(data)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="YNHALD_Report_{assessment_id[:8]}.pdf"'},
    )


@app.get("/api/assessments")
def list_assessments(
    limit: int = 100,
    offset: int = 0,
    color: Optional[str] = None,
    sales_flag: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Assessment)
    if color:
        q = q.filter(Assessment.color == color)
    if sales_flag is not None:
        q = q.filter(Assessment.sales_flag == sales_flag)

    total = q.count()
    recs  = q.order_by(Assessment.timestamp.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "items": [
            {
                "id":              str(r.id),
                "company":         r.company_name,
                "supplier":        r.supplier_name,
                "email":           r.email,
                "phone":           getattr(r, "phone", ""),
                "submitted_by":    r.submitted_by,
                "timestamp":       r.timestamp.isoformat(),
                "final_score":     r.final_score,
                "color":           r.color,
                "sales_flag":      r.sales_flag,
                "industry":        r.industry_label,
                "dimension_scores":r.dimension_scores,
                "critical_issues": r.critical_issues,
                "top_issues":      r.top_issues,
                "analysis":        r.analysis,
            }
            for r in recs
        ],
    }


# --- Newsletter ---

@app.post("/api/newsletter")
async def newsletter_signup(payload: dict, db: Session = Depends(get_db)):
    """Startet Double-Opt-in: verschickt eine Bestaetigungsmail.
    Der Kontakt wird erst nach Klick auf den Bestaetigungslink aktiv."""
    email   = payload.get("email", "").strip().lower()
    company = payload.get("company", "").strip()
    source  = payload.get("source", "bot_quiz")

    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Ungueltige E-Mail")

    status = start_newsletter_doi(db, email, company, source=source)

    if status == "already_confirmed":
        return {"status": "already_subscribed", "email": email}
    return {"status": "confirmation_sent", "email": email}


@app.get("/api/newsletter/confirm", response_class=HTMLResponse)
def newsletter_confirm(token: str, db: Session = Depends(get_db)):
    """Bestaetigt die Newsletter-Anmeldung (Double-Opt-in) via Token-Link."""
    sub = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.token == token
    ).first()

    if not sub:
        # Token unbekannt oder bereits verbraucht
        return HTMLResponse(newsletter_confirmed_page(""), status_code=200)

    if not sub.confirmed:
        sub.confirmed = 1
        sub.confirmed_at = datetime.utcnow()
        sub.token = None  # Token entwerten (einmalig nutzbar)
        db.commit()
        print(f"[NEWSLETTER] Bestaetigt: {sub.email}")

        # Jetzt erst in Resend-Audience eintragen
        RESEND_KEY = os.getenv("RESEND_API_KEY", "")
        AUDIENCE_ID = os.getenv("RESEND_AUDIENCE_ID", "")
        if RESEND_KEY and AUDIENCE_ID:
            try:
                import httpx
                httpx.post(
                    f"https://api.resend.com/audiences/{AUDIENCE_ID}/contacts",
                    json={"email": sub.email, "unsubscribed": False},
                    headers={"Authorization": f"Bearer {RESEND_KEY}"},
                    timeout=10,
                )
            except Exception as e:
                print(f"[RESEND AUDIENCE] {e}")

    return HTMLResponse(newsletter_confirmed_page(sub.email), status_code=200)


@app.get("/api/newsletter")
def get_newsletter(db: Session = Depends(get_db)):
    subs = db.query(NewsletterSubscriber).order_by(
        NewsletterSubscriber.created_at.desc()
    ).all()
    return {
        "total": len(subs),
        "items": [
            {
                "id":           s.id,
                "email":        s.email,
                "company":      s.company,
                "source":       s.source,
                "confirmed":    bool(s.confirmed),
                "confirmed_at": s.confirmed_at.isoformat() if s.confirmed_at else None,
                "created_at":   s.created_at.isoformat() if s.created_at else None,
            }
            for s in subs
        ]
    }


# --- Delete Assessment ---

@app.delete("/api/assessment/{assessment_id}")
def delete_assessment(assessment_id: str, db: Session = Depends(get_db)):
    try:
        rec = db.query(Assessment).filter(
            Assessment.id == uuid.UUID(assessment_id)
        ).first()
    except Exception:
        raise HTTPException(status_code=400, detail="Ungueltige ID")

    if not rec:
        raise HTTPException(status_code=404, detail="Nicht gefunden")

    db.delete(rec)
    db.commit()
    print(f"[DB] Assessment geloescht: {assessment_id}")
    return {"status": "deleted", "id": assessment_id}
