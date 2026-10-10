"""US4 acceptance scenarios."""

import pytest

from hydra.strategies import StrategyError
from tests.conftest import HARD, ask, make_broker


def test_s1_panel_then_aggregator(broker):
    r = ask(broker, "hydra-fusion", HARD)
    t = r.trace
    assert [c.role for c in t.calls] == ["panel", "panel", "panel", "aggregator"]
    assert t.selected_backend == "large"
    assert r.completion.text.startswith("Synthesized")


def test_panel_runs_in_parallel_sc002(raw_cfg):
    raw_cfg["mock_time_scale"] = 0.2  # make sleeps large enough to measure
    t = ask(make_broker(raw_cfg), "hydra-fusion", HARD).trace
    wall, slowest, total = t.details["panel_wall_ms"], max(c.latency_ms for c in t.calls[:3]), t.details["panel_sum_ms"]
    assert wall == pytest.approx(slowest)
    panel_phase = t.wall_ms - t.calls[-1].latency_ms
    assert panel_phase <= slowest * 1.2  # SC-002
    assert panel_phase < total  # strictly better than sequential


def test_s2_one_member_fails_quorum_met(raw_cfg):
    raw_cfg["backends"][0]["fail"] = True  # small
    t = ask(make_broker(raw_cfg), "hydra-fusion", HARD).trace
    assert t.details["failed"] == ["small"]
    assert t.details["succeeded"] == ["medium", "large"]
    assert "1 failed" in t.reason


def test_s3_below_quorum_errors(raw_cfg):
    raw_cfg["backends"][0]["fail"] = True
    raw_cfg["backends"][1]["fail"] = True
    with pytest.raises(StrategyError, match=r"only 1/3 .*quorum 2.*\['small', 'medium'\]"):
        ask(make_broker(raw_cfg), "hydra-fusion", HARD)
