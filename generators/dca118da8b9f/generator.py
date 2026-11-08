"""Generator for rectangle-corners-only task ``dca118da8b9f``.

Each returned scene contains two or three separated, solid, single-color
rectangles on a black background.  The target rule clears the scene and paints
only the four bounding-box corners of every rectangle cyan (8).
"""
from __future__ import annotations

from collections import deque
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dca118da8b9f"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "c15061e4149b"
SUMMARY = (
    "Find each separated solid rectangle, clear the input, and paint exactly "
    "the rectangle's four bounding-box corners cyan (8). Generated rectangles "
    "span the demonstrated 2..4 side lengths but exclude 2x2 identity cases."
)
INVARIANTS = [
    "background is black (0) and rectangle colors are distinct",
    "there are exactly two or three solid rectangles",
    "each side length is 2..4 and no rectangle is 2x2",
    "rectangles have at least one full background cell of separation",
    "the official output contains exactly four cyan corners per rectangle",
]

CANVAS_SIZES = {
    "compact": (9, 11),
    "standard": (11, 13),
    "large": (14, 16),
}
PALETTE_POOLS = {
    "low": (1, 2, 3, 4),
    "high": (5, 6, 7, 9),
}
SCENE_SHAPES = {
    # Two-object branch, including the square-only easy case.
    "two_square_3x3_4x4": ((3, 3), (4, 4)),
    # Directly covers the canonical thin-wide 2x4 rectangle.
    "two_public_2x4_3x3": ((2, 4), (3, 3)),
    "three_public_2x4_3x3x2": ((2, 4), (3, 3), (3, 3)),
    # D4 counterpart of the thin canonical branch plus a second non-square.
    "three_rotated_4x2_3x3_4x3": ((4, 2), (3, 3), (4, 3)),
    # No square cue: every object still requires bbox-corner extraction.
    "three_nonsquare_2x3_3x4_4x2": ((2, 3), (3, 4), (4, 2)),
    # Largest demonstrated side lengths and mixed square/non-square bodies.
    "three_full_2x4_4x3_4x4": ((2, 4), (4, 3), (4, 4)),
}
SCENE_PROFILES = tuple(SCENE_SHAPES)
CANVAS_PROFILES = tuple(CANVAS_SIZES)
PALETTE_BANDS = tuple(PALETTE_POOLS)

_BAND_SCENES = {
    "easy": (
        "two_square_3x3_4x4",
        "two_square_3x3_4x4",
        "two_public_2x4_3x3",
        "two_public_2x4_3x3",
    ),
    "medium": (
        "three_public_2x4_3x3x2",
        "three_public_2x4_3x3x2",
        "three_rotated_4x2_3x3_4x3",
        "three_rotated_4x2_3x3_4x3",
    ),
    "hard": (
        "three_nonsquare_2x3_3x4_4x2",
        "three_nonsquare_2x3_3x4_4x2",
        "three_full_2x4_4x3_4x4",
        "three_full_2x4_4x3_4x4",
    ),
    "all": SCENE_PROFILES,
}
_BAND_CANVASES = {
    "easy": ("compact", "compact", "standard"),
    "medium": ("compact", "standard", "standard", "large"),
    "hard": ("standard", "large", "large"),
    "all": CANVAS_PROFILES,
}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted linked rectangle-shape profile",
        "valid": (
            "two_square_3x3_4x4|two_public_2x4_3x3|"
            "three_public_2x4_3x3x2|three_rotated_4x2_3x3_4x3|"
            "three_nonsquare_2x3_3x4_4x2|three_full_2x4_4x3_4x4"
        ),
        "doc": "Exact multiset of rectangle heights and widths.",
    },
    "canvas_profile": {
        "type": "str",
        "default": "difficulty-weighted compact|standard|large canvas",
        "valid": "compact|standard|large",
        "doc": "Exact returned grid dimensions.",
    },
    "palette_band": {
        "type": "str",
        "default": "rng low|high",
        "valid": "low|high",
        "doc": "All rectangle colors come from one disjoint four-color pool.",
    },
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, non-degenerate rectangle lesson input."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    if isinstance(difficulty, str) and difficulty not in {
        "easy", "medium", "hard"
    }:
        raise ValueError(f"invalid difficulty: {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty if difficulty in {"easy", "medium", "hard"} else "all"
    scene_options = (
        SCENE_PROFILES
        if overrides.get("scene_profile") is not None
        else _BAND_SCENES[band]
    )
    canvas_options = (
        CANVAS_PROFILES
        if overrides.get("canvas_profile") is not None
        else _BAND_CANVASES[band]
    )
    scene_profile = ctx.draw_choice("scene_profile", scene_options)
    canvas_profile = ctx.draw_choice("canvas_profile", canvas_options)
    palette_band = ctx.draw_choice("palette_band", PALETTE_BANDS)

    height, width = CANVAS_SIZES[canvas_profile]
    shapes = SCENE_SHAPES[scene_profile]
    colors = ctx.draw_rng("colors").sample(
        list(PALETTE_POOLS[palette_band]), len(shapes)
    )
    rectangles = _place_rectangles(
        height,
        width,
        shapes,
        ctx.draw_rng("layout"),
    )
    grid = full_grid(height, width, 0)
    for (r1, c1, r2, c2), color in zip(rectangles, colors):
        _paint_rectangle(grid, r1, c1, r2, c2, color)
    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructed invalid rectangle scene: {errors}")
    return grid


def solve_python(grid):
    """Independent Python mirror used only by focused tests and audits."""
    analysis = _analyze(grid)
    output = full_grid(analysis["height"], analysis["width"], 0)
    for component in analysis["components"]:
        r1, c1, r2, c2 = component["bbox"]
        for row, col in ((r1, c1), (r1, c2), (r2, c1), (r2, c2)):
            output[row][col] = 8
    return output


def self_check(grid, *, difficulty=None, meta=None):
    """Recognize the full generated grammar and all canonical task inputs."""
    try:
        _analyze(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def observe_overrides(grid):
    """Recover every exact declared semantic axis from a returned grid."""
    try:
        analysis = _analyze(grid)
    except (TypeError, ValueError):
        return {}
    observed = {}
    dims = (analysis["height"], analysis["width"])
    for name, size in CANVAS_SIZES.items():
        if size == dims:
            observed["canvas_profile"] = name
            break
    signature = tuple(sorted(component["shape"] for component in analysis["components"]))
    for name, shapes in SCENE_SHAPES.items():
        if tuple(sorted(shapes)) == signature:
            observed["scene_profile"] = name
            break
    colors = {component["color"] for component in analysis["components"]}
    for name, pool in PALETTE_POOLS.items():
        if colors <= set(pool):
            observed["palette_band"] = name
            break
    return observed


def _paint_rectangle(grid, r1, c1, r2, c2, color):
    for row in range(r1, r2 + 1):
        for col in range(c1, c2 + 1):
            grid[row][col] = color


def _separated(candidate, placed):
    r1, c1, r2, c2 = candidate
    for pr1, pc1, pr2, pc2 in placed:
        if not (
            r2 + 1 < pr1
            or pr2 + 1 < r1
            or c2 + 1 < pc1
            or pc2 + 1 < c1
        ):
            return False
    return True


def _place_rectangles(height, width, shapes, rng):
    """Backtrack over shuffled legal placements; no fallback may hide an axis."""
    ordered = list(enumerate(shapes))
    rng.shuffle(ordered)
    ordered.sort(key=lambda item: item[1][0] * item[1][1], reverse=True)
    result = [None] * len(shapes)

    def search(index, placed):
        if index == len(ordered):
            return True
        original_index, (rect_h, rect_w) = ordered[index]
        candidates = [
            (row, col, row + rect_h - 1, col + rect_w - 1)
            for row in range(height - rect_h + 1)
            for col in range(width - rect_w + 1)
        ]
        rng.shuffle(candidates)
        for bbox in candidates:
            if not _separated(bbox, placed):
                continue
            result[original_index] = bbox
            if search(index + 1, placed + [bbox]):
                return True
        result[original_index] = None
        return False

    if not search(0, []):
        raise ValueError(
            f"scene shapes {shapes!r} do not fit separated in {height}x{width}"
        )
    return list(result)


def _coerce_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise TypeError("grid must be a nonempty rectangular sequence")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise TypeError("grid rows must be nonempty sequences")
    width = len(grid[0])
    if len(grid) > 30 or width > 30:
        raise ValueError("grid dimensions must be at most 30x30")
    converted = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            raise TypeError(f"row {row_index} must have width {width}")
        converted_row = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                raise ValueError("all cells must be integer ARC colors 0..9")
            converted_row.append(value)
        converted.append(converted_row)
    return converted


def _components4(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            start = (start_row, start_col)
            if color == 0 or start in seen:
                continue
            queue = deque([start])
            seen.add(start)
            cells = []
            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for delta_row, delta_col in (
                    (-1, 0), (0, -1), (0, 1), (1, 0)
                ):
                    candidate = (row + delta_row, col + delta_col)
                    if (
                        0 <= candidate[0] < height
                        and 0 <= candidate[1] < width
                        and candidate not in seen
                        and grid[candidate[0]][candidate[1]] == color
                    ):
                        seen.add(candidate)
                        queue.append(candidate)
            components.append((color, cells))
    return components


def _analyze(grid):
    normalized = _coerce_grid(grid)
    height, width = len(normalized), len(normalized[0])
    raw_components = _components4(normalized)
    if not 2 <= len(raw_components) <= 3:
        raise ValueError(
            f"expected exactly 2 or 3 rectangles, found {len(raw_components)}"
        )
    components = []
    for color, cells in raw_components:
        rows = [row for row, _col in cells]
        cols = [col for _row, col in cells]
        bbox = (min(rows), min(cols), max(rows), max(cols))
        r1, c1, r2, c2 = bbox
        rect_h, rect_w = r2 - r1 + 1, c2 - c1 + 1
        if len(cells) != rect_h * rect_w:
            raise ValueError(f"rectangle color {color} is not solid at {bbox}")
        if not (2 <= rect_h <= 4 and 2 <= rect_w <= 4):
            raise ValueError(
                f"rectangle color {color} has unsupported shape {(rect_h, rect_w)}"
            )
        if (rect_h, rect_w) == (2, 2):
            raise ValueError("2x2 rectangle would make corner extraction an identity")
        components.append(
            {
                "color": color,
                "cells": tuple(sorted(cells)),
                "bbox": bbox,
                "shape": (rect_h, rect_w),
            }
        )
    colors = [component["color"] for component in components]
    if len(set(colors)) != len(colors):
        raise ValueError("rectangle colors must be distinct")
    for left, right in combinations(components, 2):
        if not _separated(right["bbox"], [left["bbox"]]):
            raise ValueError(
                f"rectangles must have a one-cell background gap: "
                f"{left['bbox']} vs {right['bbox']}"
            )
    return {
        "height": height,
        "width": width,
        "components": sorted(components, key=lambda item: item["bbox"]),
    }
