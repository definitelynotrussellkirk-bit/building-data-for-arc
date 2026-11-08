"""Thin native-promotion adapter for b6f34233d788 ranking priority."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from typing import Any

_HOME = Path(__file__).resolve().parent
_PATH = _HOME / "prototype.py"
_SPEC = importlib.util.spec_from_file_location(
    "_parametric_b6f34233d788_" + hashlib.sha256(str(_PATH).encode()).hexdigest()[:12],
    _PATH,
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load sibling prototype: {_PATH}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def _settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"ranking"}:
        raise ValueError("settings must contain exactly ranking")
    return _PROTOTYPE.validate_ranking(settings["ranking"])


def program(settings: dict[str, Any]) -> str:
    return _PROTOTYPE.program_for(_settings(settings))


def generate(seed: int, settings: dict[str, Any], demos: int = 3, queries: int = 4):
    return _PROTOTYPE.generate_episode(seed, _settings(settings), demos, queries)


def public_turn(episode, query_index=0):
    return _PROTOTYPE.public_turn(episode, query_index)
