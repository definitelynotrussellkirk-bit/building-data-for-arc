#!/usr/bin/env python3
"""Source-bound lesson identifiability probe for ARC task 510b12f6a12a.

The production worker constructs a per-puzzle episode by fixing one seed and
scanning consecutive ``sample_index`` values until it has the requested number
of distinct lawful pairs.  This probe mirrors that sampler (without executing
Racket): outputs come from the independent beam oracle in ``reference_probe``.
It then evaluates the generator's *actual declared* ``LESSON_COMPETITORS`` and
``CANONICAL_SHORTCUTS`` rather than copying a reviewer-maintained rival list.

The result is bounded evidence about this deterministic curriculum.  It does
not claim that the examples identify the rule against every possible program.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from reference_probe import beam_output, canonical_pairs, load_generator, observed

SCHEMA = "arc-lesson-identifiability-probe-v1"
BANDS = ("easy", "medium", "hard")


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"))


def _source_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalize_result(value: Any) -> list[list[int]]:
    if isinstance(value, dict) and "output" in value:
        value = value["output"]
    if not isinstance(value, (list, tuple)):
        raise TypeError(f"rival returned {type(value).__name__}, expected grid")
    return [list(row) for row in value]


def _sample_lesson(module, *, seed: int, difficulty: str,
                   pairs_per_lesson: int, first_index: int = 0) -> tuple[list[dict], list[dict]]:
    """Mirror the production worker's accepted-prefix sampler.

    The worker scans at most ``wanted * 5`` consecutive indices, rejects
    malformed/self-check-failing/duplicate inputs, and takes the first wanted
    accepted pairs.  Here the independent task oracle supplies outputs.
    """
    pairs: list[dict] = []
    rejections: list[dict] = []
    seen: set[str] = set()
    for sample_index in range(first_index, first_index + pairs_per_lesson * 5):
        try:
            generated = module.generate(
                seed=seed,
                sample_index=sample_index,
                difficulty=difficulty,
            )
            grid = generated.get("input") if isinstance(generated, dict) else generated
            findings = module.self_check(grid, difficulty=difficulty)
            if findings:
                raise ValueError(f"self_check: {findings}")
            key = _grid_key(grid)
            if key in seen:
                raise ValueError("duplicate input")
            seen.add(key)
            pairs.append(
                {
                    "sample_index": sample_index,
                    "input": grid,
                    "output": beam_output(grid),
                }
            )
        except Exception as exc:  # evidence, not a swallowed sampler failure
            rejections.append(
                {
                    "seed": seed,
                    "sample_index": sample_index,
                    "error": type(exc).__name__,
                    "reason": str(exc),
                }
            )
        if len(pairs) == pairs_per_lesson:
            break
    if len(pairs) != pairs_per_lesson:
        raise RuntimeError(
            f"only {len(pairs)}/{pairs_per_lesson} accepted pairs for "
            f"seed={seed} difficulty={difficulty}; rejections={rejections}"
        )
    return pairs, rejections


def _canonical_shortcut_report(module) -> dict[str, dict[str, Any]]:
    pairs = canonical_pairs()
    report: dict[str, dict[str, Any]] = {}
    for name, shortcut in sorted(module.CANONICAL_SHORTCUTS.items()):
        disagreements = []
        for index, pair in enumerate(pairs):
            predicted = _normalize_result(shortcut(pair["input"]))
            if predicted != pair["output"]:
                disagreements.append(index)
        report[name] = {
            "canonical_pair_count": len(pairs),
            "pair_disagreements": len(disagreements),
            "disagreement_pair_indices": disagreements,
            "fits_all_canonical_pairs": not disagreements,
        }
    return report


def build_report(*, generator_path: str | Path, lessons_per_band: int = 100,
                 pairs_per_lesson: int = 4, base_seed: int = 51012000) -> dict[str, Any]:
    if lessons_per_band < 1:
        raise ValueError("lessons_per_band must be positive")
    if pairs_per_lesson < 1:
        raise ValueError("pairs_per_lesson must be positive")
    path = Path(generator_path).resolve()
    module = load_generator(path)
    competitors = dict(module.LESSON_COMPETITORS)
    shortcuts = dict(module.CANONICAL_SHORTCUTS)
    if not competitors:
        raise ValueError("generator declares no LESSON_COMPETITORS")

    bands: dict[str, Any] = {}
    for band_index, band in enumerate(BANDS):
        lessons: list[list[dict]] = []
        all_rejections: list[dict] = []
        input_keys: list[str] = []
        observations: list[dict[str, int]] = []
        profile_counts: Counter[str] = Counter()
        domain_violations: list[dict] = []

        for lesson_index in range(lessons_per_band):
            # Matches the production worker's count>1 convention: each episode
            # increments the seed while restarting the sample-index prefix.
            seed = base_seed + band_index * 1_000_000 + lesson_index
            pairs, rejected = _sample_lesson(
                module,
                seed=seed,
                difficulty=band,
                pairs_per_lesson=pairs_per_lesson,
            )
            lessons.append(pairs)
            all_rejections.extend(rejected)
            for pair in pairs:
                grid = pair["input"]
                input_keys.append(_grid_key(grid))
                observations.append(observed(grid))
                findings = module.self_check(grid, difficulty=band)
                if findings:
                    domain_violations.append(
                        {
                            "lesson_index": lesson_index,
                            "sample_index": pair["sample_index"],
                            "findings": findings,
                        }
                    )
                if callable(getattr(module, "schedule_profile", None)):
                    profile_counts[
                        module.schedule_profile(seed, pair["sample_index"], band)
                    ] += 1

        rival_stats: dict[str, Any] = {}
        for name, rival in sorted(competitors.items()):
            unrefuted: list[int] = []
            pair_disagreements = 0
            disagreement_cells = 0
            for lesson_index, lesson in enumerate(lessons):
                lesson_disagreements = 0
                for pair in lesson:
                    predicted = _normalize_result(rival(pair["input"]))
                    expected = pair["output"]
                    cells = sum(
                        actual != target
                        for actual_row, target_row in zip(predicted, expected)
                        for actual, target in zip(actual_row, target_row)
                    )
                    if cells:
                        lesson_disagreements += 1
                        pair_disagreements += 1
                        disagreement_cells += cells
                if not lesson_disagreements:
                    unrefuted.append(lesson_index)
            rival_stats[name] = {
                "lessons_refuted": lessons_per_band - len(unrefuted),
                "unrefuted_lesson_indices": unrefuted,
                "pair_disagreements": pair_disagreements,
                "disagreement_cells": disagreement_cells,
            }

        axis_limits = {
            name: {
                "min": min(item[name] for item in observations),
                "max": max(item[name] for item in observations),
                "values": sorted({item[name] for item in observations}),
            }
            for name in ("grid_h", "grid_w", "n_v", "n_h", "n_blockers")
        }
        bands[band] = {
            "lesson_count": lessons_per_band,
            "pair_count": len(input_keys),
            "unique_input_count": len(set(input_keys)),
            "cross_lesson_repeat_count": len(input_keys) - len(set(input_keys)),
            "rejected_draw_count": len(all_rejections),
            "rejections": all_rejections,
            "domain_violations": domain_violations,
            "observed_axis_limits": axis_limits,
            "schedule_profile_counts": dict(sorted(profile_counts.items())),
            "competitors": rival_stats,
        }

    return {
        "schema": SCHEMA,
        "task_id": getattr(module, "TASK_ID", "510b12f6a12a"),
        "generator": {
            "path": str(path),
            "sha256": _source_sha256(path),
            "version": getattr(module, "VERSION", None),
            "rule_hash": getattr(module, "RULE_HASH", None),
        },
        "sampler": {
            "algorithm": "production_episode_prefix",
            "bands": list(BANDS),
            "lessons_per_band": lessons_per_band,
            "pairs_per_lesson": pairs_per_lesson,
            "first_sample_index": 0,
            "max_draws_per_lesson": pairs_per_lesson * 5,
            "seed_formula": (
                "base_seed + band_index*1000000 + lesson_index; "
                "consecutive sample_index values; first distinct lawful pairs"
            ),
            "base_seed": base_seed,
            "output_oracle": "workspace/reference_probe.py::beam_output",
            "uniqueness_scope": "within each lesson (matching production worker)",
        },
        "declared_competitors": sorted(competitors),
        "canonical_shortcuts": _canonical_shortcut_report(module),
        "bands": bands,
        "limitations": [
            "The probe tests only the generator-declared rival programs.",
            "Passing establishes bounded lesson separation, not universal rule induction.",
            "Outputs use an independent Python oracle; official Racket parity is a separate gate.",
        ],
    }


def report_passes(report: dict[str, Any]) -> bool:
    if not all(
        item["fits_all_canonical_pairs"]
        for item in report["canonical_shortcuts"].values()
    ):
        return False
    for band in BANDS:
        stats = report["bands"][band]
        if stats["domain_violations"] or stats["rejected_draw_count"]:
            return False
        # The production worker enforces uniqueness within each lesson only.
        # Cross-lesson repeats remain visible in the report but are not invalid.
        if any(
            item["unrefuted_lesson_indices"]
            for item in stats["competitors"].values()
        ):
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=Path(__file__).resolve().parents[1] / "generator.py")
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--pairs-per-lesson", type=int, default=4)
    parser.add_argument("--base-seed", type=int, default=51012000)
    parser.add_argument("--json-out", type=Path, required=True)
    parser.add_argument(
        "--require-complete-refutation",
        action="store_true",
        help="exit nonzero unless every declared competitor is refuted in every sampled lesson",
    )
    args = parser.parse_args()
    report = build_report(
        generator_path=args.generator,
        lessons_per_band=args.lessons_per_band,
        pairs_per_lesson=args.pairs_per_lesson,
        base_seed=args.base_seed,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "schema": report["schema"],
                "task_id": report["task_id"],
                "bands": {
                    band: {
                        "lessons": report["bands"][band]["lesson_count"],
                        "unique_inputs": report["bands"][band]["unique_input_count"],
                        "competitors": {
                            name: stats["lessons_refuted"]
                            for name, stats in report["bands"][band]["competitors"].items()
                        },
                    }
                    for band in BANDS
                },
                "passed": report_passes(report),
            },
            sort_keys=True,
        )
    )
    return 1 if args.require_complete_refutation and not report_passes(report) else 0


if __name__ == "__main__":
    raise SystemExit(main())
