#!/usr/bin/env python3
"""Source-bound probe for the c4155b3fcecd teaching curriculum.

This is reviewer tooling, not production code.  It verifies canonical support,
profile observability, the canonical-compatible left-only shortcut, and every
cyclic lesson/query rotation without consulting private solve labels.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "c4155b3fcecd"
HOME = Path(__file__).resolve().parents[1]


def load_generator(path: str | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("c4155b3fcecd_probe_target", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return source, module


def side_set(grid: list[list[int]]) -> set[str]:
    width = len(grid[0])
    sides: set[str] = set()
    for row in grid:
        for column, value in enumerate(row):
            if not value:
                continue
            if column < width // 2:
                sides.add("left")
            elif column >= (width + 1) // 2:
                sides.add("right")
            else:
                sides.add("axis")
    return sides


def pair(module: Any, seed: int, sample_index: int, band: str) -> dict[str, Any]:
    grid = module.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": module.rule_mirror(grid)}


def run(path: str | None = None) -> dict[str, Any]:
    source, module = load_generator(path)
    canonical = canonical_pairs(TASK_ID, root=find_root(__file__))
    shortcut = module.CANONICAL_SHORTCUTS["mirror_left_side_only"]
    canonical_checks = [
        {
            "split": item["split"],
            "pair_index": item["pair_index"],
            "accepted": module.self_check(item["input"]) == [],
            "oracle_match": module.rule_mirror(item["input"]) == item["output"],
            "left_only_shortcut_match": shortcut(item["input"]) == item["output"],
        }
        for item in canonical
    ]

    profile_checks = []
    for index, profile in enumerate(module.SCENE_PROFILES):
        grid = module.generate(7100 + index, index, scene_profile=profile)
        profile_checks.append(
            {
                "profile": profile,
                "accepted": module.self_check(grid) == [],
                "observed": module.observe_overrides(grid).get("scene_profile"),
                "sides": sorted(side_set(grid)),
                "official_differs_from_left_only": module.rule_mirror(grid) != shortcut(grid),
            }
        )

    rotations = []
    for band in ("easy", "medium", "hard"):
        period = len(module._PROFILES_BY_BAND[band])
        for start in range(period):
            window = [
                pair(module, 3301, start + offset, band)
                for offset in range(module.EXAMPLES_NEEDED + 1)
            ]
            for query_index, query in enumerate(window):
                demos = window[:query_index] + window[query_index + 1 :]
                rotations.append(
                    {
                        "band": band,
                        "start": start,
                        "query_index": query_index,
                        "demo_sides": sorted(
                            {side for demo in demos for side in side_set(demo["input"])}
                        ),
                        "reasons": module.lesson_identifiable(demos, query),
                        "surviving_competitors": [
                            name
                            for name, rival in module.LESSON_COMPETITORS.items()
                            if all(rival(demo["input"]) == demo["output"] for demo in demos)
                            and rival(query["input"]) != query["output"]
                        ],
                    }
                )

    failures = []
    failures.extend(
        f"canonical {row['split']}#{row['pair_index']} failed {key}"
        for row in canonical_checks
        for key in ("accepted", "oracle_match", "left_only_shortcut_match")
        if not row[key]
    )
    failures.extend(
        f"profile {row['profile']} did not round-trip"
        for row in profile_checks
        if not row["accepted"] or row["observed"] != row["profile"]
    )
    failures.extend(
        f"rotation {row['band']} start={row['start']} query={row['query_index']} ambiguous"
        for row in rotations
        if row["reasons"] or row["surviving_competitors"] or row["demo_sides"] != ["left", "right"]
    )

    return {
        "schema": "c4155b3fcecd-curriculum-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(source),
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "canonical_checks": canonical_checks,
        "profile_checks": profile_checks,
        "rotation_count": len(rotations),
        "rotations": rotations,
        "failures": failures,
        "passed": not failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run(args.generator)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
