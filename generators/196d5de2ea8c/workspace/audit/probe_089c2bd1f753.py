#!/usr/bin/env python3
"""Find a lesson where the largest-object shortcut survives the demonstrations.

This authoring probe uses only the portable public reviewer API.  It emits
candidate inputs and rival outputs; verify the intended outputs independently
with ``python3 -m arcpuzzles apply`` so the Racket authority stays explicit.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "089c2bd1f753"
BANDS = ("easy", "medium", "hard")


def components(grid: list[list[int]]) -> list[tuple[int, list[tuple[int, int]]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[tuple[int, list[tuple[int, int]]]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = (current[0] + delta_row, current[1] + delta_col)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            found.append((color, sorted(cells)))
    return found


def crop(color: int, cells: list[tuple[int, int]]) -> list[list[int]]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    top, bottom = min(rows), max(rows)
    left, right = min(cols), max(cols)
    result = [[0 for _ in range(right - left + 1)] for _ in range(bottom - top + 1)]
    for row, col in cells:
        result[row - top][col - left] = color
    return result


def marker_rule(grid: list[list[int]]) -> list[list[int]]:
    marker = grid[0][0]
    body = [row[:] for row in grid]
    body[0][0] = 0
    targets = [(color, cells) for color, cells in components(body) if color == marker]
    return [[0]] if not targets else crop(*targets[0])


def largest_object_rival(grid: list[list[int]]) -> list[list[int]]:
    body = [row[:] for row in grid]
    body[0][0] = 0
    objects = components(body)
    if not objects:
        return [[0]]
    maximum = max(len(cells) for _, cells in objects)
    return crop(*next(item for item in objects if len(item[1]) == maximum))


def object_summary(grid: list[list[int]]) -> list[dict[str, Any]]:
    body = [row[:] for row in grid]
    body[0][0] = 0
    return [
        {"color": color, "cells": len(cells), "first_cell": list(min(cells))}
        for color, cells in components(body)
    ]


def api_probe(label: str, call) -> dict[str, Any]:
    try:
        call()
        return {"case": label, "accepted": True}
    except Exception as exc:  # diagnostic: preserve the public API response
        return {
            "case": label,
            "accepted": False,
            "exception": type(exc).__name__,
            "message": str(exc),
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--lesson-seed", type=int, default=4)
    args = parser.parse_args()
    output_path = args.out.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    root = find_root(__file__)
    generator, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID, root=root
    )

    canonical = []
    for index, pair in enumerate(canonical_pairs(TASK_ID, root=root, labeled_only=True)):
        mirror = marker_rule(pair["input"])
        canonical.append(
            {
                "index": index,
                "marker_mirror_matches_label": mirror == pair["output"],
                "largest_rival_matches_label": largest_object_rival(pair["input"])
                == pair["output"],
            }
        )

    distribution: dict[str, dict[str, int]] = {}
    for band_index, band in enumerate(BANDS):
        counts: Counter[str] = Counter()
        for index in range(300):
            seed = 89000 + band_index * 1000 + index
            grid = generator.generate(seed, index, difficulty=band)
            truth = marker_rule(grid)
            rival = largest_object_rival(grid)
            counts["draws"] += 1
            counts["self_check_pass"] += not bool(generator.self_check(grid))
            counts["rival_matches"] += rival == truth
            counts["rival_differs"] += rival != truth
        distribution[band] = dict(counts)

    lesson = []
    for sample_index in range(4):
        grid = generator.generate(args.lesson_seed, sample_index, difficulty="medium")
        mirror_output = marker_rule(grid)
        rival_output = largest_object_rival(grid)
        lesson.append(
            {
                "seed": args.lesson_seed,
                "sample_index": sample_index,
                "difficulty": "medium",
                "input": grid,
                "marker_mirror_output": mirror_output,
                "largest_object_rival_output": rival_output,
                "rival_matches": rival_output == mirror_output,
                "marker": grid[0][0],
                "objects": object_summary(grid),
                "self_check": generator.self_check(grid),
            }
        )

    api_probes = [
        api_probe("unknown_override", lambda: generator.generate(1, 2, bogus=123)),
        api_probe("boolean_seed", lambda: generator.generate(True, 2)),
        api_probe("float_sample_index", lambda: generator.generate(1, 2.0)),
    ]
    report = {
        "schema": "assigned-audit-candidate-probe-v2",
        "task_id": TASK_ID,
        "generator_path": str(generator_path.resolve()),
        "generator_sha256": generator_sha256,
        "canonical": canonical,
        "ordinary_distribution_largest_object_rival": distribution,
        "teaching_counterexample": {
            "description": (
                "Three consecutive demonstrations are also explained by cropping "
                "the largest object, while the fourth query differs."
            ),
            "demos_fit": all(row["rival_matches"] for row in lesson[:3]),
            "query_differs": not lesson[3]["rival_matches"],
            "pairs": lesson,
            "racket_verification": (
                "Run arcpuzzles apply on the emitted inputs; this probe intentionally "
                "does not substitute a Python mirror for Racket authority."
            ),
        },
        "api_probes": api_probes,
        "command": [
            "python3",
            "generators/196d5de2ea8c/workspace/audit/probe_089c2bd1f753.py",
            "--out",
            str(args.out),
        ],
        "cwd": str(Path.cwd()),
    }
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    emitted = output_path.parent / "089c2bd1f753-counterexample"
    emitted.mkdir(parents=True, exist_ok=True)
    (emitted / "input.json").write_text(
        json.dumps([row["input"] for row in lesson], indent=2) + "\n"
    )
    (emitted / "largest_object_rival.json").write_text(
        json.dumps([row["largest_object_rival_output"] for row in lesson], indent=2)
        + "\n"
    )

    summary = {
        "out": str(output_path),
        "generator_sha256": generator_sha256,
        "canonical_marker_matches": sum(
            row["marker_mirror_matches_label"] for row in canonical
        ),
        "canonical_pairs": len(canonical),
        "canonical_largest_matches": sum(
            row["largest_rival_matches_label"] for row in canonical
        ),
        "distribution": distribution,
        "demos_fit": report["teaching_counterexample"]["demos_fit"],
        "query_differs": report["teaching_counterexample"]["query_differs"],
        "api_probes": api_probes,
        "emitted_inputs_sha256": hashlib.sha256(
            (emitted / "input.json").read_bytes()
        ).hexdigest(),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if (
        summary["canonical_marker_matches"] == summary["canonical_pairs"]
        and summary["demos_fit"]
        and summary["query_differs"]
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
