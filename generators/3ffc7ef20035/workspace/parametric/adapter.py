"""Promotion adapter for the 3ffc7ef20035 orientation-selector family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "parametric_3ffc7ef20035_orientation_prototype", _HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load sibling orientation-selector prototype")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def _settings(settings: Any) -> dict[str, Any]:
    if type(settings) is not dict or set(settings) != {"scope"}:
        raise ValueError("settings must contain exactly scope")
    if settings["scope"] not in _PROTOTYPE.SCOPES:
        raise ValueError("undeclared scope")
    return settings


def program(settings: dict[str, Any]) -> str:
    settings = _settings(settings)
    return _PROTOTYPE.program_for(settings["scope"])


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    settings = _settings(settings)
    return _PROTOTYPE.generate_episode(
        seed,
        scope=settings["scope"],
        demos=demos,
        queries=queries,
    )
