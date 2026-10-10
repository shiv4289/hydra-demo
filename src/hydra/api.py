"""OpenAI-compatible HTTP surface (Constitution I). Talks only to Broker."""

from __future__ import annotations

import time
import uuid
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .broker import Broker, UnknownModel
from .config import HydraConfig
from .strategies import StrategyError


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    model: str
    messages: list[Message] = Field(min_length=1)
    temperature: float | None = None
    max_tokens: int | None = None
    stream: bool = False


def _error(status: int, message: str, type_: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"message": message, "type": type_}})


def create_app(cfg: HydraConfig | None = None, config_path: str | None = None) -> FastAPI:
    broker = Broker(cfg) if cfg else Broker.from_file(config_path)
    app = FastAPI(title="Hydra Broker", version="0.1.0")
    app.state.broker = broker

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError):
        return _error(400, str(exc.errors()[0].get("msg", "invalid request")), "invalid_request_error")

    @app.get("/v1/models")
    async def models():
        return {
            "object": "list",
            "data": [{"id": m, "object": "model", "owned_by": owner} for m, owner in broker.models()],
        }

    @app.post("/v1/chat/completions")
    async def chat(req: ChatRequest):
        if req.stream:
            return _error(400, "streaming not supported in this demo", "invalid_request_error")
        try:
            result = await broker.complete(
                req.model,
                [m.model_dump() for m in req.messages],
                temperature=req.temperature,
                max_tokens=req.max_tokens,
            )
        except UnknownModel as e:
            return _error(404, str(e), "model_not_found")
        except StrategyError as e:
            return _error(502, str(e), "upstream_error")

        c, trace = result.completion, result.trace
        body = {
            "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": req.model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": c.text}, "finish_reason": "stop"}],
            "usage": {
                "prompt_tokens": c.prompt_tokens,
                "completion_tokens": c.completion_tokens,
                "total_tokens": c.prompt_tokens + c.completion_tokens,
            },
            "hydra": trace.model_dump(),
        }
        return JSONResponse(body, headers=trace.headers())

    return app


def __getattr__(name: str):
    # `uvicorn hydra.api:app` — build lazily so importing this module never needs a config file
    if name == "app":
        return create_app()
    raise AttributeError(name)
