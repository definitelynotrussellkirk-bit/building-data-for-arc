"""Exact-path native adapter for d57b7deebba2's activated-relay family."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import types

_path = Path(__file__).with_name("prototype.py")
_body = _path.read_bytes()
_name = "_activated_relay_d57b7deebba2_" + hashlib.sha256(str(_path).encode() + _body).hexdigest()
_prototype = types.ModuleType(_name)
_prototype.__file__ = str(_path)
sys.modules[_name] = _prototype
exec(compile(_body, str(_path), "exec"), _prototype.__dict__)


def program(settings):
    return _prototype.program(settings)


def generate(seed, settings, demos, queries):
    setting = _prototype.validate_settings(settings)
    episode = _prototype.build_claimed_episode(seed, setting, demos, queries)
    return {
        "train": deepcopy(episode["train"]),
        "test": deepcopy(episode["test"]),
        "program_solution": episode["program_solution"],
    }
