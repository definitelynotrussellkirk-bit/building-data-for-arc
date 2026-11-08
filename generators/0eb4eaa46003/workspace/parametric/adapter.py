"""Exact-path native adapter for the 0eb4eaa46003 profile-source family."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import types

_path = Path(__file__).with_name("prototype.py")
_body = _path.read_bytes()
_name = "_profile_sources_0eb4eaa46003_" + hashlib.sha256(str(_path).encode() + _body).hexdigest()
_prototype = sys.modules.get(_name)
if _prototype is None:
    _prototype = types.ModuleType(_name)
    _prototype.__file__ = str(_path)
    sys.modules[_name] = _prototype
    exec(compile(_body, str(_path), "exec"), _prototype.__dict__)


def program(settings):
    selected = _prototype.validate_settings(settings)
    return _prototype.program_for(selected)


def generate(seed, settings, demos, queries):
    selected = _prototype.validate_settings(settings)
    episode = _prototype.build_claimed_episode(seed, selected, demos, queries)
    return {
        "train": deepcopy(episode["train"]),
        "test": deepcopy(episode["test"]),
        "program_solution": episode["program_solution"],
    }
