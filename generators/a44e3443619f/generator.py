"""Generator for arc_additional_puzzle_bank_volume3:E16 — diagonal X centers.

Canonical rule: every zero cell whose four immediate diagonal neighbours are
red (2) becomes blue (1); every other cell is preserved.

Ordinary draws construct exactly two or three isolated source X patterns and
reject layouts whose combined corners would accidentally create extra X
centres.  This repairs the previous retry sampler, which could emit one, four,
or five effective patterns despite declaring two or three.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a44e3443619f"
VERSION = "2.1.0"
TASK_ID = "a44e3443619f"
SUMMARY = (
    "0-background grid with exactly 2-3 isolated red X patterns. Each pattern "
    "has red (2) cells at the four diagonal corners of a 3x3 region and an "
    "empty centre. Every empty cell with red in all four immediate diagonal "
    "directions becomes blue (1); all other cells are preserved."
)

# Byte-for-byte selected canonical authority.  Parametric default adapters and
# source-bound checks use this exact text.
_CANONICAL_PROGRAM = """(rule!
  (grid-from-fn (rows g) (cols g)
    (lambda (r c)
      (if (and (= (at g r c) 0)
               (all? (lambda (d) (= (safe-at g (+ r (first d)) (+ c (second d)) 0) 2)) diagonal-deltas))
          1
          (at g r c)))))"""

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "ordinary draws contain exactly 2 or 3 complete red X patterns",
    "ordinary source patterns do not overlap or create accidental extra centres",
    "all source-pattern centres are strictly interior",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_quads", "quads_at_edge", "partial_quads")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h": {"type": "int", "default": "rng 7..9", "valid": "7..9"},
    "grid_w": {"type": "int", "default": "rng 9..11", "valid": "9..11"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                     "valid": "|".join(PALETTE_KINDS)},
    "n_quads": {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "palette_size": {"type": "int", "default": "1", "valid": "1..2"},
    "position_bias": {"type": "str", "default": "interior_quads",
                      "valid": "interior_quads"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..2"},
    "density": {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture": {"type": "str", "default": "alias for palette_kind",
                "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_DIAGONALS = ((-1, -1), (-1, 1), (1, -1), (1, 1))


def rule_program() -> str:
    """Return the exact selected canonical Racket authority."""
    return _CANONICAL_PROGRAM


def _validate_grid(grid) -> tuple[int, int]:
    if (type(grid) is not list or not grid or type(grid[0]) is not list
            or not grid[0]):
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must contain exact ARC integer colours")
    return len(grid), width


def _x_centers(grid) -> tuple[tuple[int, int], ...]:
    h, w = _validate_grid(grid)
    return tuple(
        (r, c)
        for r in range(1, h - 1)
        for c in range(1, w - 1)
        if grid[r][c] == 0
        and all(grid[r + dr][c + dc] == 2 for dr, dc in _DIAGONALS)
    )


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python mirror of the exact canonical rule."""
    _validate_grid(grid)
    centres = set(_x_centers(grid))
    return [
        [1 if (r, c) in centres else value for c, value in enumerate(row)]
        for r, row in enumerate(grid)
    ]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify the semantic source grammar without rejecting canonical overlaps."""
    try:
        h, w = _validate_grid(grid)
    except ValueError as exc:
        return [str(exc)]
    errs: list[str] = []
    quad_count = len(_x_centers(grid))
    if quad_count < 1:
        errs.append("no complete X pattern found (expected at least one)")
    wrong = [(r, c, grid[r][c]) for r in range(h) for c in range(w)
             if grid[r][c] not in (0, 2)]
    if wrong:
        errs.append(f"non-background cells not red: {wrong[:3]}")
    return errs


def _paint_quad(grid: list[list[int]], top: int, left: int) -> None:
    grid[top][left] = 2
    grid[top][left + 2] = 2
    grid[top + 2][left] = 2
    grid[top + 2][left + 2] = 2


@lru_cache(maxsize=None)
def _valid_layouts(h: int, w: int, count: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Enumerate small exact layouts once per supported shape/count.

    Pairwise separation preserves the old intended isolation contract.  The
    final centre-set equality additionally rules out accidental Xs assembled
    from corners belonging to different source patterns.
    """
    candidates = tuple((r, c) for r in range(h - 2) for c in range(w - 2))
    valid: list[tuple[tuple[int, int], ...]] = []
    for layout in combinations(candidates, count):
        if any(not (abs(ar - br) > 3 or abs(ac - bc) > 3)
               for (ar, ac), (br, bc) in combinations(layout, 2)):
            continue
        grid = full_grid(h, w, 0)
        for top, left in layout:
            _paint_quad(grid, top, left)
        expected = {(top + 1, left + 1) for top, left in layout}
        if set(_x_centers(grid)) == expected:
            valid.append(layout)
    if not valid:
        raise RuntimeError(f"no exact {count}-X layout for {h}x{w}")
    return tuple(valid)


def _strict_requested_count(overrides: dict) -> None:
    if "n_quads" not in overrides:
        return
    value = overrides["n_quads"]
    if type(value) is not int or value not in (2, 3):
        raise ValueError("n_quads must be the exact integer 2 or 3")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _strict_requested_count(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 7)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 9, 11)
    count = ctx.draw_int("n_quads", 2, 3)
    rng = ctx.draw_rng("layout")
    layouts = _valid_layouts(h, w, count)
    layout = layouts[rng.randrange(len(layouts))]
    grid = full_grid(h, w, 0)
    for top, left in layout:
        _paint_quad(grid, top, left)
    return grid


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_quads":
        for r, c in [(2, 2), (4, 5), (6, 8)]:
            g[r][c] = 2
        return g
    if name == "quads_at_edge":
        # Valid boundary-contact source X; the centre remains interior.
        _paint_quad(g, 0, 0)
        return g
    if name == "partial_quads":
        for top_r, top_c in [(2, 2), (5, 6)]:
            g[top_r][top_c] = 2
            g[top_r][top_c + 2] = 2
            g[top_r + 2][top_c] = 2
        return g
    return g
