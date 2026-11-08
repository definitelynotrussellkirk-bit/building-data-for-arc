"""Native promotion adapter for the d833a288bd7d source-cue family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "d833a288bd7d_source_cue_parametric_prototype", _HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load sibling parametric prototype")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def _settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"source_cue"}:
        raise ValueError("settings must contain exactly source_cue")
    value = settings["source_cue"]
    if type(value) is not str or value not in _PROTOTYPE.SOURCE_CUES:
        raise ValueError(f"source_cue must be one of {_PROTOTYPE.SOURCE_CUES}")
    return {"source_cue": value}


def program(settings: dict[str, Any]) -> str:
    normalized = _settings(settings)
    return _PROTOTYPE.program_for(normalized["source_cue"])


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    normalized = _settings(settings)
    return _PROTOTYPE.generate_episode(
        seed,
        source_cue=normalized["source_cue"],
        demos=demos,
        queries=queries,
    )
