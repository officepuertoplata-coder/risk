from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
import uuid


class LeadData(BaseModel):
    name: str
    company: str
    supplier: Optional[str] = ""
    email: str
    phone: Optional[str] = ""


class PriorityAction(BaseModel):
    title: str
    text: str


class Analysis(BaseModel):
    exec: str
    impact: str
    p1: PriorityAction
    p2: PriorityAction
    p3: PriorityAction
    pkg: str
    pkgWhy: str


class ScoreData(BaseModel):
    ds: Dict[str, float]    # dimension scores
    final: float
    color: str              # green | yellow | red
    crits: list             # critical issues
    top: list               # top 3 issues
    salesFlag: bool


class AssessmentRequest(BaseModel):
    lead: LeadData
    industry: str
    industryLabel: str
    answers: Dict[str, str]
    scores: ScoreData
    analysis: Analysis


class AssessmentResponse(BaseModel):
    id: str
    status: str
    email_sent: bool
    message: str
