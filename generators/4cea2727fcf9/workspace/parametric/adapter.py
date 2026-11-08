"""Strict native adapter for the portal-phase prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_HOME = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "parametric_4cea2727fcf9_prototype", _HOME / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load task-local portal-phase prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def _phase(settings) -> str:
    if type(settings) is not dict or set(settings) != {"portal_phase"}:
        raise ValueError("settings must contain exactly portal_phase")
    value = settings["portal_phase"]
    prototype._validate_phase(value)
    return value


def program(settings):
    return prototype.program_for(_phase(settings), root=prototype.ROOT)


def generate(seed, settings, demos, queries):
    return prototype.generate_claims(
        seed,
        portal_phase=_phase(settings),
        demos=demos,
        queries=queries,
        root=prototype.ROOT,
    )
