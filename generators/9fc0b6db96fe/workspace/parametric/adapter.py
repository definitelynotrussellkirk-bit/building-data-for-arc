"""Thin exact-path native adapter for the gallery transform-source family."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import types

_PATH = Path(__file__).resolve().with_name("prototype.py")
_BODY = _PATH.read_bytes()
_NAME = "_arc_9fc0b6db96fe_parametric_" + hashlib.sha256(str(_PATH).encode() + _BODY).hexdigest()
_MODULE = types.ModuleType(_NAME)
_MODULE.__file__ = str(_PATH)
sys.modules[_NAME] = _MODULE
exec(compile(_BODY, str(_PATH), "exec"), _MODULE.__dict__)


def program(settings):
    return _MODULE.program(settings)


def generate(seed, settings, demos=3, queries=4):
    episode = _MODULE.generate(seed, settings, demos=demos, queries=queries)
    return {
        "train": deepcopy(episode["train"]),
        "test": deepcopy(episode["test"]),
        "program_solution": episode["program_solution"],
    }
