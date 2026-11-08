#!/usr/bin/env python3
"""Cheap cyclic-window rival probe for generator authoring.

This is deliberately a Python diagnostic, not an export-label authority. It
uses an independent geometry renderer to ask whether every declared
canonical-fitting rival is refuted by the demonstrations after every possible
single-pair query holdout across every declared schedule start.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Iterable, Sequence

TASK_HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = TASK_HOME / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("rectangle_generator_for_probe", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _positions(grid):
    found = {}
    for color in (1, 2, 3):
        hits = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        if len(hits) != 1:
            raise ValueError(f"expected one color-{color} marker, found {len(hits)}")
        found[color] = hits[0]
    return found


def canonical_outline(grid):
    """Independent mirror used only for this authoring probe."""
    points = _positions(grid)
    top, bottom = sorted((points[1][0], points[3][0]))
    left, right = sorted((points[1][1], points[2][1]))
    out = [[0 for _ in row] for row in grid]
    for col in range(left, right + 1):
        out[top][col] = 8
        out[bottom][col] = 8
    for row in range(top, bottom + 1):
        out[row][left] = 8
        out[row][right] = 8
    return out


def run_probe(*, seeds: Iterable[int], bands: Sequence[str]) -> dict:
    generator = _load_generator()
    period = int(generator.LESSON_SCHEDULE_PERIOD)
    lesson_size = int(generator.EXAMPLES_NEEDED) + 1
    failures = []
    refutation_counts = {name: [] for name in generator.LESSON_COMPETITORS}
    lessons = 0
    rotations = 0

    for seed in seeds:
        for band in bands:
            for start in range(period):
                grids = [generator.generate(seed, start + offset, difficulty=band)
                         for offset in range(lesson_size)]
                labels = [canonical_outline(grid) for grid in grids]
                lessons += 1
                for held_out in range(lesson_size):
                    rotations += 1
                    demo_indices = [index for index in range(lesson_size) if index != held_out]
                    for name, rival in generator.LESSON_COMPETITORS.items():
                        refuting = [index for index in demo_indices if rival(grids[index]) != labels[index]]
                        refutation_counts[name].append(len(refuting))
                        if not refuting:
                            failures.append({
                                "seed": seed,
                                "band": band,
                                "start": start,
                                "held_out": held_out,
                                "rival": name,
                                "query_differs": rival(grids[held_out]) != labels[held_out],
                                "profiles": [
                                    generator.schedule_profile(seed, start + offset, band)
                                    for offset in range(lesson_size)
                                ],
                            })

    rival_summary = {
        name: {
            "checks": len(counts),
            "min_demo_refutations": min(counts) if counts else None,
            "max_demo_refutations": max(counts) if counts else None,
        }
        for name, counts in sorted(refutation_counts.items())
    }
    source_bytes = GENERATOR_PATH.read_bytes()
    return {
        "schema": "arc-schedule-probe-v1",
        "task_id": generator.TASK_ID,
        "generator_version": generator.VERSION,
        "generator_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "rule_hash": generator.RULE_HASH,
        "period": period,
        "lesson_size": lesson_size,
        "bands": list(bands),
        "seed_count": len(list(seeds)) if isinstance(seeds, range) else None,
        "lessons": lessons,
        "rotations": rotations,
        "rivals": rival_summary,
        "failures": failures,
        "status": "pass" if not failures else "fail",
        "authority_note": "Python authoring diagnostic only; Racket-backed census remains authoritative.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seed-count", type=int, default=32)
    parser.add_argument("--bands", nargs="+", default=["easy", "medium", "hard"])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.seed_count < 1:
        parser.error("--seed-count must be positive")
    seeds = range(args.seed_start, args.seed_start + args.seed_count)
    report = run_probe(seeds=seeds, bands=args.bands)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
