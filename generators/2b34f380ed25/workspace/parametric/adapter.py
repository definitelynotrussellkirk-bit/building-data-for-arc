"""Thin promotion adapter for the task-local mark-action prototype."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load_prototype():
    path = HERE / "prototype.py"
    name = "_panel_mark_action_prototype_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError("adjacent prototype could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_PROTOTYPE = _load_prototype()


def _mark_action(settings):
    if not isinstance(settings, dict) or set(settings) != {"mark_action"}:
        raise ValueError("settings must contain exactly mark_action")
    value = settings["mark_action"]
    if type(value) is not str or value not in _PROTOTYPE.SETTINGS:
        raise ValueError(f"mark_action must be one of {_PROTOTYPE.SETTINGS}")
    return value


def program(settings):
    return _PROTOTYPE.program_for(_mark_action(settings))


def generate(seed, settings, demos, queries):
    return _PROTOTYPE.promotion_episode(
        seed,
        _mark_action(settings),
        demos=demos,
        queries=queries,
    )
