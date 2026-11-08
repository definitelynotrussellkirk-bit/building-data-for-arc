"""Thin native-promotion adapter for the dfc7297269cc parametric family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "_dfc7297269cc_parametric_prototype", _HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load sibling dfc7297269cc parametric prototype")
_IMPL = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_IMPL)


def program(settings: dict[str, Any]) -> str:
    return _IMPL.program(settings)


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    return _IMPL.generate(seed, settings, demos=demos, queries=queries)
