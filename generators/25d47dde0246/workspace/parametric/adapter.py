"""Native parametric adapter for 25d47dde0246."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from puzzle_generators.base import stable_rng

BASE = Path(__file__).resolve().parent
_NAME = "_family_25d47_" + hashlib.sha256(str(BASE).encode()).hexdigest()[:16]
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
        raise ValueError("settings must be exactly followup=canonical|boundary_fill")
    return settings["followup"]


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def program(settings):
    mode = _mode(settings)
    return (BASE / ("canonical.rkt" if mode == "canonical" else "boundary_fill.rkt")).read_text()


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
    stable_rng(seed, "25d47-private-query-presentation", "1.0.0").shuffle(bank)
    visible = copy.deepcopy(bank[:queries])
    return {
        "train": train,
        "test": visible,
        "private_query_bank": copy.deepcopy(bank),
        "query_source_indices": [pair["source_index"] for pair in visible],
        "program_solution": program(settings),
    }


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
    "step_a": "Execute the exact canonical rule and crop to the joint bounding box of every nonzero input cell.",
    "intermediate": "On that cropped grid, identify the input-dependent set of zero components that touch the newly exposed crop boundary, while separating enclosed zero holes.",
    "step_b": "Recolor exactly the boundary-touching zero components cyan(8), leaving enclosed zero components unchanged.",
    "why_b_depends_on_a": "Cropping changes which zero cells lie on the active boundary. Filling original-grid boundary zeros before Stage A colors the padding and expands the later crop to the full source grid, changing the final output.",
}


def counterfactual_program():
    return (BASE / "wrong_order.rkt").read_text()


def causal_settings():
    return {"followup": "boundary_fill"}


def causal_intermediate(grid):
    return family.boundary_intermediate(grid)
