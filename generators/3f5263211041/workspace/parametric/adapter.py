"""Native promotion adapter for the keyed-gallery transformed-width relay."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any

_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_arc_3f5263211041_width_relay_" + hashlib.sha256(str(_PATH).encode()).hexdigest()[:16]
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent prototype at {_PATH}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _PROTOTYPE
_SPEC.loader.exec_module(_PROTOTYPE)


def program(settings: dict[str, Any]) -> str:
    return _PROTOTYPE.program(settings)


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    episode = _PROTOTYPE.generate(seed, settings, demos=demos, queries=queries)
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program_solution"],
    }
