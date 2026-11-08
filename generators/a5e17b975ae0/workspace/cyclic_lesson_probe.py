#!/usr/bin/env python3
"""Exhaust every five-slot curriculum start and every query rotation.

This is a cheap task-local complement to the source-bound shared lesson census.
It dynamically reads the generator's declared competitors instead of copying a
rival list, then checks randomized instances across every difficulty band.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def load_generator():
    path = HERE.parent / "generator.py"
    spec = importlib.util.spec_from_file_location("cyclic_probe_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def grid_key(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def run(seeds_per_start: int) -> dict[str, Any]:
    gen = load_generator()
    bands = (None, "easy", "medium", "hard")
    competitors = dict(gen.LESSON_COMPETITORS)
    period = len(gen.SCHEDULE_PROFILES)
    lesson_size = int(gen.EXAMPLES_NEEDED) + 1

    total_windows = 0
    total_rotations = 0
    unique_inputs: set[tuple[tuple[int, ...], ...]] = set()
    ambiguities: list[dict[str, Any]] = []
    profile_counts: dict[str, int] = {name: 0 for name in gen.SCHEDULE_PROFILES}

    for band in bands:
        band_name = "default" if band is None else band
        for start in range(period):
            for seed_offset in range(seeds_per_start):
                seed = 90_000 + 1_003 * seed_offset + 97 * start
                pairs = []
                for offset in range(lesson_size):
                    sample_index = start + offset
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    if gen.strict_canonical_like(grid):
                        raise AssertionError(
                            f"noncanonical draw at band={band_name} start={start} "
                            f"seed={seed} sample={sample_index}"
                        )
                    profile = gen.schedule_profile(seed, sample_index, band)
                    profile_counts[profile] += 1
                    unique_inputs.add(grid_key(grid))
                    pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
                total_windows += 1

                for query_index, query in enumerate(pairs):
                    demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                    hook_reasons = list(gen.lesson_identifiable(demos, query))
                    survivors = []
                    for name, rival in competitors.items():
                        fits_demos = all(
                            rival(pair["input"]) == pair["output"] for pair in demos
                        )
                        changes_query = rival(query["input"]) != query["output"]
                        if fits_demos and changes_query:
                            survivors.append(name)
                    total_rotations += 1
                    if hook_reasons or survivors:
                        ambiguities.append(
                            {
                                "band": band_name,
                                "start": start,
                                "seed": seed,
                                "query_index": query_index,
                                "schedule": [
                                    gen.schedule_profile(seed, start + i, band)
                                    for i in range(lesson_size)
                                ],
                                "hook_reasons": hook_reasons,
                                "surviving_competitors": survivors,
                                "query_input": query["input"],
                                "query_output": query["output"],
                            }
                        )

    return {
        "schema": "a5e17b975ae0-cyclic-lesson-probe-v1",
        "task_id": gen.TASK_ID,
        "generator_version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "bands": ["default", "easy", "medium", "hard"],
        "schedule_period": period,
        "examples_needed": gen.EXAMPLES_NEEDED,
        "seeds_per_start": seeds_per_start,
        "competitors": sorted(competitors),
        "windows": total_windows,
        "rotations": total_rotations,
        "unique_inputs": len(unique_inputs),
        "profile_counts": profile_counts,
        "ambiguous": len(ambiguities),
        "ambiguities": ambiguities[:20],
        "status": "pass" if not ambiguities else "fail",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=25)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error("--seeds must be at least 1")
    report = run(args.seeds)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
