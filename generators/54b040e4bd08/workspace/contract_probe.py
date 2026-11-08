#!/usr/bin/env python3
"""Exhaustive public-axis and four-profile lesson probe for 54b040e4bd08.

This is intentionally independent of the production intended-rule mirror: labels
come from ``reference_probe.reference_output`` and the declared rivals are read
from the generator at runtime.  It is portable inside a returned review packet.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from typing import Any

from reference_probe import canonical_pairs, load_generator, reference_output

BANDS = (None, "easy", "medium", "hard")
AXIS_VALUES = {
    "grid_h": range(6, 11),
    "grid_w": range(9, 13),
    "tile_shape": ("2x2", "2x3", "3x2"),
    "vertical_margin": (1, 2),
    "horizontal_margin": (1, 2),
}


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return sha256(payload).hexdigest()


def run_probe() -> dict[str, Any]:
    gen = load_generator()
    failures: list[dict[str, Any]] = []
    axis_cases = 0
    unique_axis_inputs: set[str] = set()

    names = tuple(AXIS_VALUES)
    domains = [AXIS_VALUES[name] for name in names]
    for band in BANDS:
        for case_index, values in enumerate(product(*domains)):
            options = dict(zip(names, values))
            try:
                grid = gen.generate(20261008, case_index, difficulty=band, **options)
                diagnostics = gen.self_check(grid)
                observed = gen.observe_overrides(grid)
                answer = reference_output(grid)
                if diagnostics:
                    raise AssertionError(f"self_check: {diagnostics}")
                if observed != options:
                    raise AssertionError(f"observed {observed!r} != requested {options!r}")
                if answer == grid:
                    raise AssertionError("reference transformation was identity")
                unique_axis_inputs.add(_grid_hash(grid))
            except Exception as exc:  # retained in JSON, never silently ignored
                failures.append({
                    "kind": "axis_case",
                    "band": band,
                    "options": options,
                    "error": f"{type(exc).__name__}: {exc}",
                })
            axis_cases += 1

    rotation_cases = 0
    for band in BANDS:
        for start in range(gen.LESSON_SCHEDULE_PERIOD):
            pairs = []
            for offset in range(gen.LESSON_SCHEDULE_PERIOD):
                sample_index = start + offset
                grid = gen.generate(303, sample_index, difficulty=band)
                pairs.append({"input": grid, "output": reference_output(grid)})
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                reasons = gen.lesson_identifiable(demos, query)
                survivors = [
                    name
                    for name, rival in gen.LESSON_COMPETITORS.items()
                    if all(rival(pair["input"]) == pair["output"] for pair in demos)
                ]
                if reasons or survivors:
                    failures.append({
                        "kind": "rotation_case",
                        "band": band,
                        "start": start,
                        "query_index": query_index,
                        "reasons": reasons,
                        "survivors": survivors,
                    })
                rotation_cases += 1

    canonical_checks = 0
    for pair_index, pair in enumerate(canonical_pairs()):
        for name, rival in gen.CANONICAL_SHORTCUTS.items():
            if rival(pair["input"]) != pair["output"]:
                failures.append({
                    "kind": "canonical_shortcut",
                    "pair_index": pair_index,
                    "rival": name,
                    "error": "declared canonical shortcut does not fit canonical output",
                })
            canonical_checks += 1

    default_inputs: set[str] = set()
    profile_counts: dict[str, Counter[str]] = {}
    witness_counts: dict[str, Counter[str]] = {}
    for band in BANDS:
        band_name = "none" if band is None else band
        profile_counts[band_name] = Counter()
        witness_counts[band_name] = Counter()
        for sample_index in range(200):
            grid = gen.generate(919, sample_index, difficulty=band)
            default_inputs.add(_grid_hash(grid))
            profile_counts[band_name][gen.schedule_profile(919, sample_index, band)] += 1
            for name, predicate in gen.SEMANTIC_WITNESSES.items():
                if predicate(grid):
                    witness_counts[band_name][name] += 1

    return {
        "schema": "periodic-hole-contract-probe-v1",
        "task_id": gen.TASK_ID,
        "generator_version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "axis_cases": axis_cases,
        "unique_axis_inputs": len(unique_axis_inputs),
        "rotation_cases": rotation_cases,
        "canonical_shortcut_checks": canonical_checks,
        "default_draws": 200 * len(BANDS),
        "unique_default_inputs": len(default_inputs),
        "profile_counts": {band: dict(counts) for band, counts in profile_counts.items()},
        "witness_counts": {band: dict(counts) for band, counts in witness_counts.items()},
        "failures": failures,
        "passed": not failures,
        "limits": [
            "finite declared-axis enumeration; does not prove behavior for undeclared hypotheses",
            "rotation probe exhausts the four-slot schedule starts and query positions but not every seed",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_probe()
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
