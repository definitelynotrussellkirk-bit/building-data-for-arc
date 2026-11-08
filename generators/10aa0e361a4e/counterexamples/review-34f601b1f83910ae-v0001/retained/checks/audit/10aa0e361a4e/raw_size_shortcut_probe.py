#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Iterable

from reviewer_support import canonical_pairs

TASK_ID = "10aa0e361a4e"
ROOT = Path(__file__).resolve().parents[3] / "repo"
SOURCE = ROOT / f"generators/{TASK_ID}/generator.py"


def load_source():
    spec = importlib.util.spec_from_file_location("audit_10aa", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            component: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                component.append(current)
                r, c = current
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            found.append(component)
    return found


def grown_cells(component: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    return {
        (row + dr, col + dc)
        for row, col in component
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
    }


def render(component: list[tuple[int, int]]) -> list[list[int]]:
    grown = grown_cells(component)
    min_row = min(row for row, _ in grown)
    max_row = max(row for row, _ in grown)
    min_col = min(col for _, col in grown)
    max_col = max(col for _, col in grown)
    output = [[0] * (max_col - min_col + 1) for _ in range(max_row - min_row + 1)]
    for row, col in grown:
        output[row - min_row][col - min_col] = 8
    return output


def official_output(grid: list[list[int]]) -> list[list[int]]:
    objects = components(grid)
    winner = max(range(len(objects)), key=lambda index: len(grown_cells(objects[index])))
    return render(objects[winner])


def raw_size_output(grid: list[list[int]]) -> list[list[int]]:
    objects = components(grid)
    winner = max(range(len(objects)), key=lambda index: len(objects[index]))
    return render(objects[winner])


def describe(grid: list[list[int]]) -> dict:
    objects = components(grid)
    grown = [len(grown_cells(obj)) for obj in objects]
    raw = [len(obj) for obj in objects]
    return {
        "raw_sizes_scan_order": raw,
        "grown_sizes_scan_order": grown,
        "official_winner_index": max(range(len(objects)), key=lambda i: grown[i]),
        "raw_size_winner_index": max(range(len(objects)), key=lambda i: raw[i]),
    }


def main() -> int:
    module = load_source()
    canonical = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    report = {
        "task_id": TASK_ID,
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "rule_checked_against_canonical": all(
            official_output(pair["input"]) == pair["output"] for pair in canonical
        ),
        "raw_size_shortcut_fits_all_canonical": all(
            raw_size_output(pair["input"]) == pair["output"] for pair in canonical
        ),
        "lessons_per_band": 1000,
        "pairs_per_lesson": 4,
        "query_rotation_policy": "hold out each of four pairs; other three are demonstrations",
        "bands": {},
        "first_teaching_failure": None,
    }
    for band_index, band in enumerate(("easy", "medium", "hard")):
        stats = {
            "lessons": 1000,
            "generated_pairs": 0,
            "generation_errors": 0,
            "raw_shortcut_pair_disagreements": 0,
            "teaching_failures_across_query_rotations": 0,
            "lessons_with_at_least_one_teaching_failure": 0,
        }
        for lesson_index in range(1000):
            seed = 990000 + band_index * 100000 + lesson_index
            grids = []
            try:
                for slot in range(4):
                    grids.append(
                        module.generate(seed, lesson_index * 4 + slot, difficulty=band)
                    )
            except Exception:
                stats["generation_errors"] += 1
                continue
            official = [official_output(grid) for grid in grids]
            shortcut = [raw_size_output(grid) for grid in grids]
            stats["generated_pairs"] += 4
            stats["raw_shortcut_pair_disagreements"] += sum(
                predicted != label for predicted, label in zip(shortcut, official)
            )
            lesson_failed = False
            for query_index in range(4):
                demo_indexes = [index for index in range(4) if index != query_index]
                if all(shortcut[index] == official[index] for index in demo_indexes) and (
                    shortcut[query_index] != official[query_index]
                ):
                    stats["teaching_failures_across_query_rotations"] += 1
                    lesson_failed = True
                    if report["first_teaching_failure"] is None:
                        report["first_teaching_failure"] = {
                            "band": band,
                            "seed": seed,
                            "sample_indexes": [lesson_index * 4 + slot for slot in range(4)],
                            "query_index": query_index,
                            "demo_indexes": demo_indexes,
                            "pair_descriptions": [describe(grid) for grid in grids],
                            "inputs": grids,
                            "official_outputs": official,
                            "raw_size_outputs": shortcut,
                        }
            stats["lessons_with_at_least_one_teaching_failure"] += int(lesson_failed)
        report["bands"][band] = stats
    report["summary"] = {
        key: sum(report["bands"][band][key] for band in report["bands"])
        for key in (
            "lessons",
            "generated_pairs",
            "generation_errors",
            "raw_shortcut_pair_disagreements",
            "teaching_failures_across_query_rotations",
            "lessons_with_at_least_one_teaching_failure",
        )
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
