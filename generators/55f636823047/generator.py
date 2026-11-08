"""Generator for arc_puzzle_bank_ninth21:M62 — recolor matching query shape.

Rule: a small 8-blob is the query. Find a non-8 blob whose normalized
shape matches the query's; recolor the query in that blob's color.
Other shapes erased.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_query (no 8-blob → rule's query selector returns
nothing, no shape-matching), no_match (query present but no non-8
shape matches it → rule's match selector returns nothing, query stays
8), tied_match (≥2 non-8 shapes match the query → rule's "the matching
shape" is ambiguous, tie-break decides recolor target).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.shape import (
    L_TROMINO_NE, L_TROMINO_SE, T_TETROMINO, SQUARE_2X2, V_LINE_3, H_LINE_3,
)

GENERATOR_ID = "55f636823047"
VERSION = "2.0.1"
TASK_ID = "55f636823047"
SUMMARY = (
    "0-bg grid (h~8-11, w~"
    "11-13) with: (a) TWO "
    "REFERENCE BLOBS in 2 "
    "DISTINCT non-{0, 8} "
    "colors with DISTINCT "
    "NORMALIZED SHAPES drawn "
    "from {L_TROMINO_NE, "
    "L_TROMINO_SE, T_TETROMINO, "
    "SQUARE_2X2, V_LINE_3, "
    "H_LINE_3}; (b) ONE "
    "COLOR-8 (cyan) QUERY "
    "BLOB whose normalized "
    "shape MATCHES the FIRST "
    "REFERENCE blob (placed[0])"
    ". All blobs are placed "
    "without 4-touching (1-"
    "cell padding). Rule "
    "(RECOLOR QUERY TO "
    "MATCHING REFERENCE, "
    "ERASE NON-MATCH): "
    "identify the 8-QUERY "
    "and the 2 REFERENCE "
    "blobs. For each REFERENCE, "
    "check if its normalized "
    "shape EQUALS the query's. "
    "RECOLOR the 8-query in "
    "the MATCHING reference's "
    "COLOR. ERASE the other "
    "(non-matching) reference. "
    "Net: query inherits the "
    "color of its shape-twin "
    "reference; the lone "
    "shape vanishes."
)

INVARIANTS = [
    "background is 0",
    "≥2 non-8 reference blobs of distinct normalized shapes",
    "exactly one 8-blob (query) whose shape matches one reference",
    "blobs don't 4-touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_query", "no_match", "tied_match")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":            {"type": "int", "default": "rng 11..13", "valid": "9..14"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 3..3", "valid": "3..3"},
    "position_bias":     {"type": "str", "default": "references_plus_query",
                          "valid": "references_plus_query"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..3", "valid": "3..3"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _bbox_dims(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    return max(rs) + 1, max(cs) + 1


def _free(g, r0, c0, cells):
    h, w = len(g), len(g[0])
    for r, c in cells:
        rr, cc = r0 + r, c0 + c
        if not (0 <= rr < h and 0 <= cc < w):
            return False
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = rr + dr, cc + dc
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0:
                    return False
    return True


_SHAPES = [L_TROMINO_NE, L_TROMINO_SE, T_TETROMINO, SQUARE_2X2, V_LINE_3, H_LINE_3]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 11, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 11)
        w = ctx.draw_int("grid_w", 13, 13)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 11, 13)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    shapes = rng.sample(_SHAPES, 2)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 2)
    placed = []
    for shape, color in zip(shapes, palette):
        sh, sw = _bbox_dims(shape)
        for _ in range(40):
            r0 = rng.randint(0, h - sh)
            c0 = rng.randint(0, w - sw)
            if _free(g, r0, c0, shape):
                paint_at(g, r0, c0, shape, color)
                placed.append((shape, color))
                break
    if placed:
        query_shape = placed[0][0]
        sh, sw = _bbox_dims(query_shape)
        for _ in range(40):
            r0 = rng.randint(0, h - sh)
            c0 = rng.randint(0, w - sw)
            if _free(g, r0, c0, query_shape):
                paint_at(g, r0, c0, query_shape, 8)
                break
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, at least one color-8 blob and at least one non-8 blob present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        errs.append("ragged grid")
        return errs
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    has_8 = any(grid[r][c] == 8 for r in range(h) for c in range(w))
    non8 = {grid[r][c] for r in range(h) for c in range(w)
            if grid[r][c] not in (0, 8)}
    if not has_8:
        errs.append("no color-8 query blob found")
    if not non8:
        errs.append("no non-8 reference blob found")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 9, 12
    g = full_grid(h, w, 0)
    if name == "no_query":
        # No 8-blob — rule's query selector returns nothing.
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            g[1 + dr][1 + dc] = 4
        for dr, dc in [(0, 0), (0, 1), (0, 2)]:
            g[5 + dr][6 + dc] = 6
        return g
    if name == "no_match":
        # 8-query exists but no non-8 reference matches its shape.
        for dr, dc in [(0, 0), (0, 1), (0, 2)]:
            g[1 + dr][1 + dc] = 4   # H_LINE_3
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            g[5 + dr][3 + dc] = 8   # L_TROMINO — different from H_LINE_3
        return g
    if name == "tied_match":
        # Two non-8 references share the query's shape — match is
        # ambiguous; tie-break decides recolor target.
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            g[1 + dr][1 + dc] = 4   # L
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            g[1 + dr][8 + dc] = 6   # same L
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            g[5 + dr][4 + dc] = 8   # query L
        return g
    return g
