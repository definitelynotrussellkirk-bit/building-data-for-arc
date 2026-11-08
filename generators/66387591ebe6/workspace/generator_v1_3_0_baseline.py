"""Generator for arc_puzzle_bank_21_set9_e:hard_i18.

Rule:
- key = g[0][0] (rotation count: 1..4 → 0..3 quarter-turns)
- pivot = first color-9 cell
- cells = all non-{0, 9} cells except (0, 0)
- output = blank with key at (0,0), pivot preserved, cells rotated
  around pivot by (key - 1) quarter-turns clockwise.

Combinatorial axes (8): grid_h, grid_w, palette_kind, key, n_cells,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pivot, no_key, no_cells.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "66387591ebe6"
# 1.3.0: key=1 means 0 quarter-turns -> rotation is a no-op -> output == input
# (identity, ~25% of draws). Draw key in 2..4 for default instances and verify
# the simulated rotated output actually differs from the input. Adds self_check.
VERSION = "1.3.0"
TASK_ID = "66387591ebe6"

SUMMARY = "g[0][0] = key (1..4); maroon(9) pivot + multi-color cells; rule rotates cells around pivot by (key-1) quarter-turns CW, keeping key and pivot at their positions."

# Rivals: 'rotate by fixed 90°' refuted by ≥2 demos with different
# key values. 'rotate around grid center' refuted by ≥1 demo with
# off-center pivot. 'erase pivot' refuted by any demo (pivot stays).
# 'rotate around (0,0) not pivot' refuted by ≥1 demo where pivot is
# clearly the rotation center.
# 4 demos with varied keys + pivot positions cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "g[0][0] holds an integer in 1..4 (the rotation count)",
    "exactly one color-9 pivot",
    "≥1 non-{0,9,key-color} cell whose rotation stays in-bounds",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pivot", "no_key", "no_cells")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "key":            {"type": "int", "default": "rng 1..4", "valid": "1..4"},
    "n_cells":        {"type": "int", "default": "rng 2..5", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..7"},
    "position_bias":  {"type": "str", "default": "key_pivot_cells",
                       "valid": "key_pivot_cells"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..7"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _rotate_cw(cells, pivot, turns):
    """Rotate cells around pivot by `turns` quarter-turns CW."""
    out = []
    pr, pc = pivot
    for r, c in cells:
        dr = r - pr; dc = c - pc
        for _ in range(turns):
            dr, dc = dc, -dr
        out.append((pr + dr, pc + dc))
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 7, 9)
        n_cells = ctx.draw_int("n_cells", 1, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 11, 14)
        n_cells = ctx.draw_int("n_cells", 4, 7)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 9, 12)
        n_cells = ctx.draw_int("n_cells", 2, 5)
    # key=1 -> 0 turns -> the rotation is a no-op (output == input). Draw 2..4 so
    # the demonstrated transformation is always a real rotation.
    key = int(overrides["key"]) if "key" in overrides else ctx.draw_int("key", 2, 4)
    turns = (key - 1) % 4

    last = None
    for _attempt in range(30):
        g = full_grid(h, w, 0)
        g[0][0] = key
        # Pivot at a random middle position
        pr = rng.randint(2, h - 3); pc = rng.randint(2, w - 3)
        g[pr][pc] = 9
        used = {(0, 0), (pr, pc)}
        # Place object cells whose rotation around pivot stays in-bounds.
        color_pool = [c for c in [2, 3, 4, 5, 6, 7, 8] if c != key]
        rng.shuffle(color_pool)
        placed = 0
        for _ in range(150):
            if placed >= n_cells:
                break
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if (r, c) in used or g[r][c] != 0:
                continue
            # Check rotation lands in-bounds and not on (0, 0) or pivot.
            rot = _rotate_cw([(r, c)], (pr, pc), turns)
            nr, nc = rot[0]
            if not (0 <= nr < h and 0 <= nc < w):
                continue
            if (nr, nc) in used or (nr, nc) == (0, 0) or (nr, nc) == (pr, pc):
                continue
            g[r][c] = color_pool[placed % len(color_pool)]
            used.add((r, c))
            placed += 1
        last = g
        # verify the rotation actually changes the grid (guards the rare
        # rotationally-symmetric arrangement that maps back onto itself)
        if placed >= 1 and _apply_rule(g) != g:
            return g
    return last


def _apply_rule(g):
    """Simulate the canonical rule so we can guarantee output != input."""
    h, w = len(g), len(g[0])
    key = g[0][0]
    turns = (key - 1) % 4
    pivot = None
    cells = []
    for r in range(h):
        for c in range(w):
            v = g[r][c]
            if v == 9 and pivot is None:
                pivot = (r, c)
            elif v not in (0, 9) and (r, c) != (0, 0):
                cells.append((r, c, v))
    out = full_grid(h, w, 0)
    out[0][0] = key
    if pivot is not None:
        out[pivot[0]][pivot[1]] = 9
        for r, c, v in cells:
            (nr, nc), = _rotate_cw([(r, c)], pivot, turns)
            if 0 <= nr < h and 0 <= nc < w:
                out[nr][nc] = v
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Valid rotation key (2..4 = real turn), one pivot, >=1 cell, and the
    simulated rotation actually changes the grid (no identity)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    key = grid[0][0]
    errors = []
    if not (1 <= key <= 4):
        errors.append(f"g[0][0] key must be in 1..4, got {key}")
    pivots = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9]
    if len(pivots) != 1:
        errors.append(f"expected exactly one color-9 pivot, found {len(pivots)}")
    cells = [(r, c) for r in range(h) for c in range(w)
             if grid[r][c] not in (0, 9) and (r, c) != (0, 0)]
    if not cells:
        errors.append("no rotatable cells")
    if not errors and _apply_rule(grid) == grid:
        errors.append("rotation maps the grid onto itself (identity demo)")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_pivot":
        g[0][0] = 2
        g[3][3] = 4; g[4][5] = 6
        return g
    if name == "no_key":
        g[4][5] = 9
        g[3][3] = 4
        return g
    if name == "no_cells":
        g[0][0] = 2; g[4][5] = 9
        return g
    return g
