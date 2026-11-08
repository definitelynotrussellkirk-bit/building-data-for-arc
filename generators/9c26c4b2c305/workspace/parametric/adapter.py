"""Native promotion adapter for the 9c26c4b2c305 alignment-policy family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "alignment_policy_parametric_prototype_9c26c4b2c305",
    _HERE / "prototype.py",
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load sibling alignment-policy prototype")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def _settings(settings: Any) -> dict[str, Any]:
    if type(settings) is not dict or set(settings) != {"alignment_policy"}:
        raise ValueError("settings must contain exactly alignment_policy")
    return settings


def program(settings: dict[str, Any]) -> str:
    settings = _settings(settings)
    return _PROTOTYPE.program_for(settings["alignment_policy"])


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 2,
    queries: int = 4,
) -> dict[str, Any]:
    settings = _settings(settings)
    return _PROTOTYPE.generate_episode(
        seed,
        alignment_policy=settings["alignment_policy"],
        demos=demos,
        queries=queries,
    )
