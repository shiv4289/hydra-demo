# Data Model: Hydra Multi-Model Broker

## Config (hydra.yaml)

### BackendConfig
| field | type | notes |
|---|---|---|
| name | str | unique; also addressable as a `model` (passthrough) |
| kind | `mock` \| `openai` | |
| price_in / price_out | float | USD per 1K tokens |
| skill | float 0–1 | mock only — simulated capability |
| latency_ms | int | mock only — base latency |
| base_url, model, api_key_env, timeout_s | str/str/str/float | openai only |

### StrategyConfig (discriminated on `kind`)
- **route**: `tiers: {easy, medium, hard} → backend`
- **cascade**: `steps: [backend…]` (≥1), `judge: backend`, `threshold: float = 0.7`
- **fusion**: `panel: [backend…]` (≥2), `aggregator: backend`, `quorum: int | null` (default majority)

### HydraConfig
- `backends: list[BackendConfig]`, `strategies: dict[name, StrategyConfig]`, `baseline: backend name`, `mock_time_scale: float = 1.0`
- Validation: every referenced backend exists; strategy names don't collide with backend names; quorum ≤ panel size.

## Runtime

### Completion
`text, prompt_tokens, completion_tokens`

### CallRecord
| field | type |
|---|---|
| backend | str |
| role | `answer` \| `attempt` \| `judge` \| `panel` \| `aggregator` |
| latency_ms | float |
| prompt_tokens, completion_tokens | int |
| cost_usd | float |
| ok | bool |
| score | float \| null (judge score for attempts) |
| error | str \| null |

### DecisionTrace
| field | type |
|---|---|
| strategy | str (instance name) |
| kind | str |
| calls | list[CallRecord] (ordered) |
| selected_backend | str |
| reason | str — human-readable decision |
| details | dict — strategy-specific (difficulty signals, cascade step, quorum…) |
| total_cost_usd | float |
| baseline_cost_usd | float |
| savings_pct | float |
| wall_ms | float |

### State transitions — cascade
`attempt(i) → judge(i) → [score ≥ threshold] accepted(i)`
`                      → [score < threshold, i < n] attempt(i+1)`
`                      → [i = n] exhausted (return last answer)`
Failed attempt (error/timeout) → skip judge → next step.
