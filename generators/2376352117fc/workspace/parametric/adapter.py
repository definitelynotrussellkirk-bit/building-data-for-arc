"""Thin native adapter for the marker-vector direction family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any

_SOURCE = Path(__file__).resolve().with_name("union_family.py")
_NAME = "_arc_2376352117fc_vector_direction_" + hashlib.sha256(str(_SOURCE).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _SOURCE)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load sibling prototype: {_SOURCE}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _PROTOTYPE
exec(compile(_SOURCE.read_bytes(), str(_SOURCE), "exec"), _PROTOTYPE.__dict__)


def program(settings: dict[str, Any]) -> str:
    return _PROTOTYPE.program(settings)


def generate(seed: int, settings: dict[str, Any], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    episode = _PROTOTYPE.generate(seed, settings, demos=demos, queries=queries)
    return {key: episode[key] for key in ("train", "test", "program_solution")}
