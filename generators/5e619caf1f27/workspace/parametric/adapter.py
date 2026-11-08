"""Thin source-bound adapter for native parametric qualification."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

_PROTOTYPE_PATH = Path(__file__).resolve().with_name("edge_cap_episodes.py")
_MODULE_NAME = "_arc_5e619caf1f27_edge_cap_episodes"
_spec = importlib.util.spec_from_file_location(_MODULE_NAME, _PROTOTYPE_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"cannot load prototype from {_PROTOTYPE_PATH}")
_prototype = importlib.util.module_from_spec(_spec)
sys.modules[_MODULE_NAME] = _prototype
_spec.loader.exec_module(_prototype)


def _edge_cap(settings):
    if type(settings) is not dict or set(settings) != {"edge_cap"}:
        raise ValueError("settings must name exactly edge_cap")
    edge_cap = settings["edge_cap"]
    if edge_cap not in _prototype.PROGRAMS:
        raise ValueError("edge_cap must be capped or uncapped_inner")
    return edge_cap


def program(settings):
    return _prototype.PROGRAMS[_edge_cap(settings)]


def generate(seed, settings, demos, queries):
    edge_cap = _edge_cap(settings)
    episode = _prototype.build_claimed_episode(
        seed=seed,
        edge_cap=edge_cap,
        n_train=demos,
        n_test=queries,
    )
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": program(settings),
    }
