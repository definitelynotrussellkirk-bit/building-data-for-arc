#!/usr/bin/env python3
"""Reproduce the two audit sampler-support measurements in this return."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

WORK = Path(__file__).resolve().parents[2]
REPO = WORK / "repo"
sys.path[:0] = [str(REPO / "src"), str(REPO / "shared/runtime")]
BANDS = ("easy", "medium", "hard")


def load(task_id: str):
    source = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source


def components(grid):
    unseen = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    found = []
    while unseen:
        start = unseen.pop()
        color = grid[start[0]][start[1]]
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if point in unseen and grid[point[0]][point[1]] == color:
                    unseen.remove(point)
                    cells.add(point)
                    stack.append(point)
        found.append((color, cells))
    return found


def probe_afa():
    task_id = "afa7a3af9331"
    gen, source = load(task_id)
    per_band = {}
    for band in BANDS:
        histogram: dict[str, int] = {}
        failures = 0
        for index in range(200):
            grid = gen.generate(7000 + index, index, difficulty=band)
            key = str(len(components(grid)))
            histogram[key] = histogram.get(key, 0) + 1
            failures += bool(gen.self_check(grid))
        per_band[band] = {
            "draws": 200,
            "nonzero_object_count_histogram": histogram,
            "self_check_failures": failures,
        }
    return {
        "task_id": task_id,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "sample_policy": "seed=7000+i, sample_index=i, 200 per band",
        "canonical_object_count": 2,
        "finding": (
            "ordinary draws add a nonzero op marker; it is usually a third object "
            "and occasionally merges into a same-color operand"
        ),
        "per_band": per_band,
    }


def probe_c969():
    task_id = "c96915f33c65"
    gen, source = load(task_id)
    per_band = {}
    for band in BANDS:
        repeated = 0
        failures = 0
        for index in range(200):
            grid = gen.generate(9000 + index, index, difficulty=band)
            colors = [value for row in grid for value in row if value != 0]
            repeated += len(colors) != len(set(colors))
            failures += bool(gen.self_check(grid))
        per_band[band] = {
            "draws": 200,
            "draws_with_repeated_nonzero_color": repeated,
            "self_check_failures": failures,
        }
    return {
        "task_id": task_id,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "sample_policy": "seed=9000+i, sample_index=i, 200 per band",
        "finding": "ordinary sampler never repeats a seed color",
        "per_band": per_band,
    }


def main() -> int:
    results = {
        "afa7a3af9331": probe_afa(),
        "c96915f33c65": probe_c969(),
    }
    for task_id, result in results.items():
        path = Path(__file__).resolve().parent / task_id / "sample_probe.json"
        path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
