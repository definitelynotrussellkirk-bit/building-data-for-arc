"""Native promotion adapter for the 97f17772dd96 depth-order family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "depth_order_parametric_prototype_97f17772dd96",
    _HERE / "prototype.py",
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load sibling depth-order prototype")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def _settings(settings: Any) -> dict[str, Any]:
    if type(settings) is not dict or set(settings) != {"depth_order"}:
        raise ValueError("settings must contain exactly depth_order")
    _PROTOTYPE.program_for(settings["depth_order"])
    return settings


def program(settings: dict[str, Any]) -> str:
    settings = _settings(settings)
    return _PROTOTYPE.program_for(settings["depth_order"])


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 2,
    queries: int = 4,
) -> dict[str, Any]:
    settings = _settings(settings)
    return _PROTOTYPE.generate_episode(
        seed,
        depth_order=settings["depth_order"],
        demos=demos,
        queries=queries,
    )
