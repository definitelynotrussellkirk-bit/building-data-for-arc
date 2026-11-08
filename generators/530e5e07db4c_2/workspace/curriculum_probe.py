#!/usr/bin/env python3
"""Reproducible curriculum audit for generator 530e5e07db4c_2.

Run from a prepared ARCpuzzles runtime (or the packet repository through
``run_with_racket.py``).  It checks every cyclic three-demo start, reports
which declared rivals each demo refutes, measures profile/object scale, and
checks which rivals fit all canonical pairs.  This is diagnostic evidence;
the task-local pytest suite remains the blocking regression contract.
"""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "530e5e07db4c_2"
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _component(grid, start, allowed=(5,)):
    h, w = len(grid), len(grid[0])
    allowed = set(allowed)
    seen = {start}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for dr, dc in _CARDINAL:
            nxt = (r + dr, c + dc)
            if (
                0 <= nxt[0] < h
                and 0 <= nxt[1] < w
                and nxt not in seen
                and grid[nxt[0]][nxt[1]] in allowed
            ):
                seen.add(nxt)
                queue.append(nxt)
    return seen


def _gray_component_sizes(grid):
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    }
    sizes = []
    while remaining:
        group = _component(grid, next(iter(remaining))) & remaining
        sizes.append(len(group))
        remaining -= group
    return sorted(sizes, reverse=True)


def _load_generator():
    try:
        return importlib.import_module(
            f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
        )
    except ModuleNotFoundError:
        root = find_root(__file__)
        path = root / "generators" / TASK_ID / "generator.py"
        spec = importlib.util.spec_from_file_location(
            f"curriculum_probe_{TASK_ID}", path
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load generator from {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


def audit(*, seeds: list[int], starts: int) -> dict[str, Any]:
    gen = _load_generator()
    canonical = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
    canonical_fit = {
        name: {
            "matches": [rival(pair["input"]) == pair["output"] for pair in canonical],
        }
        for name, rival in gen.SEMANTIC_RIVALS.items()
    }
    for row in canonical_fit.values():
        row["fits_all"] = all(row["matches"])

    lessons = []
    profile_counts: dict[str, int] = {}
    max_gray_objects = []
    failures = []
    for band in ("easy", "medium", "hard"):
        for seed in seeds:
            pairs = []
            for index in range(starts + gen.EXAMPLES_NEEDED):
                grid = gen.generate(seed, index, difficulty=band)
                profile = gen.classify_profile(grid)
                profile_counts[profile] = profile_counts.get(profile, 0) + 1
                max_gray_objects.append(max(_gray_component_sizes(grid)))
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            for start in range(starts):
                demos = pairs[start : start + gen.EXAMPLES_NEEDED]
                query = pairs[start + gen.EXAMPLES_NEEDED]
                refuted = {
                    name: [
                        i
                        for i, pair in enumerate(demos)
                        if rival(pair["input"]) != pair["output"]
                    ]
                    for name, rival in gen.LESSON_COMPETITORS.items()
                }
                reasons = gen.lesson_identifiable(demos, query)
                row = {
                    "band": band,
                    "seed": seed,
                    "start": start,
                    "profiles": [gen.classify_profile(pair["input"]) for pair in demos],
                    "refuted_at_demo_indices": refuted,
                    "identifiability_reasons": reasons,
                }
                lessons.append(row)
                if reasons or any(not positions for positions in refuted.values()):
                    failures.append(row)

    source = Path(gen.__file__).read_bytes()
    return {
        "schema": "530e5e07db4c-curriculum-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(source).hexdigest(),
        "examples_needed": gen.EXAMPLES_NEEDED,
        "schedule_profiles": list(gen.SCHEDULE_PROFILES),
        "canonical_rival_fit": canonical_fit,
        "lesson_count": len(lessons),
        "failed_lessons": failures,
        "profile_counts": profile_counts,
        "largest_gray_object": {
            "min": min(max_gray_objects),
            "max": max(max_gray_objects),
        },
        "lessons": lessons,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", default="19,901,4401")
    parser.add_argument("--starts", type=int, default=16)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    seeds = [int(value) for value in args.seeds.split(",") if value.strip()]
    report = audit(seeds=seeds, starts=args.starts)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    return 1 if report["failed_lessons"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
