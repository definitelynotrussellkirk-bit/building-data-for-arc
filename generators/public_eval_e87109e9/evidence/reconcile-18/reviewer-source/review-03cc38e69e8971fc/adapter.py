"""Native adapter for header-programmed cyan cursor routes.

The complete private episode is deterministic for a seed.  Both settings share
identical inputs; only the turn hand decoded from the header changes.  Public
consumers must use :func:`public_view`, which reveals one query input and never
exposes settings, programs, answers, or future queries.
"""
from __future__ import annotations

import copy
import importlib.util
import random
from pathlib import Path

BASE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "_cursor_route_model_" + str(BASE).encode().hex(), BASE / "model.py"
)
model = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(model)

PARAMETER = "turn_mode"
VALUES = ("header", "reverse")
SETTINGS = tuple({PARAMETER: value} for value in VALUES)
DEFAULT = {PARAMETER: "header"}


def checked(settings):
    if (
        type(settings) is not dict
        or set(settings) != {PARAMETER}
        or type(settings[PARAMETER]) is not str
        or settings[PARAMETER] not in VALUES
    ):
        raise ValueError("expected exactly turn_mode=header or reverse")
    return settings[PARAMETER]


def program(settings):
    mode = checked(settings)
    source = (BASE / "canonical.rkt").read_text()
    anchor = "(define turn-mode 'header)"
    if source.count(anchor) != 1:
        raise ValueError("canonical turn-mode declaration missing or duplicated")
    return source if mode == "header" else source.replace(anchor, "(define turn-mode 'reverse)")


def _presentation_order(seed):
    order = list(range(4))
    random.Random(f"cursor-route-presentation-v1|{seed}").shuffle(order)
    return order


def generate(seed, settings, demos=2, queries=4):
    mode = checked(settings)
    model.integer(seed, 0, 2**63 - 1, "seed")
    model.integer(demos, 2, 6, "demos")
    model.integer(queries, 4, 4, "queries")

    def pair(grid):
        return {"input": copy.deepcopy(grid), "output": model.solve(grid, mode)}

    demo_inputs = [model.scene(seed, i, query=False) for i in range(demos)]
    query_bank = [model.scene(seed, 100 + i, query=True) for i in range(4)]
    query_inputs = [query_bank[i] for i in _presentation_order(seed)]
    return {
        "train": [pair(grid) for grid in demo_inputs],
        "test": [pair(grid) for grid in query_inputs],
        "program_solution": program(settings),
    }


def public_view(episode, query_index):
    model.integer(query_index, 0, len(episode["test"]) - 1, "query index")
    return copy.deepcopy(
        {
            "train": [
                {"input": pair["input"], "output": pair["output"]}
                for pair in episode["train"]
            ],
            "test": [{"input": episode["test"][query_index]["input"]}],
        }
    )


def teaching_audit(episode, settings):
    """Return finite declared-setting survivors using demonstrations only."""
    checked(settings)
    survivors = []
    for candidate in SETTINGS:
        mode = candidate[PARAMETER]
        if all(model.solve(pair["input"], mode) == pair["output"] for pair in episode["train"]):
            survivors.append(copy.deepcopy(candidate))
    return {"survivors": survivors, "identified": survivors == [settings]}


def sequential_description():
    return {
        "step_a": "Decode four target colors and left/right hands, locate the cyan cursor and body objects, then derive each route's first arrival.",
        "intermediate": "Per-command route records containing target, decoded hand, initial direction, ordered cursor positions, and blocker-bounce decisions.",
        "step_b": "Paint every cursor footprint in those route records onto the header-free body.",
        "why_b_depends_on_a": "The painted cells cannot be selected without A's target alignment, turn hand, and geometry-dependent bounce direction.",
    }
