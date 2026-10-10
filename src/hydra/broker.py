"""Broker: resolves `model` → backend (passthrough) or strategy, finalizes the trace."""

from __future__ import annotations

import time

from .backends import build_backend, prompt_tokens_of
from .config import HydraConfig, load_config
from .strategies import STRATEGY_REGISTRY, Context, StrategyResult
from .strategies.base import StrategyError, timed_call
from .trace import DecisionTrace, cost_usd


class UnknownModel(LookupError):
    def __init__(self, model: str, valid: list[str]):
        self.model, self.valid = model, valid
        super().__init__(f"model '{model}' not found; valid: {', '.join(valid)}")


class Broker:
    def __init__(self, cfg: HydraConfig):
        self.cfg = cfg
        self.backends = {b.name: build_backend(b, cfg.mock_time_scale) for b in cfg.backends}
        self.strategies = {
            name: STRATEGY_REGISTRY[s.kind](name, s) for name, s in cfg.strategies.items()
        }
        self.ctx = Context(backends=self.backends)

    @classmethod
    def from_file(cls, path: str | None = None) -> "Broker":
        return cls(load_config(path))

    def models(self) -> list[tuple[str, str]]:
        return [(n, f"hydra-strategy:{s.kind}") for n, s in self.strategies.items()] + [
            (b.name, f"hydra-backend:{b.kind}") for b in self.cfg.backends
        ]

    def baseline_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        b = self.backends[self.cfg.baseline]
        return cost_usd(prompt_tokens, completion_tokens, b.price_in, b.price_out)

    async def complete(self, model: str, messages: list[dict], **params) -> StrategyResult:
        t0 = time.perf_counter()
        if model in self.strategies:
            result = await self.strategies[model].run(messages, self.ctx, **params)
        elif model in self.backends:
            c, rec = await timed_call(self.backends[model], messages, role="answer", **params)
            if c is None:
                raise StrategyError(f"backend {model} failed: {rec.error}")
            result = StrategyResult(
                completion=c,
                trace=DecisionTrace(
                    strategy=model, kind="passthrough", calls=[rec], selected_backend=model, reason="direct backend call"
                ),
            )
        else:
            raise UnknownModel(model, [m for m, _ in self.models()])

        c = result.completion
        # baseline: strongest model answering the ORIGINAL prompt once (research R5)
        result.trace.finalize(self.baseline_cost(prompt_tokens_of(messages), c.completion_tokens), (time.perf_counter() - t0) * 1000)
        return result
