"""Native adapter for the all-holes and largest-axis mirror/sweep family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any

_SOURCE = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_arc_9b2cd53e36fb_largest_axis_" + hashlib.sha256(str(_SOURCE).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _SOURCE)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load parametric prototype from {_SOURCE}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _PROTOTYPE
_SPEC.loader.exec_module(_PROTOTYPE)


def _selection(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"selection"}:
        raise ValueError("settings must name exactly selection")
    value = settings["selection"]
    _PROTOTYPE.program_for(value)
    return value


def program(settings: dict[str, Any]) -> str:
    """Return exact Racket source for one declared setting."""
    return _PROTOTYPE.program_for(_selection(settings))


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict:
    """Generate a deterministic setting-neutral episode and private labels."""
    return _PROTOTYPE.generate_episode(seed, _selection(settings), demos=demos, queries=queries)
