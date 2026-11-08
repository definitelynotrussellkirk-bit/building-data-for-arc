#!/usr/bin/env python3
"""Independent qualification runner for generator 8f221c2b552e.

The report complements the repository battery with two checks that are useful
when future agents revise the curriculum:

* pixel-level recovery of every advertised axis without production helpers;
* every query rotation of short cyclic lessons, so a semantic witness cannot
  hide only in the held-out query.

The selected Racket program is used for parity unless ``--skip-racket`` is
explicitly requested.  There is no Python fallback for that parity result.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
from typing import Any

from reference_probe import (
    analyze,
    bridge_rows,
    canonical_pairs,
    cyclic_lesson_rotations,
    load_generator,
    profile,
    racket_outputs,
)

BANDS = ("easy", "medium", "hard")
OVERRIDE_CASES = (
    {
        "grid_h": 6,
        "grid_w": 8,
        "n_pairs": 2,
        "color_mode": "distinct",
        "distractor_count": 0,
        "span_style": "short",
    },
    {
        "grid_h": 10,
        "grid_w": 14,
        "n_pairs": 5,
        "color_mode": "shared",
        "distractor_count": 3,
        "span_style": "long",
    },
    {
        "grid_h": 6,
        "grid_w": 8,
        "n_pairs": 5,
        "color_mode": "distinct",
        "distractor_count": 3,
        "span_style": "mixed",
    },
)


def _jsonable_axis_values(values: dict[str, set[Any]]) -> dict[str, list[Any]]:
    return {name: sorted(items, key=lambda item: (str(type(item)), str(item))) for name, items in values.items()}


def _failure(kind: str, **details: Any) -> dict[str, Any]:
    return {"kind": kind, **details}


def qualify(
    *,
    generator_path: str | None = None,
    samples_per_band: int = 60,
    starts_per_band: int = 60,
    racket_samples: int = 24,
    skip_racket: bool = False,
) -> dict[str, Any]:
    if samples_per_band < 1:
        raise ValueError("samples_per_band must be positive")
    if starts_per_band < 1:
        raise ValueError("starts_per_band must be positive")
    if racket_samples < 0:
        raise ValueError("racket_samples cannot be negative")

    module = load_generator(generator_path)
    source = Path(module.__file__).resolve()
    source_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    failures: list[dict[str, Any]] = []

    canon = canonical_pairs()
    canonical_failures: list[dict[str, Any]] = []
    canonical_profiles = {profile(pair["input"]) for pair in canon}
    for index, pair in enumerate(canon):
        errors = module.self_check(pair["input"])
        strict_errors = module.strict_canonical_like(pair["input"])
        independent = bridge_rows(pair["input"])
        if errors or strict_errors or independent != pair["output"]:
            canonical_failures.append(
                _failure(
                    "canonical_pair",
                    pair_index=index,
                    self_check=errors,
                    strict=strict_errors,
                    independent_match=independent == pair["output"],
                )
            )
    rival_fit = {}
    for name, rival in module.CANONICAL_SHORTCUTS.items():
        rival_fit[name] = sum(rival(pair["input"]) == pair["output"] for pair in canon)
        if rival_fit[name] != len(canon):
            canonical_failures.append(
                _failure(
                    "declared_rival_does_not_fit_canonical",
                    rival=name,
                    fits=rival_fit[name],
                    total=len(canon),
                )
            )
    failures.extend(canonical_failures)

    generated_failures: list[dict[str, Any]] = []
    generated_grids: list[list[list[int]]] = []
    generated_by_band: dict[str, dict[str, Any]] = {}
    for band_index, band in enumerate(BANDS):
        seen: set[str] = set()
        exact_profiles = 0
        axis_values: dict[str, set[Any]] = defaultdict(set)
        profile_residues: set[int] = set()
        for index in range(samples_per_band):
            seed = 120_000 + band_index * 10_000 + index
            try:
                grid = module.generate(seed, index, difficulty=band)
                repeat = module.generate(seed, index, difficulty=band)
                observed = analyze(grid)
                production_observed = module.observe_overrides(grid)
            except Exception as exc:  # report every malformed draw; do not mask it
                generated_failures.append(
                    _failure("generation_exception", band=band, index=index, error=repr(exc))
                )
                continue
            generated_grids.append(grid)
            seen.add(json.dumps(grid, separators=(",", ":")))
            exact_profiles += profile(grid) in canonical_profiles
            profile_residues.add(index % len(module.SCHEDULE_PROFILES))
            for name, value in observed.items():
                axis_values[name].add(value)

            errors = module.self_check(grid)
            independent = bridge_rows(grid)
            if grid != repeat:
                generated_failures.append(_failure("nondeterministic", band=band, index=index))
            if errors:
                generated_failures.append(
                    _failure("self_check", band=band, index=index, errors=errors)
                )
            if production_observed != observed:
                generated_failures.append(
                    _failure(
                        "axis_observation_mismatch",
                        band=band,
                        index=index,
                        independent=observed,
                        production=production_observed,
                    )
                )
            if module.rule_mirror(grid) != independent:
                generated_failures.append(
                    _failure("python_mirror_mismatch", band=band, index=index)
                )
            if independent == grid:
                generated_failures.append(
                    _failure("identity_example", band=band, index=index)
                )

        generated_by_band[band] = {
            "draws": samples_per_band,
            "unique_inputs": len(seen),
            "canonical_profile_matches": exact_profiles,
            "schedule_residues": sorted(profile_residues),
            "axis_values": _jsonable_axis_values(axis_values),
        }
    failures.extend(generated_failures)

    override_failures: list[dict[str, Any]] = []
    override_total = 0
    for band_index, band in enumerate(BANDS):
        for case_index, requested in enumerate(OVERRIDE_CASES):
            override_total += 1
            try:
                grid = module.generate(
                    220_000 + band_index * 100 + case_index,
                    37 + case_index,
                    difficulty=band,
                    **requested,
                )
                independent = analyze(grid)
                production = module.observe_overrides(grid)
            except Exception as exc:
                override_failures.append(
                    _failure(
                        "override_exception",
                        band=band,
                        requested=requested,
                        error=repr(exc),
                    )
                )
                continue
            if independent != requested or production != requested:
                override_failures.append(
                    _failure(
                        "override_round_trip",
                        band=band,
                        requested=requested,
                        independent=independent,
                        production=production,
                    )
                )
    failures.extend(override_failures)

    rotation_failures: list[dict[str, Any]] = []
    rotation_total = 0
    positions: set[int] = set()
    for band_index, band in enumerate(BANDS):
        for case in cyclic_lesson_rotations(
            module,
            seed=320_000 + band_index * 10_000,
            band=band,
            starts=starts_per_band,
            window_size=4,
        ):
            rotation_total += 1
            positions.add(case["query_index"])
            reasons = module.lesson_identifiable(case["demos"], case["query"])
            if reasons:
                rotation_failures.append(
                    _failure(
                        "lesson_not_identifiable",
                        band=band,
                        start=case["start"],
                        query_index=case["query_index"],
                        reasons=reasons,
                    )
                )
            for name, rival in module.LESSON_COMPETITORS.items():
                if all(rival(pair["input"]) == pair["output"] for pair in case["demos"]):
                    rotation_failures.append(
                        _failure(
                            "rival_survives_demo_rotation",
                            band=band,
                            start=case["start"],
                            query_index=case["query_index"],
                            rival=name,
                        )
                    )
    failures.extend(rotation_failures)

    if skip_racket:
        racket_report: dict[str, Any] = {
            "status": "skipped",
            "reason": "explicit --skip-racket",
            "checked": 0,
            "failures": [],
        }
    else:
        selected = [pair["input"] for pair in canon]
        selected.extend(generated_grids[:racket_samples])
        try:
            actual = racket_outputs(selected)
            expected = [bridge_rows(grid) for grid in selected]
            parity_failures = [index for index, (left, right) in enumerate(zip(actual, expected)) if left != right]
            racket_report = {
                "status": "pass" if not parity_failures else "fail",
                "checked": len(selected),
                "failures": parity_failures,
            }
            if parity_failures:
                failures.append(_failure("racket_parity", indexes=parity_failures))
        except Exception as exc:
            racket_report = {
                "status": "error",
                "checked": 0,
                "failures": [repr(exc)],
            }
            failures.append(_failure("racket_parity_error", error=repr(exc)))

    report = {
        "task_id": module.TASK_ID,
        "generator_source": str(source),
        "generator_sha256": source_sha256,
        "status": "pass" if not failures else "fail",
        "parameters": {
            "samples_per_band": samples_per_band,
            "starts_per_band": starts_per_band,
            "racket_samples": racket_samples,
            "skip_racket": skip_racket,
        },
        "canonical": {
            "total": len(canon),
            "failures": canonical_failures,
            "declared_rival_fit": rival_fit,
        },
        "generated": {
            "total": samples_per_band * len(BANDS),
            "bands": generated_by_band,
            "failures": generated_failures,
        },
        "exact_overrides": {
            "total": override_total,
            "failures": override_failures,
        },
        "cyclic_query_rotations": {
            "total": rotation_total,
            "query_positions": sorted(positions),
            "failures": rotation_failures,
        },
        "racket_parity": racket_report,
        "failures": failures,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", help="source path; defaults to GENERATOR_UNDER_TEST/current task")
    parser.add_argument("--samples-per-band", type=int, default=60)
    parser.add_argument("--starts-per-band", type=int, default=60)
    parser.add_argument("--racket-samples", type=int, default=24)
    parser.add_argument("--skip-racket", action="store_true")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    report = qualify(
        generator_path=args.generator,
        samples_per_band=args.samples_per_band,
        starts_per_band=args.starts_per_band,
        racket_samples=args.racket_samples,
        skip_racket=args.skip_racket,
    )
    destination = Path(args.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "status": report["status"],
                "generator_sha256": report["generator_sha256"],
                "generated": report["generated"]["total"],
                "cyclic_query_rotations": report["cyclic_query_rotations"]["total"],
                "racket_parity": report["racket_parity"]["status"],
                "out": str(destination),
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
