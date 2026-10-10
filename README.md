# hydra-demo

A HydraFusion-style multi-model **broker**, built with GitHub Spec Kit to learn
Spec-Driven Development. Runs fully offline — mock models, no keys.

> Learning SDD? Start at **[PLAYBOOK.md](PLAYBOOK.md)** on `main`. This branch
> (`001-hydra-broker`) is the reference answer. Its commits follow the SDD stages:
> `spec(001)` → `plan(001)` → `tasks(001)` → `impl(001)` per user story.

## The idea in one picture

```
client ──(model: "hydra-cascade")──▶  BROKER  ──▶ small / medium / large / judge
         looks like ONE model         picks a strategy by model name,
                                      returns answer + decision trace
```

| model | strategy | analogy | calls |
|---|---|---|---|
| `hydra-route` | classify difficulty → cheapest capable model | hospital triage nurse | 1 |
| `hydra-cascade` | cheap model first; judge scores it; escalate if < threshold | junior dev; senior reviews only when unsure | 2–5 |
| `hydra-fusion` | panel answers in parallel; aggregator synthesizes | panel of experts + an editor | N+1 |
| `small` / `large` / … | passthrough to one backend | — | 1 |

## Run it

```bash
uv venv && source .venv/bin/activate
uv pip install -e '.[dev]'

python -m hydra.cli --all                 # summary table, all strategies × sample prompts
python -m hydra.cli -s hydra-cascade -p "Design a rate limiter and analyze trade-offs step by step" --trace
uvicorn hydra.api:app --port 8080         # OpenAI-compatible server
pytest -q                                 # 48 tests, offline
```

Sample `--all` result (mock prices, 8 prompts, mostly easy):

| strategy | savings vs always-`large` | why |
|---|---|---|
| route | ~57% | one call, but trusts a heuristic classifier |
| cascade | ~48% | easy prompts stop at `small`; hard ones pay for the failed attempts (-23% on the hardest) |
| fusion | ~-170% | quality mode: 4 calls per request, latency ≈ slowest member |

Example trace:

```
▶ [hydra-cascade] Design a rate limiter for a multi-tenant API and analyze trade-offs step by step
  decision : exhausted: 2 cheaper step(s) below 0.7, returned strongest model large
    ok  attempt    small       14.7 ms    19+208  tok  $0.000085 score=0.34
    ok  judge      judge        5.3 ms    87+3    tok  $0.000010 score=0.34
    ok  attempt    medium      33.4 ms    19+208  tok  $0.000643 score=0.57
    ok  judge      judge        5.3 ms    87+3    tok  $0.000010 score=0.57
    ok  attempt    large       86.5 ms    19+208  tok  $0.003215
  cost     : $0.003963 vs baseline $0.003215 → savings -23.3%
```

Every HTTP response also carries `x-hydra-*` headers and a `hydra` body field with the same trace.

## How the mocks fake "quality"

- Each mock has a `skill` (0–1). Quality ≈ `skill − 0.8·difficulty + 0.35` (± small deterministic jitter).
- The answer ends with a visible marker `⟨mock:small q=0.62⟩`; the mock judge reads it.
- So the real judge prompt/parse path runs, and results are reproducible.

## Real models

`hydra.real.example.yaml` mixes Ollama, vLLM and a hosted API. Run with
`HYDRA_CONFIG=hydra.real.example.yaml uvicorn hydra.api:app`.

## Layout

```
specs/001-hydra-broker/   spec → plan → research → data-model → contracts → tasks
src/hydra/
  config.py      YAML → validated Pydantic (bad config fails at startup)
  difficulty.py  heuristic classifier (route + mock quality)
  backends.py    MockBackend, OpenAIBackend
  prompts.py     judge / aggregator prompts
  quality.py     JudgeCheck (pluggable)
  strategies/    route.py, cascade.py, fusion.py + registry
  broker.py      model → strategy | backend, baseline cost
  api.py         OpenAI-compatible FastAPI app
  cli.py         demo CLI
tests/           unit / integration (1 module per user story) / contract
```

## Next features to try via SDD

- `002` vote strategy (majority for short factual answers, fallback to fusion)
- `003` semantic (embedding) classifier instead of heuristics
- `004` OTel spans for the decision trace
- later: gRPC `ext_proc` shape, to mirror how semantic-router plugs into Envoy AI Gateway
