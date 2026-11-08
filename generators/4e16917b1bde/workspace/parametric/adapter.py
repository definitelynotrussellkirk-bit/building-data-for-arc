"""Native promotion adapter for the 4e16917b1bde depth-policy family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "depth_policy_parametric_prototype_4e16917b1bde",
    _HERE / "prototype.py",
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load sibling depth-policy prototype")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def _settings(settings: Any) -> dict[str, Any]:
    if type(settings) is not dict or set(settings) != {"depth_policy"}:
        raise ValueError("settings must contain exactly depth_policy")
    _PROTOTYPE.program_for(settings["depth_policy"])
    return settings


def program(settings: dict[str, Any]) -> str:
    settings = _settings(settings)
    return _PROTOTYPE.program_for(settings["depth_policy"])


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    settings = _settings(settings)
    return _PROTOTYPE.generate_episode(
        seed,
        depth_policy=settings["depth_policy"],
        demos=demos,
        queries=queries,
    )
