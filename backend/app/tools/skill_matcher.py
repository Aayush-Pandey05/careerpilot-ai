import re

from langsmith import traceable

from app.schemas.analysis import RequirementMatch

ALIASES = {
    "js": "javascript",
    "sklearn": "scikit-learn",
    "postgresql": "postgres",
    "pytorch": "pytorch",
    "tf": "tensorflow",
    "ml": "machine learning",
    "nlp": "natural language processing",
    "react.js": "react",
    "node.js": "nodejs",
}
SKILLS = [
    "Python",
    "JavaScript",
    "TypeScript",
    "Java",
    "C++",
    "C#",
    "SQL",
    "Postgres",
    "React",
    "Next.js",
    "FastAPI",
    "Django",
    "Flask",
    "Git",
    "Docker",
    "Kubernetes",
    "AWS",
    "Azure",
    "TensorFlow",
    "PyTorch",
    "scikit-learn",
    "pandas",
    "NumPy",
    "Machine Learning",
    "NLP",
    "REST",
    "HTML",
    "CSS",
    "Excel",
    "Power BI",
    "Linux",
]
RELATED = {
    "tensorflow": ["pytorch"],
    "pytorch": ["tensorflow"],
    "fastapi": ["flask", "django"],
    "postgres": ["sql"],
    "aws": ["azure"],
    "azure": ["aws"],
    "typescript": ["javascript"],
}


def normalize(value: str) -> str:
    value = value.strip().lower()
    return ALIASES.get(value, value)


def contains(text: str, term: str) -> bool:
    names = [term] + [a for a, target in ALIASES.items() if target == normalize(term)]
    return any(re.search(r"(?<![\w])" + re.escape(n) + r"(?![\w+#])", text, re.I) for n in names)


def extract_skills(text: str) -> list[str]:
    return [s for s in SKILLS if contains(text, s)]


def evidence_for(text: str, skill: str) -> str:
    return next((line.strip() for line in text.splitlines() if contains(line, skill)), "")


@traceable(name="match_requirement", run_type="tool")
def match_requirement(requirement: str, category: str, resume_text: str) -> RequirementMatch:
    evidence = evidence_for(resume_text, requirement)
    status = "Missing"
    explanation = "No evidence identified in the supplied resume."
    if evidence:
        if re.search(r"\b(?:no|without|not)\b[^.;\n]{0,35}" + re.escape(requirement), evidence, re.I):
            return RequirementMatch(
                requirement=requirement,
                category=category,
                status="Missing",
                explanation="The resume explicitly negates this experience.",
            )
        if re.search(r"\b(learning|beginner|basic|introductory|familiar)\b", evidence, re.I):
            status, explanation = "Partial Match", "Resume indicates introductory knowledge."
        else:
            status, explanation = "Direct Match", "Explicitly stated in the resume."
    else:
        for related in RELATED.get(normalize(requirement), []):
            evidence = evidence_for(resume_text, related)
            if evidence:
                status = "Related Match"
                explanation = f"{related} is transferable, but does not prove {requirement} proficiency."
                break
    return RequirementMatch(
        requirement=requirement, category=category, status=status, evidence=evidence, explanation=explanation
    )
