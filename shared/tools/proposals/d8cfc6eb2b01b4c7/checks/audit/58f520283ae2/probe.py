#!/usr/bin/env python3
"""Source-bound reproducer for audit target 58f520283ae2."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
from reviewer_support import load_selected_generator  # noqa: E402

TASK_ID = "58f520283ae2"
SEED = 20261003
SAMPLE_INDEX = 2
DIFFICULTY = "medium"


def grid_sha(grid: list[list[int]]) -> str:
    body = json.dumps(grid, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(body).hexdigest()


def motif_facts(grid: list[list[int]]) -> dict[str, Any]:
    cells = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if (r, c) != (0, 0) and value != 0
    ]
    colors = sorted({value for _, _, value in cells})
    rows = [r for r, _, _ in cells]
    cols = [c for _, c, _ in cells]
    return {
        "motif_colors": colors,
        "motif_color_count": len(colors),
        "motif_cell_count": len(cells),
        "motif_bbox": [min(rows), min(cols), max(rows), max(cols)] if cells else None,
    }


def main() -> None:
    module, source, source_sha = load_selected_generator(TASK_ID, root=REPO)
    variants = [
        {},
        {"palette_size": 2},
        {"palette_size": 3},
        {"n_distinct_colors": 2},
        {"n_distinct_colors": 3},
        {"palette_size": 2, "n_distinct_colors": 2},
    ]
    cases = []
    grids = []
    for overrides in variants:
        grid = module.generate(
            SEED,
            SAMPLE_INDEX,
            difficulty=DIFFICULTY,
            **overrides,
        )
        grids.append(grid)
        cases.append(
            {
                "seed": SEED,
                "sample_index": SAMPLE_INDEX,
                "difficulty": DIFFICULTY,
                "overrides": overrides,
                "input_sha256": grid_sha(grid),
                "validator_errors": module.self_check(grid, difficulty=DIFFICULTY),
                **motif_facts(grid),
            }
        )

    witness = grids[-1]
    unique = {grid_sha(grid) for grid in grids}
    report = {
        "schema": "arcpuzzles-local-audit-probe-v1",
        "task_id": TASK_ID,
        "finding_id": "A-58-IGNORED-PALETTE",
        "status": "reproduced_defect",
        "generator_path": str(source.relative_to(REPO)),
        "generator_version": getattr(module, "VERSION", None),
        "generator_sha256": source_sha,
        "declared_axes": {
            key: module.AXES.get(key)
            for key in ("palette_size", "n_distinct_colors")
        },
        "sampling": {
            "seed_values": [SEED],
            "sample_indices": [SAMPLE_INDEX],
            "difficulty": DIFFICULTY,
            "generation_calls": len(cases),
            "unique_inputs": len(unique),
            "all_calls_identical": len(unique) == 1,
            "cases": cases,
        },
        "counterexample": {
            "overrides": variants[-1],
            "input_sha256": grid_sha(witness),
            "expected_exact_motif_color_count": 2,
            "actual_motif_color_count": motif_facts(witness)["motif_color_count"],
            "actual_motif_colors": motif_facts(witness)["motif_colors"],
            "passes_target_validator": not module.self_check(witness, difficulty=DIFFICULTY),
            "target_validator_errors": module.self_check(witness, difficulty=DIFFICULTY),
            "documented_generator_domain": True,
            "documented_domain_reason": (
                "Ordinary generated zero-background input with command 6 at (0,0), "
                "a separate non-square motif, and every motif bounding-box edge touched."
            ),
            "input": witness,
        },
        "cause": (
            "generate() never reads palette_size or n_distinct_colors and _rand_motif() "
            "draws its own palette length from the layout RNG."
        ),
        "target_modified": False,
        "command": {
            "cwd": "WORK/repo",
            "argv": ["python3", "../checks/audit/58f520283ae2/probe.py"],
        },
    }
    (HERE / "input.json").write_text(json.dumps(witness, indent=2) + "\n", encoding="utf-8")
    (HERE / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "generator_sha256": source_sha,
        "generation_calls": len(cases),
        "unique_inputs": len(unique),
        "actual_colors": motif_facts(witness)["motif_colors"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
