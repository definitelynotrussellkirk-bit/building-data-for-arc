#!/usr/bin/env python3
"""Emit an exact canonical-shortcut counterexample for e005c30bc59a."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "shared" / "runtime"))
from puzzle_generators.runner import _apply_rule, _open_bridge_with_rule
from puzzle_generators.rule_wrap import strip_rule_wrapper

TASK_ID = "e005c30bc59a"


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("shortcut_selected_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def canonical_row(repo: Path):
    with (repo / "shared/data/canonical/puzzles.jsonl").open() as fh:
        for line in fh:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise KeyError(TASK_ID)


def racket_callable(rule_source: str) -> str:
    body = strip_rule_wrapper(rule_source)
    if body.lstrip().startswith(("(lambda", "(λ")):
        return f"(lambda (g) (let* ((h (rows g)) (w (cols g))) ({body} g)))"
    return f"(lambda (g) (let* ((h (rows g)) (w (cols g))) {body}))"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    path = repo / "generators" / TASK_ID / "generator.py"
    mod = load_module(path)
    row = canonical_row(repo)
    seed = 424242
    sample_index = 0
    overrides = {
        "grid_h": 8,
        "grid_w": 8,
        "source_edge": "top",
        "source_color": 3,
        "mirror_profile": "one_hit",
        "wall_profile": "boundary_none",
    }
    grid = mod.generate(seed, sample_index, difficulty="medium", **overrides)
    intended_python = mod.rule_mirror(grid)
    rival_name = "constant_trail_color_7"
    rival = mod.CANONICAL_SHORTCUTS[rival_name]
    rival_output = rival(grid)

    bridge, fn = _open_bridge_with_rule(racket_callable(row["program_solution"]))
    try:
        actual_racket = _apply_rule(bridge, fn, grid)
    finally:
        bridge.shutdown()

    canonical_fit = [rival(pair["input"]) == pair["output"] for pair in row["train"]]
    diff_cells = [
        [r, c, actual_racket[r][c], rival_output[r][c]]
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if actual_racket[r][c] != rival_output[r][c]
    ]
    report = {
        "schema": "generator-shortcut-counterexample-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "rule_hash": mod.RULE_HASH,
        "canonical_sha256": hashlib.sha256(
            (repo / "shared/data/canonical/puzzles.jsonl").read_bytes()
        ).hexdigest(),
        "rival_name": rival_name,
        "rival_description": "Trace the same beam but always paint traversed cells color 7.",
        "canonical_train_pair_count": len(row["train"]),
        "canonical_fit_each": canonical_fit,
        "canonical_fits_all": bool(canonical_fit) and all(canonical_fit),
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": "medium",
        "overrides": overrides,
        "validator_errors": mod.self_check(grid),
        "generator_emits_case": True,
        "input": grid,
        "actual_racket_output": actual_racket,
        "python_mirror_output": intended_python,
        "python_matches_racket": intended_python == actual_racket,
        "rival_output": rival_output,
        "outputs_disagree": rival_output != actual_racket,
        "different_cells": diff_cells,
        "command": [
            "python3", "run_with_racket.py", "python3",
            "generators/e005c30bc59a/workspace/shortcut_probe.py",
            "--repo", ".", "--out", "../checks/shortcut_constant7_counterexample.json"
        ],
        "cwd": "packet_root (wrapper executes child in repo)",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
