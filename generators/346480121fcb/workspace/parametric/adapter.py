"""Native adapter for the selector-color versus selector-area family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_PATH = Path(__file__).with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("_task_346480121fcb_parametric", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"unable to load {_PATH}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def program(settings):
    return _PROTOTYPE.program(settings)


def generate(seed, settings, demos, queries):
    episode = _PROTOTYPE.generate_episode(seed, settings, demos=demos, queries=queries)
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program"],
    }
