"""Native adapter for capped moving frames with selectable fill sweep."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("_move_fill_family", HERE / "family.py")
FAMILY = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(FAMILY)


def _setting(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {"fill_sweep"}:
        raise ValueError("settings must contain exactly fill_sweep")
    value = settings["fill_sweep"]
    if type(value) is not str or value not in ("clockwise", "counterclockwise"):
        raise ValueError("fill_sweep must be clockwise or counterclockwise")
    return value


def program(settings: object) -> str:
    value = _setting(settings)
    return (HERE / ("canonical.rkt" if value == "clockwise" else "counterclockwise.rkt")).read_text()


def mirror(grid: object, settings: object) -> list[list[int]]:
    return FAMILY.solve(grid, _setting(settings))


def analyze(grid: object, settings: object) -> dict[str, object]:
    return FAMILY.analyze(grid, _setting(settings))


def generate(seed: int, settings: object, demos: int = 2, queries: int = 4) -> dict[str, object]:
    sweep = _setting(settings)
    FAMILY._integer(seed, 0, 2**63 - 1, "seed")
    FAMILY._integer(demos, 2, 6, "demos")
    FAMILY._integer(queries, 1, 4, "queries")
    train_inputs, query_inputs = FAMILY.lesson_inputs(seed)

    def pairs(inputs):
        return [{"input": deepcopy(grid), "output": FAMILY.solve(grid, sweep)} for grid in inputs]

    return {
        "train": pairs(train_inputs[:demos]),
        "test": pairs(query_inputs[:queries]),
        "program_solution": program(settings),
        "private": FAMILY.lesson_metadata(seed),
    }


def public_turn(episode: dict[str, object], index: int) -> dict[str, object]:
    if type(index) is not int or not 0 <= index < len(episode["test"]):
        raise ValueError("query index out of range")
    return {
        "train": [{"input": deepcopy(p["input"]), "output": deepcopy(p["output"])} for p in episode["train"]],
        "test": [{"input": deepcopy(episode["test"][index]["input"])}],
    }


def rival_programs() -> dict[str, str]:
    return {
        "clockwise": (HERE / "canonical.rkt").read_text(),
        "counterclockwise": (HERE / "counterclockwise.rkt").read_text(),
        "no_fill": (HERE / "no_fill.rkt").read_text(),
        "full_distance": (HERE / "full_distance.rkt").read_text(),
    }
