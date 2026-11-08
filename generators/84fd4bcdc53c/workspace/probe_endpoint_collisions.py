"""Bounded source-bound collision probe; reference labels execute in Racket.

Run through the packet's review.py run wrapper. --phase before retains the two
historical witnesses. --phase after also probes eight seeds at each real size
boundary of the three difficulty bands. Both phases label a small selected set
through Catalog.apply, without implementing a second oracle.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import find_root, load_selected_generator


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("before", "after"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("output must be new")
    root = find_root(__file__)
    generator, source_path, source_hash = load_selected_generator(
        "84fd4bcdc53c", root=root
    )
    recipes = [
        {"seed": 6, "sample_index": 0, "difficulty": difficulty, "overrides": {}}
        for difficulty in ("medium", "hard")
    ]
    label_indices = [0, 1]
    if args.phase == "after":
        for difficulty, sizes in (
            ("easy", ((7, 8), (9, 11))),
            ("medium", ((9, 10), (13, 14))),
            ("hard", ((13, 14), (19, 20))),
        ):
            for height, width in sizes:
                label_indices.append(len(recipes))
                recipes.extend(
                    {"seed": seed, "sample_index": 0, "difficulty": difficulty,
                     "overrides": {"grid_h": height, "grid_w": width}}
                    for seed in range(8)
                )
    measurements, grids, violations = [], [], []
    for index, recipe in enumerate(recipes):
        grid = generator.generate(
            recipe["seed"], recipe["sample_index"],
            difficulty=recipe["difficulty"], **recipe["overrides"]
        )
        grids.append(grid)
        counts = Counter(cell for row in grid for cell in row if cell)
        errors = generator.self_check(grid, difficulty=recipe["difficulty"])
        row = {"recipe": recipe, "shape": [len(grid), len(grid[0])],
               "endpoint_counts": dict(counts), "self_check_errors": errors}
        measurements.append(row)
        lo, hi = {"easy": (1, 1), "medium": (2, 2), "hard": (3, 4)}[recipe["difficulty"]]
        if not lo <= len(counts) <= hi or any(n < 2 or n > 4 for n in counts.values()) or errors:
            violations.append(index)
    labels = Catalog(root).apply(
        "84fd4bcdc53c", [grids[index] for index in label_indices],
        reference="canonical", timeout=120,
    )
    assert labels["generator_sha256"] == source_hash
    assert labels["rule_hash_matches_catalog"] is True
    assert all(row["error"] is None for row in labels["results"])
    for index, row in zip(label_indices, labels["results"]):
        assert [len(row["output"]), len(row["output"][0])] == measurements[index]["shape"]
    report = {
        "task_id": "84fd4bcdc53c", "phase": args.phase,
        "scope": "Endpoint loss from cross-color input-cell collisions only; no parametric work or full battery.",
        "generator_source": str(source_path.relative_to(root)),
        "generator_sha256": source_hash,
        "measurements": measurements,
        "violation_indices": violations,
        "reference_input_indices": label_indices,
        "reference_inputs": [grids[index] for index in label_indices],
        "canonical_racket_receipt": labels,
        "passed": not violations,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"phase": args.phase, "draws": len(recipes),
                      "violations": len(violations), "racket_labels": len(label_indices),
                      "source_sha256": source_hash, "report": str(args.out)}))
    if args.phase == "after" and violations:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
