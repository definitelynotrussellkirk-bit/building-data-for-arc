#!/usr/bin/env python3
"""Exhaust every four-pair cyclic start and all four query rotations.

The shared lesson census samples production starts. This task-local probe is the
cheap exhaustive companion: for each requested start it materializes four
consecutive default pairs, holds each pair out once, and verifies that every
declared lesson competitor is refuted by the remaining three demonstrations.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("ada3_rotation_probe_target", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def pair(module, grid: list[list[int]]) -> dict[str, Any]:
    return {
        "input": copy.deepcopy(grid),
        "output": module.rule_mirror(grid),
    }


def probe(
    generator_path: Path,
    seeds: list[int],
    starts: int,
    difficulties: list[str | None],
) -> dict[str, Any]:
    module = load_generator(generator_path)
    rivals = dict(module.LESSON_COMPETITORS)
    report: dict[str, Any] = {
        "schema": "ada3-lesson-rotation-probe-v1",
        "generator": str(generator_path),
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "seeds": seeds,
        "starts": starts,
        "window_size": 4,
        "rivals": sorted(rivals),
        "difficulties": {},
    }
    total_rotations = 0
    total_ambiguous = 0
    total_hook_failures = 0
    first_ambiguity: dict[str, Any] | None = None
    first_hook_failure: dict[str, Any] | None = None

    for difficulty in difficulties:
        key = "none" if difficulty is None else difficulty
        ambiguous = 0
        hook_failures = 0
        rival_survivals = {name: 0 for name in rivals}

        for seed in seeds:
            samples = [
                pair(module, module.generate(seed, index, difficulty=difficulty))
                for index in range(starts + 3)
            ]
            for start in range(starts):
                lesson = samples[start : start + 4]
                for query_offset in range(4):
                    total_rotations += 1
                    demos = [
                        item
                        for offset, item in enumerate(lesson)
                        if offset != query_offset
                    ]
                    query = lesson[query_offset]
                    survivors = [
                        name
                        for name, rival in rivals.items()
                        if all(
                            rival(item["input"]) == item["output"]
                            for item in demos
                        )
                    ]
                    reasons = module.lesson_identifiable(demos, query)
                    if survivors:
                        ambiguous += 1
                        total_ambiguous += 1
                        for name in survivors:
                            rival_survivals[name] += 1
                        if first_ambiguity is None:
                            first_ambiguity = {
                                "difficulty": key,
                                "seed": seed,
                                "start": start,
                                "query_offset": query_offset,
                                "survivors": survivors,
                                "reasons": reasons,
                                "lesson": lesson,
                            }
                    if reasons:
                        hook_failures += 1
                        total_hook_failures += 1
                        if first_hook_failure is None:
                            first_hook_failure = {
                                "difficulty": key,
                                "seed": seed,
                                "start": start,
                                "query_offset": query_offset,
                                "reasons": reasons,
                                "survivors": survivors,
                            }

        report["difficulties"][key] = {
            "rotations": len(seeds) * starts * 4,
            "ambiguous_rotations": ambiguous,
            "hook_failure_rotations": hook_failures,
            "rival_survivals": rival_survivals,
        }

    report["summary"] = {
        "total_rotations": total_rotations,
        "ambiguous_rotations": total_ambiguous,
        "hook_failure_rotations": total_hook_failures,
        "all_rotations_identifiable": (
            total_ambiguous == 0 and total_hook_failures == 0
        ),
        "first_ambiguity": first_ambiguity,
        "first_hook_failure": first_hook_failure,
    }
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--generator",
        type=Path,
        default=HERE.parent.parent / "generator.py",
    )
    parser.add_argument("--seeds", default="0,17,91")
    parser.add_argument("--starts", type=int, default=72)
    parser.add_argument("--out", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    seeds = [int(value) for value in args.seeds.split(",") if value.strip()]
    result = probe(
        args.generator.resolve(),
        seeds=seeds,
        starts=args.starts,
        difficulties=[None, "easy", "medium", "hard"],
    )
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    return 0 if result["summary"]["all_rotations_identifiable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
