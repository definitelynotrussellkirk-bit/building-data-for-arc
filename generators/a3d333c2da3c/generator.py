"""Generator for e41c6fd3.

Rule: every object shifts vertically so its top row aligns with the top
row of the cyan(8) object.

Combinatorial axes (8): grid_h/w, object_count, target_row, palette_kind,
position_bias, anchor_corner, asymmetry_force, palette_size.
Degenerates: no_target, no_others, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a3d333c2da3c"
VERSION = "2.1.0"  # force at least one non-8 object to start on a different row; self_check catches identity demos.
TASK_ID = "a3d333c2da3c"
SUMMARY = "Every object shifts vertically to align its top row with the colour-8 object's top row."

INVARIANTS = [
    "background is color 0",
    "one object uses color 8 and supplies the target top row",
    "all objects are separated by columns so vertical alignment cannot collide",
    "object columns and internal shapes are preserved",
]

POSITION_BIASES = ("scattered", "row_offset", "tight", "spread")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_target", "no_others", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 12..14", "valid": "10..18"},
    "grid_w":         {"type": "int", "default": "12", "valid": "10..16"},
    "object_count":   {"type": "int", "default": "3", "valid": "2..5"},
    "target_row":     {"type": "int", "default": "rng 4..5", "valid": "3..7"},
    "palette_kind":   {"type": "str", "default": "rng",
                       "valid": "warm|cool|broad|primary"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "scattered|row_offset|tight|spread"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..4"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "scattered|row_offset|tight|spread|no_target|no_others|full_grid"},
}


def _paint(g, r0, c0, cells, color):
    for dr, dc in cells:
        if 0 <= r0 + dr < len(g) and 0 <= c0 + dc < len(g[0]):
            g[r0 + dr][c0 + dc] = color


def _color_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for sr in range(h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            q = [(sr, sc)]; seen.add((sr, sc)); cells = []
            while q:
                r, c = q.pop(); cells.append((r, c))
                for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); q.append((nr, nc))
            comps.append((color, cells, min(r for r, _ in cells)))
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: color-8 anchor plus at least one object that actually moves."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    comps = _color_components(grid)
    eights = [c for c in comps if c[0] == 8]
    others = [c for c in comps if c[0] not in (0, 8)]
    if not eights:
        errs.append("no color-8 object (alignment anchor) present")
        return errs
    if not others:
        errs.append("no non-8 non-bg objects to align")
        return errs
    anchor_top = min(c[2] for c in eights)
    if not any(c[2] != anchor_top for c in others):
        errs.append("all non-8 objects already share the anchor top row; output would equal input")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 10, 12
        oc_lo, oc_hi = 2, 3
    elif difficulty == "hard":
        h_lo, h_hi = 14, 18
        oc_lo, oc_hi = 4, 5
    else:
        h_lo, h_hi = 12, 14
        oc_lo, oc_hi = 2, 5
    object_count = int(overrides.get("object_count",
                                     ctx.draw_int("object_count", oc_lo, oc_hi)))
    object_count = max(2, min(5, object_count))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    pal = _build_palette(palette_kind, max(2, object_count - 1), rng)
    h = ctx.draw_int("grid_h", h_lo, h_hi)

    shapes = [
        [(0, 0), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0)],
        [(0, 0), (1, 0), (0, 1), (1, 1)],
        [(0, 0), (0, 1), (0, 2)],
        [(0, 1), (1, 0), (1, 1), (1, 2)],
    ]
    # one band per object; the 8-object sits at a random band. Each band is
    # column-separated by a gap so objects-multicolor (8-connected) never merges
    # them — guaranteeing the colour-8 object stays a distinct object.
    eight_idx = rng.randrange(object_count)
    bands = []
    for i in range(object_count):
        sh = shapes[i % len(shapes)] if i != eight_idx else [(0, 0), (0, 1), (1, 1)]
        bw = max(c for _, c in sh) + 1
        bands.append((sh, bw))
    total = sum(bw for _, bw in bands) + (object_count - 1) * 2   # +2-col gaps
    w = max(int(overrides.get("grid_w", total + 2)), total + 2)

    placements = []
    for i, (sh, _bw) in enumerate(bands):
        ish = max(r for r, _ in sh) + 1
        placements.append(rng.randint(0, max(0, h - ish - 1)))
    anchor_row = placements[eight_idx]
    if all((i == eight_idx) or (r == anchor_row) for i, r in enumerate(placements)):
        # Avoid identity demos: move one non-8 object while staying in bounds.
        j = 0 if eight_idx != 0 else 1
        ish = max(r for r, _ in bands[j][0]) + 1
        if anchor_row + 2 <= h - ish - 1:
            placements[j] = anchor_row + 2
        else:
            placements[j] = max(0, anchor_row - 2)

    g = full_grid(h, w, 0)
    cx = 1
    for i, (sh, bw) in enumerate(bands):
        color = 8 if i == eight_idx else pal[(i if i < eight_idx else i - 1) % len(pal)]
        _paint(g, placements[i], cx, sh, color)
        cx += bw + 2
    return g


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 9]
    pool = [c for c in pool if c not in (0, 8)]
    rng.shuffle(pool)
    if len(pool) < n:
        for c in [1, 2, 3, 4, 5, 6, 7, 9]:
            if c not in pool:
                pool.append(c)
            if len(pool) >= n:
                break
    return pool[:n]


def _draw_from_degenerate(name, rng):
    h, w = 12, 12
    g = full_grid(h, w, 0)
    if name == "no_target":
        g[2][2] = 3; g[3][2] = 3; g[3][3] = 3
        return g
    if name == "no_others":
        g[5][5] = 8; g[5][6] = 8; g[6][6] = 8
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 8
        return g
    return g
