"""Retain actual generated witnesses for each supplied canonical crop shape.

This is an authoring tool: canonical data includes answers. Do not use it in a
visible-only solve. It checks occupancy support, not uniformity or induction.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "b9d1d323c3ed"


def occupancy(grid):
    occupied = [(r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color]
    top = min(r for r, _ in occupied)
    bottom = max(r for r, _ in occupied)
    left = min(c for _, c in occupied)
    right = max(c for _, c in occupied)
    return tuple(tuple(int(bool(color)) for color in row[left:right + 1])
                 for row in grid[top:bottom + 1])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-seeds", type=int, default=4096)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.max_seeds < 1:
        parser.error("--max-seeds must be positive")
    if args.out.exists():
        parser.error("use a fresh output path to preserve prior evidence")
    root = find_root(__file__)
    gen, source, digest = load_selected_generator(TASK_ID, root=root)
    pairs = canonical_pairs(TASK_ID, root=root)
    wanted = {occupancy(pair["input"]) for pair in pairs}
    found = {}
    draws = 0
    for seed in range(args.max_seeds):
        grid = gen.generate(seed, 0, fg_layout="scattered")
        draws += 1
        errors = gen.self_check(grid)
        if errors:
            raise ValueError(f"generated invalid input at seed {seed}: {errors}")
        mask = occupancy(grid)
        if mask in wanted and mask not in found:
            found[mask] = {
                "seed": seed, "sample_index": 0, "difficulty": None,
                "overrides": {"fg_layout": "scattered"}, "input": grid,
                "input_sha256": hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest(),
            }
        if wanted <= found.keys():
            break
    report = {
        "schema": "b9d1d323c3ed-canonical-occupancy-support-v1",
        "task_id": TASK_ID, "generator_sha256": digest,
        "generator_path": source.relative_to(root).as_posix(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "rule_hash": gen.RULE_HASH, "cwd": str(Path.cwd()), "argv": sys.argv,
        "requested_seed_cap": args.max_seeds, "actual_seed_range": [0, draws - 1],
        "draws": draws, "canonical_pair_count": len(pairs),
        "unique_canonical_masks": len(wanted), "matched_masks": len(found),
        "passed": wanted <= found.keys(),
        "canonical_matches": [
            {"split": pair["split"], "pair_index": pair["pair_index"],
             "occupancy": occupancy(pair["input"]),
             "generated_witness": found.get(occupancy(pair["input"]))}
            for pair in pairs
        ],
        "scope": "Finite scatter override support on canonical-size inputs; not a claim of uniform sampling.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("passed", "draws", "matched_masks", "unique_canonical_masks", "generator_sha256")}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
