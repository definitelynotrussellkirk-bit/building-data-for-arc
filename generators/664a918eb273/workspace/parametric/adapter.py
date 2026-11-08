"""Native promotion adapter for tail ordering in 664a918eb273."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any

_HERE = Path(__file__).resolve().parent
_PATH = (_HERE / "prototype.py").resolve()
_NAME = "_arc_664a918eb273_tail_order_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent tail-order prototype")
prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = prototype
_SPEC.loader.exec_module(prototype)


def _order(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"tail_order"}:
        raise ValueError("settings must contain exactly tail_order")
    return prototype._tail_order(settings["tail_order"])


def program(settings: dict[str, Any]) -> str:
    return prototype.program_for(_order(settings))


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    return prototype.generate_episode(seed, _order(settings), demos, queries)
