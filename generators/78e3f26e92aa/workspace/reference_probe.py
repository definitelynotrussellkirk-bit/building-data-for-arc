"""Independent structural oracle and reusable diagnostics for 78e3f26e92aa.

Canonical Racket remains the label authority.  This module intentionally does
not import production parsing or rule helpers, so it can catch a generator and
its self-check agreeing on the same mistake.
"""
from __future__ import annotations

from collections import deque
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any

TASK_ID = "78e3f26e92aa"
HOME = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))
from reviewer_support import canonical_pairs as _canonical_pairs, find_root

_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


def load_generator(path: str | os.PathLike[str] | None = None):
    """Load the reviewed generator without relying on package installation."""
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or HOME / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_78e3f26e92aa", source)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    """Return all labeled canonical pairs across task variants and splits."""
    root = find_root(__file__)
    return _canonical_pairs(TASK_ID, root=root, labeled_only=True)


def validate_grid(grid) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty row sequence")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("rows must be non-empty sequences")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be literal ARC colors 0..9")
    return len(grid), width


def components(grid, color: int | None = None) -> list[dict[str, Any]]:
    """Parse same-color 4-connected components independently."""
    h, w = validate_grid(grid)
    unseen = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] != 0 and (color is None or grid[r][c] == color)
    }
    found: list[dict[str, Any]] = []
    while unseen:
        start = min(unseen)
        component_color = grid[start[0]][start[1]]
        unseen.remove(start)
        queue = deque([start])
        cells = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARDINAL:
                point = (r + dr, c + dc)
                if point in unseen and grid[point[0]][point[1]] == component_color:
                    unseen.remove(point)
                    queue.append(point)
                    cells.add(point)
        r1, r2 = min(r for r, _ in cells), max(r for r, _ in cells)
        c1, c2 = min(c for _, c in cells), max(c for _, c in cells)
        found.append(
            {
                "color": component_color,
                "cells": frozenset(cells),
                "bbox": (r1, c1, r2, c2),
                "height": r2 - r1 + 1,
                "width": c2 - c1 + 1,
                "filled": len(cells) == (r2 - r1 + 1) * (c2 - c1 + 1),
            }
        )
    return sorted(found, key=lambda item: (item["color"], item["bbox"]))


def pair_geometry(grid) -> dict[int, dict[str, Any]]:
    """Validate and describe the two equal-height vertical bars of each color."""
    h, w = validate_grid(grid)
    palette = {value for row in grid for value in row}
    if not palette <= {0, 3, 8}:
        raise ValueError(f"unexpected colors: {sorted(palette - {0, 3, 8})}")
    result: dict[int, dict[str, Any]] = {}
    for color in (3, 8):
        parts = components(grid, color)
        if len(parts) != 2:
            raise ValueError(f"color {color} must have exactly two components; found {len(parts)}")
        left, right = sorted(parts, key=lambda item: item["bbox"][1])
        for part in (left, right):
            if not part["filled"] or part["width"] != 1:
                raise ValueError(f"color {color} component is not a filled vertical bar: {part['bbox']}")
        if (left["bbox"][0], left["bbox"][2]) != (right["bbox"][0], right["bbox"][2]):
            raise ValueError(f"color {color} bars do not share their row span")
        inner_gap = right["bbox"][1] - left["bbox"][1] - 1
        if inner_gap < 1:
            raise ValueError(f"color {color} bars are not separated")
        result[color] = {
            "row1": left["bbox"][0],
            "row2": left["bbox"][2],
            "height": left["height"],
            "left_col": left["bbox"][1],
            "right_col": right["bbox"][1],
            "inner_gap": inner_gap,
        }
    result["shape"] = {"grid_h": h, "grid_w": w}  # type: ignore[index]
    return result


def _bbox_for_color(grid, color: int) -> tuple[int, int, int, int]:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
    if not cells:
        raise ValueError(f"color {color} is absent")
    r1, r2 = min(r for r, _ in cells), max(r for r, _ in cells)
    c1, c2 = min(c for _, c in cells), max(c for _, c in cells)
    return r1, r2 - r1 + 1, c1, c2


def _reaches(bar: tuple[int, int, int, int], r: int, c: int) -> bool:
    r1, bar_height, left_col, right_col = bar
    dr = r - r1
    step = dr // bar_height if dr >= 0 else ((-dr + bar_height - 1) // bar_height)
    return c == left_col - step or c == right_col + step


def geometry_output(grid) -> list[list[int]]:
    """Independent Python transcription of the canonical Racket geometry."""
    h, w = validate_grid(grid)
    green = _bbox_for_color(grid, 3)
    cyan = _bbox_for_color(grid, 8)
    output = [[0 for _ in range(w)] for _ in range(h)]
    for r in range(h):
        for c in range(w):
            has_green = _reaches(green, r, c)
            has_cyan = _reaches(cyan, r, c)
            output[r][c] = 6 if has_green and has_cyan else 3 if has_green else 8 if has_cyan else 0
    return output


def observed(grid) -> dict[str, Any]:
    geometry = pair_geometry(grid)
    green = geometry[3]
    cyan = geometry[8]
    green_above = green["row2"] < cyan["row1"]
    cyan_above = cyan["row2"] < green["row1"]
    if not (green_above or cyan_above):
        raise ValueError("color-pair row spans overlap")
    upper, lower = (green, cyan) if green_above else (cyan, green)
    output = geometry_output(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "green_height": green["height"],
        "green_gap": green["inner_gap"],
        "cyan_height": cyan["height"],
        "cyan_gap": cyan["inner_gap"],
        "vertical_gap": lower["row1"] - upper["row2"] - 1,
        "color_order": "green_above" if green_above else "cyan_above",
        "component_count": len(components(grid)),
        "magenta_count": sum(value == 6 for row in output for value in row),
    }


def report(generator=None, *, seed: int = 0, count: int = 12) -> dict[str, Any]:
    """Produce a compact canonical/generated structural report for future agents."""
    generator = generator or load_generator()
    canonical = [observed(pair["input"]) for pair in canonical_pairs()]
    generated = []
    for difficulty in ("easy", "medium", "hard"):
        for index in range(count):
            grid = generator.generate(seed, index, difficulty=difficulty)
            generated.append({"difficulty": difficulty, "sample_index": index, **observed(grid)})
    return {"task_id": TASK_ID, "canonical": canonical, "generated": generated}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", help="optional generator.py path")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--count", type=int, default=12)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    payload = report(load_generator(args.generator), seed=args.seed, count=args.count)
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
