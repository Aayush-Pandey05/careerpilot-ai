import re

from app.schemas.resume import ResumeProfile
from app.tools.skill_matcher import extract_skills

INSTRUCTIONS = """Extract explicit candidate facts. Preserve original project and
experience wording. Education must preserve degree, college and year if present.
Do not infer proficiency. List absent or unreadable sections in missing_information."""

HEADINGS = {
    "education": "education",
    "skills": "technical_skills",
    "technical skills": "technical_skills",
    "experience": "experience",
    "internships": "experience",
    "work experience": "experience",
    "projects": "projects",
    "academic projects": "projects",
    "certifications": "certifications",
    "achievements": "achievements",
    "summary": "professional_summary",
}


async def analyze_resume(text: str, llm) -> ResumeProfile:
    if llm.mode == "live":
        return await llm.structured(ResumeProfile, INSTRUCTIONS, {"resume": text})
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    sections = {k: [] for k in set(HEADINGS.values())}
    current = None
    for line in lines[1:]:
        heading = line.lower().rstrip(":")
        if heading in HEADINGS:
            current = HEADINGS[heading]
        elif current:
            sections[current].append(line)
    skills = extract_skills(text)
    email = re.search(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", text)
    return ResumeProfile(
        candidate_name=lines[0] if lines else "",
        email=email.group() if email else "",
        education=sections["education"],
        technical_skills=skills,
        programming_languages=[
            s for s in skills if s in ["Python", "Java", "JavaScript", "TypeScript", "SQL", "C++", "C#"]
        ],
        frameworks=[
            s
            for s in skills
            if s in ["React", "FastAPI", "Django", "Flask", "PyTorch", "TensorFlow", "scikit-learn"]
        ],
        experience=sections["experience"],
        projects=sections["projects"],
        certifications=sections["certifications"],
        achievements=sections["achievements"],
        professional_summary=" ".join(sections["professional_summary"]),
        missing_information=[
            s for s in ["education", "experience", "projects", "certifications"] if not sections[s]
        ],
    )
