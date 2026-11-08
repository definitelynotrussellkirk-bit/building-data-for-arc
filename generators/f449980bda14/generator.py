"""Generator for f449980bda14 — dock colored dots to nearest square perimeter.

Rule: find gray(5) squares and non-{0, 5} colored dots. For each dot
(in reading order), find the closest gray square (Chebyshev/L1 to bbox).
Compute the target docking position (one cell outside the square,
clamped to the dot's row/col axis). Place the dot at the target.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "f449980bda14"
VERSION = "2.1.1"  # fail-closed square placement + executable self_check
TASK_ID = "f449980bda14"
SUMMARY = (
    "0-bg grid (possibly NON-SQUARE) with: (a) 1-3 SOLID color-5 (gray) "
    "squares (2x2 to 4x4) at well-separated positions; (b) 4-10 colored DOT cells (each a "
    "singleton in some non-{0, 5} color) scattered, each at least 2 "
    "cells away from any gray square perimeter. Rule: process dots in "
    "reading order. For each dot, find the gray square at minimum L1 "
    "distance from its row/col axis. Compute target = one cell outside "
    "the square along the dot's axis (clamped to dot's row/col). Place "
    "the dot at target on a fresh canvas keeping gray squares."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "1-3 solid color-5 (gray) squares (2x2 to 4x4)",
    "4-10 colored DOT cells (singletons in non-{0, 5} colors)",
    "dots and squares don't overlap",
    "each dot is ≥2 cells from any gray square perimeter (so docking has room)",
    "squares are placed clear of grid borders so docking fits in-bounds",
]

# Free axes the runner may override. Keys match the keyed draw_int labels in
# generate(); defaults are the medium band, valid spans easy..hard. (grid is
# square — one grid_size axis. n_squares is a constant 1 in the easy band, so
# it's only keyed in medium/hard.)
AXES = {
    "grid_h":    {"type": "int", "default": "rng 11..14", "valid": "9..18",
                  "doc": "Grid height (easy 9..11, medium 11..14, hard 14..18); independent of width."},
    "grid_w":    {"type": "int", "default": "rng 11..14", "valid": "9..18",
                  "doc": "Grid width (easy 9..11, medium 11..14, hard 14..18); non-square allowed."},
    "n_squares": {"type": "int", "default": "rng 1..2", "valid": "1..3",
                  "doc": "Gray docking squares (easy 1, medium 1..2, hard 2..3)."},
    "n_dots":    {"type": "int", "default": "rng 4..6", "valid": "3..10",
                  "doc": "Colored dot cells to dock (easy 3..4, medium 4..6, hard 6..10)."},
}


def _free(g, r1, c1, r2, c2, buffer=2):
    h, w = len(g), len(g[0])
    for r in range(max(0, r1 - buffer), min(h, r2 + buffer + 1)):
        for c in range(max(0, c1 - buffer), min(w, c2 + buffer + 1)):
            if g[r][c] != 0:
                return False
    return True


def _gray_squares(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    squares = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 5 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w
                            and (nr, nc) not in seen
                            and grid[nr][nc] == 5):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rs = [rr for rr, _ in cells]
            cs = [cc for _, cc in cells]
            r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
            side_h = r2 - r1 + 1
            side_w = c2 - c1 + 1
            if side_h == side_w and 2 <= side_h <= 4 and len(cells) == side_h * side_w:
                squares.append((r1, c1, side_h))
    return squares


def _dot_cells(grid):
    return [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row)
            if v not in (0, 5)]


def _place_square(g, squares, sizes, rng):
    h, w = len(g), len(g[0])
    for buffer in (3, 2, 1):
        choices = []
        for s in sizes:
            if h - s - 2 < 2 or w - s - 2 < 2:
                continue
            for r0 in range(2, h - s - 1):
                for c0 in range(2, w - s - 1):
                    if _free(g, r0, c0, r0 + s - 1, c0 + s - 1, buffer=buffer):
                        choices.append((r0, c0, s))
        rng.shuffle(choices)
        if choices:
            r0, c0, s = choices[0]
            draw_rect(g, r0, c0, s, s, 5)
            squares.append((r0, c0, s))
            return True
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    squares = _gray_squares(grid)
    dots = _dot_cells(grid)
    if difficulty == "easy":
        sq_lo, sq_hi, dot_lo, dot_hi = 1, 1, 3, 4
    elif difficulty == "hard":
        sq_lo, sq_hi, dot_lo, dot_hi = 2, 3, 6, 10
    else:
        sq_lo, sq_hi, dot_lo, dot_hi = 1, 2, 4, 6
    if not (sq_lo <= len(squares) <= sq_hi):
        errs.append(f"expected {sq_lo}..{sq_hi} gray squares, found {len(squares)}")
    if not (dot_lo <= len(dots) <= dot_hi):
        errs.append(f"expected {dot_lo}..{dot_hi} colored dots, found {len(dots)}")
    gray_cells = sum(1 for row in grid for v in row if v == 5)
    if gray_cells != sum(s * s for _r, _c, s in squares):
        errs.append("gray cells are not exactly solid 2x2..4x4 squares")
    for sr, sc, ss in squares:
        if sr < 2 or sc < 2 or sr + ss + 1 >= h or sc + ss + 1 >= w:
            errs.append("gray square is too close to border for docking")
            break
    for r, c, _v in dots:
        for sr, sc, ss in squares:
            if sr - 1 <= r <= sr + ss and sc - 1 <= c <= sc + ss:
                errs.append("dot is inside a gray square's one-cell docking moat")
                return errs
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 9, 11)
        n_squares = 1
        n_dots = ctx.draw_int("n_dots", 3, 4)
        sq_sizes = [2, 3]
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 18); w = ctx.draw_int("grid_w", 14, 18)
        n_squares = ctx.draw_int("n_squares", 2, 3)
        n_dots = ctx.draw_int("n_dots", 6, 10)
        sq_sizes = [2, 3, 4]
    else:
        h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 11, 14)
        n_squares = ctx.draw_int("n_squares", 1, 2)
        n_dots = ctx.draw_int("n_dots", 4, 6)
        sq_sizes = [2, 3]
    g = full_grid(h, w, 0)
    # Place gray squares.  The old hard path could exhaust the random
    # attempts and silently emit a one-square board; scan shuffled candidates
    # instead and fail closed if the requested count cannot fit.
    squares = []
    sizes = list(sq_sizes)
    for _ in range(n_squares):
        rng.shuffle(sizes)
        if not _place_square(g, squares, sizes, rng):
            raise RuntimeError("could not place requested gray docking squares")
    # Place dots
    dot_colors = [1, 2, 3, 4, 6, 7, 8, 9]
    placed = 0
    candidates = [(r, c) for r in range(h) for c in range(w) if g[r][c] == 0]
    rng.shuffle(candidates)
    for r, c in candidates:
        if placed >= n_dots:
            break
        ok = True
        for (sr, sc, ss) in squares:
            if sr - 1 <= r <= sr + ss and sc - 1 <= c <= sc + ss:
                ok = False
                break
        if not ok:
            continue
        g[r][c] = rng.choice(dot_colors)
        placed += 1
    if placed < n_dots:
        raise RuntimeError("could not place requested colored dots")
    return g
