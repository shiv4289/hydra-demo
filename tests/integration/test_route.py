"""US3 acceptance scenarios."""

from tests.conftest import EASY, HARD, ask


def test_s1_easy_goes_to_small(broker):
    t = ask(broker, "hydra-route", EASY).trace
    assert t.details["tier"] == "easy"
    assert t.selected_backend == "small"
    assert len(t.calls) == 1  # FR-006: exactly one call


def test_s2_hard_goes_to_large(broker):
    t = ask(broker, "hydra-route", HARD).trace
    assert t.details["tier"] == "hard"
    assert t.selected_backend == "large"
    assert len(t.calls) == 1
    assert "keywords" in t.details["signals"]


def test_route_is_cheaper_than_cascade_on_easy(broker):
    r = ask(broker, "hydra-route", EASY).trace
    c = ask(broker, "hydra-cascade", EASY).trace
    assert r.total_cost_usd < c.total_cost_usd  # no judge call
