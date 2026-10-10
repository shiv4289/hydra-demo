"""Fusion: a panel of experts drafts in parallel, an editor writes the final answer."""

from __future__ import annotations

import asyncio

from ..backends import last_user
from ..config import FusionConfig
from ..prompts import aggregator_messages
from ..trace import DecisionTrace
from .base import Context, StrategyError, StrategyResult, timed_call


class FusionStrategy:
    kind = "fusion"

    def __init__(self, name: str, cfg: FusionConfig):
        self.name = name
        self.cfg = cfg

    async def run(self, messages: list[dict], ctx: Context, **params) -> StrategyResult:
        question = last_user(messages)
        results = await asyncio.gather(
            *(timed_call(ctx.backends[b], messages, role="panel", **params) for b in self.cfg.panel)
        )
        trace = DecisionTrace(strategy=self.name, kind=self.kind)
        drafts: list[tuple[str, str]] = []
        failed: list[str] = []
        for bname, (c, rec) in zip(self.cfg.panel, results):
            trace.calls.append(rec)
            (drafts.append((bname, c.text)) if c else failed.append(bname))

        panel_wall = max((r.latency_ms for _, r in results), default=0.0)
        trace.details = {
            "panel": self.cfg.panel,
            "quorum": self.cfg.quorum,
            "succeeded": [n for n, _ in drafts],
            "failed": failed,
            "panel_wall_ms": round(panel_wall, 1),
            "panel_sum_ms": round(sum(r.latency_ms for _, r in results), 1),
        }
        if len(drafts) < self.cfg.quorum:
            raise StrategyError(
                f"fusion '{self.name}': only {len(drafts)}/{len(self.cfg.panel)} panel members succeeded "
                f"(quorum {self.cfg.quorum}); failed: {failed}"
            )

        agg = ctx.backends[self.cfg.aggregator]
        c, rec = await timed_call(agg, aggregator_messages(question, drafts), role="aggregator", **params)
        trace.calls.append(rec)
        if c is None:
            raise StrategyError(f"fusion '{self.name}': aggregator {self.cfg.aggregator} failed: {rec.error}")
        trace.selected_backend = self.cfg.aggregator
        note = f"; {len(failed)} failed ({', '.join(failed)})" if failed else ""
        trace.reason = f"{len(drafts)}/{len(self.cfg.panel)} drafts in parallel → synthesized by {agg.name}{note}"
        return StrategyResult(completion=c, trace=trace)
