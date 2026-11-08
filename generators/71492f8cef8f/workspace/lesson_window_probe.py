#!/usr/bin/env python3
"""Check every cyclic lesson window against the generator's live contracts.

This is deliberately task-local: it imports the adjacent generator source and
iterates the declarations in that source rather than copying rival or witness
names.  It complements ``lesson-census`` by rotating every small deterministic
schedule position into the query slot.
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


TASK_DIR = Path(__file__).resolve().parents[1]
GENERATOR_PATH = TASK_DIR / "generator.py"


def _ensure_runtime_imports() -> None:
    repository_or_runtime = TASK_DIR.parents[1]
    candidates = (
        repository_or_runtime,
        repository_or_runtime / "shared" / "runtime",
    )
    for candidate in candidates:
        if (candidate / "puzzle_generators").is_dir():
            value = str(candidate)
            if value not in sys.path:
                sys.path.insert(0, value)


def _load_generator():
    _ensure_runtime_imports()
    spec = importlib.util.spec_from_file_location(
        "lesson_window_probe_generator", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pair(generator, seed: int, sample_index: int, band: str) -> dict[str, Any]:
    grid = generator.generate(seed, sample_index, difficulty=band)
    return {
        "input": grid,
        "output": generator.rule_mirror(grid),
        "profile": generator.observe_overrides(grid)["scene_profile"],
    }


def run_probe(*, seeds_per_start: int, seed_base: int) -> dict[str, Any]:
    if seeds_per_start < 1:
        raise ValueError("seeds_per_start must be at least one")
    generator = _load_generator()
    bands = ("easy", "medium", "hard")
    schedule = tuple(generator.SCHEDULE_PROFILES)
    examples_needed = int(generator.EXAMPLES_NEEDED)
    rivals = dict(generator.LESSON_COMPETITORS)
    witnesses = dict(generator.SEMANTIC_WITNESSES)
    expected_windows = len(bands) * len(schedule) * seeds_per_start

    rival_counts = {name: 0 for name in rivals}
    witness_counts = {name: 0 for name in witnesses}
    failures: list[dict[str, Any]] = []
    windows: list[dict[str, Any]] = []

    for band_index, band in enumerate(bands):
        for start in range(len(schedule)):
            for seed_offset in range(seeds_per_start):
                seed = seed_base + band_index * 100_000 + start * 1_000 + seed_offset
                pairs = [
                    _pair(generator, seed, start + offset, band)
                    for offset in range(examples_needed + 1)
                ]
                demos = pairs[:examples_needed]
                query = pairs[examples_needed]
                expected_profiles = [
                    generator.schedule_profile(seed, start + offset, difficulty=band)
                    for offset in range(examples_needed + 1)
                ]
                observed_profiles = [pair["profile"] for pair in pairs]
                window_failures: list[str] = []
                if observed_profiles != expected_profiles:
                    window_failures.append(
                        f"profile schedule mismatch: expected {expected_profiles}, "
                        f"observed {observed_profiles}"
                    )

                identifiability = generator.lesson_identifiable(demos, query)
                window_failures.extend(identifiability)

                refuted_names = []
                for name, rival in rivals.items():
                    refuted = any(
                        rival(copy.deepcopy(demo["input"])) != demo["output"]
                        for demo in demos
                    )
                    if refuted:
                        rival_counts[name] += 1
                        refuted_names.append(name)
                    else:
                        window_failures.append(
                            f"declared rival {name!r} is not refuted by the demos"
                        )

                present_names = []
                for name, witness in witnesses.items():
                    present = any(witness(demo["input"]) for demo in demos)
                    if present:
                        witness_counts[name] += 1
                        present_names.append(name)
                    else:
                        window_failures.append(
                            f"declared witness {name!r} is absent from the demos"
                        )

                record = {
                    "band": band,
                    "start": start,
                    "seed": seed,
                    "profiles": observed_profiles,
                    "rivals_refuted": sorted(refuted_names),
                    "witnesses_present": sorted(present_names),
                    "failures": window_failures,
                }
                windows.append(record)
                if window_failures:
                    failures.append(record)

    source_hash = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    return {
        "schema": "lesson-window-probe-v1",
        "task_id": generator.TASK_ID,
        "generator_sha256": source_hash,
        "version": generator.VERSION,
        "rule_hash": generator.RULE_HASH,
        "bands": list(bands),
        "schedule_profiles": list(schedule),
        "examples_needed": examples_needed,
        "seeds_per_start": seeds_per_start,
        "seed_base": seed_base,
        "windows_total": expected_windows,
        "rival_refuted_in_demos": rival_counts,
        "witness_present_in_demos": witness_counts,
        "failures": failures,
        "windows": windows,
        "status": "pass" if not failures else "fail",
        "scope_note": (
            "Finite declared-rival and declared-witness coverage over every cyclic "
            "start of the deterministic schedule; not a universal induction proof."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds-per-start", type=int, default=16)
    parser.add_argument("--seed-base", type=int, default=71_492_000)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_probe(
        seeds_per_start=args.seeds_per_start,
        seed_base=args.seed_base,
    )
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(
        json.dumps(
            {
                "status": report["status"],
                "task_id": report["task_id"],
                "generator_sha256": report["generator_sha256"],
                "windows_total": report["windows_total"],
                "failure_count": len(report["failures"]),
                "out": str(args.out) if args.out else None,
            },
            indent=2,
        )
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
