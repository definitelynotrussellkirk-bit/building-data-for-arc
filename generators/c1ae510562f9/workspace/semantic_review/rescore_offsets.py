"""Test newly proposed offset rivals against retained Racket-labelled lessons.

These proposals deliberately were absent from the original census declarations.
No labels are generated here: every expected output comes from the saved census.
Only the first exact ambiguity and compact counts are retained.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


SPIRAL = ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2),
          (2, 1), (2, 0), (1, 0), (1, 1))


def offset_prediction(grid, which, offset):
    gray = [(r, c) for r, row in enumerate(grid)
            for c, value in enumerate(row) if value == 5]
    top, floor = min(r for r, _ in gray), max(r for r, _ in gray)
    left, right = min(c for _, c in gray), max(c for _, c in gray)
    rows = [row[left + 1:right] for row in grid[top:floor]]
    if which == "area":
        amount = sum(value == 0 for row in rows for value in row) // len(rows[0])
    else:
        index = {"left": 0, "middle": len(rows[0]) // 2, "right": len(rows[0]) - 1}[which]
        amount = sum(row[index] == 0 for row in rows)
    result = [[0] * 3 for _ in range(3)]
    for r, c in SPIRAL[:max(0, min(9, amount - offset))]:
        result[r][c] = 8
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--census", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"refusing to overwrite {args.out}")
    census = json.loads(args.census.read_text())
    assert census["schema"] == "arcpuzzles-lesson-census-v1"
    assert census["task_id"] == "c1ae510562f9"
    specs = [(f"{which}_minus_{offset}", which, offset)
             for which in ("left", "middle", "right", "area") for offset in (1, 2)]
    stats = {name: {"production_ambiguities": 0, "rotation_ambiguities": 0}
             for name, _, _ in specs}
    first = None
    rotations = 0
    for lesson in census["lessons"]:
        instance = lesson["instance"]
        pairs = instance["train"] + instance["test"]
        assert len(instance["test"]) == 1 and len(pairs) == 5
        rotations += len(pairs)
        for name, which, offset in specs:
            predictions = [offset_prediction(pair["input"], which, offset) for pair in pairs]
            refuting = [index for index, pair in enumerate(pairs)
                        if pair["output"] != predictions[index]]
            if len(refuting) == 1:
                query = refuting[0]
                stats[name]["rotation_ambiguities"] += 1
                stats[name]["production_ambiguities"] += query == len(pairs) - 1
                if first is None:
                    first = {
                        "band": lesson["band"], "seed": lesson["seed"],
                        "sample_index": lesson["sample_index"],
                        "instance_sha256": lesson["instance_sha256"],
                        "instance": instance, "rival": name,
                        "rival_predictions": predictions,
                        "query_index": query,
                        "train_indices": [index for index in range(len(pairs)) if index != query],
                        "rival_query_output": predictions[query],
                        "racket_query_output": pairs[query]["output"],
                    }
    result = {
        "schema": "c1ae510562f9-offset-rival-rescore-v1",
        "task_id": census["task_id"],
        "input_census": str(args.census),
        "input_census_sha256": hashlib.sha256(args.census.read_bytes()).hexdigest(),
        "generator_sha256": census["generator_sha256"],
        "rule_source_sha256": census["rule_source_sha256"],
        "rule_callable_sha256": census["rule_callable_sha256"],
        "declared_rule_hash": census["declared_rule_hash"],
        "lesson_count": len(census["lessons"]), "rotation_count": rotations,
        "rivals": stats, "first_exact_counterexample": first,
        "status": "ambiguity_found" if first is not None else "no_ambiguity_found",
        "command": sys.argv, "cwd": str(Path.cwd()),
        "scope": "Author-proposed additional rivals, using saved Racket labels; not a fresh generation census.",
    }
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in
                      ("status", "generator_sha256", "lesson_count", "rotation_count", "rivals")}, indent=2))
    if first is not None:
        print(json.dumps({key: first[key] for key in
                          ("band", "seed", "sample_index", "query_index", "train_indices", "rival")}, indent=2))
    return int(first is not None)


if __name__ == "__main__":
    raise SystemExit(main())
