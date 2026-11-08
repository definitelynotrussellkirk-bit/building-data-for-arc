#!/usr/bin/env python3
"""Small source-bound scalar-boundary probe for audit targets."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reviewer_support import load_selected_generator


def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("task_id")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = Path.cwd()
    gen, source_path, source_sha = load_selected_generator(args.task_id, root=root)

    cases = [
        ("control", 123, 0, "hard", {}),
        ("negative_sample_index", 123, -1, "hard", {}),
        ("bool_seed", True, 0, "hard", {}),
        ("float_seed", 1.25, 0, "hard", {}),
        ("string_seed", "1", 0, "hard", {}),
        ("bool_sample_index", 123, True, "hard", {}),
        ("float_sample_index", 123, 1.25, "hard", {}),
        ("string_sample_index", 123, "1", "hard", {}),
        ("invalid_difficulty", 123, 0, "__invalid_difficulty__", {}),
    ]
    if args.task_id == "d38b0f2356c1":
        cases.extend([
            ("fractional_clean_block", 123, 0, "hard", {"clean_block": 4.75}),
            ("fractional_template_cells", 123, 0, "hard", {"template_cells": 4.75}),
        ])
    elif args.task_id == "9d11d46cb89a":
        cases.extend([
            ("fractional_motif_size", 123, 0, "hard", {"motif_size": 3.75}),
            ("string_motif_size", 123, 0, "hard", {"motif_size": "3"}),
        ])

    rows = []
    for name, seed, sample_index, difficulty, overrides in cases:
        row = {
            "case": name,
            "seed": seed,
            "sample_index": sample_index,
            "difficulty": difficulty,
            "overrides": overrides,
        }
        try:
            grid = gen.generate(seed, sample_index, difficulty=difficulty, **overrides)
            row.update(
                status="accepted",
                shape=[len(grid), len(grid[0])],
                grid_sha256=grid_hash(grid),
                self_check=gen.self_check(grid),
            )
            try:
                row["observed_overrides"] = gen.observe_overrides(grid)
            except Exception as exc:
                row["observe_error"] = f"{type(exc).__name__}: {exc}"
        except Exception as exc:
            row.update(status="rejected", error=f"{type(exc).__name__}: {exc}")
        rows.append(row)

    payload = {
        "schema": "audit-strict-scalar-probe-v1",
        "task_id": args.task_id,
        "source_path": str(source_path.relative_to(root)),
        "source_sha256": source_sha,
        "cases": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
