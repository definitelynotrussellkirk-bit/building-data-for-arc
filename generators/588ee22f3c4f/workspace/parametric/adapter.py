"""Native parametric adapter for 588ee22f3c4f."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from puzzle_generators.base import stable_rng

BASE = Path(__file__).resolve().parent
_NAME = "_family_588ee_" + hashlib.sha256(str(BASE).encode()).hexdigest()[:16]
_SPEC = importlib.util.spec_from_file_location(_NAME, BASE / "family.py")
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("could not load adjacent parametric family")
family = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = family
_SPEC.loader.exec_module(family)


def _mode(settings):
    if (type(settings) is not dict or set(settings) != {"followup"}
            or type(settings["followup"]) is not str
            or settings["followup"] not in family.MODES):
        raise ValueError("settings must be exactly followup=canonical|mirror_bridge")
    return settings["followup"]


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def program(settings):
    mode = _mode(settings)
    return (BASE / ("canonical.rkt" if mode == "canonical" else "mirror_bridge.rkt")).read_text()


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
    stable_rng(seed, "588ee-private-query-presentation", "1.0.0").shuffle(bank)
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
        "train": [{"input": pair["input"], "output": pair["output"]} for pair in episode["train"]],
        "test": [{"input": bank[source_query_index]["input"]}],
    }
    return json.loads(public_challenge_bytes(payload))


CAUSAL_DESCRIPTIONS = {
    "step_a": "Execute the exact selected guide-oriented full-grid reflection, creating a partner for every source motif cell.",
    "intermediate": "Pair each original motif cell with the same-colored reflected partner that Stage A created and record the complete source-to-partner span.",
    "step_b": "Fill every background cell strictly between each paired endpoint with that pair's color, preserving guides and existing motif cells.",
    "why_b_depends_on_a": "The reflected endpoints are absent from the input. Stage B's span length and endpoint are supplied by Stage A; replacing each full span with a fixed one-step bridge changes the final output.",
}


def counterfactual_program():
    return (BASE / "wrong_intermediate.rkt").read_text()


def causal_settings():
    return {"followup": "mirror_bridge"}


def causal_intermediate(grid):
    return family.bridge_intermediate(grid)
