"""Generator for arc_puzzle_bank_twentythird21:M159.

Rule: markers 3 and 4 define a displacement vector. The remaining
colored object is translated by that vector while the markers stay
fixed.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_3_marker, no_4_marker, no_object.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "33fcd12e6b89"
VERSION = "1.2.0"  # +self_check
TASK_ID = "33fcd12e6b89"
SUMMARY = "Move the non-marker object by the vector from marker 3 to marker 4."

INVARIANTS = [
    "there is exactly one color-3 source marker and one color-4 target marker",
    "all other nonzero cells form the translated object",
    "the translated object remains in bounds and does not cover either marker",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_3_marker", "no_4_marker", "no_object")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "object_with_3_4_markers",
                       "valid": "object_with_3_4_markers"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_SHAPES = [
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (1, 1), (2, 1)],
    [(0, 1), (1, 0), (1, 1), (1, 2)],
]
_VECTORS = [(2, 3), (3, 2), (-2, 3), (2, -3), (-2, -2)]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly one color-3 and one color-4 marker; ≥1 other nonzero cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    flat = [v for row in grid for v in row]
    n3 = flat.count(3)
    n4 = flat.count(4)
    if n3 != 1:
        errs.append(f"expected exactly 1 color-3 marker, found {n3}")
    if n4 != 1:
        errs.append(f"expected exactly 1 color-4 marker, found {n4}")
    other = [v for v in flat if v not in (0, 3, 4)]
    if not other:
        errs.append("no object cells (non-{0,3,4}) found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 7)
        w = ctx.draw_int("grid_w", 7, 7)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 10, 13)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 10)
    shape = rng.choice(_SHAPES)
    shape_h = max(r for r, _ in shape) + 1
    shape_w = max(c for _, c in shape) + 1
    color = rng.choice([2, 5, 6, 7, 8, 9])
    for _ in range(400):
        dr, dc = rng.choice(_VECTORS)
        src_r = rng.randint(max(0, -dr), min(h - 1, h - 1 - dr))
        src_c = rng.randint(max(0, -dc), min(w - 1, w - 1 - dc))
        src = (src_r, src_c)
        dst = (src_r + dr, src_c + dc)
        top = rng.randint(max(0, -dr), min(h - shape_h, h - shape_h - dr))
        left = rng.randint(max(0, -dc), min(w - shape_w, w - shape_w - dc))
        obj = {(top + r, left + c) for r, c in shape}
        moved = {(r + dr, c + dc) for r, c in obj}
        if src in obj or dst in obj or src in moved or dst in moved:
            continue
        g = full_grid(h, w, 0)
        g[src_r][src_c] = 3
        g[dst[0]][dst[1]] = 4
        for r, c in obj:
            g[r][c] = color
        return g
    raise RuntimeError("could not place vector translation instance")


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_3_marker":
        # 4-marker + object but no 3-marker — rule's source-of-vector
        # is undefined.
        g[5][6] = 4
        for r, c in [(2, 2), (2, 3), (3, 2)]: g[r][c] = 7
        return g
    if name == "no_4_marker":
        # 3-marker + object but no 4-marker — rule's target-of-vector
        # undefined.
        g[2][2] = 3
        for r, c in [(5, 5), (5, 6), (6, 5)]: g[r][c] = 7
        return g
    if name == "no_object":
        # Both markers but no object — rule has nothing to translate.
        g[2][2] = 3; g[5][6] = 4
        return g
    return g
