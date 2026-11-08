#!/usr/bin/env python3
"""Replay the exact invalid-header teaching counterexample for 0a92efb5c42c."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "repo/generators/0a92efb5c42c/generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("audit_0a92efb5c42c", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def any_nonzero_header_is_label(grid):
    h, w = len(grid), len(grid[0])
    row_marks = [r for r in range(1, h) if grid[r][0] != 0]
    col_marks = [c for c in range(1, w) if grid[0][c] != 0]
    out = [[0] * w for _ in range(h)]
    for r in row_marks:
        out[r][0] = grid[r][0]
    for c in col_marks:
        out[0][c] = grid[0][c]
    for r in row_marks:
        for c in col_marks:
            if grid[r][0] == grid[0][c]:
                out[r][c] = grid[r][0]
    return out


def main() -> int:
    gen = load_generator()
    seed = 0
    start = 1
    pairs = []
    for sample_index in range(start, start + gen.EXAMPLES_NEEDED + 1):
        grid = gen.generate(seed, sample_index, difficulty="medium")
        official = gen._mirror(grid)
        rival = any_nonzero_header_is_label(grid)
        pairs.append({
            "sample_index": sample_index,
            "input": grid,
            "author_mirror_output": official,
            "rival_output": rival,
            "rival_matches": rival == official,
        })
    demos, query = pairs[:-1], pairs[-1]
    finding = all(pair["rival_matches"] for pair in demos) and not query["rival_matches"]
    report = {
        "task_id": gen.TASK_ID,
        "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "seed": seed,
        "start_sample_index": start,
        "difficulty": "medium",
        "n_demos": gen.EXAMPLES_NEEDED,
        "demos": demos,
        "query": query,
        "rival": "treat every nonzero top/left border color as a valid row/column label",
        "finding": "all three demos fit the rival; the invalid-color query distinguishes it" if finding else "not reproduced",
    }
    (HERE / "lesson.json").write_text(json.dumps(report, indent=2) + "\n")
    (HERE / "input.json").write_text(json.dumps({"input": query["input"]}, indent=2) + "\n")
    (HERE / "rival.json").write_text(json.dumps({"output": query["rival_output"]}, indent=2) + "\n")
    print(json.dumps({
        "task_id": gen.TASK_ID,
        "demo_fit": [pair["rival_matches"] for pair in demos],
        "query_rival_matches": query["rival_matches"],
        "status": "finding" if finding else "pass",
    }, indent=2))
    return 1 if finding else 0


if __name__ == "__main__":
    raise SystemExit(main())
