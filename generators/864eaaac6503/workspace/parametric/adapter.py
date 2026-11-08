"""Thin source-bound adapter for native parametric qualification."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

_PROTOTYPE_PATH = Path(__file__).resolve().with_name("rotation_episodes.py")
_MODULE_NAME = "_arc_864eaaac6503_rotation_episodes"
_spec = importlib.util.spec_from_file_location(_MODULE_NAME, _PROTOTYPE_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"cannot load prototype from {_PROTOTYPE_PATH}")
_prototype = importlib.util.module_from_spec(_spec)
sys.modules[_MODULE_NAME] = _prototype
_spec.loader.exec_module(_prototype)


def _direction(settings):
    if type(settings) is not dict or set(settings) != {"direction"}:
        raise ValueError("settings must name exactly direction")
    direction = settings["direction"]
    if direction not in _prototype.PROGRAMS:
        raise ValueError("direction must be ccw or cw")
    return direction


def program(settings):
    """Return the exact declared Racket source for one private setting."""
    return _prototype.PROGRAMS[_direction(settings)]


def generate(seed, settings, demos, queries):
    """Return deterministic claims; the independent worker replays every label."""
    direction = _direction(settings)
    episode = _prototype.build_claimed_episode(
        seed=seed,
        direction=direction,
        n_train=demos,
        n_test=queries,
    )
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": program(settings),
    }
