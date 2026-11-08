"""Native promotion adapter for the fe0dc9f32b7b palette-direction family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "fe0dc9f32b7b_palette_direction_prototype", _HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load sibling palette-direction prototype")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def _settings(settings: Any) -> dict[str, Any]:
    if not isinstance(settings, dict) or set(settings) != {"palette_direction"}:
        raise ValueError("settings must contain exactly palette_direction")
    _PROTOTYPE.program_for(settings["palette_direction"])
    return settings


def program(settings: dict[str, Any]) -> str:
    settings = _settings(settings)
    return _PROTOTYPE.program_for(settings["palette_direction"])


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    settings = _settings(settings)
    return _PROTOTYPE.generate_episode(
        seed,
        palette_direction=settings["palette_direction"],
        demos=demos,
        queries=queries,
    )
