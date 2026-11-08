"""Strict promotion adapter for the right-anchor threshold family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_HOME = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "parametric_9d9fe128e55f_prototype", _HOME / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load task-local parametric prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def _mode(settings) -> str:
    if type(settings) is not dict or set(settings) != {"rank_policy"}:
        raise ValueError("settings must contain exactly rank_policy")
    return prototype._mode(settings["rank_policy"])


def program(settings):
    return prototype.program_for(_mode(settings))


def generate(seed, settings, demos=3, queries=4, difficulty="medium"):
    return prototype.generate_claims(
        seed,
        _mode(settings),
        demos=demos,
        queries=queries,
        difficulty=difficulty,
    )
