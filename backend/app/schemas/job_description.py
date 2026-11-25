from pydantic import Field

from app.schemas.resume import StrictModel


class JobProfile(StrictModel):
    company: str = ""
    job_title: str = ""
    job_category: str = ""
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    education_requirements: list[str] = Field(default_factory=list)
    experience_requirements: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    eligibility_criteria: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)
