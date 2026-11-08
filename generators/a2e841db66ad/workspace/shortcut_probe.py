#!/usr/bin/env python3
"""Source-bound shortcut and cyclic-lesson probe for a2e841db66ad.

The probe intentionally reads the generator's live declarations instead of
copying rival names.  It checks declared canonical shortcuts against every
usable labeled canonical pair, searches generated support for exact rival
counterexamples, and exercises every query rotation in short consecutive
lesson windows.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "a2e841db66ad"
BANDS = ("easy", "medium", "hard")


def _jsonable_grid(grid: Any) -> list[list[int]]:
    return [list(row) for row in grid]


def _pair(generator, seed: int, sample_index: int, band: str) -> dict[str, Any]:
    grid = generator.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": generator.rule_mirror(grid)}


def build_report(*, per_band: int = 16, starts: int = 8) -> dict[str, Any]:
    if type(per_band) is not int or per_band < 1:
        raise ValueError("per_band must be a positive integer")
    if type(starts) is not int or starts < 1:
        raise ValueError("starts must be a positive integer")

    root = find_root(__file__)
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    labeled = canonical_pairs(TASK_ID, root=root, labeled_only=True)

    canonical_results: dict[str, dict[str, Any]] = {}
    for name, rival in dict(generator.CANONICAL_SHORTCUTS).items():
        matched = 0
        errors: list[dict[str, Any]] = []
        for index, pair in enumerate(labeled):
            try:
                prediction = rival(pair["input"])
            except Exception as exc:  # retained as evidence, not swallowed
                errors.append({"pair_index": index, "error": repr(exc)})
                continue
            if prediction == pair["output"]:
                matched += 1
            else:
                errors.append({"pair_index": index, "error": "output mismatch"})
        canonical_results[name] = {
            "checked": len(labeled),
            "matched": matched,
            "errors": errors,
        }

    generated_counterexamples: dict[str, list[dict[str, Any]]] = {
        name: [] for name in dict(generator.CANONICAL_SHORTCUTS)
    }
    witness_counts = {name: 0 for name in dict(generator.SEMANTIC_WITNESSES)}
    generated_checked = 0
    for band_index, band in enumerate(BANDS):
        for sample_index in range(per_band):
            seed = 81000 + band_index * 10000 + sample_index
            grid = generator.generate(seed, sample_index, difficulty=band)
            errors = generator.self_check(grid)
            if errors:
                raise AssertionError(
                    f"generated input failed self_check: band={band} sample={sample_index}: {errors}"
                )
            intended = generator.rule_mirror(grid)
            generated_checked += 1
            for witness_name, predicate in dict(generator.SEMANTIC_WITNESSES).items():
                if predicate(grid):
                    witness_counts[witness_name] += 1
            for rival_name, rival in dict(generator.CANONICAL_SHORTCUTS).items():
                try:
                    rival_output = rival(grid)
                except Exception as exc:
                    if not generated_counterexamples[rival_name]:
                        generated_counterexamples[rival_name].append(
                            {
                                "band": band,
                                "seed": seed,
                                "sample_index": sample_index,
                                "kind": "rival_error",
                                "error": repr(exc),
                            }
                        )
                    continue
                if rival_output != intended and not generated_counterexamples[rival_name]:
                    generated_counterexamples[rival_name].append(
                        {
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "overrides": {},
                            "observed_axes": generator.observe_overrides(grid),
                            "input": _jsonable_grid(grid),
                            "intended_output": _jsonable_grid(intended),
                            "rival_output": _jsonable_grid(rival_output),
                        }
                    )

    rotation_failures: list[dict[str, Any]] = []
    rotation_checked = 0
    for band_index, band in enumerate(BANDS):
        for start in range(starts):
            seed = 91000 + band_index * 10000 + start
            lesson = [
                _pair(generator, seed, start + offset, band)
                for offset in range(generator.EXAMPLES_NEEDED + 1)
            ]
            for query_index, query in enumerate(lesson):
                demos = [pair for index, pair in enumerate(lesson) if index != query_index]
                reasons = generator.lesson_identifiable(demos, query)
                rotation_checked += 1
                if reasons:
                    rotation_failures.append(
                        {
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "query_index": query_index,
                            "reasons": list(reasons),
                        }
                    )

    return {
        "schema": "a2e841db66ad-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(Path(source_path).resolve()),
        "generator_sha256": source_sha256,
        "rule_hash": generator.RULE_HASH,
        "examples_needed": generator.EXAMPLES_NEEDED,
        "declarations": {
            "canonical_shortcuts": sorted(generator.CANONICAL_SHORTCUTS),
            "lesson_competitors": sorted(generator.LESSON_COMPETITORS),
            "semantic_witnesses": sorted(generator.SEMANTIC_WITNESSES),
        },
        "canonical_shortcuts": canonical_results,
        "generated_support": {
            "per_band": per_band,
            "checked": generated_checked,
            "witness_counts": witness_counts,
        },
        "generated_counterexamples": generated_counterexamples,
        "rotation_check": {
            "starts_per_band": starts,
            "query_policy": "every rotation of EXAMPLES_NEEDED+1 consecutive pairs",
            "checked": rotation_checked,
            "failures": rotation_failures,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=16)
    parser.add_argument("--starts", type=int, default=8)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    report = build_report(per_band=args.per_band, starts=args.starts)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
