"""Thin exact-path adapter for the c5a80b7a3acc largest-result relay."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys


_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_arc_c5a80b7a3acc_largest_result_" + hashlib.sha256(str(_PATH).encode()).hexdigest()[:16]
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent prototype at {_PATH}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _PROTOTYPE
_SPEC.loader.exec_module(_PROTOTYPE)


def program(settings):
    return _PROTOTYPE.program(settings)


def generate(seed, settings, demos=3, queries=4):
    episode = _PROTOTYPE.generate(seed, settings, demos=demos, queries=queries)
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program_solution"],
    }
