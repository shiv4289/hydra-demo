<!--
Sync Impact Report
- Version: (template) → 1.0.0
- Added principles: I–VI (all new)
- Added sections: Demo Constraints, Development Workflow
- Templates checked: plan-template.md ✅ (Constitution Check gates map to I–VI), tasks-template.md ✅ (tests required per III)
- Follow-ups: none
-->

# Hydra Demo Constitution

## Core Principles

### I. Drop-in Compatible (NON-NEGOTIABLE)
The broker MUST look like "just another model" to any client. It exposes an
OpenAI-compatible `POST /v1/chat/completions` and `GET /v1/models`. A client
switches between a real model and a broker strategy by changing only the
`model` field. No custom SDK, no extra request fields required.

### II. Offline-First Demo
Every feature MUST be runnable and testable with zero network access and zero
API keys, using deterministic mock backends. Real OpenAI-compatible backends
(vLLM, Ollama, hosted APIs) are an opt-in configuration, never a prerequisite.

### III. Test-First
Each user story ships with tests written against the spec's acceptance
scenarios before (or alongside) implementation. A story is not done until its
acceptance scenarios pass as automated tests. Mock backends make this cheap —
there is no excuse for untested routing logic.

### IV. Explainable Decisions
Every broker response MUST carry a decision trace: which strategy ran, which
backends were called, why escalation/selection happened, per-call latency and
estimated cost. Trace is returned in response headers and in a `hydra` field
of the response body. A routing decision that cannot be explained is a bug.

### V. Strategies Are Plugins
Each orchestration strategy (route, cascade, fusion, …) lives behind one small
interface. Adding a strategy MUST NOT require edits to the HTTP layer or to
other strategies. Strategy behaviour is driven by declarative config, not code
changes.

### VI. Simplicity
This is a demo for learning and for showing the pattern. Prefer the standard
library and a minimal dependency set. No databases, queues, or auth. No
abstraction without a second concrete user. YAGNI wins ties.

## Demo Constraints

- Language: Python 3.11+. HTTP: FastAPI + httpx. Config: YAML validated with Pydantic.
- Single process, single repo, `src/` + `tests/` layout.
- Invalid config MUST fail fast at startup with a clear message (unrepresentable bad states over runtime surprises).
- Out of scope: wiring into NAI / UEP / Envoy ext_proc, streaming, multi-tenancy, persistence.

## Development Workflow

- Every feature goes through: specify → (clarify) → plan → tasks → (analyze) → implement.
- Spec describes WHAT and WHY only; tech choices appear first in plan.md.
- Every task in tasks.md references an exact file path and a user story.
- `pytest` must be green before a task is checked off.

## Governance

This constitution supersedes ad-hoc preferences. `/speckit-plan` MUST run a
Constitution Check against Principles I–VI and justify any violation in the
plan's Complexity Tracking table. Amendments bump the version (MAJOR: removed
or redefined principle; MINOR: new principle/section; PATCH: wording).

**Version**: 1.0.0 | **Ratified**: 2026-10-10 | **Last Amended**: 2026-10-10
