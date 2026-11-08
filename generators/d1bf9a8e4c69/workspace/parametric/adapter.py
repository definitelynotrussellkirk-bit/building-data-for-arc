"""Thin native adapter for the d1bf9a8e4c69 corner-composition family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parent
_PROTOTYPE_PATH = HOME / "prototype.py"
_MODULE_NAME = "_arc_d1bf9a8e4c69_parametric_prototype"
_spec = importlib.util.spec_from_file_location(_MODULE_NAME, _PROTOTYPE_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"cannot load prototype from {_PROTOTYPE_PATH}")
_prototype = importlib.util.module_from_spec(_spec)
sys.modules[_MODULE_NAME] = _prototype
_spec.loader.exec_module(_prototype)

FINISHES = _prototype.FINISHES


def _finish(settings) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"finish"}
        or type(settings["finish"]) is not str
        or settings["finish"] not in FINISHES
    ):
        raise ValueError("settings must contain exactly one supported finish")
    return settings["finish"]


def program(settings) -> str:
    finish = _finish(settings)
    filename = "canonical.rkt" if finish == "corners_only" else "nearest_corner_bridge.rkt"
    return (HOME / "rules" / filename).read_text(encoding="utf-8")


def generate(seed, settings, demos, queries):
    finish = _finish(settings)
    episode = _prototype.build_claimed_episode(
        seed=seed,
        finish=finish,
        n_train=demos,
        n_test=queries,
    )
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": program(settings),
    }
