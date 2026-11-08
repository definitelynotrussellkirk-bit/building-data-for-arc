"""Native authoring adapter for the 38007db0 row-outlier family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from puzzle_generators.base import stable_rng

BASE = Path(__file__).resolve().parent
_NAME = "_family_380_" + hashlib.sha256(str(BASE).encode()).hexdigest()[:16]
_SPEC = importlib.util.spec_from_file_location(_NAME, BASE / "family.py")
family = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = family
assert _SPEC.loader is not None
_SPEC.loader.exec_module(family)


def program(settings):
    return family.program(settings)


def generate(seed, settings, demos, queries):
    family.integer(seed, 0, 2**63 - 1, "seed")
    family.integer(demos, 2, 6, "demos")
    family.integer(queries, 1, 4, "queries")
    return family.generate(seed, settings, demos, queries)


def presentation_order(presentation_seed):
    family.integer(presentation_seed, 0, 2**63 - 1, "presentation_seed")
    order = list(range(4))
    stable_rng(presentation_seed, "38007db0-four-query-presentation", "1").shuffle(order)
    return order


def public_view(episode, source_query_index):
    from reviewer_support import public_challenge_bytes

    family.integer(source_query_index, 0, 3, "source_query_index")
    bank = episode.get("private_query_bank")
    if type(bank) is not list or len(bank) != 4:
        raise ValueError("private four-query bank required")
    return json.loads(
        public_challenge_bytes(
            {
                "train": episode["train"],
                "test": [{"input": bank[source_query_index]["input"]}],
            }
        )
    )


CAUSAL_DESCRIPTIONS = {
    "step_a": (
        "Within each separator-bounded tile row, compare multiplicities to identify the sole "
        "outlier tile and the repeated tile, then count their cellwise disagreements."
    ),
    "intermediate": (
        "The row records containing the selected outlier tile, repeated tile, original row "
        "index, unique-tile column, and their input-derived Hamming-difference count."
    ),
    "step_b": (
        "Stable-sort those selected row records by decreasing disagreement count and stack the "
        "outlier tiles in that derived order inside the preserved horizontal separator bands."
    ),
    "why_b_depends_on_a": (
        "The ranking key is not the outlier's ink count or its source position; it is defined only "
        "after step A identifies both the outlier and repeated tile and compares them cellwise."
    ),
}


def causal_settings():
    return {"stack_order": "difference_desc"}


def causal_intermediate(grid):
    info = family.analyze(grid)
    return {
        "rows": [
            {
                "source_row": row["row_index"],
                "unique_column": row["unique_column"],
                "difference_count": row["difference_count"],
                "foreground_count": row["foreground_count"],
                "unique_tile": row["unique"],
                "repeated_tile": row["repeated"],
            }
            for row in info["rows"]
        ],
        "difference_desc_order": [
            row["row_index"]
            for row in sorted(
                info["rows"], key=lambda row: (-row["difference_count"], row["row_index"])
            )
        ],
    }


def counterfactual_program():
    return (BASE / "foreground_desc.rkt").read_text()
