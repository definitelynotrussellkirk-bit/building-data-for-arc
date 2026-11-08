"""Thin promotion adapter for df0b5d094b2d's task-local prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_PATH = Path(__file__).with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("_task_df0b5d094b2d_parametric", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(_PATH)
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def _setting(settings):
    if type(settings) is not dict or set(settings) != {"move_distance"}:
        raise ValueError("settings must contain exactly move_distance")
    distance = settings["move_distance"]
    _PROTOTYPE._validate_distance(distance)
    return distance


def program(settings):
    return _PROTOTYPE.program_for(_setting(settings))


def generate(seed, settings, demos, queries):
    distance = _setting(settings)
    return _PROTOTYPE.generate_claimed_episode(seed, distance, demos, queries)
