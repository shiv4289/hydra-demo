---
description: "Task list for 001-hydra-broker"
---

# Tasks: Hydra Multi-Model Broker

**Input**: Design documents from `/specs/001-hydra-broker/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml

**Tests**: Required (Constitution III). Each story's tests are written first and must fail before implementation.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [ ] T001 Create `pyproject.toml` (hatchling, src layout, deps: fastapi, uvicorn, httpx, pydantic, pyyaml; dev: pytest)
- [ ] T002 [P] Create package skeleton `src/hydra/__init__.py`, `src/hydra/strategies/__init__.py`
- [ ] T003 [P] Create default offline config `hydra.yaml` (mock small/medium/large/judge + 3 strategies) and `hydra.real.example.yaml`

---

## Phase 2: Foundational (blocks all stories)

- [ ] T004 [P] Config models + validation + `load_config()` in `src/hydra/config.py`
- [ ] T005 [P] Unit tests for config validation in `tests/unit/test_config.py`
- [ ] T006 [P] Difficulty classifier in `src/hydra/difficulty.py` + tests `tests/unit/test_difficulty.py`
- [ ] T007 [P] `CallRecord`, `DecisionTrace`, cost math in `src/hydra/trace.py`
- [ ] T008 Backend protocol, `MockBackend` (simulated quality/latency/tokens, mock judge + aggregator behaviour), `OpenAIBackend` in `src/hydra/backends.py`
- [ ] T009 `Strategy` protocol, `StrategyResult`, `Context` in `src/hydra/strategies/base.py`
- [ ] T010 `Broker` (model resolution, passthrough, baseline cost, registry build) in `src/hydra/broker.py`
- [ ] T011 Shared fixtures (fast `mock_time_scale`) in `tests/conftest.py`

**Checkpoint**: passthrough to a mock backend works via `Broker.complete()`.

---

## Phase 3: US1 Cascade (P1) 🎯 MVP

- [ ] T012 [US1] Tests for acceptance scenarios 1–3 + failed-attempt edge case in `tests/integration/test_cascade.py`
- [ ] T013 [P] [US1] `QualityCheck` protocol + `JudgeCheck` in `src/hydra/quality.py`
- [ ] T014 [US1] `CascadeStrategy` in `src/hydra/strategies/cascade.py`; register in `strategies/__init__.py`

**Checkpoint**: cascade demo works end-to-end in-process.

---

## Phase 4: US2 Decision trace (P1)

- [ ] T015 [US2] Tests: trace fields present for every strategy; savings math in `tests/integration/test_trace.py`
- [ ] T016 [US2] FastAPI app: `/v1/models`, `/v1/chat/completions`, `x-hydra-*` headers, `hydra` body field, error mapping (400/404/502) in `src/hydra/api.py`
- [ ] T017 [P] [US2] Contract tests vs `contracts/openapi.yaml` shape in `tests/contract/test_openai_shape.py`

---

## Phase 5: US3 Route (P2)

- [ ] T018 [P] [US3] Tests in `tests/integration/test_route.py`
- [ ] T019 [P] [US3] `RouteStrategy` in `src/hydra/strategies/route.py`; register

---

## Phase 6: US4 Fusion (P2)

- [ ] T020 [P] [US4] Tests incl. parallelism (SC-002) and quorum in `tests/integration/test_fusion.py`
- [ ] T021 [P] [US4] `FusionStrategy` in `src/hydra/strategies/fusion.py`; register

> T018–T021 are parallelizable across two agent sessions (different files, both depend only on Phase 2).

---

## Phase 7: US5 Demo CLI (P3)

- [ ] T022 [P] [US5] Sample prompts in `src/hydra/samples.py`
- [ ] T023 [US5] CLI (`--all`, `-s`, `-p`, `--trace`, `--json`) in `src/hydra/cli.py`
- [ ] T024 [US5] CLI smoke test + SC-001 savings check in `tests/integration/test_cli.py`

---

## Phase 8: Polish

- [ ] T025 [P] Project README with run instructions and strategy diagrams
- [ ] T026 Run quickstart.md end-to-end; `pytest` green

## Dependencies

- Phase 2 blocks everything. US1 → US2 (trace tests exercise cascade). US3, US4 independent of each other. US5 needs ≥ 1 strategy.
