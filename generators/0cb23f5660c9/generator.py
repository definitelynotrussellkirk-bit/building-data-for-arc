"""Generator for 21b:m141 — select legend object and rotate clockwise.

Rule: a single legend cell at (0,0) names a target color. Among the
multi-cell shapes, the one matching that color gets cropped and
rotated 90° clockwise. Output is the rotated shape.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_legend, no_matching_shape, symmetric_shape.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0cb23f5660c9"
VERSION = "3.0.1"  # + self_check
TASK_ID = "0cb23f5660c9"
SUMMARY = (
    "0-bg grid (h~9-11, w~11-13) with: (a) cell (0, 0) "
    "holds a LEGEND color C ∈ {1..9, ≠0}; (b) 3 "
    "isolated 4-conn shapes (4-cell tetrominoes) in 3 "
    "distinct colors placed elsewhere; one of the shape "
    "colors equals the legend color C. Rule: read C = "
    "g[0][0]. Find the (multi-cell) shape whose color = "
    "C. Crop to its bbox. ROTATE 90° CLOCKWISE. "
    "Output: the rotated cropped shape (in color C)."
)

INVARIANTS = [
    "background is 0",
    "legend cell at (0,0) is a non-bg color C",
    "exactly 3 multi-cell shapes elsewhere; one is color C",
    "the C-shape's CW rotation differs from itself (so output isn't degenerate)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_legend", "no_matching_shape", "symmetric_shape")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "8..15"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "10..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "legend_with_shapes",
                       "valid": "legend_with_shapes"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

def _poly(rng, size):
    """Random connected polyomino of `size` cells (normalized, asymmetric
    shapes welcome so the CW rotation is visible)."""
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        cells.add((r + dr, c + dc))
    minr = min(r for r, c in cells)
    minc = min(c for r, c in cells)
    return [(r - minr, c - minc) for r, c in cells]


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _place(g, rng, shape, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    for _ in range(40):
        r0 = rng.randint(1, h - sh); c0 = rng.randint(1, w - sw)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = color
        return True
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: (0,0) has non-zero legend; >=1 multi-cell shape matching that color."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    legend = grid[0][0]
    if legend == 0:
        errs.append("cell (0,0) is 0: no legend color defined")
        return errs
    # find 4-connected components of legend color (excluding (0,0))
    seen: set = set()
    legend_shapes = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == legend and (r, c) not in seen and (r, c) != (0, 0):
                stack = [(r, c)]
                comp: list = []
                seen.add((r, c))
                while stack:
                    cr, cc = stack.pop()
                    comp.append((cr, cc))
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = cr + dr, cc + dc
                        if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == legend
                                and (nr, nc) not in seen):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
                if len(comp) > 1:
                    legend_shapes.append(comp)
    if not legend_shapes:
        errs.append(f"no multi-cell shape with legend color {legend}: rule finds nothing to rotate")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
        n_shapes = 3
        size_lo, size_hi = 3, 5
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 15)
        w = ctx.draw_int("grid_w", 13, 16)
        n_shapes = 4
        size_lo, size_hi = 4, 7
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 11, 14)
        n_shapes = 3
        size_lo, size_hi = 3, 6
    rng = ctx.draw_rng("layout")
    if difficulty != "easy":
        n_shapes = rng.randint(3, 4)
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], n_shapes)
    legend_color = palette[0]
    g[0][0] = legend_color
    # Each color is a single random polyomino of varied size (the target color's
    # object is unique, hence trivially the largest of its color). The legend
    # color MUST place (shrink + retry until it does).
    for color in palette:
        ok = False
        for size in range(rng.randint(size_lo, size_hi), 2, -1):
            if _place(g, rng, _poly(rng, size), color):
                ok = True
                break
        if not ok and color == legend_color:
            _place(g, rng, [(0, 0), (0, 1), (1, 0)], color)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_legend":
        # Shapes but (0,0) empty — rule's color-selector has no
        # input.
        for r, c in [(3, 3), (3, 4), (3, 5), (4, 4)]: g[r][c] = 4
        for r, c in [(7, 8), (8, 8), (8, 9)]: g[r][c] = 6
        return g
    if name == "no_matching_shape":
        # Legend names a color absent from body shapes — rule's
        # selector finds nothing.
        g[0][0] = 7
        for r, c in [(3, 3), (3, 4), (4, 3)]: g[r][c] = 4
        for r, c in [(7, 8), (8, 8), (8, 9)]: g[r][c] = 6
        return g
    if name == "symmetric_shape":
        # The selected shape is rotation-invariant — rule's CW
        # rotation produces the same shape; rule's effect invisible.
        g[0][0] = 4
        for r in range(3, 5):
            for c in range(3, 5): g[r][c] = 4
        for r, c in [(7, 8), (8, 8), (8, 9)]: g[r][c] = 6
        return g
    return g
