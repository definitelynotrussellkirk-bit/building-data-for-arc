#!/usr/bin/env python3
"""Bounded review of actual consecutive windows, without editing the generator."""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from math import lcm
from pathlib import Path

from reviewer_support import find_root, load_selected_generator


def signature(profiles):
    return tuple(profiles[key] for key in (
        "canvas_profile", "lattice_profile", "marker_profile"
    ))


def run():
    gen, source, source_sha256 = load_selected_generator(
        "9971f3a5882c", root=find_root(__file__)
    )
    period_components = {
        "canvas": len(gen.CANVAS_PROFILES),
        "lattice": len(gen.LATTICE_PROFILES),
        "marker": len(gen._MARKER_SCHEDULE),
    }
    period = lcm(*period_components.values())
    assert period == 60, period
    seed = 7331
    window = gen.EXAMPLES_NEEDED + 1
    declarations = {
        f"{attr}:{name}": rival
        for attr in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS")
        for name, rival in getattr(gen, attr).items()
    }
    bands = {}
    failures = []
    rotation_count = 0
    boundary_examples = []
    for band in (None, "easy", "medium", "hard"):
        label = band or "default"
        samples = []
        for index in range(period + window - 1):
            grid = gen.generate(seed, index, difficulty=band)
            output = gen.solve_python(deepcopy(grid))
            samples.append({
                "sample_index": index,
                "input": grid,
                "output": output,
                "profiles": gen.observe_overrides(grid),
                "refutes": {
                    name: rival(deepcopy(grid)) != output
                    for name, rival in declarations.items()
                },
            })
        profile_signatures = [signature(row["profiles"]) for row in samples]
        observed_cycle = next(
            candidate for candidate in range(1, period + 1)
            if all(profile_signatures[i] == profile_signatures[(i + candidate) % period]
                   for i in range(period))
        )
        full_profiles = set(profile_signatures[:period])
        legacy_profiles = set(profile_signatures[:12])
        bands[label] = {
            "materialized_indices": [0, period + window - 2],
            "observed_profile_cycle_over_60_phases": observed_cycle,
            "legacy_12_unique_profile_tuples": len(legacy_profiles),
            "full_60_unique_profile_tuples": len(full_profiles),
            "legacy_missing_profile_tuples": [list(row) for row in sorted(full_profiles - legacy_profiles)],
            "default_profile_tuple_counts": {
                "|".join(row): count
                for row, count in sorted(Counter(profile_signatures[:period]).items())
            },
        }
        for start in range(period):
            episode = samples[start:start + window]
            for query_position in range(window):
                rotation_count += 1
                demos = [pair for position, pair in enumerate(episode) if position != query_position]
                query = episode[query_position]
                hook_reasons = gen.lesson_identifiable(
                    [{"input": pair["input"], "output": pair["output"]} for pair in demos],
                    {"input": query["input"], "output": query["output"]},
                )
                surviving = [
                    name for name in declarations
                    if not any(pair["refutes"][name] for pair in demos)
                ]
                if hook_reasons or surviving:
                    failures.append({
                        "band": label, "start": start, "query_position": query_position,
                        "hook_reasons": hook_reasons, "surviving_rivals": surviving,
                    })
        if band is None:
            for start in (9, 10, 11, 59):
                old_indices = [(start + offset) % 12 for offset in range(window)]
                actual_indices = [start + offset for offset in range(window)]
                boundary_examples.append({
                    "start": start,
                    "legacy_indices": old_indices,
                    "actual_indices": actual_indices,
                    "legacy_profiles": [samples[i]["profiles"] for i in old_indices],
                    "actual_profiles": [samples[i]["profiles"] for i in actual_indices],
                })
    return {
        "schema": "9971f3a5882c-consecutive-profile-review-v1",
        "generator_path": str(source), "generator_sha256": source_sha256,
        "generator_sha256_at_finish": hashlib.sha256(source.read_bytes()).hexdigest(),
        "seed": seed, "period_components": period_components,
        "combined_profile_period": period,
        "rotations_checked": rotation_count,
        "status": "PASS" if not failures else "FAIL",
        "failures": failures, "bands": bands,
        "boundary_examples": boundary_examples,
        "limits": [
            "All 60 profile phases at one seed; stochastic layouts are not exhausted.",
            "Consecutive indices are not wrapped before generation.",
            "Labels use the selected generator's Python mirror; Racket parity is a separate check.",
            "Only the generator's declared rivals are checked.",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run()
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: report[key] for key in (
        "status", "generator_sha256", "generator_sha256_at_finish",
        "combined_profile_period", "rotations_checked", "failures"
    )}, indent=2))
    raise SystemExit(0 if report["status"] == "PASS" else 1)
