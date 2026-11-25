from datetime import datetime, timezone
from time import perf_counter

from langgraph.graph import END, START, StateGraph
from langsmith import traceable

from app.agents.application_generator import generate_application
from app.agents.job_description_analyzer import analyze_job
from app.agents.resume_analyzer import analyze_resume
from app.agents.resume_matching_agent import match_resume
from app.agents.review_agent import review_application
from app.graph.state import WorkflowState
from app.schemas.analysis import ApplicationMaterials
from app.schemas.job_description import JobProfile
from app.schemas.resume import ResumeProfile
from app.tools.document_parser import parse_document


def build_workflow(llm, settings, emit=None, overrides=None):
    """Build a real graph. Overrides are dependency injection for controlled tests."""
    overrides = overrides or {}

    async def parse(s):
        text = s.get("resume_text") or parse_document(
            s["file_bytes"], s["filename"], settings.max_upload_mb * 1024 * 1024, settings.max_text_chars
        )
        return {"resume_text": text}

    async def resume(s):
        return {"resume": (await analyze_resume(s["resume_text"], llm)).model_dump()}

    async def job(s):
        return {
            "job": (
                await analyze_job(s["job_description"], llm, s.get("job_title", ""), s.get("company", ""))
            ).model_dump()
        }

    async def matching(s):
        if s.get("errors"):
            return {}
        return {
            "matching": await match_resume(
                s["resume_text"], ResumeProfile(**s["resume"]), JobProfile(**s["job"]), llm
            )
        }

    async def generation(s):
        count = s.get("revision_count", 0) + (1 if s.get("review") else 0)
        materials = await generate_application(
            s["resume_text"],
            ResumeProfile(**s["resume"]),
            JobProfile(**s["job"]),
            s["matching"],
            llm,
            s.get("review"),
        )
        return {"application": materials.model_dump(), "revision_count": count}

    async def review(s):
        result = await review_application(
            s["resume_text"], ApplicationMaterials(**s["application"]), JobProfile(**s["job"]), llm
        )
        return {"review": result.model_dump()}

    async def finalize(s):
        if s.get("errors"):
            status = "failed"
        elif s["review"]["approved"] and not s["review"]["revision_required"]:
            status = "approved_with_suggestions" if s["review"]["suggestions"] else "approved"
        else:
            status = "manual_review"
        return {"workflow_status": status}

    def wrapped(name, function):
        async def execute(s):
            attempt = s.get("revision_count", 0) + int(name == "generation" and bool(s.get("review")))
            start = perf_counter()
            events = []

            async def event(kind, message="", duration=None):
                item = {
                    "type": f"{name}_{kind}",
                    "node": name,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "attempt": attempt,
                    "duration_ms": duration,
                    "message": message,
                }
                events.append(item)
                if emit:
                    await emit(item)

            await event("started")
            try:
                operation = traceable(name=f"{name}_operation")(overrides.get(name, function))
                output = await operation(s)
                await event("completed", duration=round((perf_counter() - start) * 1000, 2))
                return {**output, "events": events}
            except Exception:
                # Exceptions are visible to traces; never expose provider error bodies to clients.
                await event("failed", "This stage failed. Check configuration or try again.")
                return {
                    "errors": [f"{name} failed. Check configuration, provider access or input data."],
                    "events": events,
                }

        return execute

    graph = StateGraph(WorkflowState)
    for name, fn in [
        ("parsing", parse),
        ("resume_analyzer", resume),
        ("jd_analyzer", job),
        ("matching", matching),
        ("generation", generation),
        ("review", review),
        ("finalize", finalize),
    ]:
        graph.add_node(name, wrapped(name, fn))
    graph.add_edge(START, "parsing")
    graph.add_conditional_edges(
        "parsing",
        lambda s: ["finalize"] if s.get("errors") else ["resume_analyzer", "jd_analyzer"],
        {"finalize": "finalize", "resume_analyzer": "resume_analyzer", "jd_analyzer": "jd_analyzer"},
    )
    graph.add_edge(["resume_analyzer", "jd_analyzer"], "matching")
    graph.add_conditional_edges("matching", lambda s: "finalize" if s.get("errors") else "generation")
    graph.add_conditional_edges("generation", lambda s: "finalize" if s.get("errors") else "review")

    def route(s):
        if s.get("errors"):
            return "finalize"
        report = s["review"]
        if report["approved"] and not report["revision_required"]:
            return "finalize"
        return "generation" if s.get("revision_count", 0) < settings.max_revision_attempts else "finalize"

    graph.add_conditional_edges("review", route)
    graph.add_edge("finalize", END)
    return graph.compile()
