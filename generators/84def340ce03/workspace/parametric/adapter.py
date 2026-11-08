"""Native adapter for the direct and recurrent feedback ring family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any

_SOURCE = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_arc_84def340ce03_feedback_rings_" + hashlib.sha256(str(_SOURCE).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _SOURCE)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load sibling prototype: {_SOURCE}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _PROTOTYPE
# Compile current source bytes directly so qualification cannot reuse stale bytecode.
exec(compile(_SOURCE.read_bytes(), str(_SOURCE), "exec"), _PROTOTYPE.__dict__)


def _routing(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"routing"}:
        raise ValueError("settings must name exactly routing")
    routing = settings["routing"]
    _PROTOTYPE.program_for(routing)
    return routing


def program(settings: dict[str, Any]) -> str:
    """Return the exact Racket source for one declared episode setting."""
    return _PROTOTYPE.program_for(_routing(settings))


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict:
    """Return deterministic claims; native qualification replays every label."""
    routing = _routing(settings)
    return _PROTOTYPE.generate_episode(seed, routing, demos=demos, queries=queries)
