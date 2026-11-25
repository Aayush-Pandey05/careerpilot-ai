import re

from app.schemas.analysis import ReviewReport
from app.tools.skill_matcher import extract_skills, normalize
from app.tools.source_evidence import source_quote

INSTRUCTIONS = """Independently audit email, cover letter, summary and claims against
the ORIGINAL resume, not merely the extracted profile. Look for invented numbers,
experience, skills, degrees and achievements, including claims omitted from the ledger.
Review relevance, tone and actionable recommendations. A truthful proposal to learn a
missing skill is allowed. Reject serious unsupported claims. Minor suggestions may
be approved with suggestions. quality_score is a subjective rubric, not a probability."""


def deterministic_issues(text, materials, job_title=""):
    issues = [c.claim for c in materials.claims if not source_quote(text, c.evidence)]
    prose = "\n".join([materials.email, materials.cover_letter, materials.professional_summary])
    if job_title:
        prose = prose.replace(job_title, "")
    known = {normalize(s) for s in extract_skills(text)}
    # Conservative backup: unsupported named technologies and numerical claims.
    for skill in extract_skills(prose):
        if normalize(skill) not in known:
            issues.append(f"Unsupported technology in application prose: {skill}")
    for number in re.findall(r"\b\d+(?:\.\d+)?%?", prose):
        if number not in text:
            issues.append(f"Unsupported numerical claim: {number}")
    return list(dict.fromkeys(issues))


async def review_application(text, materials, job, llm):
    issues = deterministic_issues(text, materials, job.job_title)
    if llm.mode == "live":
        report = await llm.structured(
            ReviewReport,
            INSTRUCTIONS,
            {"original_resume": text, "application": materials.model_dump(), "job": job.model_dump()},
        )
        issues = list(dict.fromkeys(issues + report.unsupported_claims))
        if issues or report.issues or report.revision_required or not report.approved:
            report.approved = False
            report.revision_required = True
        report.unsupported_claims = issues
        return report
    return ReviewReport(
        approved=not issues,
        quality_score=85 if not issues else 35,
        issues=["Remove unsupported claims."] if issues else [],
        unsupported_claims=issues,
        suggestions=["Offline review uses a limited rule set. Confirm every claim manually."],
        revision_required=bool(issues),
    )
