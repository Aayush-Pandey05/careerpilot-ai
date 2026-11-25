from app.core.config import get_settings
from app.database.models import Analysis
from app.interview.schemas import InterviewReport, NextTurn, QuestionPlan
from app.services.llm_service import LLMService


def interview_context(analysis: Analysis) -> dict:
    payload = analysis.result.payload
    resume = payload.get("resume") or {}
    job = payload.get("job") or {}

    def snippets(values):
        return [str(value)[:360] for value in (values or [])[:8]]

    return {
        "role": analysis.job_title,
        "job_description": analysis.job_description[:3500],
        "required_skills": snippets(job.get("required_skills")),
        "candidate_skills": snippets(resume.get("technical_skills")),
        "projects": snippets(resume.get("projects")),
        "experience": snippets(resume.get("experience")),
    }


async def plan_interview(context: dict) -> list[dict]:
    plan = await LLMService(get_settings()).structured(
        QuestionPlan,
        "You are planning a spoken mock interview, not generating application materials. "
        "Create ten to fourteen distinct main questions. Use ten for a focused role and add "
        "questions only for distinct resume evidence or role requirements. Mix technical, project, "
        "behavioral and skill-gap topics. Use a neutral hypothetical "
        "when experience is missing. Never assume the candidate has a skill or achievement. "
        "For each question record brief expected concepts for later grading. Keep prompts concise.",
        context,
    )
    questions = [item.model_dump() for item in plan.questions]
    if len({q["question"].casefold() for q in questions}) != len(questions):
        raise ValueError("The plan contains duplicate questions.")
    return questions


async def adapt_interview(plan, turns, latest) -> NextTurn:
    current = plan[latest["number"] - 1]
    next_item = plan[latest["number"]] if latest["number"] < len(plan) else None
    return await LLMService(get_settings()).structured(
        NextTurn,
        "Conduct a spoken practice interview. If a useful clarification is needed and "
        "follow_up_allowed is true, return one brief follow_up, otherwise return an empty string. "
        "If a next topic is provided, optionally tailor its question to the latest answer while "
        "preserving its topic and expected concepts. Do not invent experience or reveal the rubric. "
        "Return an empty next_question when no next topic exists.",
        {
            "current_topic": current["topic"],
            "latest_turn": latest,
            "covered_topics": [item["topic"] for item in plan[: latest["number"] - 1]],
            "main_answer": turns[-1]["answer"] if latest["follow_up"] else "",
            "next_topic": next_item,
            "follow_up_allowed": not latest["follow_up"],
        },
    )


async def evaluate_interview(plan, turns) -> dict:
    report = await LLMService(get_settings()).structured(
        InterviewReport,
        "Evaluate this practice interview. Write exactly one feedback item per main question, "
        "incorporating its follow-up if present. Use the stored expected concepts but accept valid "
        "alternatives. Ratings: 1 little relevant evidence, 2 partial, 3 sound, 4 specific and well "
        "reasoned. Grade what the candidate said. For evidence, copy an exact excerpt from that "
        "question's candidate answers, or return an empty string. Do not infer vocal delivery or "
        "predict hiring outcomes. Give specific practice tasks.",
        {"plan": plan, "transcript": turns},
    )
    if sorted(item.number for item in report.feedback) != list(range(1, len(plan) + 1)):
        raise ValueError("The report does not cover every question.")
    for item in report.feedback:
        if not any(item.evidence in t["answer"] for t in turns if t["number"] == item.number):
            item.evidence = ""
    report.feedback.sort(key=lambda item: item.number)
    return report.model_dump()
