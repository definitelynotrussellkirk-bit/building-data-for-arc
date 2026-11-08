"""Native adapter for the b99e7126 nested tile-mask family."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

BASE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("_b99e7126_family_adapter", BASE / "family.py")
family = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = family
_spec.loader.exec_module(family)

CAUSAL_DESCRIPTIONS = {
    "step_a": "Decode the unique color inside the rare tile as a local mask, locate its unique macro translation, and complete every missing rare tile.",
    "intermediate": "The exact completed macro coordinates of the rare-tile mask and their per-row counts.",
    "step_b": "Select the unique densest completed macro row and recolor the encoded ink cells of its rare tiles with color 9.",
    "why_b_depends_on_a": "The visible rare tiles deliberately have a different densest row from the completed mask, so Stage B must consume Stage A's completed coordinates.",
}


def _setting(settings):
    if (
        type(settings) is not dict
        or set(settings) != {"finish_rule"}
        or type(settings["finish_rule"]) is not str
        or settings["finish_rule"] not in family.SETTINGS
    ):
        raise ValueError(
            "Expected exactly finish_rule=complete_only|complete_then_highlight_densest_row"
        )
    return settings["finish_rule"]


def program(settings):
    name = (
        "canonical.rkt"
        if _setting(settings) == "complete_only"
        else "complete_then_highlight_densest_row.rkt"
    )
    return (BASE / name).read_text()


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _order(seed, tag):
    _integer(seed, 0, 2**63 - 1, "seed")
    digest = hashlib.sha256(f"b99e7126|{tag}|{seed}".encode()).digest()
    order = list(range(4))
    random.Random(int.from_bytes(digest, "big")).shuffle(order)
    return order


def generate(seed, settings, demos=2, queries=4):
    selected = _setting(settings)
    family.validate_request(seed, demos, queries)

    def pair(index, query=False):
        grid = family.scene(seed, index, query=query)
        return {"input": grid, "output": family.solve(grid, selected)}

    bank = [pair(index, True) for index in range(4)]
    order = _order(seed, "native-query-presentation")
    ordered = [bank[index] for index in order]
    return {
        "train": [pair(index) for index in range(demos)],
        "test": copy.deepcopy(ordered[:queries]),
        "private_query_bank": bank,
        "private_query_order": order,
        "program_solution": program(settings),
    }


def presentation_order(presentation_seed):
    return _order(
        _integer(presentation_seed, 0, 2**63 - 1, "presentation_seed"),
        "public-query-presentation",
    )


def public_view(episode, turn=0, presentation_seed=0):
    from reviewer_support import public_challenge_bytes

    _integer(turn, 0, 3, "turn")
    order = presentation_order(presentation_seed)
    bank = episode.get("private_query_bank")
    if type(bank) is not list or len(bank) != 4:
        raise ValueError("controller must retain exactly four private queries")
    visible = {
        "train": episode["train"],
        "test": [{"input": bank[order[turn]]["input"]}],
    }
    return json.loads(public_challenge_bytes(visible))


def causal_settings():
    return {"finish_rule": "complete_then_highlight_densest_row"}


def causal_intermediate(grid):
    return family.causal_intermediate(grid)


def counterfactual_program():
    return (BASE / "highlight_visible_densest_row.rkt").read_text()
