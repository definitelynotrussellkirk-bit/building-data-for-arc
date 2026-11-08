#!/usr/bin/env python3
"""Reproduce requested-vs-canonical transform ambiguity in 78a7024c6aa2."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "78a7024c6aa2"
ORDER = ("cw", "180", "ccw", "lr", "ud")


def quadrants(grid):
    q = (len(grid) - 1) // 2
    return (
        [row[:q] for row in grid[:q]],
        [row[q + 1 :] for row in grid[:q]],
        [row[:q] for row in grid[q + 1 :]],
        [row[q + 1 :] for row in grid[q + 1 :]],
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    root = find_root(__file__)
    gen, source, digest = load_selected_generator(TASK_ID, root=root)
    grid = gen.generate(0, 0, difficulty="easy", transform="ud")
    a, b, c, d = quadrants(grid)
    matches = [name for name in ORDER if gen._TRANSFORMS[name](a) == b]
    outputs = {name: gen._TRANSFORMS[name](c) for name in matches}
    report = {
        "task_id": TASK_ID,
        "generator_source": str(source),
        "generator_sha256": digest,
        "request": {"seed": 0, "sample_index": 0, "difficulty": "easy", "transform": "ud"},
        "self_check_errors": gen.self_check(grid),
        "canonical_search_order": list(ORDER),
        "matching_transforms": matches,
        "canonical_first_match": matches[0],
        "requested_transform": "ud",
        "candidate_outputs_on_c": outputs,
        "requested_differs_from_first": outputs["ud"] != outputs[matches[0]],
        "input": grid,
        "A": a,
        "B": b,
        "C": c,
        "D": d,
    }
    args.input.write_text(json.dumps({"input": grid}, indent=2) + "\n")
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: report[k] for k in (
        "generator_sha256", "matching_transforms", "canonical_first_match",
        "requested_transform", "requested_differs_from_first", "self_check_errors")}, indent=2))


if __name__ == "__main__":
    main()
