#!/usr/bin/env python3
"""Find a deterministic generated witness for each declared canonical shortcut.

This authoring probe is deliberately independent of private runner imports.  It
checks that every declared canonical shortcut fits every canonical pair, then
searches the public generator for a lawful input where that shortcut disagrees
with the generator's Python rule mirror.  The authoritative Racket output must
still be obtained with ``arcpuzzles apply`` and stored beside this report.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "a0444de97675"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-sample-index", type=int, default=64)
    args = parser.parse_args()

    root = find_root(Path.cwd())
    gen, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    shortcuts = getattr(gen, "CANONICAL_SHORTCUTS", {})
    if not shortcuts:
        raise SystemExit("generator declares no CANONICAL_SHORTCUTS")

    report = {
        "schema": "a0444de97675-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(source_path.relative_to(root)),
        "generator_sha256": source_sha256,
        "rule_hash": gen.RULE_HASH,
        "canonical_pair_count": len(canonical),
        "shortcuts": {},
    }

    for name, rival in shortcuts.items():
        canonical_mismatches = [
            index
            for index, pair in enumerate(canonical)
            if rival(pair["input"]) != pair["output"]
        ]
        row = {
            "fits_all_canonical_pairs": not canonical_mismatches,
            "canonical_mismatch_indices": canonical_mismatches,
            "witness": None,
        }
        for difficulty in ("easy", "medium", "hard"):
            for sample_index in range(args.max_sample_index):
                seed = 20261012
                grid = gen.generate(seed, sample_index, difficulty=difficulty)
                intended = gen.rule_mirror(grid)
                rival_output = rival(grid)
                if rival_output != intended:
                    row["witness"] = {
                        "seed": seed,
                        "sample_index": sample_index,
                        "difficulty": difficulty,
                        "schedule_profile": gen.schedule_profile(
                            seed, sample_index, difficulty
                        ),
                        "self_check": gen.self_check(grid, difficulty=difficulty),
                        "input": grid,
                        "python_rule_mirror_output": intended,
                        "rival_output": rival_output,
                    }
                    break
            if row["witness"] is not None:
                break
        if row["witness"] is None:
            raise SystemExit(f"no generated disagreement found for {name!r}")
        report["shortcuts"][name] = row

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "out": str(args.out),
        "generator_sha256": source_sha256,
        "shortcut_count": len(report["shortcuts"]),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
