"""Native promotion adapter for the component-motion parametric family."""
from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("_component_motion_prototype", HERE / "prototype.py")
if _spec is None or _spec.loader is None:
    raise ImportError("cannot load task-local prototype")
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def _mode(settings):
    if type(settings) is not dict or set(settings) != {"motion_mode"}:
        raise ValueError("settings must contain exactly motion_mode")
    return _prototype.validate_mode(settings["motion_mode"])


def program(settings):
    mode = _mode(settings)
    name = "canonical.rkt" if mode == "own_size" else "complement_to_largest.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def generate(seed, settings, demos, queries):
    mode = _mode(settings)
    return _prototype.generate_episode(seed, mode, demos, queries, program(settings))
