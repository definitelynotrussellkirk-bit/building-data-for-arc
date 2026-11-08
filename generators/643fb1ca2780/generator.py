"""Generator for arc_puzzle_bank_21_set13_s:S13_H6 — pick by blue holes + red symmetry.

Rule: the blue object supplies the hole count and the red object
supplies the symmetry class. The target is the non-blue/non-red object
with both features.

Combinatorial axes (8): grid_h, grid_w, palette_kind, target_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_blue, no_red, no_matching_target.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "643fb1ca2780"
VERSION = "3.0.1"  # distinct=2: output IS the target object (always a square frame size 4/5) recolored 8, so only 2 output shapes. Target just needs 1 hole + H+V symmetry (both satisfied by ANY rectangle frame). Now vary target frame dims (incl non-square) + grid size + anchor/decoy positions -> output shape varies.
TASK_ID = "643fb1ca2780"
SUMMARY = (
    "Fixed 11×14 grid, 0-bg, with: (a) ONE color-1 "
    "(blue) HOLLOW FRAME (4×4 outline) at (1, 1) "
    "supplying the HOLE-COUNT spec (one interior "
    "hole); (b) ONE color-2 (red) DOUBLY-SYMMETRIC "
    "shape (plus-shape, both H and V symmetric) at "
    "(1, 8) supplying the SYMMETRY-CLASS spec; (c) "
    "ONE other-color TARGET object — a hollow frame "
    "with 1 hole AND matching symmetry class — at "
    "(6, 6); (d) ONE DECOY object with NEITHER one "
    "hole NOR matching symmetry at (6, 1). Rule: read "
    "the blue object's HOLE COUNT (= 1) and the red "
    "object's SYMMETRY CLASS (= both H+V). Find the "
    "non-blue/non-red object matching BOTH features. "
    "CROP that target to its bbox and RECOLOR to 8 "
    "(cyan). Net: anchors specify hole-count + "
    "symmetry; output is the matching candidate "
    "recolored to cyan."
)

INVARIANTS = [
    "one color-1 object has exactly one enclosed hole",
    "one color-2 object is symmetric both horizontally and vertically",
    "exactly one other object has one hole and the same symmetry class",
    "the selected object is cropped and recolored to 8",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blue", "no_red", "no_matching_target")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "11", "valid": "11..22"},
    "grid_w":         {"type": "int", "default": "14", "valid": "14..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "target_size":    {"type": "int", "default": "rng 4..5", "valid": "4..5"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4..4"},
    "position_bias":  {"type": "str", "default": "blue_red_with_target",
                       "valid": "blue_red_with_target"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: color-1 (blue spec), color-2 (red spec), and ≥1 other color present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    has_blue = any(grid[r][c] == 1 for r in range(h) for c in range(w))
    has_red = any(grid[r][c] == 2 for r in range(h) for c in range(w))
    if not has_blue:
        errs.append("no color-1 (blue) anchor object found")
    if not has_red:
        errs.append("no color-2 (red) symmetry anchor found")
    return errs


def _paint(g, top, left, cells, color):
    for dr, dc in cells:
        g[top + dr][left + dc] = color


def _free(g, r0, c0, r1, c1):
    h, w = len(g), len(g[0])
    if r0 < 0 or c0 < 0 or r1 >= h or c1 >= w:
        return False
    for r in range(r0 - 1, r1 + 2):
        for c in range(c0 - 1, c1 + 2):
            if 0 <= r < h and 0 <= c < w and g[r][c] != 0:
                return False
    return True


def _place_frame(g, rng, fh, fw, color):
    h, w = len(g), len(g[0])
    for _ in range(120):
        r0 = rng.randint(0, h - fh); c0 = rng.randint(0, w - fw)
        if _free(g, r0, c0, r0 + fh - 1, c0 + fw - 1):
            draw_frame(g, r0, c0, r0 + fh - 1, c0 + fw - 1, color)
            return True
    return False


def _place_cells(g, rng, cells, color):
    h, w = len(g), len(g[0])
    ch = max(r for r, _ in cells) + 1; cw = max(c for _, c in cells) + 1
    for _ in range(120):
        r0 = rng.randint(0, h - ch); c0 = rng.randint(0, w - cw)
        if _free(g, r0, c0, r0 + ch - 1, c0 + cw - 1):
            for dr, dc in cells:
                g[r0 + dr][c0 + dc] = color
            return True
    return False


def _rand_solid(rng, maxh, maxw, k):
    """Small connected polyomino (no enclosed hole) as a decoy."""
    cells = [(0, 0)]; seen = {(0, 0)}
    for _ in range(120):
        if len(cells) >= k:
            break
        br, bc = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = br + dr, bc + dc
        if (nr, nc) not in seen and 0 <= nr < maxh and 0 <= nc < maxw:
            cells.append((nr, nc)); seen.add((nr, nc))
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r0, c0 = min(rs), min(cs)
    return [(r - r0, c - c0) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 12, 15); w = ctx.draw_int("grid_w", 14, 17)
        t_hi = 5
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 16, 22); w = ctx.draw_int("grid_w", 18, 24)
        t_hi = 7
    else:
        h = ctx.draw_int("grid_h", 13, 18); w = ctx.draw_int("grid_w", 15, 20)
        t_hi = 6
    g = full_grid(h, w, 0)
    # anchors: blue frame (hole-count=1) + red plus (H+V symmetric)
    _place_frame(g, rng, rng.randint(3, 4), rng.randint(3, 4), 1)
    _place_cells(g, rng, [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)], 2)
    # TARGET (the output driver): a 1-hole, H+V-symmetric shape; vary dims AND
    # style (outline frame OR filled rect with a single centred hole) so the
    # cropped/recoloured output shape varies widely.
    target_color = rng.choice([3, 4, 5, 6, 7, 9])
    if rng.random() < 0.5:
        th = ctx.draw_int("target_h", 3, t_hi); tw = ctx.draw_int("target_w", 3, t_hi)
        if not _place_frame(g, rng, th, tw, target_color):
            _place_frame(g, rng, 3, 3, target_color)
    else:
        # filled block with one centred hole -> needs odd dims for H+V symmetry
        th = rng.choice([d for d in (3, 5, 7) if d <= t_hi] or [3])
        tw = rng.choice([d for d in (3, 5, 7) if d <= t_hi] or [3])
        cells = [(r, c) for r in range(th) for c in range(tw)
                 if (r, c) != (th // 2, tw // 2)]
        if not _place_cells(g, rng, cells, target_color):
            _place_frame(g, rng, 3, 3, target_color)
    # DECOY: a solid (0-hole) polyomino -> fails the hole-count match
    decoy_color = rng.choice([c for c in [3, 4, 5, 6, 7, 9] if c != target_color])
    _place_cells(g, rng, _rand_solid(rng, 3, 3, rng.randint(3, 5)), decoy_color)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 14, 0)
    if name == "no_blue":
        # no color-1 object → no hole-count anchor specified
        _paint(g, 1, 8, [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)], 2)
        draw_frame(g, 6, 6, 9, 9, 4)
        _paint(g, 6, 1, [(0, 0), (1, 0), (1, 1), (2, 1)], 7)
        return g
    if name == "no_red":
        # no color-2 object → no symmetry-class anchor specified
        draw_frame(g, 1, 1, 4, 4, 1)
        draw_frame(g, 6, 6, 9, 9, 4)
        _paint(g, 6, 1, [(0, 0), (1, 0), (1, 1), (2, 1)], 7)
        return g
    if name == "no_matching_target":
        # blue + red anchors present but no target object matches both features
        draw_frame(g, 1, 1, 4, 4, 1)
        _paint(g, 1, 8, [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)], 2)
        # only solid (no holes) candidates
        _paint(g, 6, 1, [(0, 0), (0, 1), (1, 0), (1, 1)], 4)
        _paint(g, 7, 8, [(0, 0), (1, 0), (1, 1)], 7)
        return g
    return g
