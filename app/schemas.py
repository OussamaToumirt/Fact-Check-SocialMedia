from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


ClaimVerdict = Literal[
    "supported",
    "contradicted",
    "mixed",
    "unverifiable",
    "not_a_factual_claim",
]


OverallVerdict = Literal["accurate", "mostly_accurate", "mixed", "misleading", "false", "unverifiable"]


DangerCategory = Literal[
    "medical_misinformation",
    "financial_scam",
    "illegal_instructions",
    "self_harm",
    "dangerous_challenge",
    "hate_or_harassment",
    "privacy_or_doxxing",
    "other",
]


class Source(BaseModel):
    title: str
    publisher: Optional[str] = None
    url: str
    accessed_at: Optional[str] = None


class ClaimCheck(BaseModel):
    claim: str = Field(..., description="A single checkable factual claim.")
    verdict: ClaimVerdict
    confidence: int = Field(..., ge=0, le=100)
    explanation: str = Field(..., description="Why the verdict was chosen, with key evidence.")
    correction: Optional[str] = Field(None, description="If wrong/misleading, what the accurate claim should be.")
    sources: List[Source] = Field(default_factory=list)


class DangerItem(BaseModel):
    category: DangerCategory
    severity: int = Field(..., ge=0, le=5)
    description: str
    mitigation: Optional[str] = None


class FactCheckReport(BaseModel):
    generated_at: datetime
    overall_score: int = Field(..., ge=0, le=100)
    overall_verdict: OverallVerdict
    summary: str
    sources_used: List[Source] = Field(default_factory=list)
    whats_right: List[str] = Field(default_factory=list)
    whats_wrong: List[str] = Field(default_factory=list)
    missing_context: List[str] = Field(default_factory=list)
    claims: List[ClaimCheck] = Field(default_factory=list)
    danger: List[DangerItem] = Field(default_factory=list)
    limitations: Optional[str] = None


Provider = Literal["gemini", "openai", "deepseek"]


class AnalyzeRequest(BaseModel):
    url: str
    output_language: str = Field("ar", description="BCP-47 language code, e.g. ar, en, fr.")
    force: bool = Field(False, description="If true, re-run analysis and overwrite cached result for this URL+language.")
    provider: Provider = "gemini"
    api_key: Optional[str] = None


JobStatus = Literal[
    "queued",
    "downloading",
    "transcribing",
    "fact_checking",
    "completed",
    "failed",
]


class Job(BaseModel):
    id: str
    url: str
    output_language: str = "ar"
    provider: Provider = "gemini"
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    progress: int = Field(0, ge=0, le=100)
    error: Optional[str] = None
    transcript: Optional[str] = None
    report: Optional[FactCheckReport] = None


class HistoryItem(BaseModel):
    id: str
    url: str
    output_language: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    overall_score: Optional[int] = None
    overall_verdict: Optional[OverallVerdict] = None
    summary: Optional[str] = None
