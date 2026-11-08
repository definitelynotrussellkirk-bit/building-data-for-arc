#!/usr/bin/env python3
"""Reproduce the two audit lesson-ambiguity censuses without private labels.

Each probe builds three demonstrations and one query from sequential sample
indices, applies a small plausible rival, and counts lessons where the rival
matches the selected rule on every demonstration but differs on the query.
The retained single witnesses are separately bound to Racket in each target's
racket.json.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # WORK/
REPO = ROOT / "repo"


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def diagonal_truth(grid):
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] != 0:
                continue
            main = grid[r - 1][c - 1] == 4 and grid[r + 1][c + 1] == 4
            anti = grid[r - 1][c + 1] == 4 and grid[r + 1][c - 1] == 4
            if main or anti:
                out[r][c] = 8
    return out


def main_diagonal_only(grid):
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if (
                grid[r][c] == 0
                and grid[r - 1][c - 1] == 4
                and grid[r + 1][c + 1] == 4
            ):
                out[r][c] = 8
    return out


def pack_truth(grid):
    result = []
    for row in grid:
        values = [value for value in row if value != 0]
        result.append(values + [0] * (len(row) - len(values)))
    return result


def sort_then_pack(grid):
    result = []
    for row in grid:
        values = sorted(value for value in row if value != 0)
        result.append(values + [0] * (len(row) - len(values)))
    return result


PROBES = {
    "10fa03869a44": (diagonal_truth, main_diagonal_only, "main_diagonal_only"),
    "a1b1c1f9b042": (pack_truth, sort_then_pack, "sort_then_pack_left"),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_id", choices=sorted(PROBES))
    parser.add_argument("--seeds", type=int, default=1000)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    module, source_path = load_generator(args.task_id)
    truth, rival, rival_name = PROBES[args.task_id]
    bands = ("easy", "medium", "hard")
    counts = {}
    first_witness = {}
    checked = 0
    for band in bands:
        ambiguous = 0
        for seed in range(args.seeds):
            grids = [module.generate(seed, index, difficulty=band) for index in range(4)]
            actual = [truth(grid) for grid in grids]
            alternative = [rival(grid) for grid in grids]
            checked += 1
            if alternative[:3] == actual[:3] and alternative[3] != actual[3]:
                ambiguous += 1
                first_witness.setdefault(band, seed)
        counts[band] = {"ambiguous": ambiguous, "lessons": args.seeds}

    payload = {
        "schema": "arcpuzzles-audit-lesson-ambiguity-census-v1",
        "task_id": args.task_id,
        "generator_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "rival_name": rival_name,
        "lesson_policy": {"demonstrations": [0, 1, 2], "query": 3},
        "seed_range": [0, args.seeds - 1],
        "bands": list(bands),
        "counts": counts,
        "first_witness_seed": first_witness,
        "total_lessons": checked,
        "scope": "Python mirror census; retained witness.json/racket.json binds the selected examples to the canonical Racket rule.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
