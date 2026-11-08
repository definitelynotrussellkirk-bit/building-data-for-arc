#!/usr/bin/env python3
"""Independent feature-triple and shortcut probe for ARC task 71fd3c801ee1.

Input JSON may be a grid directly, ``{"input": grid}``, or a list of either.
The report lists every nonzero 4-connected object, its normalized outline and
(area, enclosed holes, reflection-symmetry class), then compares the complete
rule with four plausible shortcuts.  This module intentionally does not import
the production generator, so it can expose generator/mirror mistakes.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Iterable

Cell = tuple[int, int]
Shape = tuple[Cell, ...]
Triple = tuple[int, int, int]


def normalize(cells: Iterable[Cell]) -> Shape:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def feature_triple(cells: Iterable[Cell]) -> Triple:
    shape = set(normalize(cells))
    height = max(r for r, _ in shape) + 1
    width = max(c for _, c in shape) + 1
    seen: set[Cell] = set()
    holes = 0
    for r0 in range(height):
        for c0 in range(width):
            if (r0, c0) in shape or (r0, c0) in seen:
                continue
            region: list[Cell] = []
            stack = [(r0, c0)]
            seen.add((r0, c0))
            while stack:
                r, c = stack.pop()
                region.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = (r + dr, c + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in shape
                        and nxt not in seen
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            if all(0 < r < height - 1 and 0 < c < width - 1 for r, c in region):
                holes += 1
    row_sym = all((height - 1 - r, c) in shape for r, c in shape)
    col_sym = all((r, width - 1 - c) in shape for r, c in shape)
    symmetry = 3 if row_sym and col_sym else 1 if row_sym else 2 if col_sym else 0
    return (len(shape), holes, symmetry)


def components(grid: list[list[int]]) -> list[dict[str, Any]]:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("expected a nonempty rectangular grid")
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    result: list[dict[str, Any]] = []
    for r0 in range(height):
        for c0 in range(width):
            if grid[r0][c0] == 0 or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells: list[Cell] = []
            colors: set[int] = set()
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                colors.add(grid[r][c])
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = (r + dr, c + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] != 0
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            shape = normalize(cells)
            result.append(
                {
                    "color": next(iter(colors)) if len(colors) == 1 else None,
                    "colors": sorted(colors),
                    "cells": sorted(cells),
                    "shape": shape,
                    "triple": feature_triple(shape),
                }
            )
    return result


def recolor(grid: list[list[int]], key: Callable[[dict[str, Any]], Any]) -> list[list[int]]:
    objects = components(grid)
    keys = [key(obj) for obj in objects]
    counts = Counter(keys)
    output = [row[:] for row in grid]
    for obj, value in zip(objects, keys):
        if counts[value] > 1:
            for r, c in obj["cells"]:
                output[r][c] = 8
    return output


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    objects = components(grid)
    rules = {
        "complete_triple": lambda obj: obj["triple"],
        "exact_shape": lambda obj: obj["shape"],
        "same_area": lambda obj: obj["triple"][0],
        "same_area_and_holes": lambda obj: obj["triple"][:2],
        "same_area_and_symmetry": lambda obj: (obj["triple"][0], obj["triple"][2]),
    }
    outputs = {name: recolor(grid, key) for name, key in rules.items()}
    truth = outputs["complete_triple"]
    return {
        "shape": [len(grid), len(grid[0])],
        "palette": sorted({value for row in grid for value in row}),
        "objects": [
            {
                "color": obj["color"],
                "colors": obj["colors"],
                "cells": [list(cell) for cell in obj["cells"]],
                "shape": [list(cell) for cell in obj["shape"]],
                "triple": list(obj["triple"]),
            }
            for obj in objects
        ],
        "outputs": outputs,
        "rival_disagrees": {
            name: output != truth
            for name, output in outputs.items()
            if name != "complete_triple"
        },
    }


def _extract_grids(payload: Any) -> list[list[list[int]]]:
    if isinstance(payload, dict) and "input" in payload:
        return [payload["input"]]
    if isinstance(payload, list) and payload and isinstance(payload[0], list):
        if payload[0] and isinstance(payload[0][0], int):
            return [payload]
        grids = []
        for item in payload:
            if isinstance(item, dict) and "input" in item:
                grids.append(item["input"])
            else:
                grids.append(item)
        return grids
    raise ValueError("JSON must be a grid, an {'input': grid} object, or a list")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON grid or list of grids")
    parser.add_argument("--out", type=Path, help="write report JSON here")
    args = parser.parse_args()
    grids = _extract_grids(json.loads(args.input.read_text(encoding="utf-8")))
    report = {"count": len(grids), "reports": [analyze(grid) for grid in grids]}
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
