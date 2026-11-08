"""Generator for arc_puzzle_bank_21_set10_s:S10_E3.

Rule: a nonzero object on a zero background is cropped to its tight
bounding box.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_object, full_grid_object, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "49a23dff5b22"
VERSION = "2.0.1"  # shape-locked-out (out always 3x3): content was a FIXED 5-cell shape. Rule = crop-to-content, so output dims = content bbox. Now a RANDOM multi-colour pattern spanning a VARIED bbox (2..7 x 2..7, non-square; touches all 4 bbox edges) -> output dims and pattern vary.
TASK_ID = "49a23dff5b22"
SUMMARY = "A nonzero multi-color pattern (varied bbox) on a zero background is cropped to its tight bounding box."

INVARIANTS = [
    "zero is always the background color",
    "the nonzero content has at least one row and column of zero padding",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_object", "full_grid_object", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "random", "valid": "random"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        rh = ctx.draw_int("bbox_h", 2, 4); rw = ctx.draw_int("bbox_w", 2, 4); ncol = 2
    elif difficulty == "hard":
        rh = ctx.draw_int("bbox_h", 3, 7); rw = ctx.draw_int("bbox_w", 3, 7); ncol = rng.randint(2, 3)
    else:
        rh = ctx.draw_int("bbox_h", 2, 6); rw = ctx.draw_int("bbox_w", 2, 6); ncol = rng.randint(2, 3)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], ncol)
    # random pattern over rh x rw; force a cell on each of the 4 edges so the
    # content bbox is exactly rh x rw (-> crop-to-content output = rh x rw).
    pat = [[0] * rw for _ in range(rh)]
    for r in range(rh):
        for c in range(rw):
            if rng.random() < 0.55:
                pat[r][c] = rng.choice(colors)
    pat[0][rng.randrange(rw)] = rng.choice(colors)
    pat[rh - 1][rng.randrange(rw)] = rng.choice(colors)
    for r in range(rh):
        pat[r][0] = pat[r][0] or 0
    pat[rng.randrange(rh)][0] = rng.choice(colors)
    pat[rng.randrange(rh)][rw - 1] = rng.choice(colors)

    h = max(rh + 3, rng.randint(rh + 2, rh + 5))
    w = max(rw + 3, rng.randint(rw + 2, rw + 5))
    g = full_grid(h, w, 0)
    top = rng.randint(1, h - rh - 1); left = rng.randint(1, w - rw - 1)
    for r in range(rh):
        for c in range(rw):
            if pat[r][c]:
                g[top + r][left + c] = pat[r][c]
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 9, 0)
    if name == "no_object":
        return g
    if name == "full_grid_object":
        for r in range(9):
            for c in range(9):
                g[r][c] = 3
        return g
    if name == "full_grid":
        for r in range(9):
            for c in range(9):
                g[r][c] = 3
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """bg=0; at least one non-zero cell; non-zero region has >=2x2 extent."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonzero:
        errors.append("no non-zero cells (nothing to crop)")
        return errors
    rs = [r for r, c in nonzero]
    cs = [c for r, c in nonzero]
    bbox_h = max(rs) - min(rs) + 1
    bbox_w = max(cs) - min(cs) + 1
    if bbox_h < 2 or bbox_w < 2:
        errors.append(f"content bbox {bbox_h}x{bbox_w} is degenerate (< 2x2)")
    return errors
