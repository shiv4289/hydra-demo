"""Quality checks for cascade (research R3). Pluggable: implement QualityCheck."""

from __future__ import annotations

import re
from typing import Protocol

from .backends import Backend
from .prompts import judge_messages
from .strategies.base import timed_call
from .trace import CallRecord

_FLOAT = re.compile(r"(?<![\d.])(0(?:\.\d+)?|1(?:\.0+)?)(?![\d.])")


class QualityCheck(Protocol):
    threshold: float

    async def score(self, question: str, answer: str) -> tuple[float, CallRecord | None]: ...


class JudgeCheck:
    """Ask a (cheap) judge model for a 0–1 score."""

    def __init__(self, judge: Backend, threshold: float):
        self.judge = judge
        self.threshold = threshold

    async def score(self, question: str, answer: str) -> tuple[float, CallRecord | None]:
        c, rec = await timed_call(self.judge, judge_messages(question, answer), role="judge", max_tokens=5)
        if c is None:
            return 0.0, rec  # judge down → treat as not good enough, escalate
        m = _FLOAT.search(c.text)
        s = float(m.group(1)) if m else 0.0
        rec.score = s
        return s, rec
