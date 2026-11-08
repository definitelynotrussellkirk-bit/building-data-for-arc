"""Thin native-promotion adapter for the b8aea529acfd reflection family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "b8aea529acfd_reflection_policy_parametric_prototype",
    _HERE / "prototype.py",
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load sibling parametric prototype")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def _settings(settings: Any) -> dict[str, Any]:
    if not isinstance(settings, dict) or set(settings) != {"reflection_policy"}:
        raise ValueError("settings must contain exactly reflection_policy")
    return settings


def program(settings: dict[str, Any]) -> str:
    checked = _settings(settings)
    return _PROTOTYPE.program_for(checked["reflection_policy"])


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    checked = _settings(settings)
    return _PROTOTYPE.generate_episode(
        seed,
        reflection_policy=checked["reflection_policy"],
        demos=demos,
        queries=queries,
    )
