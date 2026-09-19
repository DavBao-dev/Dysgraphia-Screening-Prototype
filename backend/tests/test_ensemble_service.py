# backend/tests/test_ensemble_service.py
from backend.services.ensemble_service import combine

A1 = {"prediction": 1, "score": 0.9}
A0 = {"prediction": 0, "score": 0.1}
B1 = {"prediction": 1, "score": 0.8}
B0 = {"prediction": 0, "score": 0.2}


def test_agree_uses_common_result():
    assert combine(A1, B1) == {"prediction": 1, "method": "majority_vote (majority)"}


def test_disagree_uses_probabilities():
    res = combine(A1, B0)
    assert res["method"] == "majority_vote (tie -> avg prob)"
    assert res["prediction"] == 1  # avg(0.9, 0.2) = 0.55 >= 0.5


def test_model_b_absent_model_a_decides():
    assert combine(A1, None) == {"prediction": 1, "method": "majority_vote (majority)"}


def test_both_absent_raises():
    try:
        combine(None, None)
    except ValueError:
        return
    raise AssertionError("expected ValueError")