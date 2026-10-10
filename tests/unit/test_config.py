import pytest
from pydantic import ValidationError

from hydra.config import HydraConfig, load_config


def test_valid_config_loads(raw_cfg):
    cfg = HydraConfig.model_validate(raw_cfg)
    assert cfg.strategies["hydra-fusion"].quorum == 2  # default majority of 3


def test_unknown_backend_reference_fails(raw_cfg):
    raw_cfg["strategies"]["hydra-cascade"]["steps"] = ["small", "ghost"]
    with pytest.raises(ValidationError, match="unknown backends \\['ghost'\\]"):
        HydraConfig.model_validate(raw_cfg)


def test_unknown_baseline_fails(raw_cfg):
    raw_cfg["baseline"] = "nope"
    with pytest.raises(ValidationError, match="baseline 'nope'"):
        HydraConfig.model_validate(raw_cfg)


def test_strategy_name_collides_with_backend(raw_cfg):
    raw_cfg["strategies"]["small"] = raw_cfg["strategies"].pop("hydra-route")
    with pytest.raises(ValidationError, match="collide"):
        HydraConfig.model_validate(raw_cfg)


def test_quorum_larger_than_panel_fails(raw_cfg):
    raw_cfg["strategies"]["hydra-fusion"]["quorum"] = 5
    with pytest.raises(ValidationError, match="quorum 5 > panel size 3"):
        HydraConfig.model_validate(raw_cfg)


def test_route_requires_all_tiers(raw_cfg):
    del raw_cfg["strategies"]["hydra-route"]["tiers"]["hard"]
    with pytest.raises(ValidationError, match="missing"):
        HydraConfig.model_validate(raw_cfg)


def test_bundled_configs_are_valid():
    load_config("hydra.yaml")
    load_config("hydra.real.example.yaml")
