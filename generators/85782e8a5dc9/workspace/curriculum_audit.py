#!/usr/bin/env python3
"""Reproducible curriculum audit for the framed transform-transfer generator.

This task-local tool complements the shared battery by exhaustively rotating
through bounded schedule starts and reporting which declared rival rules survive
whole lessons.  It also checks whether a shortcut that fits every canonical pair
receives a generated counterexample.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from types import ModuleType
from typing import Iterable, Sequence

from reviewer_support import canonical_pairs, find_root

TASK_DIR = Path(__file__).resolve().parents[1]
GENERATOR_PATH = TASK_DIR / "generator.py"


def _load_generator(path: Path = GENERATOR_PATH) -> ModuleType:
    spec = importlib.util.spec_from_file_location("curriculum_audit_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _freeze_grid(grid) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(value) for value in row) for row in grid)


def _signature(grid) -> str:
    height = len(grid)
    width = len(grid[0]) if height else 0
    palette = len({value for row in grid for value in row})
    return f"{height}x{width}/p{palette}"


def audit_curriculum(
    generator: ModuleType,
    *,
    seeds: Iterable[int],
    starts: Iterable[int],
    bands: Sequence[str] = ("easy", "medium", "hard"),
) -> dict:
    seed_values = tuple(int(value) for value in seeds)
    start_values = tuple(int(value) for value in starts)
    band_values = tuple(str(value) for value in bands)
    failures: list[dict] = []
    profile_counts: Counter[str] = Counter()
    transform_counts: Counter[str] = Counter()
    signature_counts: Counter[str] = Counter()
    surviving_rivals: Counter[str] = Counter()
    surviving_rotated_rivals: Counter[str] = Counter()
    counterexamples: Counter[str] = Counter()
    unique_inputs: set[tuple[tuple[int, ...], ...]] = set()
    lesson_count = 0
    rotation_count = 0
    pair_count = 0

    for band in band_values:
        for seed in seed_values:
            for start in start_values:
                demos: list[dict] = []
                lesson_pairs: list[dict] = []
                for offset in range(generator.EXAMPLES_NEEDED + 1):
                    sample_index = start + offset
                    try:
                        input_grid = generator.generate(
                            seed, sample_index, difficulty=band
                        )
                        diagnostics = generator.self_check(
                            input_grid, difficulty=band
                        )
                        if diagnostics:
                            failures.append(
                                {
                                    "kind": "self_check",
                                    "band": band,
                                    "seed": seed,
                                    "start": start,
                                    "sample_index": sample_index,
                                    "diagnostics": diagnostics,
                                }
                            )
                        output_grid = generator.rule_mirror(input_grid)
                        analysis = generator.analyze_grid(input_grid)
                        profile = generator.observe_overrides(input_grid).get(
                            "scene_profile"
                        )
                    except Exception as exc:  # fail-loud diagnostic tool
                        failures.append(
                            {
                                "kind": "generation_or_analysis_exception",
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "sample_index": sample_index,
                                "exception": f"{type(exc).__name__}: {exc}",
                            }
                        )
                        lesson_pairs = []
                        break

                    pair = {"input": input_grid, "output": output_grid}
                    lesson_pairs.append(pair)
                    if offset < generator.EXAMPLES_NEEDED:
                        demos.append(pair)
                    pair_count += 1
                    unique_inputs.add(_freeze_grid(input_grid))
                    if profile is not None:
                        profile_counts[str(profile)] += 1
                    if analysis.get("transform") is not None:
                        transform_counts[str(analysis["transform"])] += 1
                    signature_counts[_signature(input_grid)] += 1
                    for name, shortcut in generator.CANONICAL_SHORTCUTS.items():
                        if shortcut(input_grid) != output_grid:
                            counterexamples[str(name)] += 1

                if len(lesson_pairs) != generator.EXAMPLES_NEEDED + 1:
                    continue
                query = lesson_pairs[-1]
                lesson_count += 1
                reasons = generator.lesson_identifiable(demos, query)
                if reasons:
                    failures.append(
                        {
                            "kind": "lesson_not_identifiable",
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "reasons": reasons,
                        }
                    )
                for name, competitor in generator.LESSON_COMPETITORS.items():
                    if all(
                        competitor(pair["input"]) == pair["output"]
                        for pair in demos
                    ):
                        surviving_rivals[str(name)] += 1

                # The production bundle contains EXAMPLES_NEEDED demos plus one
                # query.  Hold out each labelled pair once so the audit catches
                # schedules whose identifiability depends on a fixed query slot.
                for query_index, rotated_query in enumerate(lesson_pairs):
                    rotated_demos = [
                        pair
                        for pair_index, pair in enumerate(lesson_pairs)
                        if pair_index != query_index
                    ]
                    rotation_count += 1
                    rotated_reasons = generator.lesson_identifiable(
                        rotated_demos, rotated_query
                    )
                    if rotated_reasons:
                        failures.append(
                            {
                                "kind": "rotated_lesson_not_identifiable",
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "query_index": query_index,
                                "reasons": rotated_reasons,
                            }
                        )
                    for name, competitor in generator.LESSON_COMPETITORS.items():
                        if all(
                            competitor(pair["input"]) == pair["output"]
                            for pair in rotated_demos
                        ):
                            surviving_rotated_rivals[str(name)] += 1

    canonical = canonical_pairs(
        generator.TASK_ID,
        root=find_root(__file__),
    )
    canonical_shortcuts_that_fit_all: list[str] = []
    for name, shortcut in generator.CANONICAL_SHORTCUTS.items():
        if canonical and all(
            shortcut(pair["input"]) == pair["output"] for pair in canonical
        ):
            canonical_shortcuts_that_fit_all.append(str(name))
            if counterexamples[str(name)] == 0:
                failures.append(
                    {
                        "kind": "canonical_shortcut_without_generated_counterexample",
                        "shortcut": str(name),
                    }
                )

    expected_profiles = set(map(str, generator.SCENE_PROFILES))
    missing_profiles = sorted(expected_profiles - set(profile_counts))
    if missing_profiles:
        failures.append(
            {"kind": "missing_profiles", "profiles": missing_profiles}
        )
    for name, count in sorted(surviving_rivals.items()):
        failures.append(
            {
                "kind": "surviving_lesson_rival",
                "rival": name,
                "lesson_count": count,
            }
        )
    for name, count in sorted(surviving_rotated_rivals.items()):
        failures.append(
            {
                "kind": "surviving_rotated_lesson_rival",
                "rival": name,
                "rotation_count": count,
            }
        )

    generator_bytes = Path(generator.__file__).read_bytes()
    return {
        "schema": "framed-transform-curriculum-audit-v1",
        "task_id": str(generator.TASK_ID),
        "generator_sha256": hashlib.sha256(generator_bytes).hexdigest(),
        "parameters": {
            "seeds": list(seed_values),
            "starts": list(start_values),
            "bands": list(band_values),
            "examples_needed": int(generator.EXAMPLES_NEEDED),
        },
        "status": "pass" if not failures else "fail",
        "lesson_count": lesson_count,
        "rotation_count": rotation_count,
        "pair_count": pair_count,
        "unique_input_count": len(unique_inputs),
        "profiles_seen": dict(sorted(profile_counts.items())),
        "transforms_seen": dict(sorted(transform_counts.items())),
        "signatures_seen": dict(sorted(signature_counts.items())),
        "surviving_lesson_rivals": dict(sorted(surviving_rivals.items())),
        "surviving_rotated_lesson_rivals": dict(
            sorted(surviving_rotated_rivals.items())
        ),
        "canonical_shortcuts_that_fit_all": sorted(
            canonical_shortcuts_that_fit_all
        ),
        "generated_counterexamples_by_shortcut": {
            name: int(counterexamples[name])
            for name in sorted(generator.CANONICAL_SHORTCUTS)
        },
        "failures": failures,
        "limits": (
            "Finite declared-rival census only; it does not prove unique induction "
            "against every possible solver."
        ),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=16)
    parser.add_argument("--starts", type=int, default=8)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--require-clean", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.seeds <= 0 or args.starts <= 0:
        raise SystemExit("--seeds and --starts must be positive")
    if args.out.exists():
        raise SystemExit(f"refusing to overwrite existing output: {args.out}")
    generator = _load_generator()
    report = audit_curriculum(
        generator,
        seeds=range(args.seeds),
        starts=range(args.starts),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(
        f"{report['status'].upper()}: {report['lesson_count']} lessons, "
        f"{report['unique_input_count']} unique inputs, "
        f"{len(report['failures'])} failures"
    )
    if args.require_clean and report["status"] != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
