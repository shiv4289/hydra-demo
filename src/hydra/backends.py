"""Backends: anything that turns messages into a completion.

MockBackend is a deterministic stand-in (research R2): it simulates answer
quality from its `skill` vs. the prompt's difficulty, and also knows how to
play judge and aggregator so those code paths run offline too.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import re
from dataclasses import dataclass
from typing import Protocol

import httpx

from .config import MockBackendConfig, OpenAIBackendConfig
from .difficulty import classify
from .prompts import AGGREGATOR_SYSTEM, JUDGE_SYSTEM
from .trace import estimate_tokens

QUALITY_MARK = re.compile(r"⟨mock:(?P<name>[\w.-]+) q=(?P<q>[0-9.]+)⟩")


class BackendError(RuntimeError):
    pass


@dataclass
class Completion:
    text: str
    prompt_tokens: int
    completion_tokens: int


class Backend(Protocol):
    name: str
    price_in: float
    price_out: float

    async def complete(self, messages: list[dict], **params) -> Completion: ...


def last_user(messages: list[dict]) -> str:
    return next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")


def _system(messages: list[dict]) -> str:
    return next((m["content"] for m in messages if m.get("role") == "system"), "")


def prompt_tokens_of(messages: list[dict]) -> int:
    return sum(estimate_tokens(m.get("content", "")) for m in messages)


class MockBackend:
    def __init__(self, cfg: MockBackendConfig, time_scale: float = 1.0):
        self.name = cfg.name
        self.price_in = cfg.price_in
        self.price_out = cfg.price_out
        self.skill = cfg.skill
        self.latency_ms = cfg.latency_ms
        self.fail = cfg.fail
        self.time_scale = time_scale

    # deterministic ±0.05 so results look organic but tests stay stable
    def _jitter(self, text: str) -> float:
        h = int(hashlib.sha256(f"{self.name}|{text}".encode()).hexdigest()[:8], 16)
        return (h / 0xFFFFFFFF - 0.5) * 0.1

    def simulated_quality(self, prompt: str) -> float:
        d = classify(prompt).score
        return round(min(max(self.skill - 0.8 * d + 0.35 + self._jitter(prompt), 0.0), 1.0), 2)

    async def complete(self, messages: list[dict], **params) -> Completion:
        system, user = _system(messages), last_user(messages)
        if system.startswith(JUDGE_SYSTEM):
            text, d = self._judge(user), 0.0
        elif system.startswith(AGGREGATOR_SYSTEM):
            question = user.split("QUESTION:", 1)[-1].split("DRAFT 1", 1)[0]
            text, d = self._aggregate(user), classify(question).score
        else:
            text, d = self._answer(user), classify(user).score

        await asyncio.sleep(self.latency_ms * (0.6 + 0.8 * d) * self.time_scale / 1000)
        if self.fail:
            raise BackendError(f"{self.name}: simulated failure")
        words = 2 if system.startswith(JUDGE_SYSTEM) else int(30 + 220 * d)
        return Completion(text=text, prompt_tokens=prompt_tokens_of(messages), completion_tokens=estimate_tokens("w " * words))

    def _answer(self, prompt: str) -> str:
        q = self.simulated_quality(prompt)
        style = "Quick" if self.skill < 0.55 else "Solid" if self.skill < 0.85 else "Thorough"
        snippet = prompt.strip().replace("\n", " ")
        snippet = snippet if len(snippet) <= 60 else snippet[:57] + "..."
        return f"{style} answer to “{snippet}” (simulated by {self.name}). ⟨mock:{self.name} q={q:.2f}⟩"

    def _judge(self, user: str) -> str:
        # The mock judge is an honest oracle: it reads the simulated quality mark.
        answer = user.split("ANSWER:", 1)[-1]
        m = QUALITY_MARK.search(answer)
        return f"{float(m['q']):.2f}" if m else "0.50"

    def _aggregate(self, user: str) -> str:
        qs = [float(m["q"]) for m in QUALITY_MARK.finditer(user)]
        names = [m["name"] for m in QUALITY_MARK.finditer(user)]
        question = user.split("QUESTION:", 1)[-1].split("DRAFT 1", 1)[0].strip()
        best = max(qs, default=0.5)
        # editor adds value on top of the best draft, more so with more drafts
        q = round(min(1.0, max(best, self.simulated_quality(question)) + 0.03 * len(qs)), 2)
        snippet = question if len(question) <= 60 else question[:57] + "..."
        return (
            f"Synthesized answer to “{snippet}” from {len(qs)} drafts ({', '.join(names)}) "
            f"by {self.name}. ⟨mock:{self.name} q={q:.2f}⟩"
        )


class OpenAIBackend:
    """Any OpenAI-compatible server: vLLM, Ollama, LiteLLM, hosted APIs."""

    def __init__(self, cfg: OpenAIBackendConfig):
        self.name = cfg.name
        self.price_in = cfg.price_in
        self.price_out = cfg.price_out
        self.cfg = cfg

    async def complete(self, messages: list[dict], **params) -> Completion:
        headers = {}
        if self.cfg.api_key_env:
            key = os.environ.get(self.cfg.api_key_env)
            if not key:
                raise BackendError(f"{self.name}: env var {self.cfg.api_key_env} not set")
            headers["Authorization"] = f"Bearer {key}"
        payload = {"model": self.cfg.model, "messages": messages, "stream": False}
        payload.update({k: v for k, v in params.items() if k in ("temperature", "max_tokens", "top_p") and v is not None})
        try:
            async with httpx.AsyncClient(timeout=self.cfg.timeout_s) as client:
                r = await client.post(f"{self.cfg.base_url.rstrip('/')}/chat/completions", json=payload, headers=headers)
                r.raise_for_status()
                data = r.json()
        except (httpx.HTTPError, ValueError) as e:
            raise BackendError(f"{self.name}: {e}") from e
        text = data["choices"][0]["message"]["content"] or ""
        usage = data.get("usage") or {}
        return Completion(
            text=text,
            prompt_tokens=usage.get("prompt_tokens") or prompt_tokens_of(messages),
            completion_tokens=usage.get("completion_tokens") or estimate_tokens(text),
        )


def build_backend(cfg, time_scale: float = 1.0) -> Backend:
    if isinstance(cfg, MockBackendConfig):
        return MockBackend(cfg, time_scale)
    return OpenAIBackend(cfg)
