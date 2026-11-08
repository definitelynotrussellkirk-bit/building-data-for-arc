"""Generator for 15b:m99 — transform object by corner code.

Rule: cell (0,0) holds a transform code; the rest of the grid contains
a single shape. Output is that shape cropped and transformed per code.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_code, no_shape, symmetric_shape.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7bc276d26134"
VERSION = "2.0.1"
TASK_ID = "7bc276d26134"
SUMMARY = (
    "0-bg grid (h~8-10, w~9-11) with: (a) cell (0,0) = TRANSFORM "
    "CODE value in {1..7}; (b) one connected ASYMMETRIC shape "
    "(3-5 cells) of a single non-bg color, placed in the interior "
    "(not touching (0,0)). Rule: read code = grid[0][0]. Clear "
    "(0,0) to 0. Crop the rest of the grid to its non-zero bbox "
    "(the shape). Apply transform: 1 → identity, 2 → rotate-CW, "
    "3 → rotate-180, 4 → rotate-CCW, 5 → flip-LR, 6 → flip-UD, "
    "7 → transpose. Output is the transformed crop (small grid)."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "cell (0,0) is a transform code in {1..7}",
    "exactly one multi-cell shape elsewhere, isolated and asymmetric",
    "shape's color != code value (so they don't collide visually)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_code", "no_shape", "symmetric_shape")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "code_corner_with_shape",
                       "valid": "code_corner_with_shape"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: g[0][0] is a transform code in {1..7} (or 0 for no_code degenerate),
    and ≥1 nonzero cell exists outside (0,0)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    code = grid[0][0]
    if code not in range(8):  # 0 (no_code degenerate) or 1..7
        return [f"g[0][0]={code} not in {{0..7}}"]
    nz_body = sum(1 for r in range(h) for c in range(w)
                  if not (r == 0 and c == 0) and grid[r][c] != 0)
    if nz_body < 1:
        return ["expected ≥1 nonzero body cell outside (0,0); found none"]
    return []


_ASYM_SHAPES = [
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (1, 1), (2, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 0)],
    [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)],
]


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 11, 14)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 11)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    code = rng.randint(1, 7)
    g[0][0] = code
    color = rng.choice([1, 3, 4, 5, 6, 7, 8, 9])
    if color == code:
        color = (code % 9) + 1 if (code % 9) + 1 != code else 2
    shape = rng.choice(_ASYM_SHAPES)
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    for _ in range(40):
        r0 = rng.randint(2, h - sh); c0 = rng.randint(2, w - sw)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = color
        break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_code":
        # Body shape but cell (0,0) empty — rule's transform code
        # lookup fails; transform undefined.
        for r, c in [(3, 3), (4, 3), (5, 3), (5, 4)]: g[r][c] = 4
        return g
    if name == "no_shape":
        # Code but no body shape — rule has nothing to transform.
        g[0][0] = 2
        return g
    if name == "symmetric_shape":
        # Symmetric body shape — every transform code produces
        # the same output; rule's effect is invisible.
        g[0][0] = 2
        for r, c in [(3, 3), (3, 4), (4, 3), (4, 4)]: g[r][c] = 4
        return g
    return g
