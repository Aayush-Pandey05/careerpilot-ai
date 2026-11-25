import pytest

from app.schemas.analysis import RequirementMatch
from app.tools.score_calculator import calculate_score
from app.tools.skill_matcher import contains, match_requirement, normalize


@pytest.mark.parametrize(
    "alias,canonical", [("JS", "javascript"), ("sklearn", "scikit-learn"), ("PostgreSQL", "postgres")]
)
def test_aliases(alias, canonical):
    assert normalize(alias) == canonical


def test_boundaries_and_transfer():
    assert not contains("JavaScript", "Java")
    assert not contains("NoSQL", "SQL")
    assert (
        match_requirement("TensorFlow", "preferred", "Used PyTorch for image models.").status
        == "Related Match"
    )
    assert match_requirement("Docker", "preferred", "Basic Docker knowledge").status == "Partial Match"
    assert match_requirement("AWS", "mandatory", "Python developer").status == "Missing"


def test_weighted_score():
    rows = [
        RequirementMatch(requirement="Python", category="mandatory", status="Direct Match"),
        RequirementMatch(requirement="AWS", category="preferred", status="Missing"),
        RequirementMatch(requirement="Experience", category="alignment", status="Related Match"),
    ]
    assert calculate_score(rows)["match_score"] == 75


def test_absent_category_is_renormalized():
    row = RequirementMatch(requirement="Python", category="mandatory", status="Partial Match")
    result = calculate_score([row])
    assert result["match_score"] == 25
    assert result["breakdown"]["mandatory"]["weight"] == 1
    assert result["breakdown"]["preferred"]["coverage"] is None
    assert calculate_score([])["match_score"] is None


def test_unknowns_receive_no_credit():
    row = RequirementMatch(requirement="years", category="alignment", status="Cannot Determine")
    assert calculate_score([row])["match_score"] == 0


def test_negative_evidence_is_not_a_direct_match():
    row = match_requirement("AWS", "mandatory", "No experience with AWS.")
    assert row.status == "Missing" and not row.evidence
