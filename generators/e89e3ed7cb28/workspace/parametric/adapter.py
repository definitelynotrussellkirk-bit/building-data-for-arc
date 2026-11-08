"""Strict native adapter for the bottom-survivor modal-colour family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_HOME = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "parametric_e89e3ed7cb28_prototype", _HOME / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load task-local prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def _mode(settings) -> str:
    if type(settings) is not dict or set(settings) != {"output_mode"}:
        raise ValueError("settings must contain exactly output_mode")
    mode = settings["output_mode"]
    prototype._validate_mode(mode)
    return mode


def program(settings):
    return prototype.program_for(_mode(settings), root=prototype.ROOT)


def generate(seed, settings, demos=2, queries=4):
    return prototype.generate_claims(
        seed,
        output_mode=_mode(settings),
        demos=demos,
        queries=queries,
        root=prototype.ROOT,
    )
