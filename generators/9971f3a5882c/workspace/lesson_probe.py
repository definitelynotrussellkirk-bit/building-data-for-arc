#!/usr/bin/env python3
"""Replay canonical-rival fit and consecutive 3-demo / 1-query rotations.

This is a finite source-bound probe for task 9971f3a5882c.  It discovers the
rivals from the generator's declarations rather than copying a name list, checks
that every claimed canonical shortcut really fits every canonical pair, and then
rotates each member of every four-example consecutive window into the query position.
The default 60 starts cover the joint canvas/lattice/marker profile period.
Sample indices never wrap: profile repetition does not make keyed RNG inputs
periodic, and production generation advances the actual sample index.
The authoritative Racket parity is checked separately by the standard battery and
lesson-census; this probe intentionally uses the generator's independent Python
mirror to make schedule mistakes cheap to diagnose.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Callable

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "9971f3a5882c"
HERE = Path(__file__).resolve()


def _load_generator():
    return load_selected_generator(TASK_ID, root=find_root(HERE))


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(payload).hexdigest()


def _declarations(gen) -> list[tuple[str, str, Callable[[Any], Any]]]:
    found: list[tuple[str, str, Callable[[Any], Any]]] = []
    for attr in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS"):
        mapping = getattr(gen, attr, None)
        if not isinstance(mapping, dict) or not mapping:
            raise RuntimeError(f"{attr} must be a nonempty mapping")
        for name, rival in sorted(mapping.items()):
            if not callable(rival):
                raise RuntimeError(f"{attr}[{name!r}] is not callable")
            found.append((attr, name, rival))
    return found


def _band_label(value: str | None) -> str:
    return "default" if value is None else value


def run_probe(*, seed: int, period: int | None = None) -> dict[str, Any]:
    gen, _, source_hash = _load_generator()
    # These are this task's three explicit, index-based profile schedules.
    # Their period describes profile choices, not the random pixel layouts.
    profile_period = math.lcm(
        len(gen.CANVAS_PROFILES), len(gen.LATTICE_PROFILES), len(gen.SCHEDULE_PROFILES)
    )
    if period is None:
        period = profile_period
    if type(period) is not int or period < 4:
        raise ValueError("period must be a Python int of at least 4")
    declarations = _declarations(gen)
    pairs = canonical_pairs(TASK_ID, root=find_root(HERE))

    canonical: dict[str, Any] = {}
    for owner, name, rival in declarations:
        key = f"{owner}:{name}"
        errors: list[str] = []
        fits = 0
        for pair in pairs:
            try:
                predicted = rival(copy.deepcopy(pair["input"]))
            except Exception as exc:  # report exact failure rather than hiding it
                errors.append(f"{pair['split']}[{pair['pair_index']}]: {type(exc).__name__}: {exc}")
                continue
            fits += int(predicted == pair["output"])
        canonical[key] = {
            "pairs": len(pairs),
            "fits": fits,
            "errors": errors,
            "status": "fits_all" if fits == len(pairs) and not errors else "does_not_fit_all",
        }

    bands: tuple[str | None, ...] = (None, "easy", "medium", "hard")
    train = int(gen.EXAMPLES_NEEDED)
    window = train + 1
    rotations: list[dict[str, Any]] = []
    unique_inputs: set[str] = set()
    failures: list[dict[str, Any]] = []

    for band in bands:
        for start in range(period):
            episode = []
            for offset in range(window):
                sample_index = start + offset
                grid = gen.generate(seed, sample_index, difficulty=band)
                unique_inputs.add(_grid_hash(grid))
                episode.append({
                    "sample_index": sample_index,
                    "input": grid,
                    "output": gen.solve_python(copy.deepcopy(grid)),
                    "profiles": gen.observe_overrides(grid),
                    "witnesses": {
                        name: bool(predicate(grid))
                        for name, predicate in sorted(gen.SEMANTIC_WITNESSES.items())
                    },
                })

            for query_position in range(window):
                query = episode[query_position]
                demos = [
                    {"input": pair["input"], "output": pair["output"]}
                    for index, pair in enumerate(episode)
                    if index != query_position
                ]
                query_pair = {"input": query["input"], "output": query["output"]}
                hook_reasons = list(gen.lesson_identifiable(demos, query_pair))
                rival_results: dict[str, Any] = {}
                for owner, name, rival in declarations:
                    key = f"{owner}:{name}"
                    mismatching_demo_positions: list[int] = []
                    for demo_position, pair in enumerate(demos):
                        predicted = rival(copy.deepcopy(pair["input"]))
                        if predicted != pair["output"]:
                            mismatching_demo_positions.append(demo_position)
                    rival_results[key] = {
                        "refuted": bool(mismatching_demo_positions),
                        "mismatching_demo_positions": mismatching_demo_positions,
                    }
                record = {
                    "band": _band_label(band),
                    "start": start,
                    "indices": [pair["sample_index"] for pair in episode],
                    "profiles": [pair["profiles"] for pair in episode],
                    "query_position": query_position,
                    "query_sample_index": query["sample_index"],
                    "demo_sample_indices": [
                        pair["sample_index"]
                        for index, pair in enumerate(episode)
                        if index != query_position
                    ],
                    "hook_reasons": hook_reasons,
                    "rivals": rival_results,
                    "demo_witness_coverage": {
                        name: sum(
                            int(pair["witnesses"][name])
                            for index, pair in enumerate(episode)
                            if index != query_position
                        )
                        for name in sorted(gen.SEMANTIC_WITNESSES)
                    },
                }
                rotations.append(record)
                bad_rivals = sorted(
                    name for name, result in rival_results.items() if not result["refuted"]
                )
                if hook_reasons or bad_rivals:
                    failures.append({
                        "band": record["band"],
                        "start": start,
                        "query_position": query_position,
                        "hook_reasons": hook_reasons,
                        "surviving_rivals": bad_rivals,
                    })

    return {
        "schema": "9971f3a5882c-consecutive-lesson-probe-v2",
        "task_id": TASK_ID,
        "generator_sha256": source_hash,
        "rule_hash": gen.RULE_HASH,
        "probe_sha256": hashlib.sha256(HERE.read_bytes()).hexdigest(),
        "seed": seed,
        "period": period,
        "profile_schedule_period": profile_period,
        "coverage_status": (
            "complete_profile_period_at_fixed_seed" if period >= profile_period
            else "partial_profile_period_at_fixed_seed"
        ),
        "sample_index_policy": "consecutive_unwrapped",
        "bands": [_band_label(band) for band in bands],
        "train_examples": train,
        "query_rotations_per_window": window,
        "canonical_pairs": len(pairs),
        "canonical_rival_fit": canonical,
        "declared_rivals": [f"{owner}:{name}" for owner, name, _ in declarations],
        "rotations_checked": len(rotations),
        "unique_input_hashes": len(unique_inputs),
        "failures": failures,
        "status": "PASS" if not failures and all(
            item["status"] == "fits_all" for item in canonical.values()
        ) else "FAIL",
        "rotations": rotations,
        "limits": [
            "Finite checks of declared rivals are not proof of universal identifiability.",
            "Generated outputs use solve_python; the standard battery and lesson-census bind Racket authority.",
            "Exact-grid hashes count syntactic uniqueness, not semantic equivalence.",
            "Profile coverage is for the listed fixed-seed starts, not all seeds or input grids.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=7331)
    parser.add_argument("--period", type=int, default=None,
                        help="number of consecutive starts (default: joint profile period)")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.period is not None and args.period < 4:
        parser.error("--period must be at least 4")
    report = run_probe(seed=args.seed, period=args.period)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "generator_sha256": report["generator_sha256"],
        "canonical_pairs": report["canonical_pairs"],
        "rotations_checked": report["rotations_checked"],
        "unique_input_hashes": report["unique_input_hashes"],
        "coverage_status": report["coverage_status"],
        "failures": len(report["failures"]),
        "out": str(args.out),
    }, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
