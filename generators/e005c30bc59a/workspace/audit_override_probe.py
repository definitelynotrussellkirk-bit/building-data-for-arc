#!/usr/bin/env python3
"""Reproduce override-contract defects for assigned audit targets."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

# The packet wrapper runs this child from repo/.
sys.path.insert(0, str(Path.cwd() / "shared" / "runtime"))

from puzzle_generators.runner import _apply_rule, _open_bridge_with_rule
from puzzle_generators.rule_wrap import strip_rule_wrapper


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def authority(repo: Path, task_id: str, grid):
    rule_source = None
    with (repo / "shared/data/canonical/puzzles.jsonl").open() as fh:
        for line in fh:
            row = json.loads(line)
            if row.get("task_id") == task_id:
                rule_source = row.get("program_solution")
                break
    if not rule_source:
        raise KeyError(f"missing canonical program_solution for {task_id}")
    body = strip_rule_wrapper(rule_source)
    if body.lstrip().startswith(("(lambda", "(λ")):
        callable_text = f"(lambda (g) (let* ((h (rows g)) (w (cols g))) ({body} g)))"
    else:
        callable_text = f"(lambda (g) (let* ((h (rows g)) (w (cols g))) {body}))"
    bridge, fn = _open_bridge_with_rule(callable_text)
    try:
        return _apply_rule(bridge, fn, grid)
    finally:
        bridge.shutdown()


def expected_rule_hashes(repo: Path, ids: set[str]) -> dict[str, str]:
    result = {}
    with (repo / "shared/data/derived/kimi_generator_assignment.jsonl").open() as fh:
        for line in fh:
            row = json.loads(line)
            if row.get("task_id") in ids:
                result[row["task_id"]] = row.get("rule_hash_expected")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    ids = {"38eaf32b0d29", "6355eb114053"}
    rule_hashes = expected_rule_hashes(repo, ids)
    report = {
        "schema": "assigned-audit-override-probe-v1",
        "command": [
            "python3", "run_with_racket.py", "python3",
            "generators/e005c30bc59a/workspace/audit_override_probe.py",
            "--repo", ".", "--out", "../checks/audit_override_counterexamples.json"
        ],
        "cwd": "packet_root (wrapper executes child in repo)",
        "targets": {},
    }

    # 38e... claims br as a valid inner_position, but its fall-through maps br to tr.
    task = "38eaf32b0d29"
    path = repo / "generators" / task / "generator.py"
    mod = load(path, "audit_38e")
    grid = mod.generate(123, 0, difficulty="medium", inner_position="br")
    counts = Counter(v for row in grid for v in row)
    bg = max(counts, key=counts.get)
    non_bg = [v for v in counts if v != bg]
    inner = min(non_bg, key=lambda v: counts[v])
    inner_cells = [
        [r, c] for r, row in enumerate(grid) for c, value in enumerate(row)
        if value == inner
    ]
    tr_grid = mod.generate(123, 0, difficulty="medium", inner_position="tr")
    report["targets"][task] = {
        "finding": "inner_position='br' is realized at top-right, identical to 'tr'",
        "generator_sha256": sha(path),
        "rule_hash": rule_hashes.get(task),
        "seed": 123,
        "sample_index": 0,
        "difficulty": "medium",
        "overrides": {"inner_position": "br"},
        "documented_domain": True,
        "validator_errors": mod.self_check(grid),
        "grid_size": len(grid),
        "expected_marker_cell": [len(grid) - 2, len(grid[0]) - 2],
        "observed_inner_color": inner,
        "observed_marker_cells": inner_cells,
        "same_as_tr_override": grid == tr_grid,
        "input": grid,
        "actual_racket_output": authority(repo, task, grid),
        "rival_output": None,
        "rival_output_reason": "This is an input-axis realization defect, not a rival output rule.",
    }

    # 6355... advertises n_pluses 1..6, yet generate calls draw_int with [1,3].
    task = "6355eb114053"
    path = repo / "generators" / task / "generator.py"
    mod = load(path, "audit_6355")
    exception = None
    try:
        mod.generate(123, 0, difficulty="medium", n_pluses=6)
    except Exception as exc:
        exception = {"type": type(exc).__name__, "message": str(exc)}
    high = mod.generate(
        123, 0, difficulty="medium", n_pluses=3,
        palette_size=9, n_distinct_colors=9,
    )
    low = mod.generate(
        123, 0, difficulty="medium", n_pluses=3,
        palette_size=1, n_distinct_colors=1,
    )
    nonzero_colors = sorted({v for row in high for v in row if v != 0})
    report["targets"][task] = {
        "finding": "declared override contract is unrealizable: n_pluses=6 is rejected; palette axes are ignored",
        "generator_sha256": sha(path),
        "rule_hash": rule_hashes.get(task),
        "seed": 123,
        "sample_index": 0,
        "difficulty": "medium",
        "overrides_rejected": {"n_pluses": 6},
        "rejection": exception,
        "palette_probe_overrides": {
            "high": {"n_pluses": 3, "palette_size": 9, "n_distinct_colors": 9},
            "low": {"n_pluses": 3, "palette_size": 1, "n_distinct_colors": 1},
        },
        "high_low_inputs_identical": high == low,
        "observed_nonzero_colors_high": nonzero_colors,
        "documented_domain": True,
        "validator_errors": mod.self_check(high),
        "input": high,
        "actual_racket_output": authority(repo, task, high),
        "rival_output": None,
        "rival_output_reason": "This is an input-axis/override defect, not a rival output rule.",
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
