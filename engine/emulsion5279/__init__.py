"""Explicit stage API for the second-generation 5279 engine.

The validated V41 equations remain in :mod:`engine.src.emulsion_experiment`
while they are lifted, stage by stage, into this package.  This boundary is
intentional: new callers no longer need to mutate a chain of historical
profile modules or know which observer and delivery functions belong together.
"""

from .contracts import (
    DeliveryEncoding,
    EngineConfig,
    EngineMode,
    InputColourContract,
    ObserverPair,
    RenderedFrame,
)
from .pipeline import Emulsion5279Engine

__all__ = [
    "DeliveryEncoding",
    "Emulsion5279Engine",
    "EngineConfig",
    "EngineMode",
    "InputColourContract",
    "ObserverPair",
    "RenderedFrame",
]
