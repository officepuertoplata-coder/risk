import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from database import get_db, init_db
from models import Assessment
from schemas import AssessmentRequest, AssessmentResponse
from pdf_generator import generate_pdf
from email_service import send_lead_email, send_sales_alert

load_dotenv()

# ─── App Setup ────────────────────────────────────────────────
app = FastAPI(
    title="YNHALD Supplier Risk Bot API",
    description="Backend für den YNHALD Supplier Risk Assessment Bot",
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
    """Datenbank-Tabellen beim Start erstellen."""
    try:
        init_db()
        print("[DB] Tabellen erfolgreich initialisiert.")
    except Exception as e:
        print(f"[DB ERROR] {e}")


# ─── Background Tasks ─────────────────────────────────────────
def process_assessment_async(
    assessment_id: str,
    data: dict,
    lead: dict,
    scores: dict,
    analysis: dict,
    db: Session,
):
    """PDF generieren + E-Mails senden (läuft im Hintergrund)."""
    try:
        # PDF generieren
        pdf_bytes = generate_pdf(data)
        print(f"[PDF] Generiert für Assessment {assessment_id} ({len(pdf_bytes)} Bytes)")

        # E-Mail an den Lead (mit PDF-Anhang)
        ok_lead = send_lead_email(lead, scores, analysis, pdf_bytes)
        print(f"[EMAIL] Lead-E-Mail {'gesendet' if ok_lead else 'FEHLER'}: {lead.get('email')}")

        # Sales-Alert wenn salesFlag
        ok_alert = False
        if scores.get("salesFlag") or scores.get("final", 100) < 80:
            ok_alert = send_sales_alert(lead, scores, analysis, assessment_id)
            print(f"[EMAIL] Sales-Alert {'gesendet' if ok_alert else 'FEHLER'}")

        # DB-Status aktualisieren
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


# ─── Routes ───────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "YNHALD Supplier Risk Bot", "time": datetime.utcnow().isoformat()}


@app.post("/api/assessment", response_model=AssessmentResponse)
def create_assessment(
    payload: AssessmentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Speichert ein abgeschlossenes Assessment, löst PDF-Generierung
    und E-Mail-Versand als Background-Task aus.
    """
    assessment_id = str(uuid.uuid4())

    # ── In DB speichern ──────────────────────────────────────
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
        top_issues     = [t.model_dump() if hasattr(t, "model_dump") else t for t in payload.scores.top],
        critical_issues= [c.model_dump() if hasattr(c, "model_dump") else c for c in payload.scores.crits],
        sales_flag     = payload.scores.salesFlag,
        analysis       = payload.analysis.model_dump(),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    print(f"[DB] Assessment gespeichert: {assessment_id} | {payload.lead.company} | {int(payload.scores.final)}/100")

    # ── Background-Task starten ──────────────────────────────
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


@app.get("/api/assessment/{assessment_id}")
def get_assessment(assessment_id: str, db: Session = Depends(get_db)):
    """Gibt ein Assessment anhand der ID zurück."""
    try:
        rec = db.query(Assessment).filter(
            Assessment.id == uuid.UUID(assessment_id)
        ).first()
    except Exception:
        raise HTTPException(status_code=400, detail="Ungültige Assessment-ID")

    if not rec:
        raise HTTPException(status_code=404, detail="Assessment nicht gefunden")

    return {
        "id":              str(rec.id),
        "company":         rec.company_name,
        "supplier":        rec.supplier_name,
        "industry":        rec.industry_label,
        "submitted_by":    rec.submitted_by,
        "email":           rec.email,
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
    """Generiert und liefert den PDF-Report on-demand."""
    try:
        rec = db.query(Assessment).filter(
            Assessment.id == uuid.UUID(assessment_id)
        ).first()
    except Exception:
        raise HTTPException(status_code=400, detail="Ungültige ID")

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
        headers={
            "Content-Disposition": f'attachment; filename="YNHALD_Report_{assessment_id[:8]}.pdf"'
        },
    )


@app.get("/api/assessments")
def list_assessments(
    limit: int = 20,
    offset: int = 0,
    color: Optional[str] = None,
    sales_flag: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """Listet alle Assessments (für internes Dashboard)."""
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
                "id":          str(r.id),
                "company":     r.company_name,
                "supplier":    r.supplier_name,
                "email":       r.email,
                "timestamp":   r.timestamp.isoformat(),
                "final_score": r.final_score,
                "color":       r.color,
                "sales_flag":  r.sales_flag,
                "industry":    r.industry_label,
            }
            for r in recs
        ],
    }


# ─── Newsletter ────────────────────────────────────────────────

from sqlalchemy import Column, String as SAString, DateTime as SADateTime
import uuid as _uuid

class NewsletterSubscriber(Base):
    __tablename__ = "newsletter_subscribers"
    id         = Column(SAString(36), primary_key=True, default=lambda: str(_uuid.uuid4()))
    email      = Column(SAString(255), nullable=False, unique=True)
    company    = Column(SAString(255))
    created_at = Column(SADateTime, default=datetime)
    source     = Column(SAString(100))  # "bot_quiz", "landing", etc.


@app.post("/api/newsletter")
async def newsletter_signup(
    payload: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    email   = payload.get("email", "").strip().lower()
    company = payload.get("company", "").strip()
    source  = payload.get("source", "bot_quiz")

    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Ungültige E-Mail")

    # Check duplicate
    existing = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.email == email
    ).first()
    if existing:
        return {"status": "already_subscribed", "email": email}

    sub = NewsletterSubscriber(
        id=str(_uuid.uuid4()),
        email=email,
        company=company,
        source=source,
        created_at=datetime.utcnow(),
    )
    db.add(sub)
    db.commit()

    # Add to Resend Audience
    RESEND_API_KEY_VAL = os.getenv("RESEND_API_KEY", "")
    AUDIENCE_ID = os.getenv("RESEND_AUDIENCE_ID", "")
    if RESEND_API_KEY_VAL and AUDIENCE_ID:
        try:
            import httpx as _httpx
            _httpx.post(
                f"https://api.resend.com/audiences/{AUDIENCE_ID}/contacts",
                json={"email": email, "unsubscribed": False},
                headers={"Authorization": f"Bearer {RESEND_API_KEY_VAL}"},
                timeout=10,
            )
        except Exception as e:
            print(f"[RESEND AUDIENCE] {e}")

    print(f"[NEWSLETTER] Neue Anmeldung: {email}")
    return {"status": "subscribed", "email": email}


@app.get("/api/newsletter")
def get_newsletter(db: Session = Depends(get_db)):
    subs = db.query(NewsletterSubscriber).order_by(
        NewsletterSubscriber.created_at.desc()
    ).all()
    return {
        "total": len(subs),
        "items": [
            {
                "id": s.id,
                "email": s.email,
                "company": s.company,
                "source": s.source,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in subs
        ]
    }
