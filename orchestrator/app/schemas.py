from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional
from datetime import datetime
from enum import Enum


class SubmissionStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    complete = "complete"
    failed = "failed"
    manual_review = "manual_review"
    insufficient_data = "insufficient_data"


class IntakeRequest(BaseModel):
    company_name: str
    company_url: str
    email: EmailStr


class IntakeResponse(BaseModel):
    job_id: str
    message: str


class JobStatus(BaseModel):
    job_id: str
    status: SubmissionStatus
    created_at: datetime
    completed_at: Optional[datetime] = None


class OperationalSnapshot(BaseModel):
    technology_posture: str
    digital_maturity: str
    detected_technologies: list[str]
    infrastructure_signals: str


class MarketPosition(BaseModel):
    business_category: str
    public_reputation: str
    competitive_signals: str
    growth_indicators: str


class DataConfidence(BaseModel):
    overall_score: str
    sources_used: list[str]
    sources_unavailable: list[str]
    freshness: str


class OperationalProfile(BaseModel):
    company_name: str
    industry_classification: str
    location: str
    estimated_size: str
    operational_snapshot: OperationalSnapshot
    market_position: MarketPosition
    strategic_observations: list[str]
    identified_gaps: list[str]
    data_confidence: DataConfidence


class ProfileResponse(BaseModel):
    profile: OperationalProfile
    company_name: str
    created_at: datetime


class FeedbackRequest(BaseModel):
    rating: int
    comment: Optional[str] = None
