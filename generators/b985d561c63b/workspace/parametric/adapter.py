"""Native opt-in adapter for the b985d561c63b parametric family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


_TARGET = Path(__file__).resolve().with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location(
    "_parametric_b985d561c63b_prototype", _TARGET
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load {_TARGET}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _PROTOTYPE
_SPEC.loader.exec_module(_PROTOTYPE)


def program(settings: Any) -> str:
    normalized = _PROTOTYPE.validate_settings(settings)
    return _PROTOTYPE.program_for(normalized["stamp_anchor"])


def generate(
    seed: Any,
    settings: Any,
    demos: Any = 3,
    queries: Any = 4,
) -> dict[str, Any]:
    normalized = _PROTOTYPE.validate_settings(settings)
    return _PROTOTYPE.generate_episode(
        seed,
        stamp_anchor=normalized["stamp_anchor"],
        demos=demos,
        queries=queries,
    )
