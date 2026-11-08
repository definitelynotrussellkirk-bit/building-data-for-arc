"""Compare current Racket outputs with the replace-all-3/2 shortcut."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def rival(grid):
    return [[8 if value == 3 else 0 if value == 2 else value for value in row] for row in grid]


def main() -> None:
    here = Path(__file__).resolve().parent
    generation = json.loads((here / "generation.json").read_text())
    inputs = json.loads((here / "input.json").read_text())
    racket = json.loads((here / "racket.json").read_text())
    official = [row["output"] for row in racket["results"]]
    rivals = [rival(grid) for grid in inputs]
    matches = [candidate == expected for candidate, expected in zip(rivals, official)]
    if matches != [True, True, True, False]:
        raise AssertionError(f"unexpected shortcut signature: {matches}")

    differing_cells = []
    for row, expected_row in enumerate(official[3]):
        for col, expected in enumerate(expected_row):
            actual = rivals[3][row][col]
            if actual != expected:
                differing_cells.append(
                    {
                        "row": row,
                        "col": col,
                        "official": expected,
                        "rival": actual,
                        "input": inputs[3][row][col],
                    }
                )
    if len(differing_cells) != 3:
        raise AssertionError(f"expected three query differences, got {len(differing_cells)}")

    (here / "rival.json").write_text(json.dumps(rivals, indent=2) + "\n")
    record = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": generation["task_id"],
        "finding": "three-demo lesson admits replace-every-3-and-2 shortcut",
        "generator_sha256": generation["generator_sha256"],
        "executed_rule_hash": racket["executed_rule_hash"],
        "rule_text_sha256": racket["rule_text_sha256"],
        "seed": generation["seed"],
        "difficulty": generation["difficulty"],
        "sample_indices": generation["sample_indices"],
        "self_check": generation["self_check"],
        "belongs_to_generated_support": True,
        "rival": "replace every 3 with 8 and every 2 with 0, regardless of adjacency",
        "rival_matches": matches,
        "demonstrations_match_all": all(matches[:3]),
        "query_differs": not matches[3],
        "query_differing_cell_count": len(differing_cells),
        "query_differing_cells": differing_cells,
        "racket_output_sha256": [
            hashlib.sha256(canonical_json(output)).hexdigest() for output in official
        ],
        "rival_output_sha256": [
            hashlib.sha256(canonical_json(output)).hexdigest() for output in rivals
        ],
        "interpretation": (
            "the demonstrations contain no lone 3 or 2 cells, so they cannot teach "
            "the local-adjacency condition; the query's three lone 2s separate it"
        ),
        "evidence": {
            "generation": "checks/audit/ead22faa41ef/generation.json",
            "inputs": "checks/audit/ead22faa41ef/input.json",
            "racket": "checks/audit/ead22faa41ef/racket.json",
            "rival": "checks/audit/ead22faa41ef/rival.json",
        },
    }
    (here / "counterexample.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(record, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
