"""Thin source-bound adapter for native parametric qualification."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

_PROTOTYPE_PATH = Path(__file__).resolve().with_name("aligned_state_episodes.py")
_MODULE_NAME = "_arc_a178821cc6bf_aligned_state_episodes"
_spec = importlib.util.spec_from_file_location(_MODULE_NAME, _PROTOTYPE_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"cannot load prototype from {_PROTOTYPE_PATH}")
_prototype = importlib.util.module_from_spec(_spec)
sys.modules[_MODULE_NAME] = _prototype
_spec.loader.exec_module(_prototype)


def _marked_state(settings):
    if type(settings) is not dict or set(settings) != {"marked_state"}:
        raise ValueError("settings must name exactly marked_state")
    marked_state = settings["marked_state"]
    if marked_state not in _prototype.PROGRAMS:
        raise ValueError("marked_state must be both_zero or both_nonzero")
    return marked_state


def program(settings):
    """Return the exact declared Racket source for one private setting."""
    return _prototype.PROGRAMS[_marked_state(settings)]


def generate(seed, settings, demos, queries):
    """Return deterministic claims; the independent worker replays every label."""
    marked_state = _marked_state(settings)
    episode = _prototype.build_claimed_episode(
        seed=seed,
        marked_state=marked_state,
        n_train=demos,
        n_test=queries,
    )
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": program(settings),
    }
