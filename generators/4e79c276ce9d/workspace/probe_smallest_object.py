#!/usr/bin/env python3
"""Source-bound curriculum probe for ARC task 4e79c276ce9d.

The probe deliberately reads the selected generator's live declarations rather
than maintaining a second rival-name list.  It checks exact canonical-profile
coverage, all legal joint dimension overrides, canonical shortcut fit, rich
witness behavior, every start of the declared cyclic lesson schedule, and every
held-out query position.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "4e79c276ce9d"
BANDS = ("easy", "medium", "hard")


def _load_generator(root: Path):
    path = root / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _axis_values(spec: dict[str, Any]) -> list[int]:
    text = str(spec.get("valid", ""))
    try:
        low_text, high_text = text.split("..", 1)
        low, high = int(low_text), int(high_text)
    except Exception as exc:  # pragma: no cover - defensive CLI diagnosis
        raise ValueError(f"cannot parse exact integer axis domain {text!r}") from exc
    return list(range(low, high + 1))


def run_probe(*, seed: int = 441, samples_per_band: int = 100) -> dict[str, Any]:
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    if type(samples_per_band) is not int or samples_per_band < 1:
        raise ValueError("samples_per_band must be a positive literal integer")

    root = find_root(__file__)
    generator, generator_path = _load_generator(root)
    source_sha = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    pairs = canonical_pairs(TASK_ID, root=root)
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]), len({v for row in pair["input"] for v in row}))
        for pair in pairs
    }

    shortcut_failures: list[dict[str, Any]] = []
    for name, rival in generator.CANONICAL_SHORTCUTS.items():
        for pair_index, pair in enumerate(pairs):
            if rival(pair["input"]) != pair["output"]:
                shortcut_failures.append({"rival": name, "pair_index": pair_index})

    profile_violations: list[dict[str, Any]] = []
    witness_failures: list[dict[str, Any]] = []
    default_hashes: set[str] = set()
    profile_counts: dict[str, int] = {}
    witness_draw_count = 0
    for band in BANDS:
        for sample_index in range(samples_per_band):
            grid = generator.generate(seed, sample_index, difficulty=band)
            default_hashes.add(_grid_hash(grid))
            profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
            profile_key = "x".join(map(str, profile))
            profile_counts[profile_key] = profile_counts.get(profile_key, 0) + 1
            if profile not in canonical_profiles:
                profile_violations.append({
                    "band": band,
                    "sample_index": sample_index,
                    "profile": list(profile),
                })
            if generator.schedule_profile(seed, sample_index, band) != "canonical":
                witness_draw_count += 1
                expected = generator.rule_mirror(grid)
                for name, rival in generator.LESSON_COMPETITORS.items():
                    if rival(grid) == expected:
                        witness_failures.append({
                            "band": band,
                            "sample_index": sample_index,
                            "rival": name,
                            "input_sha256": _grid_hash(grid),
                        })

    override_failures: list[dict[str, Any]] = []
    combination_count = 0
    for band in BANDS:
        for grid_h in _axis_values(generator.AXES["grid_h"]):
            for grid_w in _axis_values(generator.AXES["grid_w"]):
                combination_count += 1
                sample_index = 100_000 + grid_h * 100 + grid_w
                try:
                    grid = generator.generate(
                        seed,
                        sample_index,
                        difficulty=band,
                        grid_h=grid_h,
                        grid_w=grid_w,
                    )
                except Exception as exc:
                    override_failures.append({
                        "band": band,
                        "grid_h": grid_h,
                        "grid_w": grid_w,
                        "error": f"{type(exc).__name__}: {exc}",
                    })
                    continue
                observed = generator.observe_overrides(grid)
                findings = generator.self_check(
                    grid,
                    meta={"overrides": {"grid_h": grid_h, "grid_w": grid_w}},
                )
                if observed != {"grid_h": grid_h, "grid_w": grid_w} or findings:
                    override_failures.append({
                        "band": band,
                        "grid_h": grid_h,
                        "grid_w": grid_w,
                        "observed": observed,
                        "findings": findings,
                    })

    schedule_failures: list[dict[str, Any]] = []
    start_count = 0
    rotation_count = 0
    for band in BANDS:
        for start in range(generator.LESSON_SCHEDULE_PERIOD):
            start_count += 1
            lesson = []
            for offset in range(generator.EXAMPLES_NEEDED + 1):
                grid = generator.generate(seed, start + offset, difficulty=band)
                lesson.append({"input": grid, "output": generator.rule_mirror(grid)})
            for query_index, query in enumerate(lesson):
                rotation_count += 1
                demos = [pair for index, pair in enumerate(lesson) if index != query_index]
                findings = generator.lesson_identifiable(demos, query)
                surviving = [
                    name
                    for name, rival in generator.LESSON_COMPETITORS.items()
                    if all(rival(pair["input"]) == pair["output"] for pair in demos)
                ]
                if findings or surviving:
                    schedule_failures.append({
                        "band": band,
                        "start": start,
                        "query_index": query_index,
                        "findings": findings,
                        "surviving_rivals": surviving,
                    })

    passed = not any((
        shortcut_failures,
        profile_violations,
        witness_failures,
        override_failures,
        schedule_failures,
    ))
    return {
        "schema": "arc-smallest-object-probe-v1",
        "task_id": TASK_ID,
        "generator_version": generator.VERSION,
        "generator_sha256": source_sha,
        "rule_hash": generator.RULE_HASH,
        "seed": seed,
        "samples_per_band": samples_per_band,
        "bands": list(BANDS),
        "declared_rivals": list(generator.LESSON_COMPETITORS),
        "declared_canonical_shortcuts": list(generator.CANONICAL_SHORTCUTS),
        "canonical": {
            "pair_count": len(pairs),
            "profiles": [list(profile) for profile in sorted(canonical_profiles)],
            "shortcut_failures": shortcut_failures,
        },
        "defaults": {
            "draw_count": len(BANDS) * samples_per_band,
            "unique_input_count": len(default_hashes),
            "profile_counts": profile_counts,
            "profile_violations": profile_violations,
            "witness_draw_count": witness_draw_count,
            "witness_failures": witness_failures,
        },
        "overrides": {
            "combination_count": combination_count,
            "failures": override_failures,
        },
        "schedule": {
            "demonstration_count": generator.EXAMPLES_NEEDED,
            "period": generator.LESSON_SCHEDULE_PERIOD,
            "start_count": start_count,
            "rotation_count": rotation_count,
            "failures": schedule_failures,
        },
        "passed": passed,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=441)
    parser.add_argument("--samples-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = run_probe(seed=args.seed, samples_per_band=args.samples_per_band)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(rendered, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
        print(args.out)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
