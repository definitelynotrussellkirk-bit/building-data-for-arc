#!/usr/bin/env python3
"""Reproduce the marker-4 teaching ambiguity for audit target 9adaf46a8128."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "9adaf46a8128"
SEED = 6
DIFFICULTY = "easy"
INDICES = [0, 1, 2, 3]
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
GEN_PATH = REPO / "generators" / TASK_ID / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GEN_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def rival_output(grid):
    sep = next(r for r, row in enumerate(grid) if row and all(value == 5 for value in row))
    top = grid[:sep]
    cells = [(r, c) for r, row in enumerate(top) for c, value in enumerate(row) if value != 0]
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    template = [row[c0:c1 + 1] for row in top[r0:r1 + 1]]
    out_h = len(grid) - sep - 1
    out = [[0] * len(grid[0]) for _ in range(out_h)]
    for r in range(sep + 1, len(grid)):
        for c, marker in enumerate(grid[r]):
            if marker not in (1, 2, 3, 4):
                continue
            # Rival is correct for markers 1-3 but treats unseen marker 4 as identity.
            transformed = (
                template
                if marker in (1, 4)
                else rotate_cw(template)
                if marker == 2
                else rotate_180(template)
            )
            rr0 = (r - (sep + 1)) - len(transformed) // 2
            cc0 = c - len(transformed[0]) // 2
            for dr, row in enumerate(transformed):
                for dc, value in enumerate(row):
                    rr, cc = rr0 + dr, cc0 + dc
                    if value != 0 and 0 <= rr < out_h and 0 <= cc < len(out[0]):
                        out[rr][cc] = value
    return out


def diff_cells(a, b):
    return [
        {"row": r, "column": c, "selected": a[r][c], "rival": b[r][c]}
        for r in range(len(a))
        for c in range(len(a[0]))
        if a[r][c] != b[r][c]
    ]


def main():
    gen = load_generator()
    inputs = [gen.generate(SEED, index, difficulty=DIFFICULTY) for index in INDICES]
    checks = [gen.self_check(grid, difficulty=DIFFICULTY) for grid in inputs]
    sep_rows = [next(r for r, row in enumerate(grid) if all(v == 5 for v in row)) for grid in inputs]
    markers = [
        sorted({v for r, row in enumerate(grid) if r > sep for v in row if v in (1, 2, 3, 4)})
        for grid, sep in zip(inputs, sep_rows)
    ]
    HERE.mkdir(parents=True, exist_ok=True)
    (HERE / "input.json").write_text(json.dumps(inputs, indent=2) + "\n")
    generation = {
        "schema": "arcpuzzles-audit-generation-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
        "seed": SEED,
        "difficulty": DIFFICULTY,
        "sample_indices": INDICES,
        "roles": ["demo", "demo", "demo", "query"],
        "self_check": checks,
        "marker_sets": markers,
        "documented_domain": all(not errors for errors in checks),
    }
    (HERE / "generation.json").write_text(json.dumps(generation, indent=2) + "\n")

    racket_path = HERE / "racket.json"
    if not racket_path.exists():
        print("prepared input.json and generation.json; run supported arcpuzzles apply command")
        return
    racket = json.loads(racket_path.read_text())
    selected = [row["output"] for row in racket["results"]]
    rivals = [rival_output(grid) for grid in inputs]
    matches = [actual == rival for actual, rival in zip(selected, rivals)]
    differences = diff_cells(selected[-1], rivals[-1])
    (HERE / "rival.json").write_text(
        json.dumps({"rival_name": "marker4_is_identity", "outputs": rivals, "matches_selected": matches}, indent=2) + "\n"
    )
    counterexample = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": TASK_ID,
        "finding": "The three demonstrations omit marker 4, so a marker4_is_identity rival fits every demo but disagrees on the marker-4 query.",
        "generator_sha256": generation["generator_sha256"],
        "rule_hash": racket.get("executed_rule_hash"),
        "seed": SEED,
        "difficulty": DIFFICULTY,
        "sample_indices": INDICES,
        "roles": generation["roles"],
        "self_check_passed": [not errors for errors in checks],
        "marker_sets": markers,
        "rival_name": "marker4_is_identity",
        "rival_matches_selected": matches,
        "query_differences": differences,
        "input_path": "checks/audit/9adaf46a8128/input.json",
        "racket_path": "checks/audit/9adaf46a8128/racket.json",
        "rival_path": "checks/audit/9adaf46a8128/rival.json",
        "working_directory": "WORK",
        "apply_command": [
            "python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK_ID,
            "--input", "../checks/audit/9adaf46a8128/input.json", "--out", "../checks/audit/9adaf46a8128/racket.json"
        ],
    }
    (HERE / "counterexample.json").write_text(json.dumps(counterexample, indent=2) + "\n")
    assert matches == [True, True, True, False], matches
    assert differences, "query must distinguish selected rule and rival"
    print(json.dumps({"status": "reproduced", "matches": matches, "query_differences": len(differences)}, indent=2))


if __name__ == "__main__":
    main()
