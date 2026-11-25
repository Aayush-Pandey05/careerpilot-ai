from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def new_id():
    return str(uuid4())


def utcnow():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Analysis(Base):
    __tablename__ = "analyses"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    job_title: Mapped[str] = mapped_column(String(250))
    company: Mapped[str] = mapped_column(String(250), default="")
    job_description: Mapped[str] = mapped_column(Text)
    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    workflow_status: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    result: Mapped["AnalysisResult"] = relationship(cascade="all, delete-orphan", uselist=False)
    profile: Mapped["ResumeProfileRecord"] = relationship(cascade="all, delete-orphan", uselist=False)
    application: Mapped["Application"] = relationship(cascade="all, delete-orphan", uselist=False)


class ResumeProfileRecord(Base):
    __tablename__ = "resume_profiles"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), unique=True)
    profile: Mapped[dict] = mapped_column(JSON)


class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), unique=True)
    payload: Mapped[dict] = mapped_column(JSON)
    # Needed for faithful section regeneration, never an uploaded binary.
    source_text: Mapped[str] = mapped_column(Text)


class Application(Base):
    __tablename__ = "applications"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), unique=True)
    status: Mapped[str] = mapped_column(String(50), default="Analyzed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
