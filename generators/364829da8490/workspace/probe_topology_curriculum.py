#!/usr/bin/env python3
"""Source-bound curriculum probe for 364829da8490.

This is a reviewer utility, not an output authority. It uses the task's existing
Python mirror and declared rivals to enumerate every schedule residue and every
query holdout, while reporting which profiles refute which rivals. Use the
public Racket apply/census tools for authoritative labels.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "364829da8490"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--profile-seeds", type=int, default=12)
    args = parser.parse_args()

    source_path = Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location(
        f"curriculum_probe_{TASK_ID}", source_path
    )
    if spec is None or spec.loader is None:
        raise SystemExit(f"could not load generator source at {source_path}")
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)

    profile_rows = {}
    for profile in gen.SCENE_PROFILES:
        refuted = {name: 0 for name in gen.SEMANTIC_RIVALS}
        valid = 0
        for seed in range(args.profile_seeds):
            grid = gen.generate(
                seed,
                0,
                difficulty="medium",
                scene_profile=profile,
            )
            errors = gen.self_check(grid)
            if errors:
                raise SystemExit(f"{profile} seed {seed}: {errors}")
            valid += 1
            expected = gen.rule_mirror(grid)
            for name, rival in gen.SEMANTIC_RIVALS.items():
                if rival(grid) != expected:
                    refuted[name] += 1
        profile_rows[profile] = {
            "draws": valid,
            "rivals_refuted_at_least_once": sorted(
                name for name, count in refuted.items() if count
            ),
            "per_rival_refutation_count": refuted,
        }

    schedule_failures = []
    checked_lessons = 0
    checked_holdouts = 0
    for difficulty in ("easy", "medium", "hard"):
        for start in range(gen.LESSON_SCHEDULE_PERIOD):
            pairs = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(
                    args.seed,
                    start + offset,
                    difficulty=difficulty,
                )
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            checked_lessons += 1
            for query_index, query in enumerate(pairs):
                checked_holdouts += 1
                demos = [
                    pair for index, pair in enumerate(pairs)
                    if index != query_index
                ]
                reasons = gen.lesson_identifiable(demos, query)
                survivors = [
                    name
                    for name, rival in gen.LESSON_COMPETITORS.items()
                    if all(rival(pair["input"]) == pair["output"] for pair in demos)
                ]
                if reasons or survivors:
                    schedule_failures.append(
                        {
                            "difficulty": difficulty,
                            "start": start,
                            "query_index": query_index,
                            "reasons": reasons,
                            "surviving_rivals": survivors,
                        }
                    )

    report = {
        "schema": "364829da8490-topology-curriculum-probe-v1",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "rule_hash": gen.RULE_HASH,
        "seed": args.seed,
        "profile_seed_count": args.profile_seeds,
        "examples_needed": gen.EXAMPLES_NEEDED,
        "schedule_period": gen.LESSON_SCHEDULE_PERIOD,
        "declared_rivals": sorted(gen.SEMANTIC_RIVALS),
        "profiles": profile_rows,
        "schedule": {
            "lessons_checked": checked_lessons,
            "holdouts_checked": checked_holdouts,
            "failures": schedule_failures,
            "status": "pass" if not schedule_failures else "fail",
            "scope": "all declared starts at one fixed seed in all three bands",
        },
        "authority_note": (
            "Python mirror/rival diagnostic only; use arcpuzzles apply or "
            "lesson-census for authoritative Racket labels."
        ),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["schedule"]["status"],
        "lessons_checked": checked_lessons,
        "holdouts_checked": checked_holdouts,
        "out": str(out),
    }, indent=2))
    return 0 if not schedule_failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
