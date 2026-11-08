"""Native adapter for T-arrow room-to-room color transfers."""
from __future__ import annotations

import copy
import importlib.util
import random
from pathlib import Path

BASE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "_room_transfer_model_" + str(BASE).encode().hex(), BASE / "model.py"
)
model = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(model)

PARAMETER = "payload_mode"
VALUES = ("payload", "source_only")
SETTINGS = tuple({PARAMETER: value} for value in VALUES)
DEFAULT = {PARAMETER: "payload"}


def checked(settings):
    if (
        type(settings) is not dict
        or set(settings) != {PARAMETER}
        or type(settings[PARAMETER]) is not str
        or settings[PARAMETER] not in VALUES
    ):
        raise ValueError("expected exactly payload_mode=payload or source_only")
    return settings[PARAMETER]


def program(settings):
    mode = checked(settings)
    source = (BASE / "canonical.rkt").read_text()
    anchor = "(define payload-mode 'payload)"
    if source.count(anchor) != 1:
        raise ValueError("canonical payload-mode declaration missing or duplicated")
    return source if mode == "payload" else source.replace(anchor, "(define payload-mode 'source_only)")


def _presentation_order(seed):
    order = list(range(4))
    random.Random(f"room-transfer-presentation-v1|{seed}").shuffle(order)
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
    checked(settings)
    survivors = []
    for candidate in SETTINGS:
        mode = candidate[PARAMETER]
        if all(model.solve(pair["input"], mode) == pair["output"] for pair in episode["train"]):
            survivors.append(copy.deepcopy(candidate))
    return {"survivors": survivors, "identified": survivors == [settings]}


def sequential_description():
    return {
        "step_a": "Detect disjoint T arrows, infer each source room, target seed and payload, and detect the optional five-cell L rotation cue.",
        "intermediate": "Arrow records with source, target seed, payload and glyph cells plus an optional cue record with erased background and turn direction.",
        "step_b": "Erase annotations, flood each target room from its seed, transfer the selected color, then apply the cue's global rotation.",
        "why_b_depends_on_a": "B cannot know which room to recolor or which color and final orientation to use without A's parsed arrow and cue records.",
    }
