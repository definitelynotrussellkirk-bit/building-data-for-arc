from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "8ab650d5f4cb"
HERE = Path(__file__).resolve().parent
ROOT = Path.cwd().resolve()
gen, source, source_sha = load_selected_generator(TASK_ID, root=ROOT)


def fixed_coordinate_rival(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    # Generator-specific shortcut: ignore frame discovery and fill its two
    # hard-coded interior rectangles from its two hard-coded marker cells.
    if len(grid) >= 9 and len(grid[0]) >= 12:
        c1 = grid[2][2]
        for r in range(2, 4):
            for c in range(2, 4):
                out[r][c] = c1
        c2 = grid[6][9]
        for r in range(6, 8):
            for c in range(8, 11):
                out[r][c] = c2
    return out


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def main() -> None:
    generated = []
    generation_rows = []
    for band in ("easy", "medium", "hard"):
        for i in range(10):
            seed = 7000 + i
            sample_index = i
            grid = gen.generate(seed, sample_index, difficulty=band)
            errors = gen.self_check(grid, difficulty=band)
            generated.append(grid)
            generation_rows.append({
                "difficulty": band,
                "seed": seed,
                "sample_index": sample_index,
                "shape": [len(grid), len(grid[0])],
                "self_check": errors,
                "marker_values_at_fixed_cells": [grid[2][2], grid[6][9]],
            })
    (HERE / "inputs.json").write_text(json.dumps(generated, indent=2) + "\n")

    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    canonical_rows = []
    for pair in pairs:
        rival = fixed_coordinate_rival(pair["input"])
        canonical_rows.append({
            "variant": pair.get("variant"),
            "split": pair.get("split"),
            "pair_index": pair.get("pair_index"),
            "shape": [len(pair["input"]), len(pair["input"][0])],
            "rival_matches_label": rival == pair["output"],
            "self_check": gen.self_check(pair["input"]),
        })

    report = {
        "schema": "arc-generator-audit-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(source.relative_to(ROOT)),
        "generator_sha256": source_sha,
        "generated_draws": len(generated),
        "unique_generated_inputs": len({frozen(g) for g in generated}),
        "generated_self_check_failures": sum(bool(r["self_check"]) for r in generation_rows),
        "fixed_marker_coordinates": [[2, 2], [6, 9]],
        "generation_rows": generation_rows,
        "canonical_labeled_pairs": len(canonical_rows),
        "canonical_fixed_rival_matches": sum(r["rival_matches_label"] for r in canonical_rows),
        "canonical_rows": canonical_rows,
        "inputs_sha256": hashlib.sha256((HERE / "inputs.json").read_bytes()).hexdigest(),
    }
    (HERE / "probe.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
