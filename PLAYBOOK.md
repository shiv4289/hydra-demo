# Learning SDD with Spec Kit — Hydra Demo Playbook

A hands-on path through Spec-Driven Development, using a HydraFusion-style
multi-model broker as the vehicle.

## The mental model (house analogy)

| Spec Kit step | House-building equivalent | Output |
|---|---|---|
| `/speckit-constitution` | Building codes for the whole neighbourhood | `.specify/memory/constitution.md` |
| `/speckit-specify` | Client brief: "3 bedrooms, morning light" — no mention of bricks | `specs/NNN-*/spec.md` |
| `/speckit-clarify` | Architect asks: "morning light in *which* rooms?" | Clarifications appended to spec |
| `/speckit-plan` | Blueprints: materials, wiring, plumbing | `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md` |
| `/speckit-checklist` | "Unit tests for English" — is the brief complete? | `checklists/*.md` |
| `/speckit-tasks` | Construction schedule, which crews can work in parallel | `tasks.md` |
| `/speckit-analyze` | Inspector cross-checks brief ↔ blueprints ↔ schedule | Read-only report |
| `/speckit-implement` | The crew builds, room by room | Code + tests |

Key rule: **WHAT/WHY lives in spec.md, HOW lives in plan.md.** If you catch
"FastAPI" in the spec, it leaked.

## Repo layout

- `main` — scaffold + ratified constitution. **Start here and run the steps yourself.**
- `001-hydra-broker` — reference answer: all artifacts filled + working code + tests.
  Use it to compare after each step: `git diff main 001-hydra-broker -- specs/`

## Setup

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
cd hydra-demo
claude            # skills are already in .claude/skills
```

> This repo was generated with Specify CLI 1.1.4. Older docs show `/speckit.specify`
> (dot); in this version the Claude integration installs skills as `/speckit-specify` (dash).

## Step 0 — Constitution (already done on `main`)

Read `.specify/memory/constitution.md`. Six principles; the ones that shape
everything downstream:
- **Drop-in compatible** → broker is "just another model" (`model: hydra-cascade`)
- **Offline-first** → mock backends, no API keys needed
- **Explainable decisions** → every response carries a decision trace

Prompt that produced it (for reference):

```
/speckit-constitution Demo project for a HydraFusion-style multi-model broker.
Principles: OpenAI-compatible drop-in (only the model field changes); offline-first
with deterministic mock backends; test-first per user story; every response carries
an explainable decision trace (strategy, backends called, reasons, latency, cost);
strategies are plugins behind one interface driven by YAML config; simplicity/YAGNI.
Python 3.11, FastAPI, httpx, Pydantic. Out of scope: NAI/UEP/Envoy wiring, streaming,
auth, persistence.
```

## Step 1 — Specify

```bash
git checkout -b my-001   # or let the skill create the branch
```

```
/speckit-specify Build a broker that sits in front of several LLMs and looks like a
single model to clients. Clients pick a strategy by model name. Three strategies:
(1) route — classify how hard a prompt is and send it to the cheapest model that can
handle it; (2) cascade — try a cheap model first, check if the answer is good enough,
escalate to a stronger model if not; (3) fusion — ask several models in parallel and
have an aggregator model synthesize one best answer. Every response must explain what
the broker did and why, and estimate cost vs. always using the strongest model. Must
work as a self-contained demo without any real models or keys. A small CLI should
let me fire sample prompts and see the decision trace.
```

**What to look for**
- User stories ordered P1/P2/P3, each *independently* testable (cascade alone = viable MVP)
- `[NEEDS CLARIFICATION]` markers — good! That's the spec admitting what it doesn't know
- Success criteria that are measurable and tech-free

## Step 2 — Clarify (don't skip this when learning)

```
/speckit-clarify
```

Likely questions it will raise (and the answers used on the reference branch):
- How is "good enough" judged in cascade? → a pluggable quality check; default = confidence score from a judge model with a threshold
- What happens if one fusion member fails? → continue with the rest if ≥ quorum respond
- Cost model? → per-backend price per 1K tokens from config; savings vs. always-strongest baseline

## Step 3 — Plan

```
/speckit-plan Python 3.11, FastAPI + httpx + Pydantic v2 + PyYAML, pytest. Single
project src/hydra + tests/. Backends are either "mock" (deterministic, in-process,
configurable quality/latency/price) or "openai" (any OpenAI-compatible base_url).
Config in hydra.yaml. Trace in x-hydra-* headers and a "hydra" field in the body.
CLI via python -m hydra.cli.
```

**What to look for**
- Constitution Check table — every principle gets a ✅ or a justified violation
- `contracts/openapi.yaml` — the API is pinned *before* code
- `research.md` — decisions with "alternatives considered"

Optional: `/speckit-checklist api quality` to sanity-check the requirements.

## Step 4 — Tasks

```
/speckit-tasks
```

**What to look for**
- Phases: Setup → Foundational → one phase per user story → Polish
- `[P]` = parallelizable (different files). This is the hook for fanning out
  multiple agent sessions — the "10 devboxes against one plan" pattern.
- Each task names an exact file path

## Step 5 — Analyze

```
/speckit-analyze
```

Read-only consistency report. Fix anything CRITICAL before implementing.

## Step 6 — Implement

```
/speckit-implement
```

Tip: implement one user story at a time (`/speckit-implement only Phase 3 (US1)`),
run `pytest`, commit, then move on. That's where SDD pays off: each checkpoint is a
working demo.

## Step 7 — Iterate (the real lesson)

Try a change *through the spec*, not the code:

```
/speckit-specify 002 Add a "vote" strategy: N models answer, majority wins for
short factual answers, fall back to fusion when there is no majority.
```

Then plan → tasks → implement again. Notice how the constitution keeps it
consistent (plugin interface, trace, offline mocks) without you repeating it.

## Ideas for 003+ (bridge back to NAI, later)

- Expose the broker as a gRPC `ext_proc` service — mirrors how vLLM semantic-router plugs into Envoy AI Gateway
- Emit the decision trace as OTel spans → ClickHouse
- Native "broker mode" as a third UEP routing mode next to `loadbalancer`/`fallback`
