#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs

TASK_ID = "16dfbdc731e1"
_START = Path(__file__).resolve()
ROOT = next(
    candidate
    for parent in _START.parents
    for candidate in (parent, parent / "repo")
    if (candidate / "shared" / "data" / "canonical" / "puzzles.jsonl").is_file()
)
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
OUTDIR = ROOT.parent / "checks" / "audit" / TASK_ID

spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", SOURCE)
assert spec and spec.loader
GEN = importlib.util.module_from_spec(spec)
spec.loader.exec_module(GEN)


def intended_python(grid):
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for c in range(w):
        nz = [(r, grid[r][c]) for r in range(h) if grid[r][c] != 0]
        if len(nz) == 2 and nz[0][1] == nz[1][1] and nz[1][0] - nz[0][0] >= 2:
            for r in range(nz[0][0] + 1, nz[1][0]):
                out[r][c] = nz[0][1]
    return out


def rival_ignore_endpoint_color_equality(grid):
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for c in range(w):
        nz = [(r, grid[r][c]) for r in range(h) if grid[r][c] != 0]
        if len(nz) == 2 and nz[1][0] - nz[0][0] >= 2:
            for r in range(nz[0][0] + 1, nz[1][0]):
                out[r][c] = nz[0][1]
    return out


canonical = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
canonical_rival_fits = all(
    rival_ignore_endpoint_color_equality(pair["input"]) == pair["output"]
    for pair in canonical
)
ordinary_rival_fits = True
ordinary_checked = 0
for band in ("easy", "medium", "hard"):
    for seed in range(20):
        for sample_index in range(20):
            grid = GEN.generate(seed, sample_index, difficulty=band)
            ordinary_rival_fits &= rival_ignore_endpoint_color_equality(grid) == intended_python(grid)
            ordinary_checked += 1

counterexample = [[0 for _ in range(8)] for _ in range(8)]
# Two valid columns and one mismatched negative column.
for r, c, color in ((1, 1, 2), (6, 1, 2), (0, 3, 5), (5, 3, 5), (1, 6, 4), (6, 6, 7)):
    counterexample[r][c] = color
intended = intended_python(counterexample)
rival = rival_ignore_endpoint_color_equality(counterexample)

def capture(label, fn):
    try:
        value = fn()
        return {"label": label, "status": "returned", "value": value}
    except Exception as exc:
        return {"label": label, "status": "raised", "error": f"{type(exc).__name__}: {exc}"}

baseline = GEN.generate(99, 5, difficulty="medium")
override_results = [
    capture("declared grid_h=4", lambda: [len(GEN.generate(1, 0, difficulty="easy", grid_h=4)), len(GEN.generate(1, 0, difficulty="easy", grid_h=4)[0])]),
    capture("declared grid_h=18", lambda: [len(GEN.generate(1, 0, difficulty="hard", grid_h=18)), len(GEN.generate(1, 0, difficulty="hard", grid_h=18)[0])]),
    capture("declared pairs=1", lambda: GEN.generate(2, 0, difficulty="easy", pairs=1)),
    capture("unknown bogus_axis", lambda: GEN.generate(3, 0, bogus_axis=123)),
    capture("degenerate dimensions", lambda: [len(GEN.generate(4, 0, grid_h=18, grid_w=18, texture="mismatched_colors")), len(GEN.generate(4, 0, grid_h=18, grid_w=18, texture="mismatched_colors")[0])]),
]
palette_default = GEN.generate(99, 5, difficulty="medium")
palette_override = GEN.generate(99, 5, difficulty="medium", palette_kind="rainbow")
color_override = GEN.generate(99, 5, difficulty="medium", n_distinct_colors=1)

report = {
    "task_id": TASK_ID,
    "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "candidate_rival": "fill between any two nonzero endpoints using the top color, without requiring endpoint colors to match",
    "canonical_pairs": len(canonical),
    "canonical_rival_fits": canonical_rival_fits,
    "ordinary_generated_checked": ordinary_checked,
    "ordinary_rival_fits": ordinary_rival_fits,
    "counterexample": {
        "input": counterexample,
        "self_check": GEN.self_check(counterexample),
        "intended_output_python": intended,
        "rival_output": rival,
        "disagrees": intended != rival,
    },
    "override_results": override_results,
    "unobservable_axes": {
        "palette_kind_rainbow_same_as_default": palette_override == palette_default,
        "n_distinct_colors_1_same_as_default": color_override == baseline,
    },
}
OUTDIR.mkdir(parents=True, exist_ok=True)
(OUTDIR / "mismatched_input.json").write_text(json.dumps({"input": counterexample}, indent=2) + "\n")
(OUTDIR / "audit_probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, indent=2, sort_keys=True))
raise SystemExit(0 if canonical_rival_fits and ordinary_rival_fits and intended != rival else 1)
