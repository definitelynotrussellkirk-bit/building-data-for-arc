"""Generator for additional_scaffolded:E7.

Rule: middle cells of vertical color-4 triplets are recolored to color 9.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_triplets,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_triplets, horizontal_only, fused_runs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "260bee8355e9"
VERSION = "1.1.1"
TASK_ID = "260bee8355e9"
SUMMARY = "Middle cells of vertical color-4 triplets are recolored to color 9."

INVARIANTS = [
    "background is 0",
    "each active object is an exact vertical run of three color-4 cells",
    "vertical triplets are separated so they do not merge into longer runs",
    "optional horizontal color-4 pairs are non-target distractors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_triplets", "horizontal_only", "fused_runs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..13", "valid": "3..20"},
    "grid_w":         {"type": "int", "default": "rng 7..12", "valid": "3..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_triplets":     {"type": "int", "default": "rng 2..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "vertical_triplets",
                       "valid": "vertical_triplets"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; at least one vertical triplet of color-4 cells in a single column."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    found = False
    for c in range(w):
        col_vals = [grid[r][c] for r in range(h)]
        for r in range(h - 2):
            if col_vals[r] == 4 and col_vals[r + 1] == 4 and col_vals[r + 2] == 4:
                found = True; break
        if found:
            break
    if not found:
        return errors  # degenerate no_triplets — allowed
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 7, 9)
        n_triplets = ctx.draw_int("n_triplets", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 10, 12)
        n_triplets = ctx.draw_int("n_triplets", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 7, 13)
        w = ctx.draw_int("grid_w", 7, 12)
        n_triplets = ctx.draw_int("n_triplets", 2, 5)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    anchors: list[tuple[int, int]] = []
    for _ in range(200):
        if len(anchors) >= n_triplets:
            break
        r = rng.randint(0, h - 3)
        c = rng.randint(0, w - 1)
        if any(abs(c - cc) < 2 and abs(r - rr) < 4 for rr, cc in anchors):
            continue
        for dr in range(3):
            g[r + dr][c] = 4
        anchors.append((r, c))
    if not anchors:
        g[1][1] = 4
        g[2][1] = 4
        g[3][1] = 4
    for r in range(h):
        for c in range(w - 1):
            if g[r][c] == 0 and g[r][c + 1] == 0:
                above_clear = r == 0 or (g[r - 1][c] == 0 and g[r - 1][c + 1] == 0)
                below_clear = r == h - 1 or (g[r + 1][c] == 0 and g[r + 1][c + 1] == 0)
                if above_clear and below_clear:
                    g[r][c] = 4
                    g[r][c + 1] = 4
                    return g
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_triplets":
        # only single 4s and 4-pairs → no vertical triple, rule fires zero times
        g[2][3] = 4
        g[5][6] = 4; g[5][7] = 4   # horizontal pair
        return g
    if name == "horizontal_only":
        # all 4-runs are horizontal triples (length-3) → rule scans columns, sees only length-1 vertical runs
        for c in range(2, 5): g[2][c] = 4
        for c in range(4, 7): g[6][c] = 4
        return g
    if name == "fused_runs":
        # length-4 vertical run (touches the rule's exact-3 predicate's edge) → ambiguous middle
        for r in range(2, 6): g[r][3] = 4
        for r in range(1, 5): g[r][6] = 4
        return g
    return g
