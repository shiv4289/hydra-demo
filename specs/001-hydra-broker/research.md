# Research: Hydra Multi-Model Broker

## R1 — How should a client select a strategy?

- **Decision**: The `model` field. `hydra-cascade` is a strategy; `small` is a backend.
- **Rationale**: Constitution I. Mirrors how NAI's Unified Endpoint is addressed by name, and how HydraFusion-style brokers appear as one model to Copilot clients.
- **Alternatives**: custom header (`x-hydra-strategy`) — rejected, breaks stock SDKs that can't set headers easily; extra body field — rejected, not OpenAI-shaped.

## R2 — How to simulate "quality" offline?

- **Decision**: Each mock backend has a `skill` (0–1). Simulated answer quality = `skill − 0.8·difficulty + 0.35`, ±0.05 deterministic jitter (hash of backend+prompt), clamped to [0, 1]. The answer text ends with a visible marker `⟨mock:name q=0.62⟩`; the mock judge parses it.
- **Rationale**: Deterministic, explainable in demos, and exercises the real judge code path (same prompt/parse logic a real judge uses).
- **Alternatives**: random quality — rejected, flaky tests; skipping the judge for mocks — rejected, leaves the real path untested.

## R3 — Quality check for cascade

- **Decision**: `JudgeCheck(backend, threshold)` sends a grader system prompt and parses the first float in the reply. Default threshold 0.7.
- **Alternatives**: logprob/confidence from the answering model — better in production (no extra call) but not available on every OpenAI-compatible server; kept as a future `QualityCheck` plugin.

## R4 — Route classifier

- **Decision**: Heuristic score from length, reasoning keywords (prove, design, analyze, step-by-step, trade-off…), code fences, and count of questions. Score → `easy` (<0.30) / `medium` (<0.60) / `hard`.
- **Alternatives**: embedding/semantic classifier (vLLM semantic-router style) — the natural 002+ upgrade; out of scope for an offline, dependency-light demo.

## R5 — Baseline cost

- **Decision**: Estimate, don't call: baseline = baseline backend's price × (prompt tokens + final answer's completion tokens).
- **Rationale**: Calling the strongest model on every request just to report savings would defeat the point.

## R6 — Fusion concurrency

- **Decision**: `asyncio.gather(..., return_exceptions=True)` over panel members with a per-call timeout; quorum default = ⌊n/2⌋+1.

## R7 — Token estimation for mocks

- **Decision**: `ceil(words × 1.3)`. Real backends use the `usage` block from the response.
