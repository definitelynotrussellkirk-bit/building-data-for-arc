"""Generator for arc_puzzle_bank_twelfth21:M81 — sweep blob right.

Rule: a 7-cell at (0,0) is a marker; the (single) non-7 blob extends
its cells rightward (each row of the blob fills to the right edge).

Combinatorial axes (8): grid_h, grid_w, palette_kind, blob_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_marker, no_blob, blob_at_right_edge.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "61aeeba19268"
VERSION = "1.2.0"  # add task-specific self_check coverage
TASK_ID = "61aeeba19268"
SUMMARY = "7 at (0,0) + a small blob in left half (sweep right is non-trivial)."

INVARIANTS = [
    "background is 0",
    "(0,0) is 7",
    "exactly one non-7 blob in the left half (so sweep moves cells)",
    "blob's bbox right col < w-1",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "no_blob", "blob_at_right_edge")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "blob_size":      {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "marker_origin_with_left_blob",
                       "valid": "marker_origin_with_left_blob"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 7, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 7, 10)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    g[0][0] = 7
    used = {(0, 0)}
    for r in range(h):
        for c in range(w // 2 + 1, w):
            used.add((r, c))
    color = rng.choice([2, 3, 4, 5, 6, 8, 9])
    cells = grow_blob(rng, h, w, used, rng.randint(2, 4), max_attempts=80)
    if cells:
        for r, c in cells:
            g[r][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 8
    g = full_grid(h, w, 0)
    if name == "no_marker":
        # missing 7 at (0,0) → no anchor, rule has no instruction
        for (r, c) in [(2, 1), (2, 2), (3, 2)]: g[r][c] = 4
        return g
    if name == "no_blob":
        # marker only, no blob → rule has nothing to sweep
        g[0][0] = 7
        return g
    if name == "blob_at_right_edge":
        # blob already at right edge → sweep is identity
        g[0][0] = 7
        g[2][w - 1] = 4
        g[3][w - 1] = 4
        return g
    return g


def _components4_blob(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for sr in range(h):
        for sc in range(w):
            if (sr, sc) in seen or grid[sr][sc] != color:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    if grid[0][0] != 7:
        errors.append("marker at (0,0) should be color 7")
    colors = sorted({v for row in grid for v in row if v not in (0, 7)})
    if len(colors) != 1:
        errors.append("expected exactly one sweep-blob color besides marker 7")
        return errors
    comps = _components4_blob(grid, colors[0])
    if len(comps) != 1:
        errors.append("expected exactly one connected sweep blob")
        return errors
    cells = comps[0]
    if len(cells) < 2:
        errors.append("sweep blob should have at least two cells")
    if max(c for _, c in cells) >= w - 1:
        errors.append("sweep blob should not already touch the right edge")
    if max(c for _, c in cells) >= w // 2 + 1:
        errors.append("sweep blob should stay in the left half")
    return errors
