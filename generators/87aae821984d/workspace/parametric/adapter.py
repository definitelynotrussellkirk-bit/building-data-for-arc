"""Native adapter for bottom-right and top-left motif normalization."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any

_SOURCE = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_arc_87aae821984d_anchor_" + hashlib.sha256(str(_SOURCE).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _SOURCE)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load sibling prototype: {_SOURCE}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _PROTOTYPE
exec(compile(_SOURCE.read_bytes(), str(_SOURCE), "exec"), _PROTOTYPE.__dict__)


def _settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"tile_anchor"}:
        raise ValueError("settings must contain exactly tile_anchor")
    return _PROTOTYPE._anchor(settings["tile_anchor"])


def program(settings: dict[str, Any]) -> str:
    return _PROTOTYPE.program_for(_settings(settings))


def generate(seed: int, settings: dict[str, Any], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    return _PROTOTYPE.generate_episode(seed, _settings(settings), demos=demos, queries=queries)


def public_turn(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    return _PROTOTYPE.public_turn(episode, query_index)
