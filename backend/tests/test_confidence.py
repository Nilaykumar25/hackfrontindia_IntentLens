from backend.app.models import Factors
from backend.app.reasoning import confidence as c


def test_score_weights_sum_to_one():
    assert abs(sum(c.WEIGHTS.values()) - 1.0) < 1e-9


def test_perfect_factors_high():
    f = Factors(directness=1, corroboration=1, agreement=1, currency=1, distance=1)
    s = c.score(f)
    assert s == 1.0 and c.label_for(s) == "High"


def test_no_decision_is_no_answer():
    assert c.label_for(0.99, has_decision=False) == "No answer"


def test_boundaries():
    assert c.label_for(0.75, threshold=0.35) == "High"
    assert c.label_for(0.55, threshold=0.35) == "Medium"
    assert c.label_for(0.35, threshold=0.35) == "Low"
    assert c.label_for(0.34, threshold=0.35) == "No answer"


def test_component_scores():
    assert c.corroboration_score(1) == 0.4 and c.corroboration_score(5) == 1.0
    assert c.currency_score(0) == 1.0 and c.currency_score(10) == 0.0
    assert c.distance_score(1, 3) == 1.0 and c.distance_score(2, 3) < 1.0
