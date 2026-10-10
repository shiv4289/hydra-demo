# Quickstart: Hydra Broker

```bash
uv venv && source .venv/bin/activate
uv pip install -e '.[dev]'

# 1. Offline demo, no server, no keys
python -m hydra.cli --all

# 2. One prompt, one strategy, full trace
python -m hydra.cli -s hydra-cascade -p "Design a rate limiter for a multi-tenant API and analyze trade-offs step by step" --trace

# 3. Run as a server
uvicorn hydra.api:app --port 8080
curl -s localhost:8080/v1/chat/completions -H 'content-type: application/json' \
  -d '{"model":"hydra-fusion","messages":[{"role":"user","content":"Explain CAP theorem"}]}' | jq .hydra

# 4. Any OpenAI SDK works — only `model` changes
python - <<'PY'
from openai import OpenAI
c = OpenAI(base_url="http://localhost:8080/v1", api_key="unused")
print(c.chat.completions.create(model="hydra-route", messages=[{"role":"user","content":"hi"}]).choices[0].message.content)
PY

# 5. Tests
pytest -q
```

Validation: step 1 prints a summary table where cascade shows ≥ 40% savings (SC-001).

Real models: copy `hydra.real.example.yaml`, point `base_url` at vLLM/Ollama, run with `HYDRA_CONFIG=your.yaml`.
