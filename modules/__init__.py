"""Lazy loader for submodules."""

__all__ = [
    "planner",
    "inquiry_builder",
    "router",
    "scanner",
    "orchestrator",
    "synthesizer",
    "composer",
    "tools",
]

import importlib

def __getattr__(name):
    if name in __all__:
        return importlib.import_module(f"{__name__}.{name}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

from . import polish  # expose polishing helper
