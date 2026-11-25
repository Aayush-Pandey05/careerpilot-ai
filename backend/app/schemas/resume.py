from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ResumeProfile(StrictModel):
    candidate_name: str = ""
    email: str = ""
    contact: str = ""
    education: list[str] = Field(default_factory=list)
    technical_skills: list[str] = Field(default_factory=list)
    programming_languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    professional_summary: str = ""
    missing_information: list[str] = Field(default_factory=list)
