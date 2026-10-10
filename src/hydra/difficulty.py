"""Heuristic prompt-difficulty classifier (research R4).

Think of it as a triage nurse: a few quick signals, not a diagnosis.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

REASONING_WORDS = (
    "prove", "proof", "derive", "design", "architect", "analyze", "analyse",
    "trade-off", "tradeoff", "trade off", "step by step", "step-by-step",
    "compare", "optimize", "optimise", "why", "explain how", "evaluate",
    "algorithm", "complexity", "debug", "refactor", "strategy",
)

Tier = str  # "easy" | "medium" | "hard"


@dataclass
class Difficulty:
    score: float
    tier: Tier
    signals: dict[str, float] = field(default_factory=dict)


def classify(text: str) -> Difficulty:
    t = text.lower()
    words = len(t.split())

    length = min(words / 120, 1.0) * 0.35
    hits = sorted({w for w in REASONING_WORDS if w in t})
    reasoning = min(len(hits) * 0.15, 0.55)
    code = 0.15 if "```" in text or re.search(r"\bdef |\bclass |\bfunc |;\s*$", text, re.M) else 0.0
    multipart = min(max(text.count("?") - 1, 0) * 0.05 + len(re.findall(r"^\s*\d+[.)]", text, re.M)) * 0.05, 0.15)

    score = round(min(length + reasoning + code + multipart, 1.0), 3)
    tier = "easy" if score < 0.3 else "medium" if score < 0.6 else "hard"
    signals = {
        "length": round(length, 3),
        "reasoning": round(reasoning, 3),
        "code": code,
        "multipart": round(multipart, 3),
    }
    if hits:
        signals["keywords"] = hits  # type: ignore[assignment]
    return Difficulty(score=score, tier=tier, signals=signals)
