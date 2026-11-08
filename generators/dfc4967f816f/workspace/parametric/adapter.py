"""Thin promotion adapter for dfc4967f816f's task-local prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_PATH = Path(__file__).with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("_task_dfc4967f816f_parametric", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(_PATH)
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def _setting(settings):
    if type(settings) is not dict or set(settings) != {"output_color"}:
        raise ValueError("settings must contain exactly output_color")
    color = settings["output_color"]
    _PROTOTYPE._validate_output_color(color)
    return color


def program(settings):
    return _PROTOTYPE.program_for(_setting(settings))


def generate(seed, settings, demos, queries):
    color = _setting(settings)
    return _PROTOTYPE.generate_claimed_episode(seed, color, demos, queries)
