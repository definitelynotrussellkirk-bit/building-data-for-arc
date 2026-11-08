"""Native opt-in adapter for the 547c45a21db1 parametric family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


_TARGET = Path(__file__).resolve().with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location(
    "_parametric_547c45a21db1_prototype", _TARGET
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load {_TARGET}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _PROTOTYPE
_SPEC.loader.exec_module(_PROTOTYPE)


def program(settings: Any) -> str:
    return _PROTOTYPE.program(settings)


def generate(
    seed: Any,
    settings: Any,
    demos: Any = 3,
    queries: Any = 4,
) -> dict[str, Any]:
    normalized = _PROTOTYPE.validate_settings(settings)
    return _PROTOTYPE.generate_episode(
        seed,
        coloring_mode=normalized["coloring_mode"],
        demos=demos,
        queries=queries,
    )
