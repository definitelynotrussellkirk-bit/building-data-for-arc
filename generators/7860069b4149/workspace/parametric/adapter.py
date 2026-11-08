"""Thin promotion adapter for the proposed trail-mode family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).with_name("prototype.py")
_NAME = "_arcpuzzles_7860069b4149_parametric_prototype"
_spec = importlib.util.spec_from_file_location(_NAME, _PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"cannot load adjacent prototype: {_PATH}")
prototype = importlib.util.module_from_spec(_spec)
sys.modules[_NAME] = prototype
_spec.loader.exec_module(prototype)


def _mode(settings):
    if type(settings) is not dict or set(settings) != {"trail_mode"}:
        raise ValueError("settings must contain exactly trail_mode")
    value = settings["trail_mode"]
    prototype._validate_mode(value)
    return value


def program(settings):
    return prototype.program_for(_mode(settings))


def generate(seed, settings, demos, queries):
    mode = _mode(settings)
    episode = prototype.make_episode(
        seed,
        trail_mode=mode,
        train_count=demos,
        query_count=queries,
    )
    return dict(episode, program_solution=episode["program"])
