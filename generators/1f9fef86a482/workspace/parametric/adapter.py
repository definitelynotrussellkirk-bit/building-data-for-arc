"""Native promotion adapter for the header-measure family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "header_measure_parametric_prototype_adapter_target", _HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load sibling header-measure prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def _settings(settings: Any) -> dict[str, str]:
    return prototype.normalize_settings(settings)


def program(settings: dict[str, Any]) -> str:
    chosen = _settings(settings)
    return prototype.program_for(chosen)


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    chosen = _settings(settings)
    episode = prototype.generate_episode(
        seed, chosen, demos=demos, queries=queries
    )
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program_solution"],
    }
