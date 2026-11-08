#!/usr/bin/env python3
"""Fast source-bound lesson probe for generator 946e33609350.

This is an authoring aid, not a replacement for the Racket-backed semantic gate
or lesson census. It loads the adjacent generator by exact path, materializes
ordered three-demonstration lessons, scores every declared competitor, checks
all four query rotations, and records the generator SHA-256 used for the report.

Examples:
    python3 lesson_probe.py
    python3 lesson_probe.py --starts-per-band 25 --seed 2468 --out report.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[1]
GEN_PATH = TASK_DIR / "generator.py"
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "shared/runtime"))


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_generator(path: str | Path = GEN_PATH):
    path = Path(path).resolve()
    spec = importlib.util.spec_from_file_location(
        f"lesson_probe_{path.parent.name}", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load generator spec from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _freeze(grid) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(value) for value in row) for row in grid)


def _lesson_seed(base_seed: int, band_index: int, start: int) -> int:
    return int(base_seed) + band_index * 100_003 + start * 997


def run_probe(*, starts_per_band: int = 6, seed: int = 2468) -> dict[str, Any]:
    """Run ordered and all-query-rotation checks using declared rule mirrors.

    The returned report is JSON-serializable. A zero failure count means only
    that the generator's declared rivals were refuted on this finite sample;
    authoritative labels still belong to the Racket-backed public tools.
    """
    if type(starts_per_band) is not int or starts_per_band <= 0:
        raise ValueError("starts_per_band must be a positive integer")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")

    gen = load_generator()
    bands = (None, "easy", "medium", "hard")
    expected_profiles = set(gen.SCHEDULE_PROFILES)
    competitors = dict(gen.LESSON_COMPETITORS)
    survivor_counts = {name: 0 for name in sorted(competitors)}
    production_failures: list[dict[str, Any]] = []
    rotation_failures: list[dict[str, Any]] = []
    profile_window_failures: list[dict[str, Any]] = []
    unique_inputs: set[tuple[tuple[int, ...], ...]] = set()
    profile_counts = {name: 0 for name in gen.SCHEDULE_PROFILES}

    for band_index, difficulty in enumerate(bands):
        for start in range(starts_per_band):
            lesson_seed = _lesson_seed(seed, band_index, start)
            pairs = []
            profiles = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                sample_index = start + offset
                grid = gen.generate(
                    lesson_seed,
                    sample_index,
                    difficulty=difficulty,
                )
                unique_inputs.add(_freeze(grid))
                observed = gen.observe_overrides(grid)
                profile = observed["profile"]
                profile_counts[profile] += 1
                profiles.append(profile)
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})

            demos = pairs[: gen.EXAMPLES_NEEDED]
            query = pairs[gen.EXAMPLES_NEEDED]
            demo_profiles = set(profiles[: gen.EXAMPLES_NEEDED])
            if demo_profiles != expected_profiles:
                profile_window_failures.append(
                    {
                        "difficulty": difficulty,
                        "start": start,
                        "seed": lesson_seed,
                        "profiles": profiles[: gen.EXAMPLES_NEEDED],
                    }
                )

            for name, competitor in competitors.items():
                if all(
                    competitor(pair["input"]) == pair["output"] for pair in demos
                ):
                    survivor_counts[name] += 1

            reasons = gen.lesson_identifiable(demos, query)
            if reasons:
                production_failures.append(
                    {
                        "difficulty": difficulty,
                        "start": start,
                        "seed": lesson_seed,
                        "profiles": profiles,
                        "reasons": list(reasons),
                    }
                )

            for query_index in range(len(pairs)):
                rotated_query = pairs[query_index]
                rotated_demos = [
                    pair for index, pair in enumerate(pairs) if index != query_index
                ]
                reasons = gen.lesson_identifiable(rotated_demos, rotated_query)
                if reasons:
                    rotation_failures.append(
                        {
                            "difficulty": difficulty,
                            "start": start,
                            "seed": lesson_seed,
                            "query_index": query_index,
                            "profiles": profiles,
                            "reasons": list(reasons),
                        }
                    )

    lesson_count = len(bands) * starts_per_band
    return {
        "schema": "946e33609350-lesson-probe-v1",
        "task_id": gen.TASK_ID,
        "generator_path": str(GEN_PATH),
        "generator_sha256": file_sha256(GEN_PATH),
        "rule_hash": gen.RULE_HASH,
        "examples_needed": gen.EXAMPLES_NEEDED,
        "schedule_period": gen.LESSON_SCHEDULE_PERIOD,
        "bands": ["none" if band is None else band for band in bands],
        "base_seed": seed,
        "starts_per_band": starts_per_band,
        "lesson_count": lesson_count,
        "materialized_pair_count": lesson_count * (gen.EXAMPLES_NEEDED + 1),
        "unique_input_count": len(unique_inputs),
        "profile_counts": profile_counts,
        "profile_window_failures": profile_window_failures,
        "production_failure_count": len(production_failures),
        "production_failures": production_failures,
        "rotation_count": lesson_count * (gen.EXAMPLES_NEEDED + 1),
        "rotation_failure_count": len(rotation_failures),
        "rotation_failures": rotation_failures,
        "competitor_survivor_counts": survivor_counts,
        "limitations": [
            "Uses the Python rule mirror rather than the authoritative Racket runner.",
            "Tests only declared competitors and the requested finite seed/start sample.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--starts-per-band", type=int, default=6)
    parser.add_argument("--seed", type=int, default=2468)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = run_probe(starts_per_band=args.starts_per_band, seed=args.seed)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(text, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(args.out)
    return 0 if (
        report["production_failure_count"] == 0
        and report["rotation_failure_count"] == 0
        and not report["profile_window_failures"]
        and all(count == 0 for count in report["competitor_survivor_counts"].values())
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
