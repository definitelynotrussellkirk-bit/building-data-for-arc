#!/usr/bin/env python3
"""Source-bound curriculum probe for generator 1856980929fe.

The probe deliberately imports the sibling generator file rather than an
installed package copy.  It assembles lessons the way the semantic gate does:
one seed per lesson, consecutive sample indexes for demos, and the next index
for the query.  Every competitor is read from ``LESSON_COMPETITORS`` so the
report cannot silently drift from the generator's declared semantic contract.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
GENERATOR_PATH = HERE.parent / "generator.py"
TASK_ID = "1856980929fe"
BANDS = ("easy", "medium", "hard")
LESSON_STRIDE = 11


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "review_probe_generator_1856980929fe", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def generator_sha256() -> str:
    return hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()


def _lesson_seed(band: str, lesson_index: int) -> int:
    digest = hashlib.sha256(
        f"review-probe:v1:{TASK_ID}:{band}:{lesson_index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def _grid_digest(grid) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _empty_competitor_counts() -> dict[str, int]:
    return {
        "grid_disagreements": 0,
        "survived_demos": 0,
        "query_discriminates": 0,
        "guarded_query_discriminates": 0,
        "unguarded_query_discriminates": 0,
        "survived_all": 0,
    }


def analyze(*, lessons_per_band: int = 100, demos: int = 5) -> dict[str, Any]:
    if lessons_per_band < 1:
        raise ValueError("lessons_per_band must be positive")
    if demos < 2:
        raise ValueError("demos must be at least 2")

    competitors = dict(gen.LESSON_COMPETITORS)
    witnesses = dict(gen.SEMANTIC_WITNESSES)
    witness_hits = {name: 0 for name in witnesses}
    band_rows: dict[str, Any] = {}
    total_lessons = 0
    total_invalid = 0
    total_query_survivors = 0
    total_guarded_query_survivors = 0
    total_unguarded_query_survivors = 0
    total_grids = 0

    for band in BANDS:
        unique_inputs: set[str] = set()
        profiles: dict[str, int] = {}
        competitor_counts = {
            name: _empty_competitor_counts() for name in competitors
        }
        seed_counts: dict[str, int] = {}
        size_counts: dict[str, int] = {}
        mixed_size_grids = 0
        lower_seed_grids = 0
        left_clip_grids = 0
        right_clip_grids = 0
        invalid_inputs = 0

        for lesson_index in range(lessons_per_band):
            seed = _lesson_seed(band, lesson_index)
            start = lesson_index * LESSON_STRIDE
            grids = [
                gen.generate(seed, start + offset, difficulty=band)
                for offset in range(demos + 1)
            ]
            outputs = [gen.rule_mirror(grid) for grid in grids]
            total_lessons += 1
            total_grids += len(grids)

            for offset, grid in enumerate(grids):
                unique_inputs.add(_grid_digest(grid))
                findings = gen.self_check(grid)
                if findings:
                    invalid_inputs += 1
                    total_invalid += 1
                profile = str(gen.schedule_profile(seed, start + offset, band))
                profiles[profile] = profiles.get(profile, 0) + 1
                rectangles = gen._rectangles(grid)
                seed_counts[str(len(rectangles))] = seed_counts.get(str(len(rectangles)), 0) + 1
                dims = {(rh, rw) for _, _, rh, rw in rectangles}
                for rh, rw in dims:
                    key = f"{rh}x{rw}"
                    size_counts[key] = size_counts.get(key, 0) + 1
                mixed_size_grids += int(len(dims) > 1)
                lower_seed_grids += int(
                    any(r >= len(grid) // 2 for r, _, _, _ in rectangles)
                )
                left_clip_grids += int(any(c < rw for _, c, _, rw in rectangles))
                right_clip_grids += int(
                    any(c + 2 * rw > len(grid[0]) for _, c, _, rw in rectangles)
                )
                for name, predicate in witnesses.items():
                    if predicate(grid):
                        witness_hits[name] += 1

            demo_grids, query_grid = grids[:-1], grids[-1]
            demo_outputs, query_output = outputs[:-1], outputs[-1]
            for name, rival in competitors.items():
                counts = competitor_counts[name]
                rival_outputs = [rival(grid) for grid in grids]
                counts["grid_disagreements"] += sum(
                    predicted != expected
                    for predicted, expected in zip(rival_outputs, outputs)
                )
                survives = all(
                    rival(grid) == expected
                    for grid, expected in zip(demo_grids, demo_outputs)
                )
                if not survives:
                    continue
                counts["survived_demos"] += 1
                if rival(query_grid) != query_output:
                    counts["query_discriminates"] += 1
                    total_query_survivors += 1
                    demos_payload = [
                        {"input": grid, "output": output}
                        for grid, output in zip(demo_grids, demo_outputs)
                    ]
                    gate_findings = gen.lesson_identifiable(
                        demos_payload, {"input": query_grid}
                    )
                    guarded = any(
                        finding.startswith(f"{name} fits every demo")
                        for finding in gate_findings
                    )
                    if guarded:
                        counts["guarded_query_discriminates"] += 1
                        total_guarded_query_survivors += 1
                    else:
                        counts["unguarded_query_discriminates"] += 1
                        total_unguarded_query_survivors += 1
                else:
                    counts["survived_all"] += 1

        band_rows[band] = {
            "lessons": lessons_per_band,
            "grids": lessons_per_band * (demos + 1),
            "unique_inputs": len(unique_inputs),
            "invalid_inputs": invalid_inputs,
            "schedule_profiles": dict(sorted(profiles.items())),
            "seed_counts": dict(sorted(seed_counts.items())),
            "rectangle_sizes": dict(sorted(size_counts.items())),
            "mixed_size_grids": mixed_size_grids,
            "lower_seed_grids": lower_seed_grids,
            "left_clip_grids": left_clip_grids,
            "right_clip_grids": right_clip_grids,
            "competitors": competitor_counts,
        }

    return {
        "schema": "arc-review-curriculum-probe-v1",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": generator_sha256(),
        "rule_hash": gen.RULE_HASH,
        "sampler": {
            "policy": "shared seed; five consecutive demos; next index query",
            "requested_demos": demos,
            "lesson_stride": LESSON_STRIDE,
            "seed_derivation": "sha256(review-probe:v1:task:band:lesson)[:12]",
            "bands": list(BANDS),
        },
        "domain": {
            "grid_h": "25..29",
            "grid_w": "22..29",
            "n_seeds": "1..3",
            "rect_sizes": list(gen.RECT_SIZE_NAMES),
            "schedule_profiles": list(gen.SCHEDULE_PROFILES),
        },
        "competitors": sorted(competitors),
        "witness_hits": witness_hits,
        "bands": band_rows,
        "totals": {
            "lessons": total_lessons,
            "grids": total_grids,
            "invalid_inputs": total_invalid,
            "query_discriminating_survivors": total_query_survivors,
            "guarded_query_discriminating_survivors": total_guarded_query_survivors,
            "unguarded_query_discriminating_survivors": total_unguarded_query_survivors,
        },
        "limitations": [
            "This measures the stated shared-seed consecutive-index sampler, not every possible external lesson assembler.",
            "Authority outputs use the tested Python rule mirror; the repository rule-smoke and semantic gates separately bind it to Racket.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--demos", type=int, default=5)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = analyze(lessons_per_band=args.lessons_per_band, demos=args.demos)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    return 1 if (
        report["totals"]["invalid_inputs"]
        or report["totals"]["unguarded_query_discriminating_survivors"]
    ) else 0


if __name__ == "__main__":
    raise SystemExit(main())
