#!/usr/bin/env python3
"""Exhaust cyclic four-pair windows and every three-demo query rotation.

This is a fast, task-local companion to the Racket-scored lesson census.  It
loads the selected generator, labels with its focused Python mirror, and checks
that every declared competitor is refuted by the remaining three examples.
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


def _load(path: Path):
    spec = importlib.util.spec_from_file_location("f891_curriculum_probe_target", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _pair(module, grid: list[list[int]]) -> dict[str, Any]:
    return {"input": copy.deepcopy(grid), "output": module.rule_mirror(grid)}


def probe(generator_path: Path, *, seeds: list[int], starts: int) -> dict[str, Any]:
    module = _load(generator_path)
    competitors = dict(module.LESSON_COMPETITORS)
    report: dict[str, Any] = {
        "schema": "f891d1ff5dd8-curriculum-probe-v1",
        "generator": str(generator_path),
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "seeds": seeds,
        "starts": starts,
        "window_size": 4,
        "demonstrations_per_rotation": 3,
        "competitors": sorted(competitors),
        "difficulties": {},
    }
    total = ambiguous = hook_failures = 0
    first_failure = None
    for difficulty in (None, "easy", "medium", "hard"):
        key = "none" if difficulty is None else difficulty
        local_total = local_ambiguous = local_hook = 0
        profiles: dict[str, int] = {}
        for seed in seeds:
            samples = [
                _pair(module, module.generate(seed, index, difficulty=difficulty))
                for index in range(starts + 3)
            ]
            for index in range(starts + 3):
                profile = str(module.schedule_profile(seed, index, difficulty))
                profiles[profile] = profiles.get(profile, 0) + 1
            for start in range(starts):
                lesson = samples[start : start + 4]
                for query_offset in range(4):
                    demos = [pair for i, pair in enumerate(lesson) if i != query_offset]
                    query = lesson[query_offset]
                    survivors = [
                        name
                        for name, rival in competitors.items()
                        if all(rival(pair["input"]) == pair["output"] for pair in demos)
                    ]
                    reasons = module.lesson_identifiable(demos, query)
                    total += 1
                    local_total += 1
                    if survivors:
                        ambiguous += 1
                        local_ambiguous += 1
                    if reasons:
                        hook_failures += 1
                        local_hook += 1
                    if first_failure is None and (survivors or reasons):
                        first_failure = {
                            "difficulty": key,
                            "seed": seed,
                            "start": start,
                            "query_offset": query_offset,
                            "survivors": survivors,
                            "reasons": reasons,
                            "lesson": lesson,
                        }
        report["difficulties"][key] = {
            "rotations": local_total,
            "ambiguous_rotations": local_ambiguous,
            "hook_failure_rotations": local_hook,
            "profile_counts": profiles,
        }
    report["summary"] = {
        "total_rotations": total,
        "ambiguous_rotations": ambiguous,
        "hook_failure_rotations": hook_failures,
        "all_rotations_identifiable": ambiguous == 0 and hook_failures == 0,
        "first_failure": first_failure,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path, default=HERE.parent.parent / "generator.py")
    parser.add_argument("--seeds", default="0,17,91")
    parser.add_argument("--starts", type=int, default=64)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = probe(
        args.generator.resolve(),
        seeds=[int(value) for value in args.seeds.split(",") if value.strip()],
        starts=args.starts,
    )
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if result["summary"]["all_rotations_identifiable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
