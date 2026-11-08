#!/usr/bin/env python3
"""Reproduce an unshown expand-both branch rival for audit target a80c6418f6bc."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "a80c6418f6bc"
SEED = 0
DIFFICULTY = "medium"
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


def bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def panel_info(panel):
    cells = {(r, c) for r, row in enumerate(panel) for c, value in enumerate(row) if value != 0}
    r0, c0, r1, c1 = bbox(cells)
    color = next(panel[r][c] for r, c in cells)
    return {
        "origin": (r0, c0),
        "relative": {(r - r0, c - c0) for r, c in cells},
        "height": r1 - r0 + 1,
        "width": c1 - c0 + 1,
        "color": color,
    }


def analyze(grid):
    n = len(grid)
    q = (n - 1) // 2
    a = [row[:q] for row in grid[:q]]
    b = [row[q + 1:] for row in grid[:q]]
    c = [row[:q] for row in grid[q + 1:]]
    ai, bi, ci = panel_info(a), panel_info(b), panel_info(c)
    if bi["height"] == ai["height"] and bi["width"] == ai["width"]:
        mode = "within_bbox"
    elif bi["height"] == ai["height"] and bi["width"] == ai["width"] + 1:
        mode = "expand_right"
    elif bi["height"] == ai["height"] + 1 and bi["width"] == ai["width"]:
        mode = "expand_down"
    elif bi["height"] == ai["height"] + 1 and bi["width"] == ai["width"] + 1:
        mode = "expand_both"
    else:
        mode = "other"
    return q, c, ai, bi, ci, bi["relative"] - ai["relative"], mode


def rival_output(grid):
    q, c_panel, _ai, _bi, ci, delta, mode = analyze(grid)
    out = [row[:] for row in grid]
    for r in range(q):
        for col in range(q):
            out[q + 1 + r][q + 1 + col] = c_panel[r][col]
    # Plausible branch shortcut: learn the relative edit for the three demonstrated
    # modes, but treat the never-demonstrated two-axis expansion as copy-C only.
    if mode != "expand_both":
        r0, c0 = ci["origin"]
        for dr, dc in delta:
            out[q + 1 + r0 + dr][q + 1 + c0 + dc] = ci["color"]
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
    observations = [gen.observe_overrides(grid) for grid in inputs]
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
        "observed_overrides": observations,
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
        json.dumps({"rival_name": "expand_both_is_copy_c_only", "outputs": rivals, "matches_selected": matches}, indent=2) + "\n"
    )
    counterexample = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": TASK_ID,
        "finding": "The three demonstrations cover within-bbox, right expansion, and down expansion; the query alone uses two-axis expansion. A rival that ignores the delta only for expand_both fits every demo and differs on the query.",
        "generator_sha256": generation["generator_sha256"],
        "rule_hash": racket.get("executed_rule_hash"),
        "seed": SEED,
        "difficulty": DIFFICULTY,
        "sample_indices": INDICES,
        "roles": generation["roles"],
        "self_check_passed": [not errors for errors in checks],
        "observed_overrides": observations,
        "rival_name": "expand_both_is_copy_c_only",
        "rival_matches_selected": matches,
        "query_differences": differences,
        "input_path": "checks/audit/a80c6418f6bc/input.json",
        "racket_path": "checks/audit/a80c6418f6bc/racket.json",
        "rival_path": "checks/audit/a80c6418f6bc/rival.json",
        "working_directory": "WORK",
        "apply_command": [
            "python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK_ID,
            "--input", "../checks/audit/a80c6418f6bc/input.json", "--out", "../checks/audit/a80c6418f6bc/racket.json"
        ],
    }
    (HERE / "counterexample.json").write_text(json.dumps(counterexample, indent=2) + "\n")
    assert matches == [True, True, True, False], matches
    assert differences, "query must distinguish selected rule and rival"
    print(json.dumps({"status": "reproduced", "matches": matches, "query_differences": len(differences)}, indent=2))


if __name__ == "__main__":
    main()
