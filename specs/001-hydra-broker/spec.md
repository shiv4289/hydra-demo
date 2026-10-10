# Feature Specification: Hydra Multi-Model Broker

**Feature Branch**: `001-hydra-broker`

**Created**: 2026-10-10

**Status**: Clarified

**Input**: User description: "Build a broker that sits in front of several LLMs and looks like a single model to clients. Clients pick a strategy by model name. Three strategies: (1) route — classify how hard a prompt is and send it to the cheapest model that can handle it; (2) cascade — try a cheap model first, check if the answer is good enough, escalate to a stronger model if not; (3) fusion — ask several models in parallel and have an aggregator model synthesize one best answer. Every response must explain what the broker did and why, and estimate cost vs. always using the strongest model. Must work as a self-contained demo without any real models or keys. A small CLI should let me fire sample prompts and see the decision trace."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cascade: cheap first, escalate when unsure (Priority: P1)

A developer sends a chat request to the broker using a cascade strategy name.
The broker asks the cheapest model first. If the answer passes a quality check,
it is returned immediately. If not, the broker escalates to the next stronger
model, and so on until one passes or the strongest model has answered.

**Why this priority**: Cascade is the core cost-saving idea behind HydraFusion
and alone proves the value: most prompts are answered cheaply, hard ones still
get a strong answer.

**Independent Test**: Send one easy and one hard prompt to the cascade
strategy; the easy one is answered by the cheap model with no escalation, the
hard one escalates; both responses explain why.

**Acceptance Scenarios**:

1. **Given** a cascade of [small → large], **When** an easy prompt is sent, **Then** only the small model is called and the trace records "accepted at step 1" with its quality score.
2. **Given** the same cascade, **When** a hard prompt is sent and the small model's answer scores below threshold, **Then** the large model is called, its answer is returned, and the trace lists both attempts with scores.
3. **Given** every model fails the quality check, **When** the last model answers, **Then** its answer is returned anyway and the trace marks it "exhausted".

---

### User Story 2 - Decision trace and cost comparison (Priority: P1)

Every broker response tells the caller which strategy ran, which models were
called in what order, why each decision was made, how long each call took,
the estimated cost, and the estimated cost had the strongest model been used
for everything.

**Why this priority**: Constitution Principle IV. Without the trace, the demo
cannot show *why* the broker is worth having.

**Independent Test**: Any strategy response contains a machine-readable trace
with the fields above, both in response metadata and in the response body.

**Acceptance Scenarios**:

1. **Given** any strategy request, **When** the response returns, **Then** it contains strategy name, ordered list of backend calls (name, latency, tokens, cost, outcome), the final decision reason, total cost, and baseline cost.
2. **Given** a cascade accepted at step 1, **When** savings are computed, **Then** savings = baseline cost − actual cost and is positive.

---

### User Story 3 - Route: triage by difficulty (Priority: P2)

A developer sends a request to a route strategy. The broker classifies the
prompt's difficulty and sends it directly to the cheapest model rated for that
difficulty — exactly one model call.

**Why this priority**: Cheaper and faster than cascade (no wasted attempts),
but only as good as the classifier.

**Independent Test**: Send a short greeting and a multi-step reasoning prompt;
each goes to a different model and the trace shows the classified difficulty
and the signals behind it.

**Acceptance Scenarios**:

1. **Given** route tiers [easy→small, medium→medium, hard→large], **When** "hi, what's 2+2?" is sent, **Then** it is classified easy and served by small.
2. **Given** the same tiers, **When** a long prompt asking for step-by-step proof/design/analysis is sent, **Then** it is classified hard and served by large.

---

### User Story 4 - Fusion: panel plus editor (Priority: P2)

A developer sends a request to a fusion strategy. The broker sends the prompt
to several panel models in parallel, then asks an aggregator model to
synthesize one best answer from the panel's drafts.

**Why this priority**: Highest quality mode and the most "Hydra"-looking demo,
but the most expensive; valuable once cascade and trace exist.

**Independent Test**: Send any prompt to fusion; the trace shows all panel
calls ran concurrently (wall time ≈ slowest member, not the sum) and one
aggregator call.

**Acceptance Scenarios**:

1. **Given** a panel of 3 and an aggregator, **When** a prompt is sent, **Then** 3 panel calls run in parallel, 1 aggregator call follows, and the returned answer is the aggregator's.
2. **Given** one panel member fails, **When** the remaining members meet quorum, **Then** fusion proceeds with the successful drafts and the trace records the failure.
3. **Given** fewer members than quorum succeed, **When** fusion runs, **Then** the request fails with a clear error naming the failed members.

---

### User Story 5 - Demo CLI (Priority: P3)

A developer runs a CLI that fires a set of sample prompts (or a custom one) at
one or all strategies and prints the answer and a readable decision trace,
plus a summary table of cost and savings.

**Why this priority**: Makes the demo presentable in 30 seconds; not needed
for the broker to work.

**Independent Test**: Running the CLI with no server and no keys prints a
results table for all strategies.

**Acceptance Scenarios**:

1. **Given** default config, **When** the CLI runs with `--all`, **Then** each sample prompt is sent to each strategy and a summary table is printed.

---

### Edge Cases

- Unknown `model` name → OpenAI-style 404 error listing valid names.
- `model` naming a real backend directly → passthrough to that backend (broker is optional per request).
- Backend timeout or error mid-cascade → treated as a failed attempt; cascade escalates.
- Empty `messages` → 400 validation error.
- Config references a backend that does not exist → startup fails with a clear message.
- Streaming requested → rejected with 400 "streaming not supported in this demo".

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST expose an OpenAI-compatible chat completions endpoint and a models listing endpoint.
- **FR-002**: System MUST select a strategy (or a direct backend) from the request's `model` field alone.
- **FR-003**: System MUST support three strategy kinds: route, cascade, fusion; multiple named instances of each kind MAY be configured.
- **FR-004**: Cascade MUST call backends in configured order and stop at the first answer that passes the quality check.
- **FR-005**: Quality check MUST be pluggable; default is a judge that returns a 0–1 score compared to a configured threshold.
- **FR-006**: Route MUST make exactly one backend call, chosen by a difficulty classification.
- **FR-007**: Fusion MUST call panel members concurrently and proceed if at least `quorum` succeed.
- **FR-008**: Every response MUST include a decision trace (strategy, ordered calls with latency/tokens/cost/outcome, reason, total cost, baseline cost, savings).
- **FR-009**: System MUST run fully offline with deterministic mock backends; real OpenAI-compatible backends are optional config.
- **FR-010**: Invalid configuration MUST fail at startup.
- **FR-011**: System MUST provide a CLI that runs sample prompts against strategies without a running server.

### Key Entities

- **Backend**: a model endpoint — name, kind (mock or real), price per 1K input/output tokens, capability tier.
- **Strategy**: a named orchestration recipe — kind (route/cascade/fusion) plus kind-specific settings referencing backends.
- **Decision Trace**: the per-request record of what the broker did and why.
- **Call Record**: one backend invocation inside a trace — backend, role (attempt/panel/aggregator/judge), latency, tokens, cost, outcome, score.

## Clarifications

### Session 2026-10-10

- Q: How is "good enough" judged in cascade? → A: Pluggable quality check; default asks a judge for a 0–1 confidence score and accepts at ≥ threshold (default 0.7). Mock judge is deterministic.
- Q: Does the judge's own cost count? → A: Yes, judge calls appear in the trace and in total cost.
- Q: What happens if a fusion member fails? → A: Continue if successes ≥ quorum (default: majority of panel); otherwise error.
- Q: How is cost estimated? → A: Tokens × configured per-1K price; mock backends estimate tokens as ~words × 1.3. Baseline = the configured strongest backend answering the same prompt once.
- Q: How does the route classifier work? → A: Heuristic signals (length, reasoning keywords, code blocks, multi-part questions) → score → tier. Pluggable later.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On the bundled sample prompt set, cascade reports ≥ 40% estimated cost savings vs. the always-strongest baseline.
- **SC-002**: Fusion wall-clock latency is within 20% of its slowest panel member (proves parallelism).
- **SC-003**: A newcomer can clone, install, and see the CLI summary table in under 5 minutes with no keys.
- **SC-004**: 100% of acceptance scenarios above are covered by automated tests that pass offline.
- **SC-005**: Switching a client from a direct model to a broker strategy requires changing only the `model` value.

## Assumptions

- Non-streaming only for this demo.
- Single user, local process; no auth, rate limits, or persistence.
- Mock "quality" is simulated: each mock backend has a skill level, and the mock judge scores an answer from the backend's skill vs. the prompt's difficulty.
- Integration with NAI, UEP, or Envoy is explicitly out of scope (future feature).
