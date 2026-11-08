"""Independent task-local analysis/oracles for 4c04ce6c5477 review tests.

This module deliberately does not import implementation helpers from generator.py.
It gives future reviewers a compact way to inspect object measurements, canonical
pairs, and plausible shortcut outputs.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Any

TASK_ROOT = Path(__file__).resolve().parents[1]


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or TASK_ROOT / "generator.py")
    spec = importlib.util.spec_from_file_location("generator_under_test", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _decode(rows: list[str]) -> list[list[int]]:
    return [[int(value) for value in row] for row in rows]


def canonical_pairs() -> list[dict[str, list[list[int]]]]:
    """Canonical train pairs plus the verified test pair, compactly embedded."""
    return [
        {
            "input": _decode([
                "00000000000",
                "02200333000",
                "02200333000",
                "02200000000",
                "00000000440",
                "00000000000",
                "00000000000",
            ]),
            "output": _decode(["234"]),
        },
        {
            "input": _decode([
                "000000000700",
                "000022000700",
                "550022000700",
                "550000000000",
                "550000000000",
                "550000000000",
                "000000000000",
                "000000000000",
            ]),
            "output": _decode(["572"]),
        },
        {
            "input": _decode([
                "000000009990",
                "066600009990",
                "066600009990",
                "000003000000",
                "000003000000",
                "000003000000",
                "000003000000",
                "000000000000",
            ]),
            "output": _decode(["396"]),
        },
    ]


def analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty row sequence"], "components": []}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["grid must have nonempty rows"], "components": []}
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"], "components": []}
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return {"errors": ["cells must be integer ARC colors 0..9"], "components": []}

    height = len(grid)
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            colors: set[int] = set()
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                colors.add(grid[r][c])
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
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            components.append(
                {
                    "cells": tuple(sorted(cells)),
                    "colors": tuple(sorted(colors)),
                    "color": min(colors),
                    "area": len(cells),
                    "top": min(rows),
                    "bottom": max(rows),
                    "left": min(cols),
                    "right": max(cols),
                    "height": max(rows) - min(rows) + 1,
                    "width": max(cols) - min(cols) + 1,
                }
            )
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "components": components,
    }


def _row(objects: list[dict[str, Any]]) -> list[list[int]]:
    return [[obj["color"] for obj in objects]]


def height_output(grid: Any) -> list[list[int]]:
    facts = analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return _row(
        sorted(
            facts["components"],
            key=lambda obj: (-obj["height"], obj["left"], obj["color"]),
        )
    )


def area_output(grid: Any) -> list[list[int]]:
    facts = analyze(grid)
    return _row(
        sorted(
            facts["components"],
            key=lambda obj: (-obj["area"], obj["left"], obj["color"]),
        )
    )


def left_to_right_output(grid: Any) -> list[list[int]]:
    facts = analyze(grid)
    return _row(sorted(facts["components"], key=lambda obj: (obj["left"], obj["color"])))


def top_to_bottom_output(grid: Any) -> list[list[int]]:
    facts = analyze(grid)
    return _row(
        sorted(
            facts["components"],
            key=lambda obj: (obj["top"], obj["left"], obj["color"]),
        )
    )


def numeric_color_output(grid: Any) -> list[list[int]]:
    facts = analyze(grid)
    return _row(sorted(facts["components"], key=lambda obj: obj["color"]))


def observed(grid: Any) -> dict[str, int]:
    facts = analyze(grid)
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "n_blobs": len(facts["components"]),
    }
