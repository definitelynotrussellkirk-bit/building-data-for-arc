"""Thin source-bound adapter for native parametric qualification."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

_PROTOTYPE_PATH = Path(__file__).resolve().with_name("source_row_episodes.py")
_MODULE_NAME = "_arc_235a1d06b9d3_source_row_episodes"
_spec = importlib.util.spec_from_file_location(_MODULE_NAME, _PROTOTYPE_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"cannot load prototype from {_PROTOTYPE_PATH}")
_prototype = importlib.util.module_from_spec(_spec)
sys.modules[_MODULE_NAME] = _prototype
_spec.loader.exec_module(_prototype)


def _source_row(settings):
    if type(settings) is not dict or set(settings) != {"source_row"}:
        raise ValueError("settings must name exactly source_row")
    source_row = settings["source_row"]
    if source_row not in _prototype.PROGRAMS:
        raise ValueError("source_row must be row0 or row1")
    return source_row


def program(settings):
    return _prototype.PROGRAMS[_source_row(settings)]


def generate(seed, settings, demos, queries):
    source_row = _source_row(settings)
    episode = _prototype.build_claimed_episode(
        seed=seed,
        source_row=source_row,
        n_train=demos,
        n_test=queries,
    )
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": program(settings),
    }
