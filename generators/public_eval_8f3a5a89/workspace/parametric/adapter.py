"""Native authoring adapter for public_eval_8f3a5a89."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

BASE = Path(__file__).resolve().parent
_name = "_family8f_" + hashlib.sha256(str(BASE).encode()).hexdigest()[:16]
_spec = importlib.util.spec_from_file_location(_name, BASE / "family.py")
family = importlib.util.module_from_spec(_spec)
sys.modules[_name] = family
_spec.loader.exec_module(family)


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"contour"}
            or type(settings["contour"]) is not str
            or settings["contour"] not in family.SETTINGS):
        raise ValueError("settings must be exactly contour=outer_only|include_holes")
    return settings["contour"]


def program(settings):
    setting = _setting(settings)
    path = BASE / ("canonical.rkt" if setting == "outer_only" else "include_holes.rkt")
    return path.read_text()


def generate(seed, settings, demos, queries):
    setting = _setting(settings)
    episode = family.generate(seed, {"contour": setting}, demos, queries)
    episode["settings"] = {"contour": setting}
    episode["seed"] = seed
    episode["program_solution"] = program(settings)
    return episode


def presentation_order(presentation_seed):
    family.integer(presentation_seed, 0, 2**63 - 1, "presentation_seed")
    order = list(range(4))
    random.Random(int.from_bytes(hashlib.sha256(f"8f:{presentation_seed}".encode()).digest()[:16], "big")).shuffle(order)
    return order


def public_view(episode, source_query_index):
    family.integer(source_query_index, 0, 3, "source_query_index")
    bank = episode.get("private_query_bank")
    if type(bank) is not list or len(bank) != 4:
        raise ValueError("controller must retain exactly four private queries")
    visible = {"train": copy.deepcopy(episode["train"]),
               "test": [{"input": copy.deepcopy(bank[source_query_index]["input"])}]}
    return json.loads(json.dumps(visible, sort_keys=True, separators=(",", ":")))


def counterfactual_program():
    # For an include-holes episode, ablate complement classification by treating
    # enclosed holes as filled and therefore using the canonical outer domain.
    return program({"contour": "outer_only"})


def intermediate(grid, settings=None):
    setting = "outer_only" if settings is None else _setting(settings)
    return family.intermediate(grid, setting)


def dependency():
    return family.dependency()
