"""Generator for 83b6b474.

Rule: border fragments are classified by edge type and repacked into
the smallest square.

Combinatorial axes (8): grid_h/w, offset, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_fragments, single_fragment, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9733a2d68593"
RULE_HASH = "83938db8863a"  # canonical rule this generator was written against
VERSION = "2.1.0"
TASK_ID = "9733a2d68593"
RULE_TASK_ID = TASK_ID
CONSTRUCTION_ALGORITHM_ID = "independent-role-shapes-then-scatter-v1"
SUMMARY = (
    "Five border fragments (a top-left corner, a top bar, a bottom-left and "
    "bottom-right corner, and a side piece) in distinct colours are SCATTERED at "
    "random non-overlapping positions on a nonzero modal-background grid. Rule: "
    "classify each fragment by edge type (shape-based) and repack them into a "
    "compact square frame. Fragment colours, background, positions and grid size vary."
)

INVARIANTS = [
    "background is the modal color and is normally nonzero",
    "each non-background object is a border fragment",
    "fragments include top, corner, and side classes",
    "the output packs classified fragments into a compact square frame layout",
]

OFFSET_KINDS = ("o0", "o1")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_fragments", "single_fragment", "full_grid")
HELPFUL_TEXTURES = OFFSET_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "12-16 by difficulty", "valid": "11..18"},
    "grid_w":         {"type": "int", "default": "16-20 by difficulty", "valid": "14..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "palette_size":   {"type": "int", "default": "5", "valid": "5"},
    "position_bias":  {"type": "str", "default": "scattered_fragments",
                       "valid": "scattered_fragments"},
    "background_color":{"type": "int", "default": "rng nonzero", "valid": "1..9"},
    "n_distinct_colors":{"type": "int", "default": "6 incl. background", "valid": "6"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_fragments|single_fragment|full_grid"},
}

# the 5 border-fragment shapes (normalised); the rule's classifier keys on these
_FRAGMENTS = [
    [(0, 0), (0, 1), (1, 0), (2, 0)],            # top-left corner
    [(0, 0), (0, 1), (0, 2)],                    # top bar
    [(0, 0), (1, 0), (2, 0), (2, 1)],            # bottom-left corner
    [(0, 2), (1, 2), (2, 0), (2, 1), (2, 2)],    # bottom-right corner
    [(0, 0), (1, 0)],                            # side piece
]


def _gen_fragments(rng):
    """Five border fragments with VARIED dimensions but preserved classes
    (the rule's classifier keys on full-row/full-col tests, not exact size):
    top-bar (1xW), top-left (full row0 + full col0), bottom-left (full last
    row + full col0), bottom-right (full last row + full last col), side (Hx1)."""
    tl_h = rng.randint(2, 4); tl_w = rng.randint(2, 4)
    top_w = rng.randint(2, 4)
    bl_h = rng.randint(2, 4); bl_w = rng.randint(2, 4)
    br_h = rng.randint(2, 4); br_w = rng.randint(2, 4)
    side_h = rng.randint(2, 4)
    top_left = [(0, c) for c in range(tl_w)] + [(r, 0) for r in range(1, tl_h)]
    top_bar = [(0, c) for c in range(top_w)]
    bottom_left = [(bl_h - 1, c) for c in range(bl_w)] + [(r, 0) for r in range(bl_h - 1)]
    bottom_right = [(br_h - 1, c) for c in range(br_w)] + [(r, br_w - 1) for r in range(br_h - 1)]
    side = [(r, 0) for r in range(side_h)]
    return [top_left, top_bar, bottom_left, bottom_right, side]


def _scatter(g, rng, shape, color, bg):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    for _ in range(80):
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        cells = {(r0 + dr, c0 + dc) for dr, dc in shape}
        halo = {(r + a, c + b) for (r, c) in cells for a in (-1, 0, 1) for b in (-1, 0, 1)}
        if any(g[r][c] != bg for r, c in halo if 0 <= r < h and 0 <= c < w):
            continue
        for r, c in cells:
            g[r][c] = color
        return True
    return False


def _paint(g, cells, color):
    for r, c in cells:
        g[r][c] = color


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: modal background plus exactly 5 fragment colors when non-degenerate."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    texture = (meta or {}).get("texture", "")
    if texture == "no_fragments":
        return []
    colors = {v for row in grid for v in row if v != bg}
    if not colors:
        return []
    if len(colors) != 5:
        return [f"expected exactly 5 fragment colors over modal bg {bg}; found {len(colors)}: {sorted(colors)}"]
    if bg == 0 and texture not in DEGENERATE_TEXTURES:
        return ["expected nonzero modal background to match canonical task convention"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h, w = 12, 16
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 18); w = ctx.draw_int("grid_w", 18, 22)
    else:
        h = ctx.draw_int("grid_h", 12, 15); w = ctx.draw_int("grid_w", 16, 19)
    palette = ctx.draw_distinct_colors("colors", n=6, exclude={0})
    bg, colors = palette[0], palette[1:]
    for _outer in range(20):
        g = full_grid(h, w, bg)
        fragments = _gen_fragments(rng)
        if all(_scatter(g, rng, shape, colors[i], bg) for i, shape in enumerate(fragments)):
            return g
    return g   # rare fallback (last attempt, possibly partial)


def _draw_from_degenerate(name, rng):
    bg = (rng.choice([1, 2, 4, 6, 7, 8, 9]) if rng is not None else 2)
    g = full_grid(12, 16, bg)
    frag = 3 if bg != 3 else 4
    if name == "no_fragments":
        return g
    if name == "single_fragment":
        _paint(g, [(1, 1), (1, 2), (2, 1)], frag)
        return g
    if name == "full_grid":
        for r in range(12):
            for c in range(16):
                g[r][c] = frag
        return g
    return g
