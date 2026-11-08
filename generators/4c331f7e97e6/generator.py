"""Generator for arc_additional_puzzles_21_set4:M25.

The selected reference fires four cardinal rays from every non-{0,1} marker.
Rays read the original grid, stop at color-1 walls or the edge, pass through
other markers, and paint original background cells in row-major marker order.

All retained originals place the markers inside one closed rectangular wall
chamber.  Version 3 restores that source domain while varying canvas, chamber,
marker count, marker colors, and positions.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4c331f7e97e6"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "f6aef1d09ea3"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A closed rectangular color-1 chamber contains two to five colored "
    "single-cell markers. Every marker fires four cardinal rays through "
    "original background, stopping at the chamber wall; overlapping paints "
    "resolve in row-major marker order, matching the selected Racket rule."
)

INVARIANTS = [
    "all color-1 cells form exactly one closed rectangular perimeter",
    "every non-{0,1} marker lies strictly inside that perimeter",
    "there are at least two markers and the chamber interior contains background",
]

DEGENERATE_TEXTURES = ("no_walls", "no_source", "full_grid")
HELPFUL_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-banded", "valid": "9..30"},
    "grid_w": {"type": "int", "default": "difficulty-banded", "valid": "9..30"},
    "chamber_h": {"type": "int", "default": "rng 7..grid_h", "valid": "7..30"},
    "chamber_w": {"type": "int", "default": "rng 7..grid_w", "valid": "7..30"},
    "n_markers": {"type": "int", "default": "rng 2..5", "valid": "2..5"},
}


def _bounds(difficulty):
    if difficulty == "easy":
        return (9, 14), (9, 14), (2, 3)
    if difficulty == "hard":
        return (18, 30), (18, 30), (4, 5)
    if difficulty in (None, "medium"):
        return (11, 22), (11, 24), (2, 5)
    raise ValueError("difficulty must be easy, medium, hard, or None")


def _paint_perimeter(grid, top, bottom, left, right):
    for c in range(left, right + 1):
        grid[top][c] = 1
        grid[bottom][c] = 1
    for r in range(top, bottom + 1):
        grid[r][left] = 1
        grid[r][right] = 1


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)

    (hlo, hhi), (wlo, whi), (mlo, mhi) = _bounds(difficulty)
    h = ctx.draw_int_strict("grid_h", hlo, hhi)
    w = ctx.draw_int_strict("grid_w", wlo, whi)
    chamber_h = ctx.draw_int_strict("chamber_h", 7, h)
    chamber_w = ctx.draw_int_strict("chamber_w", 7, w)
    n_markers = ctx.draw_int_strict("n_markers", mlo, mhi)
    rng = ctx.draw_rng("chamber-content")

    top = rng.randint(0, h - chamber_h)
    left = rng.randint(0, w - chamber_w)
    bottom = top + chamber_h - 1
    right = left + chamber_w - 1
    grid = full_grid(h, w, 0)
    _paint_perimeter(grid, top, bottom, left, right)

    center_r = (top + bottom) // 2
    center_c = (left + right) // 2
    upper = (max(top + 1, center_r - 2), center_c)
    lateral = (center_r, max(left + 1, center_c - 2))
    positions = [upper, lateral]
    available = [
        (r, c)
        for r in range(top + 1, bottom)
        for c in range(left + 1, right)
        if (r, c) not in positions and (r, c) != (center_r, center_c)
        and r != center_r and c != center_c
    ]
    rng.shuffle(available)
    positions.extend(available[: max(0, n_markers - 2)])
    colors = rng.sample(list(range(2, 10)), n_markers)
    for (r, c), color in zip(positions, colors, strict=True):
        grid[r][c] = color
    return grid


def _wall_box(grid):
    ones = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    if not ones:
        return None
    top = min(r for r, _ in ones)
    bottom = max(r for r, _ in ones)
    left = min(c for _, c in ones)
    right = max(c for _, c in ones)
    expected = (
        {(top, c) for c in range(left, right + 1)}
        | {(bottom, c) for c in range(left, right + 1)}
        | {(r, left) for r in range(top, bottom + 1)}
        | {(r, right) for r in range(top, bottom + 1)}
    )
    return (top, bottom, left, right) if set(ones) == expected else None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid cells must be exact ARC colors"]
    box = _wall_box(grid)
    if box is None:
        return ["color-1 cells must form one closed rectangular chamber"]
    top, bottom, left, right = box
    markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 1)
    ]
    errors = []
    if len(markers) < 2:
        errors.append("expected at least two colored markers")
    if any(not (top < r < bottom and left < c < right) for r, c in markers):
        errors.append("every marker must lie strictly inside the chamber")
    if not any(grid[r][c] == 0 for r in range(top + 1, bottom) for c in range(left + 1, right)):
        errors.append("chamber interior needs background for visible rays")
    return errors


def _draw_from_degenerate(name, rng):
    del rng
    grid = full_grid(11, 11, 0)
    if name == "no_walls":
        grid[5][4] = 3
        grid[3][5] = 7
    elif name == "no_source":
        _paint_perimeter(grid, 1, 9, 1, 9)
    elif name == "full_grid":
        for r in range(11):
            for c in range(11):
                grid[r][c] = 2
    return grid
