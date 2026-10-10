import asyncio
import copy

import pytest

from hydra.broker import Broker
from hydra.config import HydraConfig

BASE = {
    "baseline": "large",
    "mock_time_scale": 0.05,
    "backends": [
        {"name": "small", "kind": "mock", "skill": 0.45, "latency_ms": 120, "price_in": 0.0001, "price_out": 0.0004},
        {"name": "medium", "kind": "mock", "skill": 0.70, "latency_ms": 300, "price_in": 0.001, "price_out": 0.003},
        {"name": "large", "kind": "mock", "skill": 0.95, "latency_ms": 800, "price_in": 0.005, "price_out": 0.015},
        {"name": "judge", "kind": "mock", "skill": 0.60, "latency_ms": 80, "price_in": 0.0001, "price_out": 0.0004},
    ],
    "strategies": {
        "hydra-route": {"kind": "route", "tiers": {"easy": "small", "medium": "medium", "hard": "large"}},
        "hydra-cascade": {"kind": "cascade", "steps": ["small", "large"], "judge": "judge", "threshold": 0.7},
        "hydra-fusion": {"kind": "fusion", "panel": ["small", "medium", "large"], "aggregator": "large"},
    },
}

EASY = "hi, what's 2+2?"
HARD = (
    "Design a distributed rate limiter for a multi-tenant inference API. Compare token bucket "
    "and sliding window, analyze the trade-offs, and explain step by step how to avoid a single "
    "point of failure across replicas."
)


@pytest.fixture
def raw_cfg():
    return copy.deepcopy(BASE)


def make_broker(raw: dict) -> Broker:
    return Broker(HydraConfig.model_validate(raw))


@pytest.fixture
def broker(raw_cfg):
    return make_broker(raw_cfg)


def ask(broker: Broker, model: str, prompt: str):
    return asyncio.run(broker.complete(model, [{"role": "user", "content": prompt}]))
