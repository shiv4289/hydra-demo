"""The one interface every strategy implements (Constitution V)."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Protocol

from ..backends import Backend, BackendError, Completion
from ..trace import CallRecord, DecisionTrace, Role, cost_usd


class StrategyError(RuntimeError):
    """Strategy could not produce an answer (mapped to HTTP 502)."""


@dataclass
class Context:
    backends: dict[str, Backend]


@dataclass
class StrategyResult:
    completion: Completion
    trace: DecisionTrace


class Strategy(Protocol):
    name: str
    kind: str

    async def run(self, messages: list[dict], ctx: Context, **params) -> StrategyResult: ...


async def timed_call(
    backend: Backend, messages: list[dict], role: Role, **params
) -> tuple[Completion | None, CallRecord]:
    """Call a backend and always return a CallRecord, even on failure."""
    t0 = time.perf_counter()
    try:
        c = await backend.complete(messages, **params)
    except BackendError as e:
        ms = (time.perf_counter() - t0) * 1000
        return None, CallRecord(backend=backend.name, role=role, latency_ms=round(ms, 1), ok=False, error=str(e))
    ms = (time.perf_counter() - t0) * 1000
    return c, CallRecord(
        backend=backend.name,
        role=role,
        latency_ms=round(ms, 1),
        prompt_tokens=c.prompt_tokens,
        completion_tokens=c.completion_tokens,
        cost_usd=round(cost_usd(c.prompt_tokens, c.completion_tokens, backend.price_in, backend.price_out), 8),
    )
