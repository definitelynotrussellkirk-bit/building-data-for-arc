"""Thin source-bound adapter for b9ada70e7181's chamber-gravity family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_b9ada70e7181_parametric_" + hashlib.sha256(str(_PATH).encode()).hexdigest()[:16]
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(_PATH)
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def program(settings):
    return _PROTOTYPE.program(settings)


def generate(seed, settings, demos, queries):
    episode = _PROTOTYPE.generate(seed, settings, demos, queries)
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program_solution"],
    }
