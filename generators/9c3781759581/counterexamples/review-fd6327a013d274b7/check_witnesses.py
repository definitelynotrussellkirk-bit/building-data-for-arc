"""Execute the unchanged canonical Racket rule on small teaching witnesses.

Run via the review packet's run_with_racket.py wrapper.  The resulting JSON
retains reference-derived outputs, source/rule hashes, and rival predictions.
"""
from __future__ import annotations

import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import find_root


TASK_ID = "9c3781759581"
WITNESSES = [
    {
        "name": "reverse_diagonal_with_outside_distractor",
        "purpose": "A 5 outside the two 9 markers refutes cropping all nonzero cells; the opposite diagonal remains valid.",
        "input": [
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 9, 0],
            [5, 0, 2, 0, 0, 0],
            [0, 9, 0, 3, 0, 0],
            [0, 0, 0, 0, 0, 0],
        ],
    },
    {
        "name": "four_side_extrema",
        "purpose": "Four edge markers require all marker coordinates; row-major first/last miss both horizontal extents.",
        "input": [
            [0, 0, 0, 0, 0, 0, 8],
            [0, 0, 0, 9, 0, 0, 0],
            [0, 9, 4, 0, 0, 9, 0],
            [0, 0, 0, 9, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ],
    },
    {"name": "singleton", "purpose": "The reference domain includes a single marker.",
     "input": [[0, 2, 0], [0, 9, 0], [0, 0, 0]]},
    {"name": "one_row", "purpose": "The reference domain includes one-row marker boxes.",
     "input": [[0, 9, 4, 9, 0]]},
    {"name": "one_column", "purpose": "The reference domain includes one-column marker boxes.",
     "input": [[0], [9], [4], [9], [0]]},
    {"name": "only_marker", "purpose": "No non-marker content is required by the reference rule.",
     "input": [[9]]},
]


def bbox_crop(grid, cells):
    top, bottom = min(r for r, _ in cells), max(r for r, _ in cells)
    left, right = min(c for _, c in cells), max(c for _, c in cells)
    return [row[left:right + 1] for row in grid[top:bottom + 1]]


def main():
    root = find_root(__file__)
    result = Catalog(root).apply(
        TASK_ID, [witness["input"] for witness in WITNESSES],
        reference="canonical", allow_unapproved=True, check_generator_domain=False,
    )
    if not result["rule_hash_matches_catalog"]:
        raise RuntimeError("Executed rule is not the selected canonical rule")
    for witness, row in zip(WITNESSES, result["results"], strict=True):
        grid = witness["input"]
        markers = [(r, c) for r, values in enumerate(grid)
                   for c, value in enumerate(values) if value == 9]
        nonzero = [(r, c) for r, values in enumerate(grid)
                   for c, value in enumerate(values) if value != 0]
        row["witness"] = witness["name"]
        row["purpose"] = witness["purpose"]
        row["independent_marker_crop"] = bbox_crop(grid, markers)
        row["rivals"] = {
            "crop_all_nonzero": bbox_crop(grid, nonzero),
            "first_last_marker_pair": bbox_crop(grid, [markers[0], markers[-1]]),
            "column_only_crop": [values[min(c for _, c in markers):max(c for _, c in markers) + 1]
                                 for values in grid],
        }
        if row["output"] != row["independent_marker_crop"]:
            raise AssertionError(f"Reference disagrees with marker-bbox interpretation: {witness['name']}")
        row["refuted_rivals"] = [name for name, prediction in row["rivals"].items()
                                  if prediction != row["output"]]
    result["command"] = (
        ".venv/bin/python3 run_with_racket.py "
        "/workspace/scratch/dec470f4e42e/arc_review/WORK/.venv/bin/python3 "
        "generators/9c3781759581/counterexamples/review-fd6327a013d274b7/check_witnesses.py"
    )
    result["command_cwd"] = str(root.parent)
    destination = Path(__file__).with_name("reference_witnesses.json")
    destination.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "destination": str(destination),
        "generator_sha256": result["generator_sha256"],
        "executed_rule_hash": result["executed_rule_hash"],
        "rule_hash_matches_catalog": result["rule_hash_matches_catalog"],
        "witnesses_checked": len(result["results"]),
        "refuted_rivals": {row["witness"]: row["refuted_rivals"] for row in result["results"]},
    }, indent=2))


if __name__ == "__main__":
    main()
