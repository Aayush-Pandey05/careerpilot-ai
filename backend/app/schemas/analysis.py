from typing import Literal

from pydantic import Field

from app.schemas.resume import StrictModel

MatchStatus = Literal["Direct Match", "Related Match", "Partial Match", "Missing", "Cannot Determine"]
ApplicationStatus = Literal[
    "Analyzed", "Ready to Apply", "Applied", "Interview Scheduled", "Rejected", "Selected"
]


class RequirementMatch(StrictModel):
    requirement: str
    category: Literal["mandatory", "preferred", "alignment"]
    status: MatchStatus
    evidence: str = ""
    explanation: str = ""


class MatchingReasoning(StrictModel):
    requirements: list[RequirementMatch]
    project_relevance: list[str]
    experience_analysis: str
    recommendations: list[str]


class ApplicationMaterials(StrictModel):
    subject: str
    email: str
    cover_letter: str
    professional_summary: str
    resume_suggestions: list[str]
    keywords: list[str]
    project_suggestions: list[str]
    interview_questions: list[str]
    # A fact ledger ties candidate claims to verbatim resume evidence.
    claims: list["Claim"]


class Claim(StrictModel):
    claim: str
    evidence: str


class ReviewReport(StrictModel):
    approved: bool
    quality_score: int = Field(ge=0, le=100)
    issues: list[str]
    unsupported_claims: list[str]
    suggestions: list[str]
    revision_required: bool


class StatusUpdate(StrictModel):
    status: ApplicationStatus


class SectionUpdate(StrictModel):
    content: str = Field(min_length=1, max_length=20000)


class Event(StrictModel):
    type: str
    node: str
    timestamp: str
    attempt: int = 0
    duration_ms: float | None = None
    message: str = ""


class AnalysisResponse(StrictModel):
    id: str
    job_title: str
    company: str
    created_at: str
    match_score: float | None
    workflow_status: str
    application_id: str
    application_status: ApplicationStatus
    result: dict
