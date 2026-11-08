"""Native promotion adapter for midpoint fill pass count in fe54bfae4cee."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "fe54bfae4cee_fill_passes_prototype", _HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent fill-pass prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def _settings(settings) -> dict:
    if type(settings) is not dict or set(settings) != {"fill_passes"}:
        raise ValueError("settings must contain exactly fill_passes")
    passes = settings["fill_passes"]
    if isinstance(passes, bool) or not isinstance(passes, int):
        raise TypeError("fill_passes must be a literal integer")
    if passes not in prototype.PASS_OPTIONS:
        raise ValueError(f"fill_passes must be one of {prototype.PASS_OPTIONS}")
    return settings


def program(settings):
    settings = _settings(settings)
    return prototype.program_for(settings["fill_passes"])


def generate(seed, settings, demos, queries):
    settings = _settings(settings)
    return prototype.generate_episode(seed, settings["fill_passes"], demos, queries)
