#!/usr/bin/env python3
"""Replay source-bound symmetry witnesses through the public Racket apply API.

From an extracted packet:
  python3 run_with_racket.py python3 generators/a950d6dbe2e0/workspace/probe_witnesses.py --out ../checks/witnesses

The tool dynamically reads declared rivals, verifies their canonical fit, and
retains every actual Racket output. It never substitutes a Python label source.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK = "a950d6dbe2e0"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    source = Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("symmetry_witness_generator", source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    cases = [dict(grid_h=h, grid_w=w, n_cells=n, n_distinct_colors=k)
             for h, w, n, k in [(6, 10, 4, 3), (10, 6, 4, 3), (4, 30, 30, 9),
                                (30, 4, 30, 9), (30, 30, 64, 9), (8, 8, 5, 2)]]
    grids = [gen.generate(43, index, difficulty="medium", **axes)
             for index, axes in enumerate(cases)]
    canonical = canonical_pairs(TASK, root=root)
    applied = Catalog(root).apply(TASK, grids + [pair["input"] for pair in canonical])
    (args.out / "racket.json").write_text(json.dumps(applied, indent=2) + "\n")
    report = {
        "task_id": TASK,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "rule_hash": applied["executed_rule_hash"],
        "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
        "canonical_pairs": len(canonical), "canonical_shortcut_fit": {},
        "generated_cases": [], "failures": [],
    }
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        fits = sum(rival(pair["input"]) == pair["output"] for pair in canonical)
        report["canonical_shortcut_fit"][name] = {"matched": fits, "total": len(canonical)}
        if fits != len(canonical):
            report["failures"].append(f"declared canonical shortcut {name} does not fit canonical")
    for index, (axes, grid) in enumerate(zip(cases, grids)):
        actual = applied["results"][index]
        rivals = {name: rival(grid) for name, rival in gen.LESSON_COMPETITORS.items()}
        upper = [row[:len(row)//2] + row[:len(row)//2][::-1] for row in grid[:len(grid)//2]]
        geometric_expectation = upper + [row[:] for row in upper[::-1]]
        entry = {"seed": 43, "sample_index": index, "difficulty": "medium", "overrides": axes,
                 "input": grid, "self_check": gen.self_check(grid), "racket_output": actual["output"],
                 "rival_outputs": rivals,
                 "distinguished": [name for name, output in rivals.items() if output != actual["output"]]}
        report["generated_cases"].append(entry)
        if actual["output"] != geometric_expectation or entry["self_check"]:
            report["failures"].append(f"case {index}: reference/domain mismatch")
        if axes["grid_h"] != axes["grid_w"] and any(
                name not in entry["distinguished"] for name in gen.CANONICAL_SHORTCUTS):
            report["failures"].append(f"case {index}: rectangular witness did not refute every square shortcut")
    for index, pair in enumerate(canonical, len(grids)):
        if applied["results"][index]["output"] != pair["output"]:
            report["failures"].append(f"canonical pair {index-len(grids)}: reference mismatch")
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"generated_cases": len(grids), "canonical_pairs": len(canonical),
                      "canonical_shortcut_fit": report["canonical_shortcut_fit"],
                      "failures": report["failures"], "out": str(args.out)}))
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
