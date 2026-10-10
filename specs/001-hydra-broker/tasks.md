---
description: "Task list for 001-hydra-broker"
---

# Tasks: Hydra Multi-Model Broker

**Input**: Design documents from `/specs/001-hydra-broker/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml

**Tests**: Required (Constitution III). Each story's tests are written first and must fail before implementation.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [x] T001 Create `pyproject.toml` (hatchling, src layout, deps: fastapi, uvicorn, httpx, pydantic, pyyaml; dev: pytest)
- [x] T002 [P] Create package skeleton `src/hydra/__init__.py`, `src/hydra/strategies/__init__.py`
- [x] T003 [P] Create default offline config `hydra.yaml` (mock small/medium/large/judge + 3 strategies) and `hydra.real.example.yaml`

---

## Phase 2: Foundational (blocks all stories)

- [x] T004 [P] Config models + validation + `load_config()` in `src/hydra/config.py`
- [x] T005 [P] Unit tests for config validation in `tests/unit/test_config.py`
- [x] T006 [P] Difficulty classifier in `src/hydra/difficulty.py` + tests `tests/unit/test_difficulty.py`
- [x] T007 [P] `CallRecord`, `DecisionTrace`, cost math in `src/hydra/trace.py`
- [x] T008 Backend protocol, `MockBackend` (simulated quality/latency/tokens, mock judge + aggregator behaviour), `OpenAIBackend` in `src/hydra/backends.py`
- [x] T009 `Strategy` protocol, `StrategyResult`, `Context` in `src/hydra/strategies/base.py`
- [x] T010 `Broker` (model resolution, passthrough, baseline cost, registry build) in `src/hydra/broker.py`
- [x] T011 Shared fixtures (fast `mock_time_scale`) in `tests/conftest.py`

**Checkpoint**: passthrough to a mock backend works via `Broker.complete()`.

---

## Phase 3: US1 Cascade (P1) 🎯 MVP

- [x] T012 [US1] Tests for acceptance scenarios 1–3 + failed-attempt edge case in `tests/integration/test_cascade.py`
- [x] T013 [P] [US1] `QualityCheck` protocol + `JudgeCheck` in `src/hydra/quality.py`
- [x] T014 [US1] `CascadeStrategy` in `src/hydra/strategies/cascade.py`; register in `strategies/__init__.py`

**Checkpoint**: cascade demo works end-to-end in-process.

---

## Phase 4: US2 Decision trace (P1)

- [x] T015 [US2] Tests: trace fields present for every strategy; savings math in `tests/integration/test_trace.py`
- [x] T016 [US2] FastAPI app: `/v1/models`, `/v1/chat/completions`, `x-hydra-*` headers, `hydra` body field, error mapping (400/404/502) in `src/hydra/api.py`
- [x] T017 [P] [US2] Contract tests vs `contracts/openapi.yaml` shape in `tests/contract/test_openai_shape.py`

---

## Phase 5: US3 Route (P2)

- [x] T018 [P] [US3] Tests in `tests/integration/test_route.py`
- [x] T019 [P] [US3] `RouteStrategy` in `src/hydra/strategies/route.py`; register

---

## Phase 6: US4 Fusion (P2)

- [x] T020 [P] [US4] Tests incl. parallelism (SC-002) and quorum in `tests/integration/test_fusion.py`
- [x] T021 [P] [US4] `FusionStrategy` in `src/hydra/strategies/fusion.py`; register

> T018–T021 are parallelizable across two agent sessions (different files, both depend only on Phase 2).

---

## Phase 7: US5 Demo CLI (P3)

- [x] T022 [P] [US5] Sample prompts in `src/hydra/samples.py`
- [x] T023 [US5] CLI (`--all`, `-s`, `-p`, `--trace`, `--json`) in `src/hydra/cli.py`
- [x] T024 [US5] CLI smoke test + SC-001 savings check in `tests/integration/test_cli.py`

---

## Phase 8: Polish

- [x] T025 [P] Project README with run instructions and strategy diagrams
- [x] T026 Run quickstart.md end-to-end; `pytest` green

## Dependencies

- Phase 2 blocks everything. US1 → US2 (trace tests exercise cascade). US3, US4 independent of each other. US5 needs ≥ 1 strategy.
