"""Native authoring adapter for the edb79dae legend/template family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from puzzle_generators.base import stable_rng

BASE = Path(__file__).resolve().parent
_NAME = "_edb_family_" + hashlib.sha256(str(BASE).encode()).hexdigest()[:16]
_SPEC = importlib.util.spec_from_file_location(_NAME, BASE / "family.py")
family = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = family
assert _SPEC.loader is not None
_SPEC.loader.exec_module(family)


def program(settings):
    return family.program(settings)


def generate(seed, settings, demos, queries):
    """Return a prefix plus the complete private four-query bank.

    `family.generate` already draws setting-independent inputs and a deterministic
    source-query permutation.  The adapter always materializes all four claims so
    later public presentation can independently permute and reveal one at a time.
    """
    family.integer(seed, 0, 2**63 - 1, "seed")
    family.integer(demos, 2, 6, "demos")
    family.integer(queries, 1, 4, "queries")
    full = family.generate(seed, settings, demos, 4)
    bank = copy.deepcopy(full["test"])
    full["test"] = copy.deepcopy(bank[:queries])
    full["private_query_bank"] = bank
    return full


def presentation_order(presentation_seed):
    family.integer(presentation_seed, 0, 2**63 - 1, "presentation_seed")
    order = list(range(4))
    stable_rng(presentation_seed, "edb79dae-four-query-presentation", "1").shuffle(order)
    return order


def public_view(episode, source_query_index):
    from reviewer_support import public_challenge_bytes

    family.integer(source_query_index, 0, 3, "source_query_index")
    bank = episode.get("private_query_bank")
    if type(bank) is not list or len(bank) != 4:
        raise ValueError("private four-query bank required")
    payload = {
        "train": episode["train"],
        "test": [{"input": bank[source_query_index]["input"]}],
    }
    return json.loads(public_challenge_bytes(payload))


CAUSAL_DESCRIPTIONS = {
    "step_a": (
        "For each solid source-colored square inside the frame, retain its original "
        "source color and use that source to select the complete exterior template mask."
    ),
    "intermediate": (
        "The ordered block records containing each original source color, its source-specific "
        "normalized template mask, and the mapped paint color."
    ),
    "step_b": (
        "Apply the episode mapping policy to the original source color, then paint the already "
        "selected source-template mask with that mapped color at the block position."
    ),
    "why_b_depends_on_a": (
        "Different source colors have different, sometimes disconnected masks.  Looking up a "
        "template after recoloring can select the destination color's geometry, so the final "
        "pixels require the original-source template intermediate from step A."
    ),
}


def causal_settings():
    return {"mapping_policy": "once"}


def causal_intermediate(grid):
    parsed = family.parse_grid(grid)
    records = []
    for block in parsed["blocks"]:
        source = block["color"]
        records.append(
            {
                "bbox": list(block["bbox"]),
                "source": source,
                "mapped_color": parsed["mapping"].get(source, source),
                "template_mask": [list(point) for point in sorted(parsed["templates"][source])],
            }
        )
    return {
        "mapping": [[source, target] for source, target in sorted(parsed["mapping"].items())],
        "blocks": records,
    }


def counterfactual_program():
    return (BASE / "wrong_order.rkt").read_text()
