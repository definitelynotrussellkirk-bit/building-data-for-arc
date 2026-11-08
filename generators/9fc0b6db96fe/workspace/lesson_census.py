#!/usr/bin/env python3
"""Source-bound lesson census for 9fc0b6db96fe.

Run inside a prepared ARC runtime (the same layout used by ``arcpuzzles check``).
It uses the shared semantic gate's pinned lesson plan and canonical Racket oracle,
then tests all four cyclic choices of query position for each 3-demo lesson.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib
import json
from pathlib import Path

from scripts.generator_semantic_gate import BANDS, materialize_lessons, evaluate_competitors

TASK = "9fc0b6db96fe"


def grid_key(grid) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def run(count: int) -> dict:
    gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
    lessons, errors = materialize_lessons(TASK, count, n_demos=3, bands=BANDS)
    per_band = {
        band: {
            "lessons": 0,
            "cyclic_windows": 0,
            "identifiable": 0,
            "unidentifiable": 0,
            "unique_inputs": set(),
        }
        for band in BANDS
    }
    survivors = Counter()
    failures = []
    for lesson in lessons:
        band = lesson["band"]
        row = per_band[band]
        row["lessons"] += 1
        pairs = list(lesson["demos"]) + [lesson["query"]]
        for pair in pairs:
            row["unique_inputs"].add(grid_key(pair["input"]))
        for start in range(len(pairs)):
            rotated = pairs[start:] + pairs[:start]
            demos, query = rotated[:3], rotated[3]
            row["cyclic_windows"] += 1
            reasons = gen.lesson_identifiable(demos, query)
            scored = evaluate_competitors(gen.LESSON_COMPETITORS, {
                "index": lesson["index"],
                "replay": f"{lesson['replay']} cyclic_start={start}",
                "demos": demos,
                "query": query,
            })
            survivors.update(scored["survived_demos"])
            if reasons:
                row["unidentifiable"] += 1
                if len(failures) < 10:
                    failures.append({
                        "band": band,
                        "lesson": lesson["index"],
                        "seed": lesson["seed"],
                        "sample_index": lesson["sample_index"],
                        "cyclic_start": start,
                        "reasons": reasons,
                        "survivors": scored["survived_demos"],
                    })
            else:
                row["identifiable"] += 1
    encoded = {}
    for band, row in per_band.items():
        encoded[band] = {
            **{k: v for k, v in row.items() if k != "unique_inputs"},
            "unique_inputs": len(row["unique_inputs"]),
            "input_slots": row["lessons"] * 4,
        }
    return {
        "schema": "9fc0b6db96fe-lesson-census-v1",
        "task_id": TASK,
        "requested_lessons": count,
        "requested_per_band": count // len(BANDS),
        "n_demos": 3,
        "cyclic_starts_tested_per_lesson": 4,
        "sampler": "scripts.generator_semantic_gate.materialize_lessons; pinned per-band seeds; sample_index stride 11; canonical Racket outputs",
        "materialized": len(lessons),
        "materialization_errors": errors,
        "per_band": encoded,
        "competitor_survived_demo_counts": dict(survivors),
        "failures": failures,
        "passed": not errors and not failures and len(lessons) == count,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lessons", type=int, default=300)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = run(args.lessons)
    text = json.dumps(result, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
