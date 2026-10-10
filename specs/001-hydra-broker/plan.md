# Implementation Plan: Hydra Multi-Model Broker

**Branch**: `001-hydra-broker` | **Date**: 2026-10-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-hydra-broker/spec.md`

## Summary

An in-process Python broker exposing an OpenAI-compatible API. The `model`
field resolves to either a backend (passthrough) or a strategy instance
(route / cascade / fusion). Strategies are plugins behind one async interface
and emit a `DecisionTrace`. Deterministic mock backends simulate quality,
latency, and token cost so the whole demo — server, CLI, tests — runs
offline. A YAML config, validated by Pydantic at startup, wires backends to
strategies.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: FastAPI, uvicorn, httpx, Pydantic v2, PyYAML

**Storage**: N/A (config file only)

**Testing**: pytest (+ FastAPI TestClient); async code exercised via `asyncio.run`

**Target Platform**: Linux/macOS dev laptop

**Project Type**: web-service + CLI (single project)

**Performance Goals**: Broker overhead < 5 ms per request excluding backend time; fusion wall time ≈ slowest panel member

**Constraints**: Offline-capable; zero required secrets; no streaming

**Scale/Scope**: Demo — single user, ~10 backends, ~10 strategies

## Constitution Check

| Principle | Gate | Status |
|---|---|---|
| I. Drop-in Compatible | `/v1/chat/completions` + `/v1/models` follow OpenAI shape; strategy chosen by `model` only | ✅ contracts/openapi.yaml |
| II. Offline-First | `MockBackend` default; `hydra.yaml` ships with mocks only; tests never touch network | ✅ |
| III. Test-First | One integration test module per user story, mapped 1:1 to acceptance scenarios | ✅ tasks.md |
| IV. Explainable Decisions | `DecisionTrace` in `hydra` body field + `x-hydra-*` headers | ✅ data-model.md |
| V. Strategies Are Plugins | `Strategy` protocol + `STRATEGY_REGISTRY[kind]`; HTTP layer only talks to `Broker` | ✅ |
| VI. Simplicity | 5 runtime deps, stdlib CLI (no rich/click), no DB | ✅ |

Post-design re-check: ✅ no violations.

## Project Structure

### Documentation (this feature)

```text
specs/001-hydra-broker/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/openapi.yaml
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
src/hydra/
├── __init__.py
├── config.py          # Pydantic config models + load_config()
├── difficulty.py      # heuristic prompt difficulty classifier
├── backends.py        # Backend protocol, MockBackend, OpenAIBackend
├── prompts.py         # judge + aggregator prompts (shared by real and mock)
├── trace.py           # CallRecord, DecisionTrace, cost math
├── quality.py         # QualityCheck protocol, JudgeCheck
├── strategies/
│   ├── __init__.py    # STRATEGY_REGISTRY
│   ├── base.py        # Strategy protocol, StrategyResult, Context
│   ├── route.py
│   ├── cascade.py
│   └── fusion.py
├── broker.py          # resolves model → backend|strategy, baseline cost
├── api.py             # FastAPI app factory
├── samples.py         # bundled demo prompts
└── cli.py             # python -m hydra.cli

tests/
├── conftest.py
├── unit/              # difficulty, config, trace math
├── integration/       # one module per user story
└── contract/          # OpenAI response shape
hydra.yaml             # default offline config
```

**Structure Decision**: single project; `src/` layout so tests import the installed package.

## Complexity Tracking

No violations.
