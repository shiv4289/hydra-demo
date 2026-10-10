"""Contract tests: HTTP surface matches contracts/openapi.yaml (Constitution I)."""

import pytest
from fastapi.testclient import TestClient

from hydra.api import create_app
from hydra.config import HydraConfig
from tests.conftest import EASY


@pytest.fixture
def client(raw_cfg):
    return TestClient(create_app(HydraConfig.model_validate(raw_cfg)))


def chat(client, model, content=EASY, **extra):
    return client.post("/v1/chat/completions", json={"model": model, "messages": [{"role": "user", "content": content}], **extra})


def test_models_lists_strategies_and_backends(client):
    r = client.get("/v1/models").json()
    assert r["object"] == "list"
    ids = {m["id"]: m["owned_by"] for m in r["data"]}
    assert ids["hydra-cascade"] == "hydra-strategy:cascade"
    assert ids["small"] == "hydra-backend:mock"


@pytest.mark.parametrize("model", ["hydra-route", "hydra-cascade", "hydra-fusion", "large"])
def test_chat_completion_shape(client, model):
    r = chat(client, model)
    assert r.status_code == 200
    b = r.json()
    assert b["object"] == "chat.completion" and b["model"] == model
    assert b["choices"][0]["message"]["role"] == "assistant"
    assert b["choices"][0]["message"]["content"]
    u = b["usage"]
    assert u["total_tokens"] == u["prompt_tokens"] + u["completion_tokens"]
    assert b["hydra"]["strategy"] == model
    for h in ("x-hydra-strategy", "x-hydra-backends", "x-hydra-selected", "x-hydra-cost-usd", "x-hydra-baseline-usd", "x-hydra-savings-pct"):
        assert h in r.headers


def test_sc005_only_model_field_changes(client):
    # identical payloads except `model`
    assert chat(client, "large").status_code == chat(client, "hydra-cascade").status_code == 200


def test_unknown_model_404_lists_valid(client):
    r = chat(client, "gpt-9")
    assert r.status_code == 404
    assert "hydra-cascade" in r.json()["error"]["message"]


def test_empty_messages_400(client):
    r = client.post("/v1/chat/completions", json={"model": "hydra-route", "messages": []})
    assert r.status_code == 400


def test_stream_rejected_400(client):
    r = chat(client, "hydra-route", stream=True)
    assert r.status_code == 400 and "streaming" in r.json()["error"]["message"]


def test_strategy_failure_502(raw_cfg):
    for b in raw_cfg["backends"]:
        b["fail"] = True
    c = TestClient(create_app(HydraConfig.model_validate(raw_cfg)))
    r = chat(c, "hydra-fusion")
    assert r.status_code == 502 and r.json()["error"]["type"] == "upstream_error"
