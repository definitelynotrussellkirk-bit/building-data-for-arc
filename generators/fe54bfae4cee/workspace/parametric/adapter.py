"""Native promotion adapter for the exact-pass midpoint cascade family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "fe54bfae4cee_exact_pass_prototype",
    _HERE / "prototype.py",
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load exact-pass midpoint prototype")
prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = prototype
_SPEC.loader.exec_module(prototype)


def _settings(settings) -> int:
    if type(settings) is not dict or set(settings) != {"passes"}:
        raise ValueError("settings must contain exactly passes")
    passes = settings["passes"]
    if type(passes) is not int or passes not in (1, 2):
        raise ValueError("passes must be exact integer 1 or 2")
    return passes


def program(settings) -> str:
    return prototype.program_for(_settings(settings))


def generate(seed, settings, demos, queries) -> dict:
    passes = _settings(settings)
    return prototype.generate_episode(
        seed,
        passes=passes,
        demos=demos,
        queries=queries,
    )
