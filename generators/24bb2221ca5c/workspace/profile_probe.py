#!/usr/bin/env python3
"""Reproducible curriculum probe for generator 24bb2221ca5c.

This is deliberately task-local: it exercises the generator's public semantic
hooks, records exact witness grids, and fails when a three-example lesson window
no longer eliminates a declared rival rule.  It gives future reviewers a fast,
human-readable check before running the full Racket-backed battery.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


TASK_HOME = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
RUNTIME = REPO / "shared/runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load_generator():
    path = TASK_HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("profile_probe_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pair(gen, grid: list[list[int]]) -> dict[str, Any]:
    return {"input": grid, "output": gen.rule_mirror(grid)}


def collect_report(
    *,
    seed_count: int = 4,
    window_count: int = 4,
    seed_base: int = 2400,
    difficulties: tuple[str, ...] = ("easy", "medium", "hard"),
) -> dict[str, Any]:
    if seed_count < 1:
        raise ValueError("seed_count must be positive")
    if window_count < 1:
        raise ValueError("window_count must be positive")

    gen = _load_generator()
    failures: list[dict[str, Any]] = []
    profiles_seen: set[str] = set()
    witnesses_seen: set[str] = set()
    rivals_refuted: set[str] = set()
    witness_examples: dict[str, dict[str, Any]] = {}
    rival_examples: dict[str, dict[str, Any]] = {}
    dimension_counts: dict[str, int] = {}
    observed_axis_counts: dict[str, int] = {}
    topology_counts: dict[str, Any] = {
        "scenes_with_multiple_holes": 0,
        "scenes_with_reused_color": 0,
        "scenes_with_corner_gap": 0,
        "scenes_with_nonrectangular_hole": 0,
        "components_by_hole_count": {},
    }
    windows: list[dict[str, Any]] = []

    for difficulty in difficulties:
        for seed_offset in range(seed_count):
            seed = seed_base + seed_offset
            for window_index in range(window_count):
                start = window_index * gen.EXAMPLES_NEEDED
                grids: list[list[list[int]]] = []
                window_profiles: set[str] = set()
                window_witnesses: set[str] = set()
                window_rivals: set[str] = set()

                for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                    try:
                        grid = gen.generate(seed, sample_index, difficulty=difficulty)
                    except Exception as exc:  # evidence tool: preserve the exact failure
                        failures.append(
                            {
                                "kind": "generation_error",
                                "difficulty": difficulty,
                                "seed": seed,
                                "sample_index": sample_index,
                                "message": f"{type(exc).__name__}: {exc}",
                            }
                        )
                        continue

                    grids.append(grid)
                    profile = gen.schedule_profile(seed, sample_index, difficulty)
                    profiles_seen.add(profile)
                    window_profiles.add(profile)
                    dimension_key = f"{len(grid)}x{len(grid[0])}"
                    dimension_counts[dimension_key] = dimension_counts.get(dimension_key, 0) + 1

                    errors = gen.self_check(grid, difficulty=difficulty)
                    if errors:
                        failures.append(
                            {
                                "kind": "self_check",
                                "difficulty": difficulty,
                                "seed": seed,
                                "sample_index": sample_index,
                                "errors": errors,
                            }
                        )
                        continue

                    observed = gen.observe_overrides(grid)
                    observed_key = json.dumps(observed, sort_keys=True, separators=(",", ":"))
                    observed_axis_counts[observed_key] = observed_axis_counts.get(observed_key, 0) + 1
                    components = gen._component_cells(grid)
                    component_colors = [color for color, _ in components]
                    component_kinds = [
                        gen._classify_component(cells) for _color, cells in components
                    ]
                    hole_regions = [
                        gen._component_hole_regions(cells)
                        for _color, cells in components
                    ]
                    hole_counts = [len(regions) for regions in hole_regions]
                    if len(set(component_colors)) < len(component_colors):
                        topology_counts["scenes_with_reused_color"] += 1
                    if any(count > 1 for count in hole_counts):
                        topology_counts["scenes_with_multiple_holes"] += 1
                    if "closed_corner_gap" in component_kinds:
                        topology_counts["scenes_with_corner_gap"] += 1
                    if any(
                        not gen._is_rectangular_region(region)
                        for regions in hole_regions
                        for region in regions
                    ):
                        topology_counts["scenes_with_nonrectangular_hole"] += 1
                    for count in hole_counts:
                        key = str(count)
                        by_holes = topology_counts["components_by_hole_count"]
                        by_holes[key] = by_holes.get(key, 0) + 1
                    truth = gen.rule_mirror(grid)

                    for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
                        if not witness(grid):
                            continue
                        witnesses_seen.add(witness_name)
                        window_witnesses.add(witness_name)
                        witness_examples.setdefault(
                            witness_name,
                            {
                                "difficulty": difficulty,
                                "seed": seed,
                                "sample_index": sample_index,
                                "profile": profile,
                                "input": grid,
                                "output": truth,
                            },
                        )

                    for rival_name, rival in gen.SEMANTIC_RIVALS.items():
                        rival_output = rival(grid)
                        if rival_output == truth:
                            continue
                        rivals_refuted.add(rival_name)
                        window_rivals.add(rival_name)
                        rival_examples.setdefault(
                            rival_name,
                            {
                                "difficulty": difficulty,
                                "seed": seed,
                                "sample_index": sample_index,
                                "profile": profile,
                                "input": grid,
                                "intended_output": truth,
                                "rival_output": rival_output,
                            },
                        )

                expected_profiles = set(gen.SCHEDULE_PROFILES)
                if window_profiles != expected_profiles:
                    failures.append(
                        {
                            "kind": "profile_window",
                            "difficulty": difficulty,
                            "seed": seed,
                            "start": start,
                            "expected": sorted(expected_profiles),
                            "actual": sorted(window_profiles),
                        }
                    )

                if len(grids) == gen.EXAMPLES_NEEDED:
                    demos = [_pair(gen, grid) for grid in grids]
                    query_index = start + gen.EXAMPLES_NEEDED
                    query_grid = gen.generate(seed, query_index, difficulty=difficulty)
                    lesson_reasons = gen.lesson_identifiable(demos, _pair(gen, query_grid))
                    if lesson_reasons:
                        failures.append(
                            {
                                "kind": "lesson_identifiability",
                                "difficulty": difficulty,
                                "seed": seed,
                                "start": start,
                                "reasons": lesson_reasons,
                            }
                        )

                for witness_name, required_rivals in gen.WITNESS_RIVALS.items():
                    if witness_name not in window_witnesses:
                        failures.append(
                            {
                                "kind": "missing_witness",
                                "difficulty": difficulty,
                                "seed": seed,
                                "start": start,
                                "witness": witness_name,
                            }
                        )
                    for rival_name in required_rivals:
                        if rival_name not in window_rivals:
                            failures.append(
                                {
                                    "kind": "surviving_rival",
                                    "difficulty": difficulty,
                                    "seed": seed,
                                    "start": start,
                                    "witness": witness_name,
                                    "rival": rival_name,
                                }
                            )

                windows.append(
                    {
                        "difficulty": difficulty,
                        "seed": seed,
                        "start": start,
                        "profiles": sorted(window_profiles),
                        "witnesses": sorted(window_witnesses),
                        "rivals_refuted": sorted(window_rivals),
                    }
                )

    report = {
        "schema": "arc-generator-profile-probe-v1",
        "task_id": gen.TASK_ID,
        "generator_version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "parameters": {
            "seed_count": seed_count,
            "window_count": window_count,
            "seed_base": seed_base,
            "difficulties": list(difficulties),
        },
        "summary": {
            "windows_checked": len(windows),
            "samples_checked": len(windows) * gen.EXAMPLES_NEEDED,
            "failures": len(failures),
            "profiles_seen": sorted(profiles_seen),
            "witnesses_seen": sorted(witnesses_seen),
            "rivals_refuted": sorted(rivals_refuted),
            "dimension_counts": dict(sorted(dimension_counts.items())),
            "observed_axis_counts": dict(sorted(observed_axis_counts.items())),
            "topology_counts": {
                **topology_counts,
                "components_by_hole_count": dict(
                    sorted(
                        topology_counts["components_by_hole_count"].items(),
                        key=lambda item: int(item[0]),
                    )
                ),
            },
        },
        "failures": failures,
        "witness_examples": witness_examples,
        "rival_examples": rival_examples,
        "windows": windows,
    }
    return report


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=4, help="number of consecutive seeds")
    parser.add_argument("--windows", type=int, default=4, help="lesson windows per seed/band")
    parser.add_argument("--seed-base", type=int, default=2400)
    parser.add_argument("--output", type=Path, help="write JSON here instead of stdout")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        report = collect_report(
            seed_count=args.seeds,
            window_count=args.windows,
            seed_base=args.seed_base,
        )
    except (ValueError, RuntimeError) as exc:
        print(f"profile probe error: {exc}", file=sys.stderr)
        return 2

    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(
            f"wrote {args.output}: {report['summary']['samples_checked']} samples, "
            f"{report['summary']['failures']} failures"
        )
    else:
        sys.stdout.write(text)
    return 0 if report["summary"]["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
