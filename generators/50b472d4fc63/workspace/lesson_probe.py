#!/usr/bin/env python3
"""Independent finite lesson probe for task 50b472d4fc63.

This tool complements the shared lesson census.  It uses the task-local
independent oracle in ``reference_probe.py`` and, crucially, rotates each of
four sequential pairs through the query position.  Rival names are read from
the generator's current declarations rather than copied into this script.

The probe is finite: a pass means only that the sampled lessons refute the
currently declared rivals.  It is not a proof of universal ARC induction.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

TASK_DIR = Path(__file__).resolve().parents[1]
REPO = TASK_DIR.parents[1]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reference_probe import canonical_pairs, exact_output, load_generator, observed

DEFAULT_SEED = "50b472d4fc63-lesson-probe-v1"
BANDS = ("easy", "medium", "hard")


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": exact_output(grid)}


def _rival_failures(generator: Any, demos: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    for name, rival in generator.LESSON_COMPETITORS.items():
        try:
            if not any(rival(pair["input"]) != pair["output"] for pair in demos):
                failures.append(name)
        except Exception as exc:  # keep a broken rival executable visible
            failures.append(f"{name}: {type(exc).__name__}: {exc}")
    return failures


def run_probe(per_band: int, seed: str) -> dict[str, Any]:
    if per_band < 1:
        raise ValueError("--per-band must be at least 1")

    generator_path = TASK_DIR / "generator.py"
    generator = load_generator(generator_path)
    generator_sha256 = hashlib.sha256(generator_path.read_bytes()).hexdigest()

    canonical = canonical_pairs()
    canonical_fit: dict[str, dict[str, Any]] = {}
    for name, rival in generator.CANONICAL_SHORTCUTS.items():
        fits = [rival(pair["input"]) == pair["output"] for pair in canonical]
        canonical_fit[name] = {
            "fits_all": all(fits),
            "pairs_fit": sum(fits),
            "pairs_total": len(fits),
        }

    report: dict[str, Any] = {
        "schema": "50b472d4fc63-lesson-probe-v1",
        "task_id": generator.TASK_ID,
        "generator_version": generator.VERSION,
        "generator_sha256": generator_sha256,
        "declared_rule_hash": generator.RULE_HASH,
        "seed": seed,
        "per_band": per_band,
        "canonical_shortcuts_fit": canonical_fit,
        "declared_lesson_competitors": sorted(generator.LESSON_COMPETITORS),
        "declared_semantic_witnesses": sorted(generator.SEMANTIC_WITNESSES),
        "bands": {},
        "limits": [
            "finite generated sample",
            "independent Python transcription, not an authority execution",
            "tests only currently declared rivals",
        ],
    }

    blocking = []
    if not canonical_fit:
        blocking.append("no canonical shortcuts declared")
    for name, row in canonical_fit.items():
        if not row["fits_all"]:
            blocking.append(f"declared canonical shortcut {name} does not fit every canonical pair")

    for band in BANDS:
        # Each start needs four sequential pairs.  Materialize once so overlapping
        # windows exercise exactly the same deterministic examples.
        pairs: list[dict[str, Any]] = []
        generation_errors: list[dict[str, Any]] = []
        witness_counts = {name: 0 for name in generator.SEMANTIC_WITNESSES}
        observed_axes: set[tuple[tuple[str, int], ...]] = set()
        input_hashes: set[str] = set()
        for sample_index in range(per_band + 3):
            try:
                grid = generator.generate(seed, sample_index, difficulty=band)
                errors = generator.self_check(grid, difficulty=band)
                if errors:
                    generation_errors.append(
                        {"sample_index": sample_index, "self_check_errors": errors}
                    )
                pair = _pair(grid)
                pairs.append(pair)
                input_hashes.add(_grid_hash(grid))
                observed_axes.add(tuple(sorted(observed(grid).items())))
                for name, witness in generator.SEMANTIC_WITNESSES.items():
                    if witness(grid):
                        witness_counts[name] += 1
            except Exception as exc:
                generation_errors.append(
                    {
                        "sample_index": sample_index,
                        "exception": f"{type(exc).__name__}: {exc}",
                    }
                )
                break

        fixed_failures: list[dict[str, Any]] = []
        rotation_failures: list[dict[str, Any]] = []
        fixed_tested = 0
        rotations_tested = 0
        if len(pairs) == per_band + 3:
            for start in range(per_band):
                quartet = pairs[start : start + 4]
                demos = quartet[:3]
                query = quartet[3]
                issues = generator.lesson_identifiable(demos, query)
                surviving = _rival_failures(generator, demos)
                fixed_tested += 1
                if issues or surviving:
                    fixed_failures.append(
                        {
                            "start": start,
                            "issues": issues,
                            "surviving_rivals": surviving,
                        }
                    )

                # Rotate each pair through the query role; the other three are
                # demonstrations.  This is the coverage absent from the shared
                # source-bound census.
                for query_offset, rotated_query in enumerate(quartet):
                    rotated_demos = [
                        pair for offset, pair in enumerate(quartet) if offset != query_offset
                    ]
                    issues = generator.lesson_identifiable(rotated_demos, rotated_query)
                    surviving = _rival_failures(generator, rotated_demos)
                    rotations_tested += 1
                    if issues or surviving:
                        rotation_failures.append(
                            {
                                "start": start,
                                "query_offset": query_offset,
                                "issues": issues,
                                "surviving_rivals": surviving,
                            }
                        )

        band_row = {
            "materialized_pairs": len(pairs),
            "sample_indices": f"0..{max(0, per_band + 2)}",
            "unique_inputs": len(input_hashes),
            "unique_observed_axis_tuples": len(observed_axes),
            "witness_counts": witness_counts,
            "generation_errors": generation_errors,
            "fixed_query_windows_tested": fixed_tested,
            "fixed_query_failures": fixed_failures,
            "query_rotations_tested": rotations_tested,
            "query_rotation_failures": rotation_failures,
        }
        report["bands"][band] = band_row
        if generation_errors:
            blocking.append(f"{band}: generation/self-check errors")
        if fixed_failures:
            blocking.append(f"{band}: fixed-query lesson failures")
        if rotation_failures:
            blocking.append(f"{band}: cyclic query-rotation failures")
        for name, count in witness_counts.items():
            if count == 0:
                blocking.append(f"{band}: no sampled witness for {name}")

    report["blocking_findings"] = blocking
    report["status"] = "pass" if not blocking else "fail"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--seed", default=DEFAULT_SEED)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    report = run_probe(args.per_band, args.seed)
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
