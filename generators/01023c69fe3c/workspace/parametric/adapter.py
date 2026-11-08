"""Thin source-bound adapter for the 01023c69fe3c cue-payload family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_parametric_01023c69fe3c_" + hashlib.sha256(str(_PATH).encode()).hexdigest()[:16]
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(_PATH)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)


def _mode(settings):
    return _MODULE.validate_settings(settings)


def program(settings):
    return _MODULE.program_for(_mode(settings))


def generate(seed, settings, demos, queries):
    mode = _mode(settings)
    episode = _MODULE.generate_episode(seed, mode, demos=demos, queries=queries)
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program_solution"],
    }
