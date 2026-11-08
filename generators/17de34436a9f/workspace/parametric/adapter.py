"""Native promotion adapter for the 17de34436a9f rotation-sense family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "rotation_sense_parametric_prototype_adapter_target", _HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load sibling parametric prototype")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def _settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"rotation_sense"}:
        raise ValueError("settings must contain exactly rotation_sense")
    value = settings["rotation_sense"]
    if type(value) is not str or value not in _PROTOTYPE.ROTATION_SENSES:
        raise ValueError(
            f"rotation_sense must be one of {_PROTOTYPE.ROTATION_SENSES}"
        )
    return {"rotation_sense": value}


def program(settings: dict[str, Any]) -> str:
    normalized = _settings(settings)
    return _PROTOTYPE.program_for(normalized["rotation_sense"])


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    normalized = _settings(settings)
    return _PROTOTYPE.generate_episode(
        seed,
        rotation_sense=normalized["rotation_sense"],
        demos=demos,
        queries=queries,
    )
