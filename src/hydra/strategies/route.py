"""Route: a triage nurse sends each patient straight to the right doctor."""

from __future__ import annotations

from ..backends import last_user
from ..config import RouteConfig
from ..difficulty import classify
from ..trace import DecisionTrace
from .base import Context, StrategyError, StrategyResult, timed_call


class RouteStrategy:
    kind = "route"

    def __init__(self, name: str, cfg: RouteConfig):
        self.name = name
        self.cfg = cfg

    async def run(self, messages: list[dict], ctx: Context, **params) -> StrategyResult:
        d = classify(last_user(messages))
        bname = self.cfg.tiers[d.tier]
        c, rec = await timed_call(ctx.backends[bname], messages, role="answer", **params)
        trace = DecisionTrace(
            strategy=self.name,
            kind=self.kind,
            calls=[rec],
            selected_backend=bname,
            reason=f"classified {d.tier} (score {d.score:.2f}) → {bname}",
            details={"difficulty": d.score, "tier": d.tier, "signals": d.signals},
        )
        if c is None:
            raise StrategyError(f"route '{self.name}': backend {bname} failed: {rec.error}")
        return StrategyResult(completion=c, trace=trace)
