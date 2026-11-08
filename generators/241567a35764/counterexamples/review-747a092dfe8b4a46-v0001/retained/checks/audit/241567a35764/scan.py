#!/usr/bin/env python3
"""Reproduce the ordinary-domain stamp-count audit for task 241567a35764."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKET_ROOT = HERE.parents[2]
REPO = PACKET_ROOT / "repo"
GENERATOR = REPO / "generators" / "241567a35764" / "generator.py"
sys.path[:0] = [str(REPO / "src"), str(REPO / "shared" / "runtime")]


def load_generator():
    spec = importlib.util.spec_from_file_location("audit_generator_241567a35764", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalize(cells):
    cells = list(cells)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return sorted((r - min_r, c - min_c) for r, c in cells)


def rotate_cw(cells):
    cells = normalize(cells)
    height = max(r for r, _ in cells) + 1
    return normalize((c, height - 1 - r) for r, c in cells)


def stamp_count(grid):
    h, w = len(grid), len(grid[0])
    flat = [v for row in grid for v in row]
    shape = normalize(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    )
    control = 2 if 2 in flat else 3 if 3 in flat else 4 if 4 in flat else 2
    for _ in range({2: 0, 3: 1, 4: 2}[control]):
        shape = rotate_cw(shape)
    if 6 in flat:
        max_c = max(c for _, c in shape)
        shape = normalize((r, max_c - c) for r, c in shape)
    start = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 7
    )
    nxt = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    )
    dr, dc = nxt[0] - start[0], nxt[1] - start[1]
    anchor_r, anchor_c = start
    count = 0
    while all(
        0 <= anchor_r + r < h and 0 <= anchor_c + c < w
        for r, c in shape
    ):
        count += 1
        anchor_r += dr
        anchor_c += dc
    return count


def main():
    generator = load_generator()
    counts = Counter()
    first_zero = None
    accepted = 0
    for difficulty in ("easy", None, "hard"):
        label = "medium" if difficulty is None else difficulty
        for seed in range(100):
            for sample_index in range(100):
                grid = generator.generate(seed, sample_index, difficulty=difficulty)
                problems = generator.self_check(grid, difficulty=difficulty)
                if not problems:
                    accepted += 1
                count = stamp_count(grid)
                counts[f"{label}:{count}"] += 1
                if count == 0 and first_zero is None:
                    first_zero = {
                        "difficulty": label,
                        "seed": seed,
                        "sample_index": sample_index,
                        "input": grid,
                        "self_check": problems,
                    }
    report = {
        "schema": "arc-audit-stamp-count-v1",
        "task_id": "241567a35764",
        "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
        "method": "Exact Python transcription of the selected canonical transform-and-step loop; official Racket output retained separately for first_zero.",
        "domain": {
            "difficulties": ["easy", "medium", "hard"],
            "seeds": "0..99 inclusive",
            "sample_indices": "0..99 inclusive",
            "draws": 30000,
        },
        "self_check_accepted": accepted,
        "stamp_counts": dict(sorted(counts.items())),
        "zero_stamp_total": sum(v for k, v in counts.items() if k.endswith(":0")),
        "one_stamp_total": sum(v for k, v in counts.items() if k.endswith(":1")),
        "fewer_than_two_total": sum(v for k, v in counts.items() if k.endswith(":0") or k.endswith(":1")),
        "first_zero": first_zero,
    }
    (HERE / "scan_summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ["generator_sha256", "self_check_accepted", "zero_stamp_total", "one_stamp_total", "fewer_than_two_total"]}, indent=2))


if __name__ == "__main__":
    main()
