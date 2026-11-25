import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.database.database import get_engine, get_session
from app.schemas.analysis import AnalysisResponse, SectionUpdate
from app.services.analysis_service import (
    execute_analysis,
    get_analysis,
    list_analyses,
    save_result,
    serialize,
    streaming_response,
    update_section,
)
from app.services.report_service import generate_report
from app.tools.document_parser import DocumentError, parse_document

router = APIRouter(prefix="/analyses", tags=["Analyses"])


async def read_input(resume: UploadFile, job_description: str, job_title: str, company: str):
    settings = get_settings()
    if not 40 <= len(job_description.strip()) <= settings.max_text_chars:
        raise HTTPException(422, f"Job description must contain 40–{settings.max_text_chars} characters.")
    if len(job_title) > 250 or len(company) > 250:
        raise HTTPException(422, "Job title and company must be at most 250 characters.")
    data = await resume.read(settings.max_upload_mb * 1024 * 1024 + 1)
    try:
        # Preflight gives useful HTTP errors before SSE headers are sent.
        await asyncio.to_thread(
            parse_document,
            data,
            resume.filename or "",
            settings.max_upload_mb * 1024 * 1024,
            settings.max_text_chars,
        )
    except DocumentError as exc:
        raise HTTPException(422, str(exc)) from exc
    finally:
        await resume.close()
    return {
        "file_bytes": data,
        "filename": resume.filename or "",
        "job_description": job_description.strip(),
        "job_title": job_title.strip(),
        "company": company.strip(),
    }


@router.post("", response_model=AnalysisResponse, status_code=201)
async def create_analysis(
    resume: Annotated[UploadFile, File()],
    job_description: Annotated[str, Form()],
    job_title: Annotated[str, Form()] = "",
    company: Annotated[str, Form()] = "",
    session: Session = Depends(get_session),
):
    data = await read_input(resume, job_description, job_title, company)
    state = await execute_analysis(data, get_settings())
    return await asyncio.to_thread(save_result, session, state)


@router.post("/stream")
async def stream_analysis(
    resume: Annotated[UploadFile, File()],
    job_description: Annotated[str, Form()],
    job_title: Annotated[str, Form()] = "",
    company: Annotated[str, Form()] = "",
):
    data = await read_input(resume, job_description, job_title, company)
    return streaming_response(data, get_settings(), sessionmaker(get_engine(), expire_on_commit=False))


@router.get("", response_model=list[AnalysisResponse])
def history(session: Session = Depends(get_session)):
    return list_analyses(session)


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def detail(analysis_id: str, session: Session = Depends(get_session)):
    return serialize(get_analysis(session, analysis_id))


@router.delete("/{analysis_id}", status_code=204)
def delete(analysis_id: str, session: Session = Depends(get_session)):
    session.delete(get_analysis(session, analysis_id))
    session.commit()
    return Response(status_code=204)


@router.get("/{analysis_id}/report")
def report(analysis_id: str, session: Session = Depends(get_session)):
    data = generate_report(serialize(get_analysis(session, analysis_id)))
    return Response(
        data,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="careerpilot-report.pdf"'},
    )


@router.patch("/{analysis_id}/sections/{section}", response_model=AnalysisResponse)
async def edit_section(
    analysis_id: str, section: str, body: SectionUpdate, session: Session = Depends(get_session)
):
    row = await update_section(get_analysis(session, analysis_id), section, get_settings(), body.content)
    session.commit()
    return serialize(row)


@router.post("/{analysis_id}/sections/{section}/regenerate", response_model=AnalysisResponse)
async def regenerate(analysis_id: str, section: str, session: Session = Depends(get_session)):
    row = await update_section(get_analysis(session, analysis_id), section, get_settings())
    session.commit()
    return serialize(row)
