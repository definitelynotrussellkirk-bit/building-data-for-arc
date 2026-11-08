#!/usr/bin/env python3
"""Independent adversarial probes for review-df404da564d3592d audit targets."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "repo/shared/runtime"
sys.path.insert(0, str(RUNTIME))


def load_generator(task_id: str):
    path = ROOT / f"repo/generators/{task_id}/generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def components(grid: list[list[int]], color: int | None = None):
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, list[tuple[int, int]]]] = []
    for row in range(h):
        for col in range(w):
            value = grid[row][col]
            if (color is not None and value != color) or (color is None and value == 0):
                continue
            if (row, col) in seen:
                continue
            todo = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while todo:
                r, c = todo.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == value
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            result.append((value, cells))
    return result


def perimeter(cells: Iterable[tuple[int, int]]) -> int:
    cell_set = set(cells)
    return sum(
        (r + dr, c + dc) not in cell_set
        for r, c in cell_set
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
    )


def perimeter_rule(grid: list[list[int]]) -> list[list[int]]:
    ranked = sorted(
        components(grid),
        key=lambda item: (-perimeter(item[1]), item[0]),
    )
    return [[color for color, _ in ranked]]


def area_rival(grid: list[list[int]]) -> list[list[int]]:
    ranked = sorted(components(grid), key=lambda item: (-len(item[1]), item[0]))
    return [[color for color, _ in ranked]]


def border_rule(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    output = [row[:] for row in grid]
    for _, cells in components(grid, 1):
        if any(r in (0, h - 1) or c in (0, w - 1) for r, c in cells):
            for r, c in cells:
                output[r][c] = 2
    return output


def horizontal_border_only_rival(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rival: recognize top/bottom contact but ignore left/right contact."""
    h = len(grid)
    output = [row[:] for row in grid]
    for _, cells in components(grid, 1):
        if any(r in (0, h - 1) for r, _ in cells):
            for r, c in cells:
                output[r][c] = 2
    return output


def scan_bd(lessons_per_band: int) -> dict:
    generator = load_generator("bd6bfb1f0c20")
    bands: dict[str, dict] = {}
    for band in ("easy", "medium", "hard"):
        surviving = 0
        exact_pair_matches = 0
        unique_inputs: set[str] = set()
        for lesson in range(lessons_per_band):
            lesson_matches = []
            for offset in range(4):
                sample_index = lesson * 4 + offset
                grid = generator.generate(0, sample_index, difficulty=band)
                encoded = json.dumps(grid, separators=(",", ":"))
                unique_inputs.add(encoded)
                actual = perimeter_rule(grid)
                rival = area_rival(grid)
                match = actual == rival
                lesson_matches.append(match)
                exact_pair_matches += int(match)
            surviving += int(all(lesson_matches))
        bands[band] = {
            "lessons": lessons_per_band,
            "demos_per_lesson": 4,
            "area_rival_survives_all_demos": surviving,
            "area_rival_survival_fraction": surviving / lessons_per_band,
            "matching_demo_pairs": exact_pair_matches,
            "demo_pairs": lessons_per_band * 4,
            "unique_inputs": len(unique_inputs),
            "seed": 0,
            "sample_indices": [0, lessons_per_band * 4 - 1],
        }
    return {"task_id": "bd6bfb1f0c20", "bands": bands}


def scan_dcf(samples_per_band: int) -> dict:
    generator = load_generator("dcf954423fbb")
    bands: dict[str, dict] = {}
    for band in ("easy", "medium", "hard"):
        rival_matches = 0
        unique_inputs: set[str] = set()
        touched_sides = {"top": 0, "bottom": 0, "left": 0, "right": 0}
        for sample_index in range(samples_per_band):
            grid = generator.generate(0, sample_index, difficulty=band)
            unique_inputs.add(json.dumps(grid, separators=(",", ":")))
            rival_matches += int(border_rule(grid) == horizontal_border_only_rival(grid))
            h, w = len(grid), len(grid[0])
            for _, cells in components(grid, 1):
                touched_sides["top"] += int(any(r == 0 for r, _ in cells))
                touched_sides["bottom"] += int(any(r == h - 1 for r, _ in cells))
                touched_sides["left"] += int(any(c == 0 for _, c in cells))
                touched_sides["right"] += int(any(c == w - 1 for _, c in cells))
        bands[band] = {
            "samples": samples_per_band,
            "horizontal_border_only_rival_matches": rival_matches,
            "horizontal_border_only_rival_match_fraction": rival_matches / samples_per_band,
            "unique_inputs": len(unique_inputs),
            "seed": 0,
            "sample_indices": [0, samples_per_band - 1],
            "border_side_touch_counts_across_components": touched_sides,
        }
    return {"task_id": "dcf954423fbb", "bands": bands}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bd-lessons", type=int, default=100)
    parser.add_argument("--dcf-samples", type=int, default=1000)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = {
        "schema": "review-audit-probe-v1",
        "bd": scan_bd(args.bd_lessons),
        "dcf": scan_dcf(args.dcf_samples),
    }
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
