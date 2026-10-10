"""US2 acceptance scenarios: every response explains itself."""

import pytest

from tests.conftest import EASY, HARD, ask

STRATEGIES = ["hydra-route", "hydra-cascade", "hydra-fusion", "small"]


@pytest.mark.parametrize("model", STRATEGIES)
@pytest.mark.parametrize("prompt", [EASY, HARD])
def test_s1_trace_has_required_fields(broker, model, prompt):
    t = ask(broker, model, prompt).trace
    assert t.strategy == model
    assert t.calls and all(c.backend and c.role and c.latency_ms >= 0 for c in t.calls)
    assert t.selected_backend
    assert t.reason
    assert t.total_cost_usd > 0
    assert t.baseline_cost_usd > 0
    assert t.wall_ms > 0


def test_s2_savings_math(broker):
    t = ask(broker, "hydra-cascade", EASY).trace
    expected = (t.baseline_cost_usd - t.total_cost_usd) / t.baseline_cost_usd * 100
    assert t.savings_pct == pytest.approx(expected, abs=0.1)
    assert t.savings_pct > 0


def test_headers_mirror_trace(broker):
    t = ask(broker, "hydra-cascade", HARD).trace
    h = t.headers()
    assert h["x-hydra-strategy"] == "hydra-cascade"
    assert h["x-hydra-selected"] == t.selected_backend
    assert h["x-hydra-backends"].split(",")[0] == "small:attempt"
