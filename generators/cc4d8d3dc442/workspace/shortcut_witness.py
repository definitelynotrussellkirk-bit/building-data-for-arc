#!/usr/bin/env python3
"""Emit a deterministic counterexample to the one-key-vs-many shortcut.

Run from the repository root:

    PYTHONPATH=shared/runtime python3 \
      generators/cc4d8d3dc442/workspace/shortcut_witness.py

The canonical Racket output can be cross-checked with `arcpuzzles generate`
using the printed seed, sample index, and overrides.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

GENERATOR = HERE.parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location("cc4d8d3dc442_generator", GENERATOR)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {GENERATOR}")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=71)
    parser.add_argument("--sample-index", type=int, default=5)
    args = parser.parse_args()
    overrides = {
        "ch_h": 4,
        "ch_w": 4,
        "n_rows": 2,
        "n_cols": 2,
        "split_count": 1,
        "count_profile": "high_parity",
    }
    grid = GEN.generate(
        args.seed,
        args.sample_index,
        difficulty="hard",
        **overrides,
    )
    intended = GEN.rule_mirror(grid)
    rival = GEN.SEMANTIC_RIVALS["one_vs_many"](grid)
    counts = [
        sum(grid[r][c] == 2 for r, c in region)
        for region in GEN._open_regions(grid)
    ]
    differences = [
        [r, c, intended[r][c], rival[r][c]]
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if intended[r][c] != rival[r][c]
    ]
    payload = {
        "task_id": GEN.TASK_ID,
        "seed": args.seed,
        "sample_index": args.sample_index,
        "difficulty": "hard",
        "overrides": overrides,
        "observed": GEN.observe_overrides(grid),
        "region_key_counts": counts,
        "input": grid,
        "intended_parity_output": intended,
        "one_vs_many_output": rival,
        "difference_cells": differences,
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
