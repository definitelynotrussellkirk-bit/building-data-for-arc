"""Thin native adapter for the finite H31 rotate/cue-payload family."""
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
    if path.parent != _HOME or path.is_symlink() or not path.is_file():
        raise ImportError(f"missing regular adjacent adapter resource: {filename}")
    name = "_arc_9d2f7c9e2ac4_" + path.stem + "_" + hashlib.sha256(path.read_bytes()).hexdigest()
    cached = sys.modules.get(name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load adjacent adapter resource: {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_FAMILY = _load_adjacent("family.py")
_PROGRAM_FILES = {"copy_only": "canonical.rkt", "cue_payload": "cue_payload.rkt"}


def _mode(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"mode"}:
        raise ValueError("settings must contain exactly mode")
    value = settings["mode"]
    if type(value) is not str or value not in _PROGRAM_FILES:
        raise ValueError("mode must be exactly 'copy_only' or 'cue_payload'")
    return value


def program(settings: dict[str, Any]) -> str:
    """Materialize the exact adjacent Racket source for one finite setting."""
    filename = _PROGRAM_FILES[_mode(settings)]
    path = (_HOME / filename).resolve()
    if path.parent != _HOME or path.is_symlink() or not path.is_file():
        raise ValueError(f"missing regular adjacent program resource: {filename}")
    source = path.read_text(encoding="utf-8")
    if not source:
        raise ValueError(f"empty program resource: {filename}")
    return source


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, object]:
    """Generate matched inputs and labels claimed by the selected native rule."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer; bool is forbidden")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6; bool is forbidden")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be exactly the integer 4; bool is forbidden")
    mode = _mode(settings)
    source = program({"mode": mode})
    return _FAMILY.generate_episode(seed, mode, demos, queries, source)
