#!/usr/bin/env python3
"""Search edge-local Boolean shortcuts for task 1ce259f214c8.

Each competitor agrees with occupancy XOR except on one output-border region,
where it substitutes a simpler Boolean operation.  All listed regions are blank
in the canonical examples, so many such rules fit every public pair.  The probe
measures whether a two-demonstration generated lesson refutes each competitor
before its query can expose the mistake.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable

TASK_ID = "1ce259f214c8"
BANDS = ("easy", "medium", "hard")
Cell = tuple[int, int]
Mask = set[Cell]
Operation = Callable[[Mask, Mask], Mask]


def _masks(grid: list[list[int]]) -> tuple[Mask, Mask, int, int]:
    h = len(grid)
    half = (len(grid[0]) - 1) // 2
    left = {(r, c) for r in range(h) for c in range(half) if grid[r][c] != 0}
    right = {
        (r, c - half - 1)
        for r in range(h)
        for c in range(half + 1, 2 * half + 1)
        if grid[r][c] != 0
    }
    return left, right, h, half


def _output(mask: Mask, h: int, half: int) -> list[list[int]]:
    return [[8 if (r, c) in mask else 0 for c in range(half)] for r in range(h)]


def _xor_output(grid: list[list[int]]) -> list[list[int]]:
    left, right, h, half = _masks(grid)
    return _output(left ^ right, h, half)


OPERATIONS: dict[str, Operation] = {
    "zero": lambda left, right: set(),
    "or": lambda left, right: left | right,
    "and": lambda left, right: left & right,
    "left": lambda left, right: set(left),
    "right": lambda left, right: set(right),
    "left_minus_right": lambda left, right: left - right,
    "right_minus_left": lambda left, right: right - left,
}


def _regions(h: int, half: int) -> dict[str, set[Cell]]:
    top = {(0, c) for c in range(half)}
    bottom = {(h - 1, c) for c in range(half)}
    left_edge = {(r, 0) for r in range(h)}
    right_edge = {(r, half - 1) for r in range(h)}
    corners = {
        (0, 0),
        (0, half - 1),
        (h - 1, 0),
        (h - 1, half - 1),
    }
    return {
        "border": top | bottom | left_edge | right_edge,
        "top": top,
        "bottom": bottom,
        "left_edge": left_edge,
        "right_edge": right_edge,
        "corners": corners,
        "top_left": {(0, 0)},
        "top_right": {(0, half - 1)},
        "bottom_left": {(h - 1, 0)},
        "bottom_right": {(h - 1, half - 1)},
    }


def _regional_output(
    grid: list[list[int]], region_name: str, operation_name: str
) -> list[list[int]]:
    left, right, h, half = _masks(grid)
    region = _regions(h, half)[region_name]
    intended = left ^ right
    alternate = OPERATIONS[operation_name](left, right)
    mask = (intended - region) | (alternate & region)
    return _output(mask, h, half)


def _canonical_pairs(runtime: Path) -> list[dict[str, Any]]:
    ledger = runtime / "data/canonical/puzzles.jsonl"
    for line in ledger.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
            return [*row["train"], *tests]
    raise RuntimeError(f"canonical task {TASK_ID} not found in {ledger}")


def _relation_counts_by_region(grid: list[list[int]]) -> dict[str, dict[str, int]]:
    left, right, h, half = _masks(grid)
    relation_masks = {
        "left_only": left - right,
        "right_only": right - left,
        "overlap": left & right,
    }
    return {
        region_name: {
            relation_name: len(region & relation_mask)
            for relation_name, relation_mask in relation_masks.items()
        }
        for region_name, region in _regions(h, half).items()
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--lessons", type=int, default=1000)
    parser.add_argument("--draws", type=int, default=1000)
    parser.add_argument(
        "--demos", type=int, default=None,
        help="demonstrations per lesson; defaults to generator EXAMPLES_NEEDED",
    )
    parser.add_argument("--expect-repaired", action="store_true")
    args = parser.parse_args()

    runtime = args.runtime.resolve()
    sys.path.insert(0, str(runtime))
    gen = importlib.import_module(
        f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    )

    pairs = _canonical_pairs(runtime)
    demos_per_lesson = (
        int(args.demos)
        if args.demos is not None
        else int(getattr(gen, "EXAMPLES_NEEDED", 2))
    )
    if demos_per_lesson < 1:
        raise ValueError("--demos must be at least 1")
    candidate_names = [
        f"{region}:{operation}"
        for region in _regions(5, 5)
        for operation in OPERATIONS
    ]
    canonical_fit: dict[str, int] = {}
    for name in candidate_names:
        region, operation = name.split(":", 1)
        canonical_fit[name] = sum(
            pair["output"] == _regional_output(pair["input"], region, operation)
            for pair in pairs
        )
    compatible = [name for name in candidate_names if canonical_fit[name] == len(pairs)]

    report: dict[str, Any] = {
        "schema": "xor-regional-shortcut-probe-v2",
        "task_id": TASK_ID,
        "generator_version": getattr(gen, "VERSION", None),
        "runtime": str(runtime),
        "canonical_pairs": len(pairs),
        "candidate_count": len(candidate_names),
        "canonical_compatible_count": len(compatible),
        "canonical_compatible": compatible,
        "draws_per_band": args.draws,
        "lessons_per_band": args.lessons,
        "demos_per_lesson": demos_per_lesson,
        "bands": {},
    }

    for band in BANDS:
        relation_presence: dict[str, Counter[str]] = {
            region: Counter() for region in _regions(5, 5)
        }
        generalized_draws = 0
        for index in range(args.draws):
            seed = 310_000 + index
            sample_index = (index * 37 + 11) % 20
            grid = gen.generate(seed, sample_index, difficulty=band)
            profile = (
                gen.schedule_profile(seed, sample_index, difficulty=band)
                if hasattr(gen, "schedule_profile")
                else "unknown"
            )
            if profile != "generalized":
                continue
            generalized_draws += 1
            counts = _relation_counts_by_region(grid)
            for region, region_counts in counts.items():
                for relation, count in region_counts.items():
                    if count:
                        relation_presence[region][relation] += 1
                if all(region_counts.values()):
                    relation_presence[region]["all_three"] += 1

        stats = {
            name: {
                "survives_all_demos": 0,
                "dangerous_query_disagreement": 0,
                "query_disagreement": 0,
                "first_dangerous_case": None,
            }
            for name in compatible
        }
        for lesson_index in range(args.lessons):
            seed = 510_000 + lesson_index
            start = lesson_index % 20
            demos = [
                gen.generate(seed, start + offset, difficulty=band)
                for offset in range(demos_per_lesson)
            ]
            query = gen.generate(
                seed, start + demos_per_lesson, difficulty=band
            )
            intended_demos = [_xor_output(grid) for grid in demos]
            intended_query = _xor_output(query)
            for name in compatible:
                region, operation = name.split(":", 1)
                survives = all(
                    _regional_output(grid, region, operation) == intended
                    for grid, intended in zip(demos, intended_demos)
                )
                disagrees = (
                    _regional_output(query, region, operation) != intended_query
                )
                dangerous = survives and disagrees
                row = stats[name]
                row["survives_all_demos"] += int(survives)
                row["query_disagreement"] += int(disagrees)
                row["dangerous_query_disagreement"] += int(dangerous)
                if dangerous and row["first_dangerous_case"] is None:
                    row["first_dangerous_case"] = {
                        "seed": seed,
                        "start": start,
                        "demo_profiles": [
                            gen.schedule_profile(seed, start + offset, difficulty=band)
                            if hasattr(gen, "schedule_profile")
                            else None
                            for offset in range(demos_per_lesson)
                        ],
                        "query_profile": (
                            gen.schedule_profile(
                                seed, start + demos_per_lesson, difficulty=band
                            )
                            if hasattr(gen, "schedule_profile")
                            else None
                        ),
                    }

        ordered = sorted(
            stats.items(),
            key=lambda item: (
                -item[1]["dangerous_query_disagreement"],
                -item[1]["survives_all_demos"],
                item[0],
            ),
        )
        report["bands"][band] = {
            "generalized_draws_in_census": generalized_draws,
            "regional_relation_presence": {
                region: dict(counter) for region, counter in relation_presence.items()
            },
            "competitors": dict(ordered),
            "worst_ten": [
                {"name": name, **row} for name, row in ordered[:10]
            ],
            "competitors_with_dangerous_lessons": sum(
                row["dangerous_query_disagreement"] > 0 for row in stats.values()
            ),
            "max_dangerous_query_disagreement": max(
                (row["dangerous_query_disagreement"] for row in stats.values()),
                default=0,
            ),
        }

    failures: list[str] = []
    if not compatible:
        failures.append("no regional competitor fits every canonical pair")
    if args.expect_repaired:
        for band, band_report in report["bands"].items():
            dangerous = band_report["competitors_with_dangerous_lessons"]
            if dangerous:
                failures.append(
                    f"{band}: {dangerous} regional competitors survive demos and fail a query"
                )
    report["passed"] = not failures
    report["failures"] = failures

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
