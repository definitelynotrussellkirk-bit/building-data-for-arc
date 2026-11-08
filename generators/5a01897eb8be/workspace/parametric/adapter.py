"""Thin native promotion adapter for the corner-ring parameter family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any

_HERE = Path(__file__).resolve().parent
_PROTOTYPE_PATH = _HERE / "prototype.py"
_MODULE_NAME = "_parametric_5a01897eb8be_" + hashlib.sha256(
    str(_PROTOTYPE_PATH).encode("utf-8")
).hexdigest()[:12]


def _load_prototype():
    module = sys.modules.get(_MODULE_NAME)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, _PROTOTYPE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load adjacent prototype: {_PROTOTYPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


_PROTOTYPE = _load_prototype()


def _settings(settings: Any) -> tuple[int, str]:
    if type(settings) is not dict or set(settings) != {"ring_step", "corners"}:
        raise ValueError("settings must contain exactly ring_step and corners")
    ring_step = settings["ring_step"]
    corners = settings["corners"]
    _PROTOTYPE._validate_setting(ring_step, corners)
    return ring_step, corners


def _count(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def program(settings: dict[str, Any]) -> str:
    """Return one exact declared Racket program."""
    ring_step, corners = _settings(settings)
    return _PROTOTYPE.materialize_rule(ring_step, corners)


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    """Project the reviewed prototype into the native labeled episode schema."""
    ring_step, corners = _settings(settings)
    demo_count = _count("demos", demos, 2, 6)
    query_count = _count("queries", queries, 4, 4)
    return _PROTOTYPE.generate_claim_episode(
        seed=seed,
        ring_step=ring_step,
        corners=corners,
        train=demo_count,
        test=query_count,
    )
