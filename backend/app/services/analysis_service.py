import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from app.agents.review_agent import review_application
from app.database.models import Analysis, AnalysisResult, Application, ResumeProfileRecord
from app.graph.workflow import build_workflow
from app.schemas.analysis import ApplicationMaterials, SectionUpdate
from app.schemas.job_description import JobProfile
from app.services.llm_service import LLMService


def serialize(row, detail=True):
    return {
        "id": row.id,
        "job_title": row.job_title,
        "company": row.company,
        "created_at": row.created_at.isoformat(),
        "match_score": row.match_score,
        "workflow_status": row.workflow_status,
        "application_id": row.application.id,
        "application_status": row.application.status,
        "result": row.result.payload if detail else {},
    }


def get_analysis(session, analysis_id):
    row = session.get(Analysis, analysis_id)
    if row is None:
        from fastapi import HTTPException

        raise HTTPException(404, "Analysis not found.")
    return row


def list_analyses(session):
    rows = session.scalars(select(Analysis).order_by(Analysis.created_at.desc()).limit(200)).all()
    return [serialize(row, False) for row in rows]


def save_result(session, state):
    job = state.get("job", {})
    row = Analysis(
        job_title=job.get("job_title", state.get("job_title") or "Untitled role"),
        company=job.get("company", state.get("company", "")),
        job_description=state["job_description"],
        match_score=state.get("matching", {}).get("match_score"),
        workflow_status=state.get("workflow_status", "failed"),
    )
    payload = {
        key: state[key]
        for key in [
            "resume",
            "job",
            "matching",
            "application",
            "review",
            "events",
            "errors",
            "revision_count",
            "mode",
        ]
        if key in state
    }
    row.result = AnalysisResult(payload=payload, source_text=state.get("resume_text", ""))
    row.profile = ResumeProfileRecord(profile=state.get("resume", {}))
    row.application = Application(status="Analyzed")
    session.add(row)
    session.commit()
    session.refresh(row)
    return serialize(row)


async def execute_analysis(data, settings, emit=None):
    llm = LLMService(settings)
    graph = build_workflow(llm, settings, emit)
    result = await graph.ainvoke(
        {**data, "errors": [], "events": [], "revision_count": 0, "workflow_status": "running"},
        config={
            "recursion_limit": 30,
            "run_name": "CareerPilot Analysis",
            "tags": ["careerpilot", settings.llm_mode],
            "metadata": {"mode": settings.llm_mode, "version": "1.0.0"},
        },
    )
    result["mode"] = settings.llm_mode
    return result


def streaming_response(data, settings, session_factory):
    import json

    from fastapi.responses import StreamingResponse

    async def stream():
        queue = asyncio.Queue()

        async def emit(event):
            await queue.put(event)

        async def run():
            try:
                await emit(
                    {
                        "type": "workflow_started",
                        "node": "workflow",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
                state = await execute_analysis(data, settings, emit)

                def persist():
                    with session_factory() as session:
                        return save_result(session, state)

                result = await asyncio.to_thread(persist)
                await emit(
                    {
                        "type": "workflow_failed" if state.get("errors") else "workflow_completed",
                        "node": "workflow",
                        "analysis": result,
                    }
                )
            except Exception:
                await emit(
                    {
                        "type": "workflow_failed",
                        "node": "workflow",
                        "message": "Analysis could not be completed or saved. Check PostgreSQL and API configuration.",
                    }
                )
            finally:
                await queue.put(None)

        task = asyncio.create_task(run())
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                    continue
                if event is None:
                    break
                yield f"data: {json.dumps(event)}\n\n"
        finally:
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


LIST_SECTIONS = {"resume_suggestions", "keywords", "project_suggestions", "interview_questions"}
EDITABLE_SECTIONS = {"subject", "email", "cover_letter", "professional_summary"} | LIST_SECTIONS


async def update_section(row, section, settings, content=None):
    """Only regenerate one section; never re-run parsing or matching."""
    if section not in EDITABLE_SECTIONS:
        from fastapi import HTTPException

        raise HTTPException(422, "Unsupported editable section.")
    payload = dict(row.result.payload)
    app = ApplicationMaterials(**payload["application"])
    llm = LLMService(settings)
    generated = content is None
    if content is None:
        if llm.mode == "live":
            draft = await llm.structured(
                SectionUpdate,
                f"Rewrite ONLY the {section}. Use only source facts, no invented claims. Return content.",
                {
                    "source_resume": row.result.source_text,
                    "job": payload["job"],
                    "current_content": getattr(app, section),
                    "feedback": payload.get("review", {}),
                },
            )
            content = draft.content
        else:
            # Offline regeneration edits actual prior content without inventing facts.
            old = getattr(app, section)
            content = "\n".join(old) if isinstance(old, list) else old
            content = content.replace("Dear Hiring Team,", "Dear Recruitment Team,")
    setattr(
        app,
        section,
        [line.strip() for line in content.splitlines() if line.strip()]
        if section in LIST_SECTIONS
        else content,
    )
    report = await review_application(row.result.source_text, app, JobProfile(**payload["job"]), llm)
    payload["application"], payload["review"] = app.model_dump(), report.model_dump()
    payload["edited_at"] = datetime.now(timezone.utc).isoformat()
    payload["edit_origin"] = "generated" if generated else "user"
    row.result.payload = payload
    row.workflow_status = (
        ("approved_with_suggestions" if report.suggestions else "approved")
        if (report.approved and not report.revision_required)
        else "manual_review"
    )
    return row
