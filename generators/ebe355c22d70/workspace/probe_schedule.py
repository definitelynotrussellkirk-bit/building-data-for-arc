#!/usr/bin/env python3
"""Exhaust the finite teaching schedule and every one-query rotation.

This is a task-local prototype for a shared curriculum gate: it derives the
period and rivals from the live generator instead of copying either list into
the probe.  It does not claim uniqueness against undeclared hypotheses.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Any

HOME = Path(__file__).resolve().parents[1]
DEFAULT_GENERATOR = HOME / "generator.py"


def load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("schedule_probe_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def independent_output(grid: list[list[int]]) -> list[list[int]]:
    points = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    ]
    if len(points) != 2:
        raise ValueError(f"expected exactly two color-1 cells, got {len(points)}")
    (r0, c0), (r1, c1) = points
    height = abs(r1 - r0) + 1
    width = abs(c1 - c0) + 1
    return [[8] * width for _ in range(height)]


def grid_error(value: Any) -> str | None:
    if not isinstance(value, list) or not value:
        return "not a nonempty list"
    if not isinstance(value[0], list) or not value[0]:
        return "rows are not nonempty lists"
    width = len(value[0])
    for row in value:
        if not isinstance(row, list) or len(row) != width:
            return "rows are ragged"
        for cell in row:
            if type(cell) is not int or not 0 <= cell <= 9:
                return f"invalid ARC cell {cell!r}"
    return None


def freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def run_probe(generator_path: Path) -> dict[str, Any]:
    gen = load_generator(generator_path)
    profiles = tuple(getattr(gen, "SCHEDULE_PROFILES", ()))
    if not profiles:
        raise ValueError("generator has no finite SCHEDULE_PROFILES declaration")
    period = len(profiles)
    rivals = dict(getattr(gen, "LESSON_COMPETITORS", {}))
    if not rivals:
        raise ValueError("generator has no LESSON_COMPETITORS declaration")

    # A seed divisible by the period makes sample_index equal the schedule slot
    # for this generator, while still using the production sampler unchanged.
    seed = period * 1000
    violations: list[dict[str, Any]] = []
    rotations = 0
    rival_checks = 0
    starts = 0
    observed_outputs: set[tuple[tuple[int, ...], ...]] = set()
    profile_names: set[str] = set()

    for band in ("easy", "medium", "hard"):
        for start in range(period):
            starts += 1
            pairs = []
            for offset in range(4):
                sample_index = start + offset
                grid = gen.generate(seed, sample_index, difficulty=band)
                errors = list(gen.self_check(grid) or [])
                if errors:
                    violations.append(
                        {
                            "band": band,
                            "start": start,
                            "sample_index": sample_index,
                            "kind": "self_check",
                            "errors": errors,
                        }
                    )
                output = independent_output(grid)
                observed_outputs.add(freeze(output))
                profile_names.add(str(gen.schedule_profile(seed, sample_index, band)))
                pairs.append({"input": grid, "output": output})

            for query_index in range(4):
                rotations += 1
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                query = pairs[query_index]
                hook_errors = list(gen.lesson_identifiable(demos, query) or [])
                if hook_errors:
                    violations.append(
                        {
                            "band": band,
                            "start": start,
                            "query_index": query_index,
                            "kind": "lesson_identifiable",
                            "errors": hook_errors,
                        }
                    )

                truth = query["output"]
                for name, rival in rivals.items():
                    rival_checks += 1
                    demo_predictions = []
                    malformed = []
                    for pair_index, pair in enumerate(demos):
                        prediction = rival(pair["input"])
                        error = grid_error(prediction)
                        if error:
                            malformed.append({"pair_index": pair_index, "error": error})
                        demo_predictions.append(prediction)
                    query_prediction = rival(query["input"])
                    query_error = grid_error(query_prediction)
                    if query_error:
                        malformed.append({"pair_index": "query", "error": query_error})
                    if malformed:
                        violations.append(
                            {
                                "band": band,
                                "start": start,
                                "query_index": query_index,
                                "kind": "malformed_rival_output",
                                "rival": name,
                                "details": malformed,
                            }
                        )
                        continue
                    fits_demos = all(
                        prediction == pair["output"]
                        for prediction, pair in zip(demo_predictions, demos)
                    )
                    if fits_demos and query_prediction != truth:
                        violations.append(
                            {
                                "band": band,
                                "start": start,
                                "query_index": query_index,
                                "kind": "surviving_query_changing_rival",
                                "rival": name,
                            }
                        )

    expected_codomain = getattr(gen, "EXPECTED_OUTPUT_CODOMAIN", None)
    if expected_codomain != len(observed_outputs):
        violations.append(
            {
                "kind": "output_codomain_mismatch",
                "declared": expected_codomain,
                "observed": len(observed_outputs),
            }
        )
    if len(profile_names) != period:
        violations.append(
            {
                "kind": "schedule_profile_coverage",
                "period": period,
                "observed_profiles": sorted(profile_names),
            }
        )

    return {
        "schema": "ebe355c22d70-schedule-probe-v1",
        "task_id": getattr(gen, "TASK_ID", "unknown"),
        "generator_path": str(generator_path),
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "period": period,
        "bands": 3,
        "cyclic_starts": starts,
        "query_rotations": rotations,
        "declared_rivals": sorted(rivals),
        "rival_rotation_checks": rival_checks,
        "declared_output_codomain": expected_codomain,
        "observed_output_codomain": len(observed_outputs),
        "observed_schedule_profiles": len(profile_names),
        "violations": violations,
        "status": "pass" if not violations else "fail",
        "limits": (
            "Exhaustive only for the declared finite schedule and declared rivals; "
            "does not prove identifiability against every possible rule."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--generator",
        type=Path,
        default=Path(os.environ.get("GENERATOR_UNDER_TEST", DEFAULT_GENERATOR)),
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = run_probe(args.generator.resolve())
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
