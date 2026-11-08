#!/usr/bin/env python3
"""Enumerate the selected generator's finite curriculum against declared rivals.

This is an authoring probe, not an authority runner.  It imports the exact
selected source through reviewer_support, labels grids with the generator's
Python rule mirror, and checks every five-pair window/query rotation across the
private finite schedule.  Use the Racket-backed lesson census for authority
labels; this probe is the cheap regression/reproducer for schedule changes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from reviewer_support import find_root, load_selected_generator

TASK_ID = "147c2b92e5c1"


def _label(gen: Any, grid: list[list[int]]) -> dict[str, Any]:
    return {"input": grid, "output": gen.rule_mirror(grid)}


def audit(seed_values: tuple[int, ...]) -> dict[str, Any]:
    root = find_root(__file__)
    gen, source, digest = load_selected_generator(TASK_ID, root=root)
    period = int(getattr(gen, "_FULL_CYCLE"))
    competitors = dict(getattr(gen, "LESSON_COMPETITORS"))
    ambiguities: list[dict[str, Any]] = []
    checked_lessons = 0
    checked_rotations = 0

    for band in ("easy", "medium", "hard"):
        for seed in seed_values:
            for start in range(period):
                lesson = [
                    _label(gen, gen.generate(seed, start + offset, difficulty=band))
                    for offset in range(5)
                ]
                checked_lessons += 1
                for query_index, query in enumerate(lesson):
                    demos = [pair for index, pair in enumerate(lesson) if index != query_index]
                    checked_rotations += 1
                    hook_reasons = list(gen.lesson_identifiable(demos, query))
                    if hook_reasons:
                        ambiguities.append(
                            {
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "query_index": query_index,
                                "kind": "lesson_hook",
                                "reasons": hook_reasons,
                            }
                        )
                    for name, rival in competitors.items():
                        survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
                        differs = rival(query["input"]) != query["output"]
                        if survives and differs:
                            ambiguities.append(
                                {
                                    "band": band,
                                    "seed": seed,
                                    "start": start,
                                    "query_index": query_index,
                                    "kind": "declared_rival",
                                    "rival": name,
                                }
                            )

    seed60_lesson = [gen.generate(60, index, difficulty="easy") for index in range(5)]
    identity = competitors["fixed_transform_1"]
    seed60 = {
        "difficulty": "easy",
        "seed": 60,
        "sample_indices": list(range(5)),
        "transform_codes": [gen.observe_overrides(grid)["transform_code"] for grid in seed60_lesson],
        "identity_disagreements": sum(
            identity(grid) != gen.rule_mirror(grid) for grid in seed60_lesson
        ),
    }

    return {
        "schema": "arc-generator-schedule-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(source.relative_to(root)),
        "generator_sha256": digest,
        "rule_hash": gen.RULE_HASH,
        "scope": {
            "authority": "generator Python rule mirror; confirm labels separately with Racket-backed census",
            "bands": ["easy", "medium", "hard"],
            "seeds": list(seed_values),
            "period": period,
            "lesson_size": 5,
            "demonstrations_per_rotation": 4,
            "declared_rivals": sorted(competitors),
        },
        "summary": {
            "lessons_checked": checked_lessons,
            "rotations_checked": checked_rotations,
            "ambiguities": len(ambiguities),
            "status": "no_ambiguity_found" if not ambiguities else "ambiguity_found",
        },
        "retained_seed60_identity_case": seed60,
        "ambiguities": ambiguities,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = audit(tuple(args.seeds or (0, 60)))
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if not report["ambiguities"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
