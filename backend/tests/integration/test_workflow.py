import asyncio

from app.graph.workflow import build_workflow
from app.schemas.analysis import ReviewReport
from tests.conftest import run


def initial(resume, job):
    return {"resume_text": resume, "job_description": job, "events": [], "errors": [], "revision_count": 0}


def test_full_workflow_and_parallel_start(resume_text, job_text, settings, llm):
    events = []

    async def emit(e):
        events.append(e)

    state = run(build_workflow(llm, settings, emit).ainvoke(initial(resume_text, job_text)))
    assert state["workflow_status"].startswith("approved")
    assert not state["errors"] and state["matching"]["match_score"] > 0
    assert state["application"]["email"] and state["review"]["approved"]
    assert all(r["evidence"] in resume_text for r in state["matching"]["requirements"] if r["evidence"])
    types = [e["type"] for e in events]
    assert types.index("matching_started") > types.index("resume_analyzer_completed")
    assert types.index("matching_started") > types.index("jd_analyzer_completed")


def test_branches_actually_overlap(resume_text, job_text, settings, llm):
    async def scenario():
        entered = set()
        both = asyncio.Event()
        from app.agents.job_description_analyzer import analyze_job
        from app.agents.resume_analyzer import analyze_resume

        async def resume(s):
            entered.add("resume")
            if len(entered) == 2:
                both.set()
            await asyncio.wait_for(both.wait(), 2)
            return {"resume": (await analyze_resume(s["resume_text"], llm)).model_dump()}

        async def job(s):
            entered.add("job")
            if len(entered) == 2:
                both.set()
            await asyncio.wait_for(both.wait(), 2)
            return {"job": (await analyze_job(s["job_description"], llm)).model_dump()}

        return await build_workflow(
            llm, settings, overrides={"resume_analyzer": resume, "jd_analyzer": job}
        ).ainvoke(initial(resume_text, job_text))

    assert not run(scenario())["errors"]


def test_revision_limit_routes_to_manual_review(resume_text, job_text, settings, llm):
    calls = []

    async def reject(s):
        calls.append(s["revision_count"])
        return {
            "review": ReviewReport(
                approved=False,
                quality_score=20,
                issues=["Unsupported claim"],
                unsupported_claims=["False achievement"],
                suggestions=[],
                revision_required=True,
            ).model_dump()
        }

    result = run(
        build_workflow(llm, settings, overrides={"review": reject}).ainvoke(initial(resume_text, job_text))
    )
    assert calls == [0, 1, 2]
    assert result["revision_count"] == 2 and result["workflow_status"] == "manual_review"


def test_controlled_injected_claim_is_revised(resume_text, job_text, settings, llm):
    from app.agents.application_generator import generate_application
    from app.schemas.job_description import JobProfile
    from app.schemas.resume import ResumeProfile

    async def generate(s):
        revision = s.get("revision_count", 0) + int(bool(s.get("review")))
        materials = await generate_application(
            s["resume_text"],
            ResumeProfile(**s["resume"]),
            JobProfile(**s["job"]),
            s["matching"],
            llm,
            s.get("review"),
        )
        if revision == 0:
            materials.email += "\nI achieved a 99% improvement using AWS."
        return {"application": materials.model_dump(), "revision_count": revision}

    result = run(
        build_workflow(llm, settings, overrides={"generation": generate}).ainvoke(
            initial(resume_text, job_text)
        )
    )
    assert result["revision_count"] == 1
    assert result["review"]["approved"] and "99%" not in result["application"]["email"]


def test_provider_failure_returns_failed_result(resume_text, job_text, settings, llm):
    async def fail(s):
        raise RuntimeError("sensitive provider error")

    result = run(
        build_workflow(llm, settings, overrides={"resume_analyzer": fail}).ainvoke(
            initial(resume_text, job_text)
        )
    )
    assert result["workflow_status"] == "failed"
    assert "sensitive" not in str(result["errors"])
