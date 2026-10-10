"""Config models. Invalid config fails at load time (FR-010)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, Literal, Union

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

# ---- backends ---------------------------------------------------------------


class _BackendBase(BaseModel):
    name: str
    price_in: float = Field(0.0, ge=0, description="USD per 1K prompt tokens")
    price_out: float = Field(0.0, ge=0, description="USD per 1K completion tokens")


class MockBackendConfig(_BackendBase):
    kind: Literal["mock"] = "mock"
    skill: float = Field(0.5, ge=0, le=1)
    latency_ms: int = Field(100, ge=0)
    fail: bool = False  # force errors (handy for tests/demos)


class OpenAIBackendConfig(_BackendBase):
    kind: Literal["openai"]
    base_url: str
    model: str
    api_key_env: str | None = None
    timeout_s: float = 30.0


BackendConfig = Annotated[Union[MockBackendConfig, OpenAIBackendConfig], Field(discriminator="kind")]

# ---- strategies -------------------------------------------------------------


class RouteConfig(BaseModel):
    kind: Literal["route"]
    tiers: dict[Literal["easy", "medium", "hard"], str]

    @field_validator("tiers")
    @classmethod
    def _all_tiers(cls, v: dict) -> dict:
        missing = {"easy", "medium", "hard"} - set(v)
        if missing:
            raise ValueError(f"route tiers missing: {sorted(missing)}")
        return v

    def referenced(self) -> list[str]:
        return list(self.tiers.values())


class CascadeConfig(BaseModel):
    kind: Literal["cascade"]
    steps: list[str] = Field(min_length=1)
    judge: str
    threshold: float = Field(0.7, ge=0, le=1)

    def referenced(self) -> list[str]:
        return [*self.steps, self.judge]


class FusionConfig(BaseModel):
    kind: Literal["fusion"]
    panel: list[str] = Field(min_length=2)
    aggregator: str
    quorum: int | None = Field(None, ge=1)

    @model_validator(mode="after")
    def _quorum(self) -> "FusionConfig":
        if self.quorum is None:
            self.quorum = len(self.panel) // 2 + 1
        if self.quorum > len(self.panel):
            raise ValueError(f"quorum {self.quorum} > panel size {len(self.panel)}")
        return self

    def referenced(self) -> list[str]:
        return [*self.panel, self.aggregator]


StrategyConfig = Annotated[Union[RouteConfig, CascadeConfig, FusionConfig], Field(discriminator="kind")]

# ---- root -------------------------------------------------------------------


class HydraConfig(BaseModel):
    backends: list[BackendConfig] = Field(min_length=1)
    strategies: dict[str, StrategyConfig] = Field(default_factory=dict)
    baseline: str
    mock_time_scale: float = Field(1.0, ge=0)

    @model_validator(mode="after")
    def _references(self) -> "HydraConfig":
        names = [b.name for b in self.backends]
        dupes = {n for n in names if names.count(n) > 1}
        if dupes:
            raise ValueError(f"duplicate backend names: {sorted(dupes)}")
        known = set(names)
        clash = known & set(self.strategies)
        if clash:
            raise ValueError(f"strategy names collide with backend names: {sorted(clash)}")
        if self.baseline not in known:
            raise ValueError(f"baseline '{self.baseline}' is not a backend; known: {sorted(known)}")
        for sname, s in self.strategies.items():
            bad = [r for r in s.referenced() if r not in known]
            if bad:
                raise ValueError(f"strategy '{sname}' references unknown backends {bad}; known: {sorted(known)}")
        return self

    def backend(self, name: str):
        return next(b for b in self.backends if b.name == name)


DEFAULT_PATH = "hydra.yaml"


def load_config(path: str | os.PathLike | None = None) -> HydraConfig:
    p = Path(path or os.environ.get("HYDRA_CONFIG", DEFAULT_PATH))
    if not p.exists():
        raise FileNotFoundError(f"hydra config not found: {p.resolve()}")
    return HydraConfig.model_validate(yaml.safe_load(p.read_text()))
