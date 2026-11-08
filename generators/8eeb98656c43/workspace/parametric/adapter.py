"""Native parametric adapter for 8eeb98656c43."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from puzzle_generators.base import stable_rng

BASE = Path(__file__).resolve().parent
_NAME = "_family_8eeb_" + hashlib.sha256(str(BASE).encode()).hexdigest()[:16]
_SPEC = importlib.util.spec_from_file_location(_NAME, BASE / "family.py")
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("could not load adjacent parametric family")
family = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = family
_SPEC.loader.exec_module(family)


def _mode(settings):
    if (
        type(settings) is not dict
        or set(settings) != {"followup"}
        or type(settings["followup"]) is not str
        or settings["followup"] not in family.MODES
    ):
        raise ValueError("settings must be exactly followup=canonical|ray_tail")
    return settings["followup"]


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def program(settings):
    mode = _mode(settings)
    filename = "canonical.rkt" if mode == "canonical" else "ray_tail.rkt"
    return (BASE / filename).read_text()


def _pair(seed, source_index, mode):
    grid = family.scene(seed, source_index)
    return {"input": grid, "output": family.solve(grid, mode), "source_index": source_index}


def generate(seed, settings, demos, queries):
    mode = _mode(settings)
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")

    train = [_pair(seed, index, mode) for index in range(demos)]
    bank = [_pair(seed, index, mode) for index in range(6, 10)]
    stable_rng(seed, "8eeb-private-query-presentation", "1.0.0").shuffle(bank)
    visible = copy.deepcopy(bank[:queries])
    return {
        "train": train,
        "test": visible,
        "private_query_bank": copy.deepcopy(bank),
        "query_source_indices": [pair["source_index"] for pair in visible],
        "program_solution": program(settings),
    }


def presentation_order(presentation_seed):
    _integer(presentation_seed, 0, 2**63 - 1, "presentation_seed")
    order = list(range(4))
    stable_rng(presentation_seed, "8eeb-four-query-presentation", "1.0.0").shuffle(order)
    return order


def public_view(episode, source_query_index):
    from reviewer_support import public_challenge_bytes

    _integer(source_query_index, 0, 3, "source_query_index")
    bank = episode.get("private_query_bank")
    if type(bank) is not list or len(bank) != 4:
        raise ValueError("controller must retain exactly four private queries")
    payload = {
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [{"input": bank[source_query_index]["input"]}],
    }
    return json.loads(public_challenge_bytes(payload))


CAUSAL_DESCRIPTIONS = {
    "step_a": "Execute the exact canonical reflection: every red cell in the left half is mirrored across the center axis and the reflected copy is painted orange.",
    "intermediate": "Locate the unique color-1 marker on the center axis; on its row, record the first contiguous orange run to the right that Stage A created and its exact length.",
    "step_b": "Immediately after that orange run, paint an equal-length color-1 tail on background cells.",
    "why_b_depends_on_a": "The input contains no orange run. Its position and length exist only after Stage A mirrors the adjacent red run, so replacing the measured length with a fixed one-cell guess changes the final grid.",
}


def counterfactual_program():
    return (BASE / "wrong_intermediate.rkt").read_text()


def causal_settings():
    return {"followup": "ray_tail"}


def causal_intermediate(grid):
    return family.ray_intermediate(grid)
