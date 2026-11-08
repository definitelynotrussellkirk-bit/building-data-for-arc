#!/usr/bin/env python3
"""Exhaustively probe the task's small cyclic lesson schedule under query rotation.

The probe derives rivals and schedule metadata from the generator itself, verifies
that every declared canonical shortcut fits every labeled canonical pair, then
checks all query positions for every cyclic start, difficulty band, and requested
seed.  It writes compact JSON suitable for review evidence and exits nonzero on
any failure.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "0a9e3d364bb3"


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-base", type=int, default=2678160609)
    parser.add_argument("--seeds", type=int, default=16)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error("--seeds must be positive")

    root = find_root(__file__)
    generator_path = Path(__file__).resolve().parents[1] / "generator.py"
    spec = spec_from_file_location(f"rotation_probe_{TASK_ID}", generator_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {generator_path}")
    gen = module_from_spec(spec)
    spec.loader.exec_module(gen)
    generator_sha256 = hashlib.sha256(generator_path.read_bytes()).hexdigest()

    canonical = canonical_pairs(TASK_ID, root=root)
    shortcut_canonical_failures: list[dict[str, Any]] = []
    for rival_name, rival in gen.CANONICAL_SHORTCUTS.items():
        for pair_index, pair in enumerate(canonical):
            if rival(pair["input"]) != pair["output"]:
                shortcut_canonical_failures.append(
                    {"rival": rival_name, "canonical_pair_index": pair_index}
                )

    period = len(gen.SCHEDULE_PROFILES)
    lesson_pair_count = gen.EXAMPLES_NEEDED + 1
    failures: list[dict[str, Any]] = []
    generated_lessons = 0
    rotations_checked = 0
    unique_inputs: set[str] = set()

    for difficulty in ("easy", "medium", "hard"):
        for seed_offset in range(args.seeds):
            seed = args.seed_base + seed_offset
            for start in range(period):
                pairs = []
                for offset in range(lesson_pair_count):
                    sample_index = start + offset
                    grid = gen.generate(seed, sample_index, difficulty=difficulty)
                    pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
                    unique_inputs.add(_grid_hash(grid))
                generated_lessons += 1

                textures = [
                    gen.observe_overrides(pair["input"])["texture"] for pair in pairs
                ]
                texture_counts = Counter(textures)
                expected_repeats = lesson_pair_count // period if lesson_pair_count % period == 0 else None
                if expected_repeats is None or texture_counts != Counter(
                    {texture: expected_repeats for texture in gen.HELPFUL_TEXTURES}
                ):
                    failures.append(
                        {
                            "kind": "profile_coverage",
                            "difficulty": difficulty,
                            "seed": seed,
                            "start": start,
                            "textures": textures,
                        }
                    )

                for query_index, query in enumerate(pairs):
                    rotations_checked += 1
                    demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                    reasons = gen.lesson_identifiable(demos, query)
                    survivors = []
                    differing_survivors = []
                    truth = query["output"]
                    for rival_name, rival in gen.LESSON_COMPETITORS.items():
                        if all(rival(demo["input"]) == demo["output"] for demo in demos):
                            survivors.append(rival_name)
                            if rival(query["input"]) != truth:
                                differing_survivors.append(rival_name)
                    if reasons or differing_survivors:
                        failures.append(
                            {
                                "kind": "rotation_ambiguity",
                                "difficulty": difficulty,
                                "seed": seed,
                                "start": start,
                                "query_index": query_index,
                                "query_input_sha256": _grid_hash(query["input"]),
                                "textures": textures,
                                "reasons": reasons,
                                "surviving_rivals": survivors,
                                "differing_query_rivals": differing_survivors,
                            }
                        )

    report = {
        "schema": "rotation_curriculum_probe/1",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": generator_sha256,
        "rule_hash": gen.RULE_HASH,
        "seed_base": args.seed_base,
        "seed_count": args.seeds,
        "difficulties": ["easy", "medium", "hard"],
        "schedule_profiles": list(gen.SCHEDULE_PROFILES),
        "helpful_textures": list(gen.HELPFUL_TEXTURES),
        "examples_needed": gen.EXAMPLES_NEEDED,
        "lesson_pair_count": lesson_pair_count,
        "cyclic_starts_per_seed_band": period,
        "generated_lessons": generated_lessons,
        "rotations_checked": rotations_checked,
        "unique_inputs": len(unique_inputs),
        "declared_canonical_shortcuts": list(gen.CANONICAL_SHORTCUTS),
        "canonical_pair_count": len(canonical),
        "canonical_shortcut_failures": shortcut_canonical_failures,
        "failure_count": len(failures) + len(shortcut_canonical_failures),
        "failures": failures,
        "passed": not failures and not shortcut_canonical_failures,
    }
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
