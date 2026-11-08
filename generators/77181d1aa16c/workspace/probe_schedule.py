#!/usr/bin/env python3
"""Replay every cyclic lesson start and every query rotation for task 77181d1aa16c.

This is a task-local authoring probe, not a universal identifiability proof.  It
checks the generator's declared deterministic rivals on five-pair windows.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK_ID = "77181d1aa16c"
HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[3]
for support in (REPO_ROOT / "shared" / "runtime", REPO_ROOT / "src"):
    if support.is_dir() and str(support) not in sys.path:
        sys.path.insert(0, str(support))
GENERATOR = HERE.parents[1] / "generator.py"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"schedule_probe_{TASK_ID}", GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {GENERATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(*, starts: int = 12, window: int = 5) -> dict:
    gen = _load_generator()
    failures: list[dict] = []
    profiles: dict[str, dict[str, int]] = {}
    lessons = rotations = rival_checks = unique_inputs = 0
    seen: set[str] = set()

    for band in ("easy", "medium", "hard"):
        band_profiles: dict[str, int] = {}
        for start in range(starts):
            seed = 1207 + start
            pairs = []
            for offset in range(window):
                sample_index = start + offset
                grid = gen.generate(seed, sample_index, difficulty=band)
                profile = str(gen.schedule_profile(seed, sample_index, difficulty=band))
                band_profiles[profile] = band_profiles.get(profile, 0) + 1
                errors = gen.self_check(grid, difficulty=band)
                if errors:
                    failures.append({
                        "kind": "self_check",
                        "band": band,
                        "start": start,
                        "offset": offset,
                        "seed": seed,
                        "sample_index": sample_index,
                        "errors": errors,
                    })
                truth = gen.rule_mirror(grid)
                pairs.append({"input": grid, "output": truth})
                digest = hashlib.sha256(
                    json.dumps(grid, separators=(",", ":")).encode("utf-8")
                ).hexdigest()
                seen.add(digest)
            lessons += 1

            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                reasons = gen.lesson_identifiable(demos, query)
                if reasons:
                    failures.append({
                        "kind": "lesson_identifiable",
                        "band": band,
                        "start": start,
                        "seed": seed,
                        "query_index": query_index,
                        "reasons": reasons,
                    })
                for name, rival in gen.LESSON_COMPETITORS.items():
                    rival_checks += 1
                    if not any(rival(pair["input"]) != pair["output"] for pair in demos):
                        failures.append({
                            "kind": "unrefuted_rival",
                            "band": band,
                            "start": start,
                            "seed": seed,
                            "query_index": query_index,
                            "rival": name,
                        })
                rotations += 1
        profiles[band] = band_profiles

    unique_inputs = len(seen)
    return {
        "schema": "arcpuzzles-task-schedule-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": _sha256(GENERATOR),
        "generator_version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "policy": {
            "bands": ["easy", "medium", "hard"],
            "seed_rule": "1207 + start",
            "starts": [0, starts - 1],
            "schedule_period": gen.LESSON_SCHEDULE_PERIOD,
            "window_pairs": window,
            "query_policy": "every pair held out once; remaining pairs are demonstrations",
            "rivals": sorted(gen.LESSON_COMPETITORS),
        },
        "counts": {
            "lessons": lessons,
            "rotations": rotations,
            "rival_checks": rival_checks,
            "unique_inputs": unique_inputs,
            "failures": len(failures),
        },
        "profiles_per_band": profiles,
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "limitations": [
            "Finite check against only the generator's declared rivals.",
            "Enumerates every schedule residue twice but not every possible RNG seed or hypothesis.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--starts", type=int, default=12)
    parser.add_argument("--window", type=int, default=5)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.starts <= 0 or args.window < 2:
        parser.error("--starts must be positive and --window must be at least 2")
    result = run(starts=args.starts, window=args.window)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
