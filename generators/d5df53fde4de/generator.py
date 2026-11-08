"""Generator for 15b:m102 — frame each blob with key color.

Rule: a single corner key cell defines a key color. Each non-key blob
gets its bbox border painted with the key color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_key, no_blobs, blob_uses_key_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "d5df53fde4de"
VERSION = "2.2.0"
TASK_ID = "d5df53fde4de"
SUMMARY = (
    "0-bg grid with: (a) one KEY cell at the TOP-RIGHT corner (0, w-1) "
    "in some non-bg color cK; (b) 2-3 NON-RECTANGULAR blobs in distinct "
    "non-cK colors, placed in the interior. Each blob is 4-connected "
    "with bbox dims ≥2×2 and SHAPE differs from its bbox (so the "
    "rule's bbox-fill is visible). Rule: read key = g[0][w-1]. For "
    "each non-key blob, compute its bbox. Paint all cells in the bbox "
    "(including any bg holes) with the key color. Key cell preserved."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "key cell at (0, w-1) in some non-bg color",
    "2-3 non-key blobs in distinct colors (none == key color)",
    "each blob has shape that doesn't fill its bbox (so painting bbox is visible)",
    "blobs don't 4-touch the key or each other",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_key", "no_blobs", "blob_uses_key_color")
HELPFUL_TEXTURES = PALETTE_KINDS


_CANONICAL_NONRECT_SHAPES = (
    ((0, 0), (1, 0), (1, 1), (1, 2)),  # L, bbox 2x3
    ((0, 1), (1, 1), (1, 0), (2, 0)),  # skew stair, bbox 3x2
    ((0, 0), (0, 1), (0, 2), (1, 1)),  # T, bbox 2x3
    ((0, 1), (1, 0), (1, 1), (2, 1)),  # offset T, bbox 3x2
)


def _blob_teaches_bbox_fill(cells):
    """True when the blob's bbox fill is visible and non-degenerate."""
    if not cells:
        return False
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    bh = max(rs) - min(rs) + 1
    bw = max(cs) - min(cs) + 1
    return bh >= 2 and bw >= 2 and len(cells) < bh * bw


def _touches_reserved(cells, used):
    for r, c in cells:
        if (r, c) in used:
            return True
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (r + dr, c + dc) in used:
                return True
    return False


def _fallback_teaching_blob(rng, h, w, used):
    positions = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(positions)
    shapes = list(_CANONICAL_NONRECT_SHAPES)
    rng.shuffle(shapes)
    for r, c in positions:
        for shape in shapes:
            cells = {(r + dr, c + dc) for dr, dc in shape}
            if not all(0 <= rr < h and 0 <= cc < w for rr, cc in cells):
                continue
            if _touches_reserved(cells, used):
                continue
            return cells
    return None


def _grow_teaching_blob(rng, h, w, used):
    for _ in range(120):
        cells = grow_blob(rng, h, w, used, rng.randint(4, 6), max_attempts=8)
        if cells is not None and _blob_teaches_bbox_fill(cells):
            return cells
    return _fallback_teaching_blob(rng, h, w, used)


AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "9..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "2", "valid": "2..2"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "key_at_corner_with_blobs",
                       "valid": "key_at_corner_with_blobs"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 9, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 14, 18)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 11, 14)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 3)
    key = palette[0]
    g[0][w - 1] = key
    used = {(0, w - 1), (0, w - 2), (1, w - 1)}
    for color in palette[1:]:
        cells = _grow_teaching_blob(rng, h, w, used)
        if cells is None:
            continue
        for r, c in cells: g[r][c] = color
        # Reserve cells + 1-cell buffer
        for r, c in cells:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w:
                        used.add((nr, nc))
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_key":
        # blobs but no key cell → no color to frame with
        g[2][2] = 4; g[2][3] = 4; g[3][2] = 4
        g[5][6] = 6; g[5][7] = 6
        return g
    if name == "no_blobs":
        # key only, no blobs → nothing to frame
        g[0][w - 1] = 4
        return g
    if name == "blob_uses_key_color":
        # one of the blobs uses the same color as the key → no contrast
        g[0][w - 1] = 4
        g[2][2] = 4; g[2][3] = 4; g[3][2] = 4   # SAME as key color
        g[5][6] = 6
        return g
    return g



def _components_by_color(grid, bg=0):
    h = len(grid); w = len(grid[0]) if h else 0
    seen = [[False] * w for _ in range(h)]
    comps = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == bg or seen[r][c]:
                continue
            stack = [(r, c)]; seen[r][c] = True; cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] and grid[nr][nc] == color:
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    """Check the key-color bbox-border training structure is present."""
    errs = []
    h = len(grid); w = len(grid[0]) if h else 0
    if h == 0 or w == 0:
        return ["empty grid"]
    key = grid[0][w - 1]
    if key == 0:
        errs.append("top-right key cell is background")
    comps = _components_by_color(grid, 0)
    blobs = [(color, cells) for color, cells in comps
             if not (color == key and cells == [(0, w - 1)])]
    non_key = [(color, cells) for color, cells in blobs if color != key]
    if len(non_key) < 2:
        errs.append(f"expected at least two non-key blobs, found {len(non_key)}")
    colors = [color for color, _ in non_key]
    if len(colors) != len(set(colors)):
        errs.append("non-key blob colors are not distinct")
    for color, cells in non_key:
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        bh = max(rs) - min(rs) + 1
        bw = max(cs) - min(cs) + 1
        if bh < 2 or bw < 2:
            errs.append(f"blob color {color} has bbox {bh}x{bw}, expected >=2x2")
        if len(cells) >= bh * bw:
            errs.append(f"blob color {color} fills its bbox; border rule is hidden")
    if any(color == key for color, _ in blobs):
        extra = [cells for color, cells in blobs if color == key and cells != [(0, w - 1)]]
        if extra:
            errs.append("found a non-key blob using the key color")
    return errs
