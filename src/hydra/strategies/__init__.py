"""Strategy plugin registry. Add a strategy = add a module + one line here."""

from .base import Context, Strategy, StrategyError, StrategyResult
from .cascade import CascadeStrategy
from .fusion import FusionStrategy
from .route import RouteStrategy

STRATEGY_REGISTRY = {
    "route": RouteStrategy,
    "cascade": CascadeStrategy,
    "fusion": FusionStrategy,
}

__all__ = ["STRATEGY_REGISTRY", "Context", "Strategy", "StrategyError", "StrategyResult"]
