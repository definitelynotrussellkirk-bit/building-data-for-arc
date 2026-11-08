"""Native parametric episode layer for public_eval_35ab12c3.

The portable generator owns deterministic input construction and a tested Python
mirror.  The protected Racket program remains the label authority at preflight.
"""
from __future__ import annotations

from pathlib import Path
import copy
import json
import random

from reviewer_support import find_root, load_selected_generator

TASK_ID = "public_eval_35ab12c3"
HOME = Path(__file__).resolve().parents[2]
_base, _source, _source_sha256 = load_selected_generator(TASK_ID, root=find_root(__file__))

_int = _base._int
analyse = _base.analyse
solve = _base.solve
sample = _base.sample
EDGE_MODES = _base.EDGE_MODES


def settings(value: object) -> str:
    if (
        type(value) is not dict
        or set(value) != {"edge_mode"}
        or type(value["edge_mode"]) is not str
        or value["edge_mode"] not in EDGE_MODES
    ):
        raise ValueError("settings must contain exactly one declared edge_mode")
    return value["edge_mode"]


def program(value: object) -> str:
    edge_mode = settings(value)
    source = Path(__file__).with_name("canonical.rkt").read_text()
    if edge_mode == "all_8":
        return source
    needle = "(define edge-mode 'all_8)"
    if source.count(needle) != 1:
        raise ValueError("canonical edge-mode declaration drifted")
    return source.replace(needle, "(define edge-mode 'orthogonal)")


def generate(seed: object, value: object, demos: object, queries: object) -> dict[str, object]:
    edge_mode = settings(value)
    _int(seed, 0, 2**63 - 1, "seed")
    _int(demos, 2, 6, "demos")
    _int(queries, 4, 4, "queries")

    banks = {
        "train": [sample(seed, index) for index in range(demos)],
        "test": [sample(seed, index) for index in range(100, 104)],
    }
    inputs = [grid for split in ("train", "test") for grid in banks[split]]
    if len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) != len(inputs):
        raise ValueError("episode contains duplicate inputs")

    return {
        "train": [dict(input=grid, output=solve(grid, edge_mode)) for grid in banks["train"]],
        "test": [dict(input=grid, output=solve(grid, edge_mode)) for grid in banks["test"]],
        "program_solution": program(value),
    }


def public_turns(episode: object, presentation_seed: object, stop_after: object = 4) -> list[dict[str, object]]:
    _int(presentation_seed, 0, 2**63 - 1, "presentation_seed")
    _int(stop_after, 1, 4, "stop_after")
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    if len(episode["test"]) != 4:
        raise ValueError("materialize the complete four-query bank first")

    order = list(range(4))
    random.Random(presentation_seed).shuffle(order)
    train = [
        {
            "input": copy.deepcopy(pair["input"]),
            "output": copy.deepcopy(pair["output"]),
        }
        for pair in episode["train"]
    ]
    return [
        {
            "train": copy.deepcopy(train),
            "test": [{"input": copy.deepcopy(episode["test"][index]["input"])}],
        }
        for index in order[:stop_after]
    ]
