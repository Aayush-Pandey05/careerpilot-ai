import argparse
import asyncio

from app.core.config import get_settings
from app.graph.workflow import build_workflow
from app.schemas.analysis import RequirementMatch
from app.services.llm_service import LLMService, configure_tracing
from app.tools.score_calculator import calculate_score
from scripts.evaluation_cases import CASES


def predict(inputs):
    settings = get_settings()
    llm = LLMService(settings)
    overrides = None
    if inputs.get("inject_claim"):
        from app.agents.application_generator import generate_application
        from app.schemas.job_description import JobProfile
        from app.schemas.resume import ResumeProfile

        async def controlled_generation(s):
            count = s.get("revision_count", 0) + int(bool(s.get("review")))
            app = await generate_application(
                s["resume_text"],
                ResumeProfile(**s["resume"]),
                JobProfile(**s["job"]),
                s["matching"],
                llm,
                s.get("review"),
            )
            if count == 0:
                app.email += "\nI achieved a 99% improvement using AWS."
            return {"application": app.model_dump(), "revision_count": count}

        overrides = {"generation": controlled_generation}
    return asyncio.run(
        build_workflow(llm, settings, overrides=overrides).ainvoke(
            {
                "resume_text": inputs["resume"],
                "job_description": inputs["job"],
                "errors": [],
                "events": [],
                "revision_count": 0,
            },
            config={
                "run_name": "CareerPilot Evaluation",
                "recursion_limit": 30,
                "tags": ["evaluation", settings.llm_mode],
            },
        )
    )


def checks(result, expected, inputs):
    match = result.get("matching", {})
    rows = [RequirementMatch(**r) for r in match.get("requirements", [])]
    score = match.get("match_score")
    correct_range = (
        score is None
        if expected["min_score"] is None
        else (score is not None and expected["min_score"] <= score <= expected["max_score"])
    )
    return {
        "workflow_completed": not result.get("errors")
        and result.get("workflow_status", "").startswith("approved"),
        "extraction_name": result.get("resume", {}).get("candidate_name") == expected["candidate"],
        "requirements_extracted": set(expected["required"]).issubset(
            result.get("job", {}).get("required_skills", [])
        ),
        "expected_score": correct_range,
        "score_arithmetic": calculate_score(rows)["match_score"] == score,
        "evidence_grounding": all(
            r.evidence and r.evidence in inputs["resume"]
            for r in rows
            if r.status in ["Direct Match", "Related Match", "Partial Match"]
        ),
        "email_role_relevance": result.get("job", {}).get("job_title", "!")
        in result.get("application", {}).get("email", ""),
        "review_recovery": result.get("revision_count", 0) >= 1 if expected.get("revision") else True,
    }


def evaluator(run, example):
    result = checks(run.outputs, example.outputs, example.inputs)
    return {"results": [{"key": key, "score": float(value)} for key, value in result.items()]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", action="store_true", help="Run checks without uploading to LangSmith")
    args = parser.parse_args()
    if args.local:
        failed = 0
        for case in CASES:
            values = checks(predict(case), case["expected"], case)
            print(case["name"], values)
            failed += sum(not v for v in values.values())
        raise SystemExit(1 if failed else 0)
    settings = get_settings()
    if not settings.langsmith_api_key.get_secret_value():
        raise SystemExit("Configure LANGSMITH_API_KEY before cloud evaluation.")
    configure_tracing(settings)
    from langsmith import Client, evaluate

    client = Client(api_key=settings.langsmith_api_key.get_secret_value())
    evaluate(
        predict,
        data="careerpilot-synthetic-v1",
        evaluators=[evaluator],
        experiment_prefix=f"careerpilot-{settings.llm_mode}",
        max_concurrency=1,
        client=client,
    )


if __name__ == "__main__":
    main()
