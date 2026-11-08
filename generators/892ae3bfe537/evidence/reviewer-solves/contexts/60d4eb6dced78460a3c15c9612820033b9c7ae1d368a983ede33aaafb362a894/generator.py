"""Generator for 892ae3bfe537 — fill rectangles from same-color point pairs.

Every non-background color appears exactly twice.  Its two cells are opposite
corners of an axis-aligned bounding box; the unchanged Racket authority fills
that complete box.  Ordinary lessons deliberately contain both a collinear
pair and a true rectangle, so line-only and diagonal-only shortcuts are visible.
"""
from __future__ import annotations

from itertools import combinations
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "892ae3bfe537"
TASK_ID = GENERATOR_ID
RULE_HASH = "5b511829e91b"
VERSION = "3.0.0"
SUMMARY = (
    "A 0-background 6..10 by 8..10 grid contains two or three distinct "
    "colors, each used at exactly two opposite bbox corners.  Exactly one "
    "pair spans both rows and columns and the remaining pair(s) are "
    "collinear.  The pair bboxes are disjoint.  Fill every pair's complete "
    "axis-aligned bbox with its own color."
)

EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is 0 and every foreground color is in 1..9",
    "there are exactly 2 or 3 foreground colors and each appears exactly twice",
    "exactly one pair spans both axes; every other pair is horizontal or vertical",
    "every bbox contains at least three cells and pair bboxes are disjoint",
]

# The override surface is intentionally small: every advertised value is exact,
# independently observable from returned pixels, and constructive in every band.
AXES = {
    "grid_h": {"type": "int", "default": "band anchor", "valid": "6..10"},
    "grid_w": {"type": "int", "default": "band anchor", "valid": "8..10"},
    "n_pairs": {"type": "int", "default": "2 easy/medium; 3 hard", "valid": "2..3"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

_PROFILE = {
    "easy": (6, 9, 2),
    "medium": (8, 8, 2),
    "hard": (10, 10, 3),
}


def _axis(ctx, overrides, name: str, values: range, default: int) -> int:
    """Draw one exact public axis while keeping band defaults deterministic."""
    options = tuple(values) if overrides.get(name) is not None else (default,)
    return ctx.draw_choice(name, options)


def _transform_point(r: int, c: int, h: int, w: int, *,
                     reflect_rows: bool, reflect_cols: bool, transpose: bool) -> tuple[int, int]:
    if reflect_rows:
        r = h - 1 - r
    if reflect_cols:
        c = w - 1 - c
    if transpose:
        r, c = c, r
    return r, c


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")

    if difficulty in _PROFILE:
        default_h, default_w, default_n = _PROFILE[difficulty]
    else:
        # Unbanded probes and exports cycle through all source-backed profiles
        # instead of collapsing to one shape.  Explicit overrides still win.
        default_h, default_w, default_n = tuple(_PROFILE.values())[
            (seed + sample_index) % len(_PROFILE)
        ]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _axis(ctx, overrides, "grid_h", range(6, 11), default_h)
    w = _axis(ctx, overrides, "grid_w", range(8, 11), default_w)
    n_pairs = _axis(ctx, overrides, "n_pairs", range(2, 4), default_n)

    rng = ctx.draw_rng("layout")
    colors = ctx.draw_distinct_colors("pair_colors", n=n_pairs, exclude=(0,))

    # Constructive slots.  The true rectangle stays left of the reserved line
    # columns and above the reserved horizontal row.  This works at the minimum
    # 6x8 boundary without rejection loops or silently dropped pairs.
    area_r1 = rng.randint(0, h - 4)
    area_r2 = rng.randint(area_r1 + 2, h - 2)
    area_c1 = rng.randint(0, w - 6)
    area_c2 = rng.randint(area_c1 + 2, w - 4)
    if rng.randrange(2):
        area = ((area_r1, area_c1), (area_r2, area_c2))
    else:
        area = ((area_r1, area_c2), (area_r2, area_c1))

    line1_r1 = rng.randint(0, h - 4)
    line1_r2 = rng.randint(line1_r1 + 2, h - 2)
    line1 = ((line1_r1, w - 2), (line1_r2, w - 2))

    pairs = [area, line1]
    if n_pairs == 3:
        if rng.randrange(2):
            line2_r1 = rng.randint(0, h - 4)
            line2_r2 = rng.randint(line2_r1 + 2, h - 2)
            line2 = ((line2_r1, w - 1), (line2_r2, w - 1))
        else:
            line2_c1 = rng.randint(0, w - 3)
            line2_c2 = rng.randint(line2_c1 + 2, w - 1)
            line2 = ((h - 1, line2_c1), (h - 1, line2_c2))
        pairs.append(line2)

    reflect_rows = bool(rng.randrange(2))
    reflect_cols = bool(rng.randrange(2))
    transpose = h == w and bool(rng.randrange(2))
    grid = full_grid(h, w, 0)
    for color, pair in zip(colors, pairs):
        for r, c in pair:
            rr, cc = _transform_point(
                r, c, h, w,
                reflect_rows=reflect_rows,
                reflect_cols=reflect_cols,
                transpose=transpose,
            )
            grid[rr][cc] = color
    return grid


def _positions_by_color(grid) -> dict[int, list[tuple[int, int]]]:
    positions: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                positions.setdefault(value, []).append((r, c))
    return positions


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _bbox_cells(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r1, c1, r2, c2 = box
    return {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]

    h, w = len(grid), width
    errors: list[str] = []
    if not 6 <= h <= 10:
        errors.append(f"grid_h={h} outside 6..10")
    if not 8 <= w <= 10:
        errors.append(f"grid_w={w} outside 8..10")

    positions = _positions_by_color(grid)
    if not 2 <= len(positions) <= 3:
        errors.append(f"expected 2 or 3 foreground colors, found {len(positions)}")

    boxes: list[tuple[int, tuple[int, int, int, int]]] = []
    area_pairs = 0
    line_pairs = 0
    for color, cells in positions.items():
        if len(cells) != 2:
            errors.append(f"color {color} appears {len(cells)} times (expected 2)")
            continue
        box = _bbox(cells)
        r1, c1, r2, c2 = box
        if (r2 - r1 + 1) * (c2 - c1 + 1) < 3:
            errors.append(f"color {color} bbox has fewer than 3 cells")
        if r1 == r2 or c1 == c2:
            line_pairs += 1
        else:
            area_pairs += 1
        boxes.append((color, box))

    if positions and area_pairs != 1:
        errors.append(f"expected exactly one area pair, found {area_pairs}")
    expected_lines = max(0, len(positions) - 1)
    if positions and line_pairs != expected_lines:
        errors.append(f"expected {expected_lines} collinear pair(s), found {line_pairs}")

    for (color_a, box_a), (color_b, box_b) in combinations(boxes, 2):
        if _bbox_cells(box_a) & _bbox_cells(box_b):
            errors.append(f"bbox overlap between colors {color_a} and {color_b}")
    return errors


def strict_canonical_like(grid):
    """Lawful inputs in the source-supported pair/bbox grammar."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid generator grid: " + "; ".join(errors))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_pairs": len(_positions_by_color(grid)),
    }


def _fill_pairs(grid, predicate: Callable[[int, int], bool] | None = None,
                *, border_only: bool = False):
    """Independent Python oracle used by tests and explicit rival rules."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    output = full_grid(h, w, 0)
    for color, cells in _positions_by_color(grid).items():
        if len(cells) != 2:
            continue
        (ra, ca), (rb, cb) = cells
        row_span, col_span = abs(rb - ra), abs(cb - ca)
        if predicate is not None and not predicate(row_span, col_span):
            continue
        r1, c1, r2, c2 = _bbox(cells)
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if border_only and r not in (r1, r2) and c not in (c1, c2):
                    continue
                output[r][c] = color
    return output


def _diagonal_only(grid):
    return _fill_pairs(grid, lambda row_span, col_span: row_span > 0 and col_span > 0)


def _line_only(grid):
    return _fill_pairs(grid, lambda row_span, col_span: row_span == 0 or col_span == 0)


def _border_only(grid):
    return _fill_pairs(grid, border_only=True)


def _has_collinear_pair(grid) -> bool:
    return any(
        len(cells) == 2 and (cells[0][0] == cells[1][0] or cells[0][1] == cells[1][1])
        for cells in _positions_by_color(grid).values()
    )


def _has_area_pair(grid) -> bool:
    return any(
        len(cells) == 2 and cells[0][0] != cells[1][0] and cells[0][1] != cells[1][1]
        for cells in _positions_by_color(grid).values()
    )


def _has_solid_interior(grid) -> bool:
    for cells in _positions_by_color(grid).values():
        if len(cells) != 2:
            continue
        r1, c1, r2, c2 = _bbox(cells)
        if r2 - r1 >= 2 and c2 - c1 >= 2:
            return True
    return False


SEMANTIC_WITNESSES = {
    "collinear_pair": _has_collinear_pair,
    "area_pair": _has_area_pair,
    "solid_interior": _has_solid_interior,
}
SEMANTIC_RIVALS = {
    "diagonal_only": _diagonal_only,
    "line_only": _line_only,
    "border_only": _border_only,
}
WITNESS_RIVALS = {
    "collinear_pair": ["diagonal_only"],
    "area_pair": ["line_only"],
    "solid_interior": ["border_only"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    del query
    survivors = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            survivors.append(name)
    return [] if not survivors else [f"rival(s) survive every demo: {survivors}"]
