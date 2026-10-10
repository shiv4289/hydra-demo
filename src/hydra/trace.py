"""Decision trace + cost math (Constitution IV)."""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import BaseModel, Field

Role = Literal["answer", "attempt", "judge", "panel", "aggregator"]


def estimate_tokens(text: str) -> int:
    """~1.3 tokens per word (research R7)."""
    return max(1, math.ceil(len(text.split()) * 1.3))


def cost_usd(prompt_tokens: int, completion_tokens: int, price_in: float, price_out: float) -> float:
    return prompt_tokens / 1000 * price_in + completion_tokens / 1000 * price_out


class CallRecord(BaseModel):
    backend: str
    role: Role
    latency_ms: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    ok: bool = True
    score: float | None = None
    error: str | None = None


class DecisionTrace(BaseModel):
    strategy: str
    kind: str
    calls: list[CallRecord] = Field(default_factory=list)
    selected_backend: str = ""
    reason: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
    total_cost_usd: float = 0.0
    baseline_cost_usd: float = 0.0
    savings_pct: float = 0.0
    wall_ms: float = 0.0

    def finalize(self, baseline_cost: float, wall_ms: float) -> "DecisionTrace":
        self.total_cost_usd = round(sum(c.cost_usd for c in self.calls), 8)
        self.baseline_cost_usd = round(baseline_cost, 8)
        self.savings_pct = (
            round((baseline_cost - self.total_cost_usd) / baseline_cost * 100, 1) if baseline_cost > 0 else 0.0
        )
        self.wall_ms = round(wall_ms, 1)
        return self

    def headers(self) -> dict[str, str]:
        return {
            "x-hydra-strategy": self.strategy,
            "x-hydra-backends": ",".join(f"{c.backend}:{c.role}" for c in self.calls),
            "x-hydra-selected": self.selected_backend,
            "x-hydra-cost-usd": f"{self.total_cost_usd:.6f}",
            "x-hydra-baseline-usd": f"{self.baseline_cost_usd:.6f}",
            "x-hydra-savings-pct": f"{self.savings_pct}",
        }
