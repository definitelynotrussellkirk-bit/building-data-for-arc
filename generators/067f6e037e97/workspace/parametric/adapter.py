"""Native adapter for the 067f6e037e97 growth-scope family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_parametric_067_" + hashlib.sha256(str(_PATH).encode()).hexdigest()[:16]
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(_PATH)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
program = _MODULE.program


def generate(seed, settings, demos, queries):
    episode = _MODULE.generate(seed, settings, demos, queries)
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program_solution"],
    }
