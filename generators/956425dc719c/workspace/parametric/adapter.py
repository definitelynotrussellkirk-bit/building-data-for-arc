"""Strict promotion adapter for the 956425dc719c post-filter family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_HOME = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "parametric_956425dc719c_prototype", _HOME / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load task-local prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def _mode(settings) -> str:
    if type(settings) is not dict or set(settings) != {"post_select"}:
        raise ValueError("settings must contain exactly post_select")
    mode = settings["post_select"]
    prototype._validate_mode(mode)
    return mode


def program(settings):
    return prototype.program_for(_mode(settings), root=prototype.ROOT)


def generate(seed, settings, demos=3, queries=4, difficulty="medium"):
    return prototype.generate_claims(
        seed,
        post_select=_mode(settings),
        difficulty=difficulty,
        demos=demos,
        queries=queries,
        root=prototype.ROOT,
    )
