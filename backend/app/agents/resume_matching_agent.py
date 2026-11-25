from app.schemas.analysis import MatchingReasoning, RequirementMatch
from app.tools.score_calculator import calculate_score
from app.tools.skill_matcher import match_requirement, normalize
from app.tools.source_evidence import source_quote

INSTRUCTIONS = """Compare each supplied requirement with the ORIGINAL resume.
Classify it Direct Match, Related Match, Partial Match, Missing or Cannot Determine.
Each nonzero match needs a VERBATIM quote from the resume. State partial/transferable
limitations explicitly. Related technologies are not equivalent. Missing and unknown
get no evidence. Return all requirements exactly once, with unchanged category and
wording. Education and certifications are mandatory. Years of experience and
responsibilities belong to alignment. Never use personal protected characteristics.
Copy requirement wording and category exactly, including capitalization and punctuation.
Copy evidence from a single contiguous source passage, without paraphrases, labels,
quotation marks or ellipses. Preserve punctuation; PDF line wrapping may differ.
Assess project relevance and experience in words; do not calculate a score."""


def requirements_for(job):
    result = []
    for category, values in [
        (
            "mandatory",
            job.required_skills + job.education_requirements + job.certifications + job.eligibility_criteria,
        ),
        ("preferred", job.preferred_skills),
        ("alignment", job.experience_requirements + job.responsibilities),
    ]:
        seen = set()
        for value in values:
            if normalize(value) not in seen:
                result.append((value, category))
                seen.add(normalize(value))
    return result


async def match_resume(text, resume, job, llm):
    expected = requirements_for(job)
    validation_issues = []
    if llm.mode == "live":
        data = {
            "original_resume": text,
            "job": job.model_dump(),
            "requirements": [{"requirement": r, "category": c} for r, c in expected],
        }
        # Give the model one bounded chance to correct malformed quotes or row keys.
        for attempt in range(2):
            reasoning = await llm.structured(MatchingReasoning, INSTRUCTIONS, data)
            lookup = {(r.requirement, r.category): r for r in reasoning.requirements}
            rows, validation_issues = [], []
            for requirement, category in expected:
                row = lookup.get((requirement, category))
                quote = source_quote(text, row.evidence) if row else ""
                if row is None or (
                    row.status in ["Direct Match", "Related Match", "Partial Match"] and not quote
                ):
                    validation_issues.append({"requirement": requirement, "category": category})
                    row = RequirementMatch(
                        requirement=requirement,
                        category=category,
                        status="Cannot Determine",
                        explanation="Valid source evidence was not returned. Please retry the analysis.",
                    )
                else:
                    row.evidence = (
                        quote if row.status in ["Direct Match", "Related Match", "Partial Match"] else ""
                    )
                rows.append(row)
            if not validation_issues or attempt == 1:
                break
            data["validation_feedback"] = {
                "invalid_requirements": validation_issues,
                "instruction": "Return all requirements again with exact wording and categories. "
                "For positive matches, copy a contiguous quote from original_resume. "
                "Use Missing or Cannot Determine when the source does not support a match.",
            }
        reasoning.requirements = rows
    else:
        rows = [match_requirement(r, c, text) for r, c in expected]
        # For natural-language requirements the offline matcher remains conservative.
        for row in rows:
            if row.requirement not in job.required_skills + job.preferred_skills and row.status == "Missing":
                row.status = "Cannot Determine"
                row.explanation = "Offline keyword matching cannot establish this natural-language qualification or responsibility."
        reasoning = MatchingReasoning(
            requirements=rows,
            project_relevance=[
                p for p in resume.projects if any(s.lower() in p.lower() for s in job.required_skills)
            ]
            or ["No project relevance established."],
            experience_analysis="; ".join(resume.experience) or "No explicit work experience found.",
            recommendations=[
                (
                    f"Address {r.requirement}: add truthful evidence if available, otherwise build this skill."
                    if r.requirement in job.required_skills + job.preferred_skills
                    else f"Clarify this requirement and provide accurate supporting evidence: {r.requirement}"
                )
                for r in rows
                if r.status != "Direct Match"
            ],
        )
    score = calculate_score(reasoning.requirements)
    if validation_issues:
        score.update(
            match_score=None,
            breakdown={},
            notice="Score unavailable: resume evidence could not be validated. Please retry the analysis.",
        )
    return {**reasoning.model_dump(), **score, "validation_issues": validation_issues}
