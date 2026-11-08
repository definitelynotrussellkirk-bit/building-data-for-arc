"""Thin native adapter for the reviewed recolor-origin prototype."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import sys


_HERE = Path(__file__).resolve().parent
_NAME = "_arcpuzzles_76b818438a96_recolor_origin_prototype"
_SPEC = importlib.util.spec_from_file_location(_NAME, _HERE / "prototype.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("Cannot load this task's adjacent parametric prototype")
_prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _prototype
_SPEC.loader.exec_module(_prototype)


def _parameter(settings: dict) -> str:
    if type(settings) is not dict:
        raise TypeError("settings must be an exact dictionary")
    if set(settings) != {"recolor_origin"}:
        raise ValueError("settings must name exactly recolor_origin")
    parameter = settings["recolor_origin"]
    if type(parameter) is not str:
        raise TypeError("recolor_origin must be an exact string")
    if parameter not in ("opposite", "aligned"):
        raise ValueError("recolor_origin must be opposite or aligned")
    return parameter


def _integer(name: str, value: int, low: int, high: int) -> None:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")


def program(settings: dict) -> str:
    """Return the prototype's exact Racket source for one declared setting."""
    parameter = _parameter(settings)
    return _prototype.load_programs()[parameter]


def generate(seed: int, settings: dict, demos: int, queries: int) -> dict:
    """Build a privately labeled episode with independent supported counts."""
    parameter = _parameter(settings)
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    episode = _prototype.build_episode(
        seed=seed, parameter=parameter, n_train=demos, n_test=queries
    )

    def pairs(split: str) -> list[dict]:
        return [
            {"input": deepcopy(pair["input"]),
             "output": deepcopy(pair["selected_output"])}
            for pair in episode[split]
        ]

    return {"train": pairs("train"), "test": pairs("test"),
            "program_solution": program(settings)}
