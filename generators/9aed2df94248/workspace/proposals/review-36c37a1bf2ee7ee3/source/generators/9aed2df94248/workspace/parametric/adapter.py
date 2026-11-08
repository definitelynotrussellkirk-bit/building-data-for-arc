"""Native promotion adapter for the 9aed2df94248 analogy-direction family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_HOME = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "parametric_9aed2df94248_prototype", _HOME / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load task-local prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def _direction(settings) -> str:
    if type(settings) is not dict or set(settings) != {"analogy_direction"}:
        raise ValueError("settings must contain exactly analogy_direction")
    direction = settings["analogy_direction"]
    prototype._validate_direction(direction)
    return direction


def program(settings):
    return prototype.program_for(_direction(settings))


def generate(seed, settings, demos=3, queries=4):
    return prototype.generate_claims(
        seed,
        direction=_direction(settings),
        demos=demos,
        queries=queries,
    )
