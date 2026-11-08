"""Native promotion adapter for direction-parametric marker rotation."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "ffcd7510821d_direction_prototype",
    _HERE / "prototype.py",
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load direction-parametric marker rotation prototype")
prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = prototype
_SPEC.loader.exec_module(prototype)


def _direction(settings) -> str:
    if type(settings) is not dict or set(settings) != {"direction"}:
        raise ValueError("settings must contain exactly direction")
    direction = settings["direction"]
    if type(direction) is not str or direction not in prototype.DIRECTIONS:
        raise ValueError("direction must be clockwise or counterclockwise")
    return direction


def program(settings) -> str:
    return prototype.program_for(_direction(settings))


def generate(seed, settings, demos, queries) -> dict:
    direction = _direction(settings)
    return prototype.generate_episode(
        seed,
        direction=direction,
        demos=demos,
        queries=queries,
    )
