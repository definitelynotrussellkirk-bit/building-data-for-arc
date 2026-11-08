#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
GEN = REPO / "generators/c56657e663d9/generator.py"
CANON = REPO / "shared/data/canonical/puzzles.jsonl"

spec = importlib.util.spec_from_file_location("audit_c566", GEN)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def profile(grid):
    size = len(grid)
    out = {"upper_only": 0, "lower_only": 0, "conflict_diff": 0, "conflict_same": 0, "diagonal": 0}
    for r in range(size):
        out["diagonal"] += grid[r][r] != 0
        for c in range(r + 1, size):
            a, b = grid[r][c], grid[c][r]
            if a and not b: out["upper_only"] += 1
            elif b and not a: out["lower_only"] += 1
            elif a and b and a == b: out["conflict_same"] += 1
            elif a and b: out["conflict_diff"] += 1
    return out

def duplicate_cancel(grid):
    n = len(grid)
    result = [[0] * n for _ in range(n)]
    for r in range(n):
        for c in range(n):
            current, transposed = grid[r][c], grid[c][r]
            result[r][c] = 0 if r != c and current and current == transposed else (transposed if transposed else current)
    return result

row = next(json.loads(line) for line in CANON.read_text().splitlines() if json.loads(line).get("task_id") == "c56657e663d9")
canonical = [pair for split in ("train", "test") for pair in row[split]]

seen = {band: 0 for band in ("easy", "medium", "hard")}
default_mismatches = []
for band in seen:
    for index in range(500):
        grid = module.generate(910000 + index, index, difficulty=band)
        seen[band] += profile(grid)["conflict_same"]
        if duplicate_cancel(grid) != module.rule_mirror(grid):
            default_mismatches.append({"band": band, "index": index})

counterexample = [[0] * 6 for _ in range(6)]
counterexample[0][4] = 2                 # upper-only
counterexample[5][2] = 3                 # lower-only for pair (2,5)
counterexample[0][3] = 4                 # different-color conflict
counterexample[3][0] = 7
counterexample[1][5] = 6                 # equal-color conflict omitted by defaults
counterexample[5][1] = 6

report = {
    "schema": "arc-audit-equal-conflict-v1",
    "task_id": "c56657e663d9",
    "generator_sha256": hashlib.sha256(GEN.read_bytes()).hexdigest(),
    "rule_hash": module.RULE_HASH,
    "claim": "A duplicate-cancel rival fits all canonical pairs and sampled defaults because neither contains an equal-color occupied transpose pair, but differs on a self_check-accepted input.",
    "canonical_pair_count": len(canonical),
    "canonical_equal_conflict_counts": [profile(pair["input"])["conflict_same"] for pair in canonical],
    "canonical_rival_matches": [duplicate_cancel(pair["input"]) == pair["output"] for pair in canonical],
    "sampled_defaults_per_band": 500,
    "sampled_default_equal_conflict_totals": seen,
    "sampled_default_rival_mismatches": default_mismatches,
    "counterexample": {
        "input": counterexample,
        "profile": profile(counterexample),
        "self_check_errors": module.self_check(counterexample),
        "intended_python_mirror": module.rule_mirror(counterexample),
        "duplicate_cancel_rival": duplicate_cancel(counterexample),
        "differing_cells": [
            [r, c]
            for r in range(6) for c in range(6)
            if module.rule_mirror(counterexample)[r][c] != duplicate_cancel(counterexample)[r][c]
        ],
    },
}
(ROOT / "checks/audit/c56657e663d9/input.json").write_text(json.dumps(counterexample, indent=2) + "\n")
(ROOT / "checks/audit/c56657e663d9/rival.json").write_text(json.dumps({"output": report["counterexample"]["duplicate_cancel_rival"]}, indent=2) + "\n")
(ROOT / "checks/audit/c56657e663d9/probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "canonical_rival_matches": all(report["canonical_rival_matches"]),
    "default_mismatches": len(default_mismatches),
    "default_equal_conflicts": seen,
    "self_check_errors": report["counterexample"]["self_check_errors"],
    "differing_cells": report["counterexample"]["differing_cells"],
}, indent=2))
