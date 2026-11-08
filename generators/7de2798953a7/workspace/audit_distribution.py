#!/usr/bin/env python3
"""Reproducible distribution, lesson-window, rival, and Racket parity audit."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from reference_probe import (
    any_two_nonzero_rival,
    canonical_pairs,
    intended_output,
    load_generator,
    mismatched_rows,
    pair_rows,
    racket_outputs,
    right_phase_rival,
    shortcut_witness,
    solid_fill_rival,
)

CANONICAL_PROFILES = {(6, 7, 4), (5, 8, 4), (4, 9, 3), (4, 8, 3)}


def profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def audit(module, count, windows):
    report = {
        "schema": "7de2798953a7-distribution-audit-v1",
        "generator_version": module.VERSION,
        "generator_sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        "canonical_profiles": sorted(map(list, CANONICAL_PROFILES)),
        "by_band": {},
    }
    sample_grids = []
    for band in ("easy", "medium", "hard"):
        counts = Counter()
        shapes = set()
        colours = set()
        inputs = set()
        for index in range(count):
            grid = module.generate(50000 + index, index, difficulty=band)
            replay = module.generate(50000 + index, index, difficulty=band)
            pairs = pair_rows(grid)
            out = intended_output(grid)
            counts["draws"] += 1
            counts["self_check_errors"] += bool(module.self_check(grid))
            counts["nondeterministic"] += grid != replay
            counts["canonical_profile_hits"] += profile(grid) in CANONICAL_PROFILES
            counts["odd_span_witnesses"] += any((right - left) % 2 for _, _, left, right in pairs)
            counts["mismatch_witnesses"] += bool(mismatched_rows(grid))
            counts["solid_fill_disagreements"] += solid_fill_rival(grid) != out
            counts["right_phase_disagreements"] += right_phase_rival(grid) != out
            counts["any_two_disagreements"] += any_two_nonzero_rival(grid) != out
            shapes.add((len(grid), len(grid[0])))
            colours.update(colour for _, colour, _, _ in pairs)
            inputs.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            if index < 4:
                sample_grids.append(grid)

        rotation_failures = []
        for start in range(windows):
            grids = [
                module.generate(90000 + start, start + offset, difficulty=band)
                for offset in range(module.EXAMPLES_NEEDED + 1)
            ]
            for query_index in range(len(grids)):
                demos = [
                    {"input": grid, "output": intended_output(grid)}
                    for index, grid in enumerate(grids)
                    if index != query_index
                ]
                query = {
                    "input": grids[query_index],
                    "output": intended_output(grids[query_index]),
                }
                reasons = module.lesson_identifiable(demos, query)
                if reasons:
                    rotation_failures.append(
                        {"start": start, "query_index": query_index, "reasons": reasons}
                    )
        counts["rotations_checked"] = windows * (module.EXAMPLES_NEEDED + 1)
        counts["rotation_failures"] = len(rotation_failures)
        report["by_band"][band] = {
            "counts": dict(counts),
            "distinct_shapes": sorted(map(list, shapes)),
            "distinct_pair_colours": sorted(colours),
            "distinct_inputs": len(inputs),
            "rotation_failures": rotation_failures[:10],
        }

    canonical = canonical_pairs()
    report["canonical"] = {
        "pair_count": len(canonical),
        "oracle_matches": sum(intended_output(pair["input"]) == pair["output"] for pair in canonical),
        "any_two_shortcut_fits": sum(any_two_nonzero_rival(pair["input"]) == pair["output"] for pair in canonical),
        "self_check_accepts": sum(not module.self_check(pair["input"]) for pair in canonical),
    }
    witness = shortcut_witness()
    intended = intended_output(witness)
    rival = any_two_nonzero_rival(witness)
    report["shortcut_witness"] = {
        "input": witness,
        "intended": intended,
        "any_two_nonzero": rival,
        "differing_cells": [
            [r, c]
            for r in range(len(witness))
            for c in range(len(witness[0]))
            if intended[r][c] != rival[r][c]
        ],
        "self_check": module.self_check(witness),
    }
    return report, [pair["input"] for pair in canonical] + [witness] + sample_grids


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--windows", type=int, default=100)
    parser.add_argument("--racket", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.count < 1 or args.windows < 1:
        parser.error("--count and --windows must be positive")

    module = load_generator(args.generator)
    report, grids = audit(module, args.count, args.windows)
    report["racket"] = {"status": "not_requested", "checked": 0}
    exit_code = 0
    for band, data in report["by_band"].items():
        counts = data["counts"]
        failures = (
            counts["self_check_errors"]
            + counts["nondeterministic"]
            + counts["rotation_failures"]
            + (args.count - counts["canonical_profile_hits"])
            + (args.count - counts["odd_span_witnesses"])
            + (args.count - counts["solid_fill_disagreements"])
            + (args.count - counts["right_phase_disagreements"])
        )
        if failures:
            exit_code = 1
    if report["canonical"] != {
        "pair_count": 4,
        "oracle_matches": 4,
        "any_two_shortcut_fits": 4,
        "self_check_accepts": 4,
    }:
        exit_code = 1
    if report["shortcut_witness"]["differing_cells"] != [[1, 2], [1, 4]]:
        exit_code = 1

    if args.racket:
        try:
            actual = racket_outputs(grids)
            expected = [intended_output(grid) for grid in grids]
            mismatches = [index for index, pair in enumerate(zip(actual, expected)) if pair[0] != pair[1]]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(actual),
                "mismatches": mismatches,
            }
            if mismatches:
                exit_code = 1
        except Exception as exc:  # retained as explicit evidence, never fallback
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            exit_code = 2

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"by_band": report["by_band"], "canonical": report["canonical"], "racket": report["racket"]}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
