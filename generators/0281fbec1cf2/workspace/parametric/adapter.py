"""Native finite adapter for the 0281fbec1cf2 largest-pocket family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

_HOME = Path(__file__).resolve().parent


def _load_adjacent(filename: str) -> ModuleType:
    path = (_HOME / filename).resolve()
    if path.parent != _HOME or not path.is_file():
        raise ValueError(f"missing adjacent adapter resource: {filename}")
    name = "_arc_0281fbec1cf2_" + path.stem + "_" + hashlib.sha256(str(path).encode()).hexdigest()
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


_FAMILY = _load_adjacent("native_family.py")


def _finish(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"finish"}:
        raise ValueError("settings must name exactly finish")
    value = settings["finish"]
    if type(value) is not str or value not in _FAMILY.FINISHES:
        raise ValueError("finish must be exactly 'rays_only' or 'largest_pocket'")
    return value


def program(settings: dict[str, Any]) -> str:
    """Return exact Racket source for one declared setting."""
    return _FAMILY.program_source(_finish(settings))


def generate(seed: int, settings: dict[str, Any], demos: int,
             queries: int) -> dict[str, Any]:
    """Generate matched inputs and setting-specific deterministic labels."""
    if type(seed) is not int:
        raise TypeError("seed must be a nonnegative integer; bool is forbidden")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6; bool is forbidden")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an integer in 1..4; bool is forbidden")
    finish = _finish(settings)
    source = program({"finish": finish})
    return _FAMILY.generate_episode(seed, finish, demos, queries, source)
