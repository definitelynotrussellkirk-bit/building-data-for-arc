#!/usr/bin/env python3
"""Audit every query rotation of generated transform-stamp lessons.

The shared lesson census follows the production assembly order but intentionally
leaves query rotations to task-local probes.  This script materializes the same
kind of consecutive sample window, rotates every member into the query slot,
and checks the generator's *actual* ``LESSON_COMPETITORS`` declarations.  It
also treats a competitor exception as a contract failure rather than silently
counting a partial function as refuted.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any

from reference_probe import GENERATOR, geometry_output, load_generator

TASK = "4296e507c770"
BANDS = ("easy", "medium", "hard")


def _seed(band: str, index: int) -> int:
    raw = f"lesson-rotation:v1:{TASK}:{band}:{index}".encode("utf-8")
    return int(hashlib.sha256(raw).hexdigest()[:8], 16)


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _short_failure(
    *,
    band: str,
    lesson_index: int,
    seed: int,
    start: int,
    query_position: int,
    competitor: str | None = None,
    detail: Any = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "band": band,
        "lesson_index": lesson_index,
        "seed": seed,
        "start": start,
        "query_position": query_position,
    }
    if competitor is not None:
        row["competitor"] = competitor
    if detail is not None:
        row["detail"] = detail
    return row


def audit_rotations(module: Any, *, per_band: int = 100) -> dict[str, Any]:
    """Return a compact cyclic-identifiability report for ``module``.

    A lesson contains ``EXAMPLES_NEEDED`` demonstrations plus one query.  Each
    generated pair is used as the query exactly once.  Rival functions must be
    total on every pair, and any rival that survives the demonstrations but
    changes the query is retained as an ambiguity.
    """
    if type(per_band) is not int or per_band <= 0:
        raise ValueError("per_band must be a positive integer")
    lesson_width = int(module.EXAMPLES_NEEDED) + 1
    if lesson_width < 2:
        raise ValueError("EXAMPLES_NEEDED must be at least 1")
    competitors = dict(module.LESSON_COMPETITORS)
    if not competitors:
        raise ValueError("LESSON_COMPETITORS must declare at least one rival")

    report: dict[str, Any] = {
        "schema": "4296e507c770-cyclic-lesson-audit-v1",
        "task_id": TASK,
        "sampler": {
            "bands": list(BANDS),
            "per_band": per_band,
            "seed_recipe": "uint32(first 8 hex chars of sha256('lesson-rotation:v1:TASK:BAND:INDEX'))",
            "start_recipe": "lesson index; each lesson uses consecutive sample indices",
            "rotation_policy": "cyclically rotate each pair into the final query slot",
        },
        "lesson_width": lesson_width,
        "competitors": sorted(competitors),
        "lessons_checked": 0,
        "rotations_checked": 0,
        "ambiguities": [],
        "competitor_errors": [],
        "hook_failures": [],
        "by_band": {},
        "limits": [
            "Finite declared-rival audit, not a proof against every possible rule.",
            "Expected labels use the independent geometry oracle from reference_probe.py.",
            "Racket parity is checked by the separate independent reference probe.",
        ],
    }

    for band in BANDS:
        counts: Counter[str] = Counter()
        unique_inputs: set[str] = set()
        competitor_refutations: Counter[str] = Counter()
        for lesson_index in range(per_band):
            seed = _seed(band, lesson_index)
            start = lesson_index
            pairs = []
            for offset in range(lesson_width):
                grid = module.generate(seed, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": geometry_output(grid)})
                unique_inputs.add(_grid_hash(grid))
            counts["lessons"] += 1
            report["lessons_checked"] += 1

            # A left rotation followed by "last is query" visits every original
            # pair as query exactly once.
            for shift in range(lesson_width):
                rotated = pairs[shift:] + pairs[:shift]
                demos, query = rotated[:-1], rotated[-1]
                query_position = (shift - 1) % lesson_width
                counts["rotations"] += 1
                report["rotations_checked"] += 1
                rotation_failed = False

                try:
                    hook_reasons = list(module.lesson_identifiable(demos, query))
                except Exception as exc:  # retained as evidence, never a pass
                    hook_reasons = [f"{type(exc).__name__}: {exc}"]
                if hook_reasons:
                    rotation_failed = True
                    report["hook_failures"].append(
                        _short_failure(
                            band=band,
                            lesson_index=lesson_index,
                            seed=seed,
                            start=start,
                            query_position=query_position,
                            detail=hook_reasons,
                        )
                    )

                for name, competitor in competitors.items():
                    try:
                        demo_predictions = [competitor(pair["input"]) for pair in demos]
                        query_prediction = competitor(query["input"])
                    except Exception as exc:
                        rotation_failed = True
                        report["competitor_errors"].append(
                            _short_failure(
                                band=band,
                                lesson_index=lesson_index,
                                seed=seed,
                                start=start,
                                query_position=query_position,
                                competitor=name,
                                detail=f"{type(exc).__name__}: {exc}",
                            )
                        )
                        continue

                    fits_demos = all(
                        prediction == pair["output"]
                        for prediction, pair in zip(demo_predictions, demos)
                    )
                    changes_query = query_prediction != query["output"]
                    if not fits_demos:
                        competitor_refutations[name] += 1
                    elif changes_query:
                        rotation_failed = True
                        report["ambiguities"].append(
                            _short_failure(
                                band=band,
                                lesson_index=lesson_index,
                                seed=seed,
                                start=start,
                                query_position=query_position,
                                competitor=name,
                                detail={
                                    "query_input_sha256": _grid_hash(query["input"]),
                                    "query_expected_sha256": _grid_hash(query["output"]),
                                    "query_rival_sha256": _grid_hash(query_prediction),
                                },
                            )
                        )

                if not rotation_failed:
                    counts["rotations_passed"] += 1

        report["by_band"][band] = {
            "lessons": counts["lessons"],
            "rotations": counts["rotations"],
            "rotations_passed": counts["rotations_passed"],
            "pairs": counts["lessons"] * lesson_width,
            "unique_inputs": len(unique_inputs),
            "competitor_refutations": {
                name: competitor_refutations[name] for name in sorted(competitors)
            },
        }

    report["status"] = (
        "pass"
        if not report["ambiguities"]
        and not report["competitor_errors"]
        and not report["hook_failures"]
        else "fail"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.per_band < 100:
        parser.error("--per-band must be at least 100 for retained evidence")

    module = load_generator(args.generator)
    report = audit_rotations(module, per_band=args.per_band)
    generator_path = (args.generator or GENERATOR).resolve()
    report["generator_sha256"] = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
