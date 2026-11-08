"""Thin native adapter for the 2dacb90452ce modal-frequency scale family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "_2dacb90452ce_native_family", _HERE / "native.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load sibling 2dacb90452ce native family")
_IMPL = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_IMPL)


def program(settings: dict[str, Any]) -> str:
    return _IMPL.program(settings)


def generate(seed: int, settings: dict[str, Any], demos: int = 3, queries: int = 4):
    return _IMPL.generate(seed, settings, demos=demos, queries=queries)
