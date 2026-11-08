#!/usr/bin/env python3
"""Exhaust the finite generator and four-step teaching contracts.

This is a source-bound maintainer probe.  It checks the Python mirror against
all labeled canonical pairs, enumerates every advertised exact-axis combination,
exhausts every cyclic lesson start and query position at one fixed seed, and
verifies that aligned four-answer blocks hold nuisance controls constant.  The
selected Racket authority remains the final label oracle; use the repository
battery for independent Racket evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "637229802e6f"
HERE = Path(__file__).resolve().parent
GENERATOR_PATH = HERE.parent / "generator.py"
REPO = HERE.parents[2]
RUNTIME = REPO / "shared" / "runtime"
for candidate in (RUNTIME, REPO / "src", REPO):
    if candidate.exists() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load_generator(path: Path):
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid_key(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def analyze(generator_path: Path | str = GENERATOR_PATH) -> dict[str, Any]:
    path = Path(generator_path).resolve()
    gen = _load_generator(path)
    root = find_root(__file__)
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)

    canonical_failures: list[str] = []
    for index, pair in enumerate(pairs):
        errors = gen.self_check(pair["input"])
        if errors:
            canonical_failures.append(f"pair {index}: self_check: {errors}")
        if gen.rule_mirror(pair["input"]) != pair["output"]:
            canonical_failures.append(f"pair {index}: mirror mismatch")

    exact_failures: list[str] = []
    output_keys: set[tuple[tuple[int, ...], ...]] = set()
    exact_count = 0
    domains = (
        gen.QUADRANTS,
        range(4),
        gen.DECORATION_PROFILES,
    )
    for index, (quadrant, slot, profile) in enumerate(itertools.product(*domains)):
        requested = {
            "marker_quadrant": quadrant,
            "marker_slot": slot,
            "decoration_profile": profile,
        }
        grid = gen.generate(20_261_011 + index, index, difficulty="hard", **requested)
        exact_count += 1
        errors = gen.self_check(grid)
        if errors:
            exact_failures.append(f"{requested}: self_check: {errors}")
        observed = gen.observe_overrides(grid)
        if observed != requested:
            exact_failures.append(f"{requested}: observed {observed}")
        output_keys.add(_grid_key(gen.rule_mirror(grid)))

    schedule_failures: list[str] = []
    schedule_cases = 0
    for band in ("easy", "medium", "hard"):
        for start in range(gen.LESSON_SCHEDULE_PERIOD):
            materialized = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(0, start + offset, difficulty=band)
                materialized.append({"input": grid, "output": gen.rule_mirror(grid)})
            for query_index, query in enumerate(materialized):
                demos = [pair for index, pair in enumerate(materialized) if index != query_index]
                reasons = gen.lesson_identifiable(demos, query)
                schedule_cases += 1
                if reasons:
                    schedule_failures.append(
                        f"band={band} start={start} query={query_index}: {reasons}"
                    )

    nuisance_failures: list[str] = []
    nuisance_blocks = 0
    for band in ("easy", "medium", "hard"):
        for block in range(2):
            observations = [
                gen.observe_overrides(
                    gen.generate(0, block * gen.LESSON_SCHEDULE_PERIOD + offset, difficulty=band)
                )
                for offset in range(gen.LESSON_SCHEDULE_PERIOD)
            ]
            nuisance_blocks += 1
            profiles = {item["decoration_profile"] for item in observations}
            slots = {item["marker_slot"] for item in observations}
            quadrants = {item["marker_quadrant"] for item in observations}
            if len(profiles) != 1 or len(slots) != 1 or quadrants != set(gen.QUADRANTS):
                nuisance_failures.append(
                    f"band={band} block={block}: profiles={sorted(profiles)}, "
                    f"slots={sorted(slots)}, quadrants={sorted(quadrants)}"
                )

    old_schedule = [gen.QUADRANTS[(2 * index) % 4] for index in range(4)]
    new_schedule = [gen.schedule_profile(0, index, "easy") for index in range(4)]

    report: dict[str, Any] = {
        "schema": f"{TASK_ID}-contract-probe/1",
        "task_id": TASK_ID,
        "version": gen.VERSION,
        "generator_path": str(path),
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "rule_hash": gen.RULE_HASH,
        "canonical_pairs": len(pairs),
        "canonical_failures": canonical_failures,
        "exact_axis_combinations": exact_count,
        "exact_axis_failures": exact_failures,
        "declared_output_codomain": gen.EXPECTED_OUTPUT_CODOMAIN,
        "distinct_outputs": len(output_keys),
        "schedule_cases": schedule_cases,
        "schedule_failures": schedule_failures,
        "nuisance_blocks": nuisance_blocks,
        "nuisance_failures": nuisance_failures,
        "old_two-step_schedule": old_schedule,
        "old_two-step_unique_quadrants": len(set(old_schedule)),
        "current_four_step_schedule": new_schedule,
        "current_unique_quadrants": len(set(new_schedule)),
    }
    report["ok"] = all(
        (
            len(pairs) == 4,
            not canonical_failures,
            exact_count == 64,
            not exact_failures,
            len(output_keys) == gen.EXPECTED_OUTPUT_CODOMAIN == 4,
            schedule_cases == 48,
            not schedule_failures,
            not nuisance_failures,
            len(set(new_schedule)) == 4,
        )
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=GENERATOR_PATH)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    report = analyze(args.generator)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "ok": report["ok"],
                "generator_sha256": report["generator_sha256"],
                "exact_axis_combinations": report["exact_axis_combinations"],
                "schedule_cases": report["schedule_cases"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
