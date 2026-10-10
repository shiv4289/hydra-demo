"""US1 acceptance scenarios."""

import pytest

from hydra.strategies import StrategyError
from tests.conftest import EASY, HARD, ask, make_broker


def test_s1_easy_prompt_accepted_at_step_1(broker):
    t = ask(broker, "hydra-cascade", EASY).trace
    attempts = [c for c in t.calls if c.role == "attempt"]
    assert [c.backend for c in attempts] == ["small"]
    assert t.selected_backend == "small"
    assert t.details["outcome"] == "accepted"
    assert "accepted at step 1" in t.reason
    assert attempts[0].score >= 0.7


def test_s2_hard_prompt_escalates(broker):
    t = ask(broker, "hydra-cascade", HARD).trace
    attempts = [c for c in t.calls if c.role == "attempt"]
    assert [c.backend for c in attempts] == ["small", "large"]
    assert attempts[0].score < 0.7
    assert t.selected_backend == "large"
    assert [c.role for c in t.calls] == ["attempt", "judge", "attempt"]


def test_s3_exhausted_returns_last_answer(raw_cfg):
    raw_cfg["strategies"]["hydra-cascade"]["threshold"] = 0.95  # nothing cheap passes
    raw_cfg["strategies"]["hydra-cascade"]["steps"] = ["small", "medium", "large"]
    t = ask(make_broker(raw_cfg), "hydra-cascade", HARD).trace
    assert [c.backend for c in t.calls if c.role == "attempt"] == ["small", "medium", "large"]
    assert t.details["outcome"] == "exhausted"
    assert t.selected_backend == "large"
    assert "exhausted" in t.reason


def test_failed_attempt_escalates(raw_cfg):
    raw_cfg["backends"][0]["fail"] = True  # small is down
    t = ask(make_broker(raw_cfg), "hydra-cascade", EASY).trace
    assert t.calls[0].ok is False and t.calls[0].error
    assert t.selected_backend == "large"


def test_judge_cost_is_counted(broker):
    t = ask(broker, "hydra-cascade", EASY).trace
    assert any(c.role == "judge" and c.cost_usd > 0 for c in t.calls)
    assert t.total_cost_usd == pytest.approx(sum(c.cost_usd for c in t.calls))


def test_all_steps_failing_raises(raw_cfg):
    for b in raw_cfg["backends"]:
        b["fail"] = True
    with pytest.raises(StrategyError, match="every step failed"):
        ask(make_broker(raw_cfg), "hydra-cascade", EASY)
