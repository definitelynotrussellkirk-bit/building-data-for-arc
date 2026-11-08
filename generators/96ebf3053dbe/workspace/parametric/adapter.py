"""Exact-path native adapter for the 96ebf3053dbe endpoint-policy family."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import types

_path = Path(__file__).with_name("prototype.py")
_body = _path.read_bytes()
_name = "_endpoint_policy_96ebf3053dbe_" + hashlib.sha256(str(_path).encode() + _body).hexdigest()
_prototype = types.ModuleType(_name)
_prototype.__file__ = str(_path)
sys.modules[_name] = _prototype
exec(compile(_body, str(_path), "exec"), _prototype.__dict__)


def program(settings):
    setting = _prototype.validate_settings(settings)
    return _prototype.program_for(setting)


def generate(seed, settings, demos, queries):
    setting = _prototype.validate_settings(settings)
    episode = _prototype.build_claimed_episode(seed, setting, demos, queries)
    return {
        "train": deepcopy(episode["train"]),
        "test": deepcopy(episode["test"]),
        "program_solution": episode["program_solution"],
    }
