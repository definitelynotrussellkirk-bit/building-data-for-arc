"""Generator for arc_additional_puzzles_21_set8:E55.

Rule: a colored motif is placed away from the outer border; output is
the motif cropped to its bounding box.

Combinatorial axes (8): grid_h/w, palette_kind, motif_position,
palette_size, position_bias, n_distinct_colors, motif_density, texture.
Degenerates: motif_at_border, motif_fills_grid, no_motif.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c7e852398e08"
VERSION = "1.3.0"  # shape-locked-out fixed in 1.2; 1.3 forces >=2 visible motif colors so crop outputs cannot collapse to single-color fields."
TASK_ID = "c7e852398e08"
SUMMARY = "A colored motif is placed away from the outer border and then cropped to content."

INVARIANTS = [
    "zero padding surrounds the motif on every side",
    "the motif's bounding box is smaller than the input grid",
]

PALETTE_KINDS = ("default", "warm", "cool", "rainbow")
DEGENERATE_TEXTURES = ("motif_at_border", "motif_fills_grid", "no_motif")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "motif_position": {"type": "str", "default": "interior",
                       "valid": "interior"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "interior",
                       "valid": "interior"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "motif_density":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9); w = ctx.draw_int("grid_w", 9, 11); k_lo, k_hi = 3, 5
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 14); w = ctx.draw_int("grid_w", 11, 14); k_lo, k_hi = 5, 9
    else:
        h = ctx.draw_int("grid_h", 8, 12); w = ctx.draw_int("grid_w", 9, 13); k_lo, k_hi = 4, 7
    n_col = ctx.draw_int("n_colors_used", 2, 3)
    colors = list(ctx.draw_distinct_colors("colors", n=n_col, exclude=[0]))
    # random connected motif; bbox kept smaller than the grid (rule = crop-to-content,
    # so output dims = the motif bbox -> varies incl. non-square)
    motif = _poly(rng, rng.randint(k_lo, k_hi))
    mh = max(r for r, _ in motif) + 1; mw = max(c for _, c in motif) + 1
    if mh > h - 2:
        motif = [(r, c) for r, c in motif if r < h - 2]; mh = max((r for r, _ in motif), default=0) + 1
    if mw > w - 2:
        motif = [(r, c) for r, c in motif if c < w - 2]; mw = max((c for _, c in motif), default=0) + 1
    g = full_grid(h, w, 0)
    top = rng.randint(1, max(1, h - 1 - mh)); left = rng.randint(1, max(1, w - 1 - mw))
    used_colors = set()
    for (dr, dc) in motif:
        color = rng.choice(colors)
        g[top + dr][left + dc] = color
        used_colors.add(color)
    if len(used_colors) < 2 and len(motif) >= 2:
        dr, dc = motif[-1]
        g[top + dr][left + dc] = next(c for c in colors if c != next(iter(used_colors)))
    return g


def _content_bbox(g):
    cells = [(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v != 0]
    if not cells:
        return None
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    h, w = len(grid), len(grid[0]) if grid else 0
    bb = _content_bbox(grid)
    if bb is None:
        return ["no motif/content cells"]
    r1, c1, r2, c2 = bb
    if r1 == 0 or c1 == 0 or r2 == h - 1 or c2 == w - 1:
        msgs.append("motif touches outer border; crop-to-content padding hidden")
    if r1 == 0 and r2 == h - 1 and c1 == 0 and c2 == w - 1:
        msgs.append("motif bbox fills the input grid")
    crop_vals = [grid[r][c] for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]
    nz_colors = {v for v in crop_vals if v != 0}
    if len(nz_colors) < 2:
        msgs.append("cropped motif has fewer than 2 visible nonzero colors")
    if len(set(crop_vals)) < 2:
        msgs.append("cropped output would be a single-color field")
    return msgs


def _poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "motif_at_border":
        # motif touches the top-left corner — zero-padding invariant violated
        for dr, dc, color in [(0, 0, 2), (0, 1, 2), (1, 1, 3), (2, 1, 3), (2, 3, 4)]:
            g[dr][dc] = color
        return g
    if name == "motif_fills_grid":
        # motif fills entire grid — crop equals input (rule trivial)
        for r in range(h):
            for c in range(w):
                g[r][c] = ((r + c) % 3) + 2
        return g
    if name == "no_motif":
        # empty grid — nothing to crop
        return g
    return g
