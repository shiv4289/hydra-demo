"""Cascade: junior answers first; the senior only steps in when unsure."""

from __future__ import annotations

from ..backends import last_user
from ..config import CascadeConfig
from ..quality import JudgeCheck
from ..trace import DecisionTrace
from .base import Context, StrategyError, StrategyResult, timed_call


class CascadeStrategy:
    kind = "cascade"

    def __init__(self, name: str, cfg: CascadeConfig):
        self.name = name
        self.cfg = cfg

    async def run(self, messages: list[dict], ctx: Context, **params) -> StrategyResult:
        question = last_user(messages)
        check = JudgeCheck(ctx.backends[self.cfg.judge], self.cfg.threshold)
        trace = DecisionTrace(strategy=self.name, kind=self.kind, details={"threshold": self.cfg.threshold, "steps": []})
        last_ok = None
        n = len(self.cfg.steps)

        for i, bname in enumerate(self.cfg.steps, start=1):
            backend = ctx.backends[bname]
            c, rec = await timed_call(backend, messages, role="attempt", **params)
            trace.calls.append(rec)
            if c is None:
                trace.details["steps"].append({"step": i, "backend": bname, "outcome": "error"})
                continue
            last_ok = (bname, c)

            if i == n:  # strongest model: no point judging, nothing left to escalate to
                rec.score = None
                trace.details["steps"].append({"step": i, "backend": bname, "outcome": "final"})
                break

            s, jrec = await check.score(question, c.text)
            if jrec:
                trace.calls.append(jrec)
            rec.score = s
            if s >= self.cfg.threshold:
                trace.selected_backend = bname
                trace.reason = f"accepted at step {i}/{n}: {bname} scored {s:.2f} ≥ {self.cfg.threshold}"
                trace.details["steps"].append({"step": i, "backend": bname, "score": s, "outcome": "accepted"})
                trace.details["outcome"] = "accepted"
                return StrategyResult(completion=c, trace=trace)
            trace.details["steps"].append({"step": i, "backend": bname, "score": s, "outcome": "escalate"})

        if last_ok is None:
            raise StrategyError(f"cascade '{self.name}': every step failed ({', '.join(self.cfg.steps)})")
        bname, c = last_ok
        trace.selected_backend = bname
        escalated = [s for s in trace.details["steps"] if s["outcome"] == "escalate"]
        if trace.details["steps"][-1]["outcome"] == "final":
            trace.reason = (
                f"exhausted: {len(escalated)} cheaper step(s) below {self.cfg.threshold}, "
                f"returned strongest model {bname}"
            )
        else:
            trace.reason = f"exhausted: strongest step failed, returned last successful answer from {bname}"
        trace.details["outcome"] = "exhausted"
        return StrategyResult(completion=c, trace=trace)
