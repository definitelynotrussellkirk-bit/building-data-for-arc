"""Generator for arc_additional_puzzles_21_set5:H30.

The exact selected rule removes the two color-5 guides, then reflects every
other nonzero cell across the *full-grid* center.  Guide orientation selects the
reflection: same-row guides flip rows; same-column guides flip columns.  Version
3 places the source motif on the corresponding top or left half, with its mirror
partner initially empty.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "588ee22f3c4f"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "6f11c3f4c1e7"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Two color-5 guides share a row or column. Same-row guides select a "
    "top-to-bottom full-grid reflection; same-column guides select a left-to-"
    "right reflection. A varied motif occupies only the source half and the "
    "selected Racket rule completes its mirror while preserving the guides."
)

INVARIANTS = [
    "exactly two color-5 guides share exactly one row or one column",
    "same-row guides have all motif cells strictly in the top half",
    "same-column guides have all motif cells strictly in the left half",
    "every reflected partner cell is initially background",
]

DEGENERATE_TEXTURES = ("no_guides", "motif_on_both_sides", "single_guide")
HELPFUL_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-banded", "valid": "7..30"},
    "grid_w": {"type": "int", "default": "difficulty-banded", "valid": "7..30"},
    "axis": {"type": "int", "default": "rng 0..1", "valid": "0..1"},
    "motif_cells": {"type": "int", "default": "rng 3..8", "valid": "3..8"},
}

COLORS = (1, 2, 3, 4, 6, 7, 8, 9)


def _bounds(difficulty):
    if difficulty == "easy":
        return (7, 10), (8, 12), (3, 4)
    if difficulty == "hard":
        return (16, 30), (16, 30), (6, 8)
    if difficulty in (None, "medium"):
        return (9, 18), (10, 20), (3, 7)
    raise ValueError("difficulty must be easy, medium, hard, or None")


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
    (hlo, hhi), (wlo, whi), (nlo, nhi) = _bounds(difficulty)
    h = ctx.draw_int_strict("grid_h", hlo, hhi)
    w = ctx.draw_int_strict("grid_w", wlo, whi)
    axis = ctx.draw_int_strict("axis", 0, 1)
    limit = min(nhi, w - 2 if axis == 0 else h - 2)
    n_cells = ctx.draw_int_strict("motif_cells", nlo, limit)
    rng = ctx.draw_rng("reflection-content")
    grid = full_grid(h, w, 0)

    if axis == 0:  # same row -> flip rows across the full grid
        guide_row = h - 1
        guide_cols = (0, w - 1)
        for c in guide_cols:
            grid[guide_row][c] = 5
        columns = list(range(1, w - 1))
        rng.shuffle(columns)
        rows = list(range(0, h // 2))
        for index, c in enumerate(columns[:n_cells]):
            r = rows[(index + rng.randrange(len(rows))) % len(rows)]
            grid[r][c] = rng.choice(COLORS)
    else:  # same column -> flip columns across the full grid
        guide_col = w - 1
        guide_rows = (0, h - 1)
        for r in guide_rows:
            grid[r][guide_col] = 5
        rows = list(range(1, h - 1))
        rng.shuffle(rows)
        columns = list(range(0, w // 2))
        for index, r in enumerate(rows[:n_cells]):
            c = columns[(index + rng.randrange(len(columns))) % len(columns)]
            grid[r][c] = rng.choice(COLORS)
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    guides = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    motif = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 5)]
    errors = []
    if len(guides) != 2:
        return [f"expected exactly two color-5 guides, found {len(guides)}"]
    same_row = guides[0][0] == guides[1][0]
    same_col = guides[0][1] == guides[1][1]
    if same_row == same_col:
        errors.append("guides must share exactly one row or one column")
    if not motif:
        errors.append("motif must contain at least one non-guide cell")
    if same_row:
        for r, c in motif:
            mr = h - 1 - r
            if not r < mr or grid[mr][c] != 0:
                errors.append("same-row guides require an empty bottom-half mirror partner")
                break
    elif same_col:
        for r, c in motif:
            mc = w - 1 - c
            if not c < mc or grid[r][mc] != 0:
                errors.append("same-column guides require an empty right-half mirror partner")
                break
    return errors


def _draw_from_degenerate(name, rng):
    del rng
    h, w = 8, 10
    grid = full_grid(h, w, 0)
    if name == "no_guides":
        grid[1][1] = 2
        grid[2][3] = 4
    elif name == "motif_on_both_sides":
        grid[7][0] = grid[7][9] = 5
        grid[1][2] = 2
        grid[6][2] = 3
    elif name == "single_guide":
        grid[7][0] = 5
        grid[1][2] = 2
    return grid
