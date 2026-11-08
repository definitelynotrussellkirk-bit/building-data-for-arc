"""Thin native adapter for the proposed 6143c7ef56be route-marker family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


_PATH = Path(__file__).with_name("prototype.py")
_NAME = "_arcpuzzles_6143c7ef56be_parametric_prototype"
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load {_PATH}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _PROTOTYPE
_SPEC.loader.exec_module(_PROTOTYPE)


def _setting(settings):
    if settings is None:
        return _PROTOTYPE.DEFAULT_ROUTE_MARKER
    if not isinstance(settings, dict) or set(settings) != {"route_marker"}:
        raise ValueError("settings must name exactly route_marker")
    value = settings["route_marker"]
    _PROTOTYPE._validate_route_marker(value)
    return value


def program(settings=None):
    return _PROTOTYPE.program_for(_setting(settings))


def generate(seed, settings, demos, queries, **kwargs):
    route_marker = _setting(settings)
    episode = _PROTOTYPE.make_episode(
        seed,
        route_marker=route_marker,
        demos=demos,
        queries=queries,
        **kwargs,
    )
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program"],
    }
