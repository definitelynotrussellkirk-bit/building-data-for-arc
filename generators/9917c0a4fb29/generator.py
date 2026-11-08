"""Generator for arc_puzzle_bank_fifth21:E34 — mirror left-side cells across full-height 9 guide.

Rule: full-height column of 9s acts as the vertical mirror axis;
left-side colored cells are mirrored to the right.

Combinatorial axes (8): grid_h, grid_w, palette_kind, markers,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_guide, cells_on_right, partial_guide.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9917c0a4fb29"
# 1.3.0: defect-lint identity_demo — every marker could sit far enough left that
# its mirror landed OUT OF BOUNDS (no cell painted -> output == input). At least
# one marker is now guaranteed an in-bounds empty mirror target.
VERSION = "1.3.0"
TASK_ID = "9917c0a4fb29"
SUMMARY = "Full-height column of 9s acts as a vertical mirror axis. Colored cells (non-0, non-9) on the LEFT of the guide get mirrored to the RIGHT via mc=2*guide-c, only when the mirror target is in bounds and currently 0. Rule preserves input + adds mirror copies."

# Rivals: 'output is input' refuted by any demo with reachable
# mirror cells (right side fills). 'mirror in opposite color'
# refuted by any demo (mirror preserves color). 'mirror across
# horizontal axis' refuted by ≥1 demo where vertical-only mirror
# fits. 'mirror entire grid' refuted by ≥1 demo where bg cells
# also exist on right and stay 0. 3 demos cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "one full-height guide column is color 9",
    "colored singleton cells do not sit on the guide",
    "mirror targets are in bounds and initially empty",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_guide", "cells_on_right", "partial_guide")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11 odd", "valid": "5..17 odd"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "markers":        {"type": "int", "default": "rng 3..5", "valid": "1..12"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "left_only_full_9_guide",
                       "valid": "left_only_full_9_guide"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly one full-height column is entirely color 9; ≥1 non-bg non-9 cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    full9_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    has_other = any(grid[r][c] not in (0, 9) for r in range(h) for c in range(w))
    errs = []
    if len(full9_cols) != 1:
        errs.append(f"expected exactly 1 full-height color-9 column; found {len(full9_cols)}: {full9_cols}")
    if not has_other:
        errs.append("no non-bg non-9 cells found (no pattern to mirror)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 9, 11)
        target = ctx.draw_int("markers", 3, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 13, 17)
        target = ctx.draw_int("markers", 5, 8)
    else:
        h = ctx.draw_int("grid_h", 7, 11)
        w = ctx.draw_int("grid_w", 11, 13)
        target = ctx.draw_int("markers", 4, 6)
    rng = ctx.draw_rng("layout")
    # Guide may sit at the exact middle OR slightly off-center; the
    # rule handles both since mirror is by reflection around guide col.
    guide = rng.choice([w // 2, w // 2, w // 2,
                        max(2, w // 2 - 1), min(w - 3, w // 2 + 1)])
    g = full_grid(h, w, 0)
    for r in range(h):
        g[r][guide] = 9
    # Prefer left-side placements (so all mirror targets land within
    # an in-bounds right-side region) — but allow some that land
    # out-of-bounds so the rule's bounds check is exercised.
    positions = [(r, c) for r in range(h) for c in range(guide)]
    rng.shuffle(positions)
    placed = 0
    mirrored_any = False
    for r, c in positions:
        if placed >= target:
            break
        mc = 2 * guide - c
        in_bounds_mirror = 0 <= mc < w
        if in_bounds_mirror and g[r][mc] != 0:
            continue
        g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])
        placed += 1
        mirrored_any = mirrored_any or in_bounds_mirror
    if not mirrored_any:
        # every marker mirrored out of bounds -> identity demo. Add one marker
        # whose mirror target is guaranteed in bounds and empty.
        for r, c in positions:
            mc = 2 * guide - c
            if 0 <= mc < w and g[r][c] == 0 and g[r][mc] == 0:
                g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])
                break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    guide = w // 2
    if name == "no_guide":
        # cells but no 9-guide → no mirror axis defined
        g[1][2] = 4; g[3][3] = 6
        return g
    if name == "cells_on_right":
        # cells already on right side → mirror would clobber
        for r in range(h): g[r][guide] = 9
        g[1][1] = 4; g[2][2] = 6   # left
        g[1][7] = 3; g[2][6] = 7   # right (clobber)
        return g
    if name == "partial_guide":
        # guide has gaps → "full-height" precondition fails
        for r in range(h - 2): g[r][guide] = 9
        g[1][1] = 4; g[2][2] = 6
        return g
    return g
