from app.schemas.analysis import ApplicationMaterials, Claim

INSTRUCTIONS = """Write a concise customized application email with subject,
cover letter, summary, resume suggestions, project suggestions and interview questions.
Every factual candidate claim MUST appear in the claims ledger with its VERBATIM
original resume evidence. Do not claim missing job skills. Suggestions to learn a
skill are distinct from claiming proficiency. No invented results, metrics or dates.
Incorporate review feedback. Never send mail or submit an application."""


async def generate_application(text, resume, job, matching, llm, feedback=None):
    if llm.mode == "live":
        return await llm.structured(
            ApplicationMaterials,
            INSTRUCTIONS,
            {
                "original_resume": text,
                "candidate": resume.model_dump(),
                "job": job.model_dump(),
                "matching": matching,
                "review_feedback": feedback or {},
            },
        )
    direct = [
        r["requirement"]
        for r in matching["requirements"]
        if r["status"] == "Direct Match" and r["category"] != "alignment"
    ]
    skills = ", ".join(direct) or "the background described in my attached resume"
    name = resume.candidate_name or "[Your name]"
    employer = job.company or "your organization"
    project = resume.projects[0] if resume.projects else ""
    summary = (
        f"My resume includes {skills}." if direct else "Please review my attached resume for my background."
    )
    body = (
        f"Dear Hiring Team,\n\nI am applying for the {job.job_title} position at {employer}. "
        f"{summary}\n\n"
        + (f"One relevant project from my resume: {project}\n\n" if project else "")
        + f"I would welcome the opportunity to discuss how my background fits this role. "
        f"Thank you for your consideration.\n\nKind regards,\n{name}"
    )
    evidence = [r["evidence"] for r in matching["requirements"] if r["status"] == "Direct Match"]
    if project:
        evidence.append(project)
    claims = [Claim(claim=e, evidence=e) for e in dict.fromkeys(evidence) if e and e in text]
    return ApplicationMaterials(
        subject=f"Application for {job.job_title} — {name}",
        email=body,
        cover_letter=body.replace("I am applying", "I am writing to express my interest in applying"),
        professional_summary=summary,
        resume_suggestions=matching["recommendations"],
        keywords=direct,
        project_suggestions=[
            f"Highlight this existing project with your role and verified outcome: {p}"
            for p in resume.projects
        ],
        interview_questions=[
            f"How have you used {s}? Explain an example and a limitation." for s in job.required_skills
        ]
        + [f"Explain the design decisions in: {p}" for p in resume.projects]
        + [
            f"How would you start learning {r['requirement']}?"
            for r in matching["requirements"]
            if r["status"] == "Missing" and r["requirement"] in job.required_skills + job.preferred_skills
        ],
        claims=claims,
    )
