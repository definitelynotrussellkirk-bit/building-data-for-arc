"""Native finite adapter for the 8291f3ee7e54 ring-order family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

_HOME = Path(__file__).resolve().parent
_ROOT = _HOME.parents[3]


def _load_adjacent(filename: str) -> ModuleType:
    path = (_HOME / filename).resolve()
    if path.parent != _HOME or not path.is_file():
        raise ValueError(f"missing adjacent adapter resource: {filename}")
    name = "_arc_8291f3ee7e54_" + path.stem + "_" + hashlib.sha256(str(path).encode()).hexdigest()
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load adjacent adapter resource: {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_PROTOTYPE = _load_adjacent("prototype.py")
_FAMILY = _load_adjacent("native_family.py")


def _ring_order(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"ring_order"}:
        raise ValueError("settings must name exactly ring_order")
    value = settings["ring_order"]
    if type(value) is not str or value not in _FAMILY.RING_ORDERS:
        raise ValueError(
            "ring_order must be exactly 'largest_outside' or 'smallest_outside'"
        )
    return value


def program(settings: dict[str, Any]) -> str:
    """Return exact Racket source for one declared setting."""
    return _PROTOTYPE.materialize_rule(_ring_order(settings), root=_ROOT)


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int,
    queries: int,
) -> dict[str, Any]:
    """Generate setting-independent inputs and setting-specific claimed labels."""
    if type(seed) is not int:
        raise TypeError("seed must be a nonnegative integer; bool is forbidden")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6; bool is forbidden")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an integer in 1..4; bool is forbidden")
    ring_order = _ring_order(settings)
    source = program({"ring_order": ring_order})
    return _FAMILY.generate_episode(seed, ring_order, demos, queries, source)
