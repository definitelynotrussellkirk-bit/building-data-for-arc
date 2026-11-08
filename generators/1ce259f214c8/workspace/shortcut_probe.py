#!/usr/bin/env python3
"""Measure the strongest public-example shortcut for task 1ce259f214c8.

The public examples all leave the output border blank, so the rival tested here
computes XOR only in the interior and forces the output border to zero.  The
script is intentionally runtime-agnostic: point it at an immutable before or a
repaired prepared runtime and compare the same deterministic census.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any

TASK_ID = "1ce259f214c8"
BANDS = ("easy", "medium", "hard")


def masks(grid: list[list[int]]) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    h = len(grid)
    half = (len(grid[0]) - 1) // 2
    left = {(r, c) for r in range(h) for c in range(half) if grid[r][c] != 0}
    right = {
        (r, c - half - 1)
        for r in range(h)
        for c in range(half + 1, 2 * half + 1)
        if grid[r][c] != 0
    }
    return left, right


def xor_output(grid: list[list[int]]) -> list[list[int]]:
    left, right = masks(grid)
    h = len(grid)
    half = (len(grid[0]) - 1) // 2
    active = left ^ right
    return [[8 if (r, c) in active else 0 for c in range(half)] for r in range(h)]


def empty_output_border(grid: list[list[int]]) -> list[list[int]]:
    output = xor_output(grid)
    h, w = len(output), len(output[0])
    return [
        [
            0 if r in (0, h - 1) or c in (0, w - 1) else output[r][c]
            for c in range(w)
        ]
        for r in range(h)
    ]


def border_xor(grid: list[list[int]]) -> int:
    output = xor_output(grid)
    h, w = len(output), len(output[0])
    return sum(
        output[r][c] == 8
        for r in range(h)
        for c in range(w)
        if r in (0, h - 1) or c in (0, w - 1)
    )


def canonical_pairs(runtime: Path) -> list[dict[str, Any]]:
    ledger = runtime / "data/canonical/puzzles.jsonl"
    for line in ledger.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
            return [*row["train"], *tests]
    raise RuntimeError(f"canonical task {TASK_ID} not found in {ledger}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--draws", type=int, default=300)
    parser.add_argument("--lessons", type=int, default=300)
    parser.add_argument("--expect-repaired", action="store_true")
    args = parser.parse_args()

    runtime = args.runtime.resolve()
    sys.path.insert(0, str(runtime))
    gen = importlib.import_module(
        f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    )

    pairs = canonical_pairs(runtime)
    canonical_fit = [
        pair["output"] == empty_output_border(pair["input"]) for pair in pairs
    ]

    report: dict[str, Any] = {
        "schema": "xor-empty-border-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_version": getattr(gen, "VERSION", None),
        "runtime": str(runtime),
        "shortcut": "XOR occupancy, then force the complete output border to zero",
        "canonical_pairs": len(pairs),
        "canonical_pairs_fit": sum(canonical_fit),
        "canonical_fit_all": all(canonical_fit),
        "draws_per_band": args.draws,
        "lessons_per_band": args.lessons,
        "bands": {},
        "counterexample": None,
    }

    for band in BANDS:
        draw_stats = {
            "draws": args.draws,
            "border_counterexamples": 0,
            "shortcut_disagreements": 0,
            "canonical_like": 0,
        }
        for index in range(args.draws):
            seed = 70_000 + index
            sample_index = index * 17 + 3
            grid = gen.generate(seed, sample_index, difficulty=band)
            disagreement = empty_output_border(grid) != xor_output(grid)
            bx = border_xor(grid)
            draw_stats["border_counterexamples"] += int(bx > 0)
            draw_stats["shortcut_disagreements"] += int(disagreement)
            if hasattr(gen, "strict_canonical_like"):
                draw_stats["canonical_like"] += int(not gen.strict_canonical_like(grid))
            if disagreement and report["counterexample"] is None:
                report["counterexample"] = {
                    "band": band,
                    "seed": seed,
                    "sample_index": sample_index,
                    "input": grid,
                    "intended_output": xor_output(grid),
                    "shortcut_output": empty_output_border(grid),
                    "border_xor": bx,
                }

        lesson_stats = {
            "lessons": args.lessons,
            "shortcut_survives_both_demos": 0,
            "dangerous_query_disagreement": 0,
        }
        for lesson_index in range(args.lessons):
            seed = 90_000 + lesson_index
            start = lesson_index % 20
            demos = [
                gen.generate(seed, start + offset, difficulty=band)
                for offset in (0, 1)
            ]
            query = gen.generate(seed, start + 2, difficulty=band)
            survives = all(
                empty_output_border(grid) == xor_output(grid) for grid in demos
            )
            dangerous = survives and empty_output_border(query) != xor_output(query)
            lesson_stats["shortcut_survives_both_demos"] += int(survives)
            lesson_stats["dangerous_query_disagreement"] += int(dangerous)

        report["bands"][band] = {
            "draw_census": draw_stats,
            "two_demo_lesson_census": lesson_stats,
        }

    if hasattr(gen, "schedule_profile"):
        schedule_checks = []
        for seed in range(50):
            profiles = [gen.schedule_profile(seed, i) for i in range(20)]
            schedule_checks.append(
                {
                    "seed": seed,
                    "canonical_count": profiles.count("canonical"),
                    "has_adjacent_canonical": any(
                        a == b == "canonical"
                        for a, b in zip(profiles + profiles[:1], profiles[1:] + profiles[:1])
                    ),
                }
            )
        report["schedule"] = {
            "checked_seeds": len(schedule_checks),
            "all_nine_of_twenty": all(
                row["canonical_count"] == 9 for row in schedule_checks
            ),
            "no_adjacent_canonical": not any(
                row["has_adjacent_canonical"] for row in schedule_checks
            ),
        }

    failures: list[str] = []
    if not report["canonical_fit_all"]:
        failures.append("shortcut did not fit every canonical pair")
    if report["counterexample"] is None:
        failures.append("generator emitted no shortcut counterexample")
    if args.expect_repaired:
        for band, band_report in report["bands"].items():
            lesson = band_report["two_demo_lesson_census"]
            if lesson["shortcut_survives_both_demos"]:
                failures.append(
                    f"{band}: shortcut survived {lesson['shortcut_survives_both_demos']} repaired lessons"
                )
            if lesson["dangerous_query_disagreement"]:
                failures.append(
                    f"{band}: {lesson['dangerous_query_disagreement']} dangerous repaired lessons"
                )
        schedule = report.get("schedule", {})
        if not schedule.get("all_nine_of_twenty"):
            failures.append("repaired schedule is not exactly 9/20 canonical")
        if not schedule.get("no_adjacent_canonical"):
            failures.append("repaired schedule has adjacent canonical slots")

    report["passed"] = not failures
    report["failures"] = failures
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
