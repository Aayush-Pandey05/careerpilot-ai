import pytest

from scripts.evaluation_cases import CASES
from scripts.run_langsmith_evaluation import checks, predict


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["name"])
def test_synthetic_regressions(case):
    result = predict(case)
    for name, passed in checks(result, case["expected"], case).items():
        assert passed, name
