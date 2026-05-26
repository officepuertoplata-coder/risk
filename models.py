import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from database import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name  = Column(String(255), nullable=False)
    supplier_name = Column(String(255))
    industry      = Column(String(100))
    industry_label= Column(String(200))
    submitted_by  = Column(String(255), nullable=False)
    email         = Column(String(255), nullable=False)
    phone         = Column(String(100))
    timestamp     = Column(DateTime, default=datetime.utcnow, index=True)

    # Assessment-Daten
    answers        = Column(JSON)   # {"Q1.1": "Ja", "Q1.2": "Nein", ...}
    dimension_scores = Column(JSON) # {"legal": 80, "cyber": 60, ...}
    final_score    = Column(Float)
    color          = Column(String(20))   # green | yellow | red
    top_issues     = Column(JSON)   # [{id, label, score}, ...]
    critical_issues= Column(JSON)   # [{id, label}, ...]
    sales_flag     = Column(Boolean, default=False)

    # KI-Analyse
    analysis       = Column(JSON)   # {exec, impact, p1, p2, p3, pkg, pkgWhy}

    # Status
    email_sent_lead  = Column(Boolean, default=False)
    email_sent_alert = Column(Boolean, default=False)
    pdf_generated    = Column(Boolean, default=False)
