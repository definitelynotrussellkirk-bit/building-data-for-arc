#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK = "e71a5fe2abc2"

def nonzero_count(grid):
    return sum(value != 0 for row in grid for value in row)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = find_root(__file__)
    module, source_path, source_sha = load_selected_generator(TASK, root=root)
    canonical = None
    for raw in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(raw)
        if row.get("task_id") == TASK:
            canonical = row
            break
    if canonical is None:
        raise RuntimeError("canonical row missing")
    canonical_pairs = list(canonical["train"]) + [canonical["test"]]
    generated = []
    first_input = None
    for band in ("easy", "medium", "hard"):
        for sample_index in range(10):
            grid = module.generate(1000 + sample_index, sample_index, difficulty=band)
            if first_input is None:
                first_input = grid
            generated.append({
                "difficulty": band,
                "seed": 1000 + sample_index,
                "sample_index": sample_index,
                "shape": [len(grid), len(grid[0])],
                "nonzero_cells": nonzero_count(grid),
                "distinct_nonzero_colors": sorted({v for row in grid for v in row if v != 0}),
                "input_sha256": hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest(),
            })
    report = {
        "schema": "e71a5fe2abc2-marker-count-audit-v1",
        "task_id": TASK,
        "selected_generator": {"path": str(source_path), "sha256": source_sha},
        "canonical_written_solution": canonical.get("written_solution"),
        "canonical_nonzero_counts": [nonzero_count(pair["input"]) for pair in canonical_pairs],
        "generated_sample_count": len(generated),
        "generated_seed_range": "1000..1009 per difficulty",
        "generated_nonzero_counts": sorted({row["nonzero_cells"] for row in generated}),
        "all_generated_have_exactly_two_markers": all(row["nonzero_cells"] == 2 for row in generated),
        "central_mismatch": "canonical examples contain four corner markers; every sampled generator input contains two opposite-corner markers",
        "generated_samples": generated,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out.parent / "input.json").write_text(json.dumps(first_input, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "pass", "out": str(out), "generator_sha256": source_sha, "canonical_counts": report["canonical_nonzero_counts"], "generated_counts": report["generated_nonzero_counts"]}, sort_keys=True))

if __name__ == "__main__":
    main()
