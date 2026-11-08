"""Thin native adapter for the post-stamp component family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any

_SOURCE = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_arc_d3575d4206d7_finish_" + hashlib.sha256(str(_SOURCE).encode()).hexdigest()
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
