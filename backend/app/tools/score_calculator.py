from langsmith import traceable

from app.schemas.analysis import RequirementMatch

WEIGHTS = {"mandatory": 0.7, "preferred": 0.2, "alignment": 0.1}
CREDITS = {
    "Direct Match": 1.0,
    "Related Match": 0.5,
    "Partial Match": 0.25,
    "Missing": 0.0,
    "Cannot Determine": 0.0,
}


@traceable(name="calculate_compatibility", run_type="tool")
def calculate_score(rows: list[RequirementMatch]) -> dict:
    """Redistribute absent category weights; unknown requirements earn no credit."""
    breakdown = {}
    active_weight = sum(w for c, w in WEIGHTS.items() if any(r.category == c for r in rows))
    for category, weight in WEIGHTS.items():
        items = [r for r in rows if r.category == category]
        coverage = sum(CREDITS[r.status] for r in items) / len(items) if items else None
        effective = weight / active_weight if items and active_weight else 0
        breakdown[category] = {
            "coverage": round(100 * coverage, 2) if coverage is not None else None,
            "weight": effective,
            "count": len(items),
            "contribution": 100 * (coverage or 0) * effective,
        }
    return {
        "match_score": round(sum(b["contribution"] for b in breakdown.values()), 2)
        if active_weight
        else None,
        "breakdown": breakdown,
        "notice": "Resume compatibility, not a probability of selection or hiring.",
    }
