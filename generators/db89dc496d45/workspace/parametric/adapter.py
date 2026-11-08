"""Thin exact-path native adapter for the db89dc496d45 size-relay family."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import types

_PATH = Path(__file__).resolve().with_name("prototype.py")
_BODY = _PATH.read_bytes()
_NAME = "_db89dc496d45_size_relay_" + hashlib.sha256(
    str(_PATH).encode() + _BODY
).hexdigest()
_PROTOTYPE = types.ModuleType(_NAME)
_PROTOTYPE.__file__ = str(_PATH)
sys.modules[_NAME] = _PROTOTYPE
exec(compile(_BODY, str(_PATH), "exec"), _PROTOTYPE.__dict__)


def program(settings):
    mode = _PROTOTYPE.validate_settings(settings)["mode"]
    return _PROTOTYPE.rule_text(mode)


def generate(seed, settings, demos, queries):
    mode = _PROTOTYPE.validate_settings(settings)["mode"]
    episode = _PROTOTYPE.generate_episode(
        seed=seed, mode=mode, demos=demos, queries=queries
    )
    return {
        "train": deepcopy(episode["train"]),
        "test": deepcopy(episode["test"]),
        "program_solution": episode["program_solution"],
    }
