#!/usr/bin/env python3
"""Source-bound census for every declared exact-crop shortcut rival.

This is an authoring/review tool, never a visible-only solve helper.  It reads
canonical labels and the selected generator, checks every declared canonical
shortcut against all labeled canonical occurrences, then measures both ordinary
generalized schedule slots across a deterministic seed range in every band.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "70c33a3391ac"
BANDS = ("easy", "medium", "hard")
GENERALIZED_SLOTS = (1, 2)


def _freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _difference(expected: list[list[int]], rival: list[list[int]]) -> dict[str, Any]:
    if len(expected) != len(rival) or any(len(a) != len(b) for a, b in zip(expected, rival)):
        return {
            "shape_mismatch": True,
            "expected_shape": [len(expected), len(expected[0]) if expected else 0],
            "rival_shape": [len(rival), len(rival[0]) if rival else 0],
        }
    cells = [
        {"row": r, "column": c, "expected": value, "rival": rival[r][c]}
        for r, row in enumerate(expected)
        for c, value in enumerate(row)
        if value != rival[r][c]
    ]
    return {"shape_mismatch": False, "different_cells": cells}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-start", type=int, default=90000)
    parser.add_argument("--per-band", type=int, default=200)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.per_band < 1:
        raise SystemExit("--per-band must be positive")
    if args.out.exists():
        raise SystemExit(f"refusing to overwrite {args.out}")

    root = find_root(__file__)
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    shortcut_names = tuple(generator.CANONICAL_SHORTCUTS)
    competitor_names = tuple(generator.LESSON_COMPETITORS)
    witness_names = tuple(generator.SEMANTIC_WITNESSES)
    if not shortcut_names or set(shortcut_names) != set(competitor_names) or set(shortcut_names) != set(witness_names):
        raise SystemExit("declared shortcut/competitor/witness names are missing or disagree")

    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    canonical_results: dict[str, Any] = {}
    for name, rival in generator.CANONICAL_SHORTCUTS.items():
        mismatches = []
        for index, pair in enumerate(canonical):
            if rival(copy.deepcopy(pair["input"])) != pair["output"]:
                mismatches.append(index)
        canonical_results[name] = {
            "occurrences_checked": len(canonical),
            "mismatch_indices": mismatches,
            "fits_all": not mismatches,
        }
    if any(not row["fits_all"] for row in canonical_results.values()):
        raise SystemExit("a declared canonical shortcut no longer fits all canonical labels")

    counts = {
        band: {
            name: {"generated": 0, "witness_true": 0, "rival_refuted": 0}
            for name in shortcut_names
        }
        for band in BANDS
    }
    all_refuted = {band: 0 for band in BANDS}
    unique_inputs = {band: set() for band in BANDS}
    first_witness: dict[str, Any] = {}
    domain_failures: list[dict[str, Any]] = []

    for band_index, band in enumerate(BANDS):
        for offset in range(args.per_band):
            seed = args.seed_start + band_index * args.per_band + offset
            for sample_index in GENERALIZED_SLOTS:
                grid = generator.generate(seed, sample_index, difficulty=band)
                errors = generator.self_check(grid, difficulty=band)
                if errors:
                    domain_failures.append(
                        {"band": band, "seed": seed, "sample_index": sample_index, "errors": errors}
                    )
                    continue
                unique_inputs[band].add(_freeze(grid))
                analysis = generator._analysis(grid)
                expected = [list(row) for row in analysis["duplicate"]["crop"]]
                sample_all_refuted = True
                for name in shortcut_names:
                    witness = bool(generator.SEMANTIC_WITNESSES[name](copy.deepcopy(grid)))
                    rival_output = generator.LESSON_COMPETITORS[name](copy.deepcopy(grid))
                    refuted = rival_output != expected
                    row = counts[band][name]
                    row["generated"] += 1
                    row["witness_true"] += int(witness)
                    row["rival_refuted"] += int(refuted)
                    sample_all_refuted = sample_all_refuted and witness and refuted
                    if name not in first_witness and witness and refuted:
                        first_witness[name] = {
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "observed_overrides": generator.observe_overrides(grid),
                            "input": grid,
                            "intended_output": expected,
                            "rival_output": rival_output,
                            "difference": _difference(expected, rival_output),
                        }
                all_refuted[band] += int(sample_all_refuted)

    if domain_failures:
        raise SystemExit(f"generated domain failures: {domain_failures[:3]}")
    expected_per_band = args.per_band * len(GENERALIZED_SLOTS)
    for band in BANDS:
        if all_refuted[band] != expected_per_band:
            raise SystemExit(
                f"not every {band} generalized sample refuted every rival: "
                f"{all_refuted[band]}/{expected_per_band}"
            )
    if set(first_witness) != set(shortcut_names):
        raise SystemExit("missing a retained witness for one or more declared rivals")

    report = {
        "schema": "70c33a3391ac-declared-shortcut-census-v1",
        "status": "passed",
        "task_id": TASK_ID,
        "generator_source": str(source_path),
        "generator_sha256": source_sha256,
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "seed_start": args.seed_start,
        "per_band_seed_count": args.per_band,
        "sample_indices": list(GENERALIZED_SLOTS),
        "generated_per_band": expected_per_band,
        "generated_total": expected_per_band * len(BANDS),
        "canonical_occurrences": len(canonical),
        "unique_canonical_inputs": len({_freeze(pair["input"]) for pair in canonical}),
        "canonical_shortcuts": canonical_results,
        "counts": counts,
        "all_declared_rivals_refuted": all_refuted,
        "unique_generated_inputs": {band: len(values) for band, values in unique_inputs.items()},
        "first_witness": first_witness,
        "scope": (
            "Deterministic finite census of both ordinary generalized schedule slots; "
            "declared rivals only, with Python contract labels. Racket parity and lesson "
            "assembly are checked separately by the battery and lesson census."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "passed",
                "generator_sha256": source_sha256,
                "generated_total": report["generated_total"],
                "all_declared_rivals_refuted": all_refuted,
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
