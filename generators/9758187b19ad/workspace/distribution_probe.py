#!/usr/bin/env python3
"""Retained adversarial census for generator 9758187b19ad.

The general battery checks validity and sampled semantic diversity. This
review-local probe exhausts the finite curriculum schedule, evaluates every
declared lesson rival, verifies every canonical-shortcut claim against the
public pairs, records exact disagreement cases, and stress-tests the full
public-axis boundary matrix.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

TASK_ID = "9758187b19ad"
HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
GENERATOR_PATH = HERE.parent.parent / "generator.py"
CANONICAL_PATH = REPO / "shared/data/canonical/puzzles.jsonl"
DIFFICULTIES = ("easy", "medium", "hard")

sys.path.insert(0, str(REPO / "shared/runtime"))


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"review_generator_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_pairs() -> list[dict[str, Any]]:
    for line in CANONICAL_PATH.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        test = row["test"] if isinstance(row["test"], list) else [row["test"]]
        return [*row["train"], *test]
    raise RuntimeError(f"task {TASK_ID} absent from {CANONICAL_PATH}")


def _grid_hash(grid: list[list[int]]) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _shape_signature(gen, grid) -> str:
    _, _, cells = gen._template_shape(grid)
    return ";".join(f"{r},{c}" for r, c in sorted(cells))


def _first_disagreement(intended, rival) -> dict[str, Any] | None:
    for r, (left_row, right_row) in enumerate(zip(intended, rival)):
        for c, (left, right) in enumerate(zip(left_row, right_row)):
            if left != right:
                return {"row": r, "col": c, "intended": left, "rival": right}
    return None


def _schedule_period(gen) -> int:
    """Return the complete finite period of every deterministic curriculum axis."""
    schedules = (
        gen.SCHEDULE_PROFILES,
        gen._SOURCE_SIDE_SCHEDULE,
        gen._MARKER_COUNT_SCHEDULE,
        gen._SHORTCUT_BREAKER_SCHEDULE,
    )
    return math.lcm(*(len(values) for values in schedules))


def _lesson_feature_predicates(gen) -> dict[str, Callable[[list[list[int]]], bool]]:
    return {
        "noncanonical_grid_size": lambda grid: (
            len(grid), len(grid[0])
        ) not in gen._CANONICAL_GRID_SIZES,
        "noncanonical_template_box": lambda grid: gen._template_shape(grid)[:2]
        not in gen._CANONICAL_TEMPLATE_BOXES,
        "more_than_five_template_cells": lambda grid: len(
            gen._template_entries_from_grid(grid)
        )
        > 5,
        "contains_color_one": lambda grid: any(1 in row for row in grid),
    }


def _exact_disagreement_cases(
    gen,
    rivals: dict[str, Callable[[list[list[int]]], list[list[int]]]],
    period: int,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Find one deterministic generated counterexample for every named rival."""
    cases: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    seed = 707
    for difficulty in DIFFICULTIES:
        for sample_index in range(period):
            if len(cases) == len(rivals):
                return cases, errors
            grid = gen.generate(seed, sample_index, difficulty=difficulty)
            intended = gen._solve_candidate(grid)
            for name, rival in rivals.items():
                if name in cases:
                    continue
                try:
                    rival_output = rival(grid)
                except Exception as exc:
                    errors.append(
                        f"{name}: exact-witness rival errored at "
                        f"{difficulty}/{sample_index}: {type(exc).__name__}: {exc}"
                    )
                    continue
                disagreement = _first_disagreement(intended, rival_output)
                if disagreement is None:
                    continue
                cases[name] = {
                    "seed": seed,
                    "sample_index": sample_index,
                    "difficulty": difficulty,
                    "input": grid,
                    "intended_output": intended,
                    "rival_output": rival_output,
                    "first_disagreement": disagreement,
                    "input_sha256": _grid_hash(grid),
                    "intended_output_sha256": _grid_hash(intended),
                    "rival_output_sha256": _grid_hash(rival_output),
                }
    return cases, errors


def run_probe(seed_count: int) -> tuple[dict[str, Any], bool]:
    gen = _load_generator()
    failures: list[str] = []
    period = _schedule_period(gen)

    canonical = _canonical_pairs()
    canonical_shortcuts: dict[str, dict[str, Any]] = {}
    for name, shortcut in sorted(gen.CANONICAL_SHORTCUTS.items()):
        try:
            fits = [shortcut(pair["input"]) == pair["output"] for pair in canonical]
        except Exception as exc:
            failures.append(
                f"declared canonical shortcut {name} errored: "
                f"{type(exc).__name__}: {exc}"
            )
            fits = [False] * len(canonical)
        canonical_shortcuts[name] = {
            "pairs_fit": sum(fits),
            "pairs_total": len(fits),
            "fits_all": all(fits),
        }
        if not all(fits):
            failures.append(
                f"declared canonical shortcut {name} does not fit every canonical pair"
            )
        if name not in gen.SEMANTIC_RIVALS:
            failures.append(f"canonical shortcut {name} absent from SEMANTIC_RIVALS")
        if name not in gen.LESSON_COMPETITORS:
            failures.append(f"canonical shortcut {name} absent from LESSON_COMPETITORS")

    # The schedules should fully cross all public categorical factors.
    expected_cross = {
        (profile, side, count)
        for profile in gen.SCHEDULE_PROFILES
        for side in ("left", "middle", "right")
        for count in (4, 5, 6)
    }
    schedule_cross: dict[str, dict[str, Any]] = {}
    for difficulty in DIFFICULTIES:
        observed = {
            (
                gen.schedule_profile(0, index, difficulty),
                gen._source_side_for(index, difficulty),
                gen._marker_count_for(index, difficulty),
            )
            for index in range(period)
        }
        missing = sorted(expected_cross - observed)
        schedule_cross[difficulty] = {
            "observed_combinations": len(observed),
            "expected_combinations": len(expected_cross),
            "missing": missing,
        }
        if missing:
            failures.append(f"{difficulty}: {len(missing)} schedule combinations missing")

    # Exhaust every cyclic three-demo window against every named lesson rival,
    # plus the explicit feature conditions added in this second review round.
    rivals = dict(sorted(gen.LESSON_COMPETITORS.items()))
    feature_predicates = _lesson_feature_predicates(gen)
    lesson_windows: dict[str, dict[str, Any]] = {}
    for difficulty in DIFFICULTIES:
        survivor_starts = {name: [] for name in rivals}
        missing_feature_starts = {name: [] for name in feature_predicates}
        rival_errors: list[dict[str, Any]] = []
        for start in range(period):
            demos = [
                gen.generate(707, start + offset, difficulty=difficulty)
                for offset in range(gen.EXAMPLES_NEEDED)
            ]
            intended = [gen._solve_candidate(grid) for grid in demos]
            for name, rival in rivals.items():
                try:
                    survives = all(
                        rival(grid) == expected
                        for grid, expected in zip(demos, intended)
                    )
                except Exception as exc:
                    rival_errors.append(
                        {
                            "start": start,
                            "rival": name,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
                    survives = True
                if survives:
                    survivor_starts[name].append(start)
            for name, predicate in feature_predicates.items():
                if not any(predicate(grid) for grid in demos):
                    missing_feature_starts[name].append(start)

        lesson_windows[difficulty] = {
            "windows_checked": period,
            "survivor_starts_by_rival": survivor_starts,
            "missing_feature_starts": missing_feature_starts,
            "rival_errors": rival_errors,
        }
        for name, starts in survivor_starts.items():
            if starts:
                failures.append(
                    f"{difficulty}: rival {name} survives {len(starts)} lesson windows"
                )
        for name, starts in missing_feature_starts.items():
            if starts:
                failures.append(
                    f"{difficulty}: feature {name} absent from {len(starts)} lesson windows"
                )
        if rival_errors:
            failures.append(
                f"{difficulty}: lesson-rival evaluation had {len(rival_errors)} errors"
            )

    # Ordinary generation census: structural validity, source-side support,
    # morphology support, uniqueness, feature support and deterministic replay.
    ordinary_draws = 0
    unique_hashes: set[str] = set()
    source_sides = Counter()
    marker_counts = Counter()
    grid_sizes = Counter()
    template_boxes = Counter()
    template_cell_counts = Counter()
    contains_color_one = Counter()
    shapes_by_profile: dict[str, set[str]] = defaultdict(set)
    errors: list[dict[str, Any]] = []
    for difficulty in DIFFICULTIES:
        for seed in range(seed_count):
            for sample_index in range(18):
                ordinary_draws += 1
                try:
                    grid = gen.generate(seed, sample_index, difficulty=difficulty)
                    check = gen.self_check(grid)
                    if check:
                        errors.append(
                            {
                                "kind": "self_check",
                                "difficulty": difficulty,
                                "seed": seed,
                                "sample_index": sample_index,
                                "errors": check,
                            }
                        )
                        continue
                    unique_hashes.add(_grid_hash(grid))
                    source_sides[gen._source_side_observation(grid)] += 1
                    marker_counts[gen.observe_overrides(grid)["n_markers"]] += 1
                    grid_sizes[f"{len(grid)}x{len(grid[0])}"] += 1
                    template_h, template_w, cells = gen._template_shape(grid)
                    template_boxes[f"{template_h}x{template_w}"] += 1
                    template_cell_counts[len(cells)] += 1
                    contains_color_one[str(any(1 in row for row in grid)).lower()] += 1
                    profile = gen.schedule_profile(seed, sample_index, difficulty)
                    shapes_by_profile[profile].add(_shape_signature(gen, grid))
                    if seed == 0 and sample_index < 6:
                        replay = gen.generate(seed, sample_index, difficulty=difficulty)
                        if replay != grid:
                            errors.append(
                                {
                                    "kind": "nondeterministic",
                                    "difficulty": difficulty,
                                    "seed": seed,
                                    "sample_index": sample_index,
                                }
                            )
                except Exception as exc:  # retained evidence, not a hidden crash
                    errors.append(
                        {
                            "kind": "exception",
                            "difficulty": difficulty,
                            "seed": seed,
                            "sample_index": sample_index,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
    if errors:
        failures.append(f"ordinary census had {len(errors)} failures")

    # Full public-axis boundary matrix over every morphology profile and band.
    boundary_cases = 0
    boundary_errors: list[dict[str, Any]] = []
    for difficulty in DIFFICULTIES:
        for sample_index in range(len(gen.SCHEDULE_PROFILES)):
            for seed in range(5):
                for h in (12, 18):
                    for w in (19, 24):
                        for n_markers in (4, 6):
                            boundary_cases += 1
                            try:
                                grid = gen.generate(
                                    seed,
                                    sample_index,
                                    difficulty=difficulty,
                                    grid_h=h,
                                    grid_w=w,
                                    n_markers=n_markers,
                                )
                                observed = gen.observe_overrides(grid)
                                check = gen.self_check(grid)
                                if observed != {
                                    "grid_h": h,
                                    "grid_w": w,
                                    "n_markers": n_markers,
                                } or check:
                                    boundary_errors.append(
                                        {
                                            "difficulty": difficulty,
                                            "sample_index": sample_index,
                                            "seed": seed,
                                            "requested": [h, w, n_markers],
                                            "observed": observed,
                                            "self_check": check,
                                        }
                                    )
                            except Exception as exc:
                                boundary_errors.append(
                                    {
                                        "difficulty": difficulty,
                                        "sample_index": sample_index,
                                        "seed": seed,
                                        "requested": [h, w, n_markers],
                                        "error": f"{type(exc).__name__}: {exc}",
                                    }
                                )
    if boundary_errors:
        failures.append(f"boundary matrix had {len(boundary_errors)} failures")

    disagreement_cases, disagreement_errors = _exact_disagreement_cases(
        gen, rivals, period
    )
    failures.extend(disagreement_errors)
    missing_cases = sorted(set(rivals) - set(disagreement_cases))
    if missing_cases:
        failures.append(
            "no generated exact disagreement case for rivals: "
            + ", ".join(missing_cases)
        )

    result = {
        "schema": "9758187b19ad-distribution-probe-v2",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "schedule_period": period,
        "canonical_shortcuts": canonical_shortcuts,
        "schedule_cross": schedule_cross,
        "lesson_windows": lesson_windows,
        "ordinary_census": {
            "seed_count": seed_count,
            "draws": ordinary_draws,
            "unique_inputs": len(unique_hashes),
            "unique_fraction": len(unique_hashes) / ordinary_draws
            if ordinary_draws
            else 0,
            "source_sides": dict(sorted(source_sides.items())),
            "marker_counts": {str(k): v for k, v in sorted(marker_counts.items())},
            "grid_sizes": dict(sorted(grid_sizes.items())),
            "template_boxes": dict(sorted(template_boxes.items())),
            "template_cell_counts": {
                str(k): v for k, v in sorted(template_cell_counts.items())
            },
            "contains_color_one": dict(sorted(contains_color_one.items())),
            "unique_shapes_by_profile": {
                key: len(value) for key, value in sorted(shapes_by_profile.items())
            },
            "errors": errors,
        },
        "boundary_matrix": {
            "cases": boundary_cases,
            "errors": boundary_errors,
        },
        "exact_disagreement_cases": disagreement_cases,
        "failures": failures,
        "passed": not failures,
    }
    return result, not failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=80)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error("--seeds must be positive")
    result, passed = run_probe(args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "passed": passed,
                "schedule_period": result["schedule_period"],
                "rivals_checked": len(result["exact_disagreement_cases"]),
                "ordinary_draws": result["ordinary_census"]["draws"],
                "unique_inputs": result["ordinary_census"]["unique_inputs"],
                "boundary_cases": result["boundary_matrix"]["cases"],
                "failures": result["failures"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
