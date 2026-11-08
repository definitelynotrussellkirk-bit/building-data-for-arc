"""Generator for arc_puzzle_bank_21_set15:S15_E2.

Combinatorial axes (8): height, width, palette_kind, marker_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_template, no_markers, marker_overlaps_template.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2855283336a4"
VERSION = "1.2.1"
TASK_ID = "2855283336a4"
SUMMARY = "One color-2 template is stamped at every color-1 marker using top-left-relative offsets."

INVARIANTS = [
    "background is 0",
    "there is exactly one color-2 template component",
    "there are two to four color-1 marker cells",
    "template stamps at the markers do not overlap the template or each other",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_template", "no_markers", "marker_overlaps_template")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "height":         {"type": "int", "default": "rng 10..13", "valid": "8..16"},
    "width":          {"type": "int", "default": "rng 12..15", "valid": "9..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "marker_count":   {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "template_left_markers_scattered",
                       "valid": "template_left_markers_scattered"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: color-2 template present, ≥2 color-1 marker cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_template", "no_markers", "marker_overlaps_template"):
        return []
    errs = []
    c1 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 1)
    c2 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 2)
    if c2 == 0:
        errs.append("no color-2 template cells")
    if c1 < 2:
        errs.append(f"only {c1} color-1 marker cell(s); expected ≥2")
    return errs


_SHAPES = [
    [(0, 0), (0, 2), (1, 0), (1, 1), (1, 2)],
    [(0, 0), (1, 0), (1, 1), (2, 0)],
    [(0, 0), (0, 1), (1, 1), (2, 1)],
    [(0, 1), (1, 0), (1, 1), (1, 2)],
]


def _size(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _stamp_cells(anchor, shape):
    ar, ac = anchor
    return {(ar + dr, ac + dc) for dr, dc in shape}


def _box_free(g, r0, c0, sh, sw, pad=1):
    h, w = len(g), len(g[0])
    if r0 < 0 or c0 < 0 or r0 + sh > h or c0 + sw > w:
        return False
    for r in range(max(0, r0 - pad), min(h, r0 + sh + pad)):
        for c in range(max(0, c0 - pad), min(w, c0 + sw + pad)):
            if g[r][c] != 0:
                return False
    return True


def _paint(g, r0, c0, shape, color):
    for dr, dc in shape:
        g[r0 + dr][c0 + dc] = color


def _place_template(g, rng, shape):
    sh, sw = _size(shape)
    h, w = len(g), len(g[0])
    for _ in range(80):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, max(0, w // 2 - sw))
        if _box_free(g, r0, c0, sh, sw):
            _paint(g, r0, c0, shape, 2)
            return
    raise ValueError("could not place template")


def _place_markers(g, rng, shape, count):
    sh, sw = _size(shape)
    h, w = len(g), len(g[0])
    anchors = []
    # `occupied` is the set of cells that would already be part of a stamped
    # template copy.  It MUST include the original color-2 template cells.  The
    # previous code only tracked marker-stamp footprints, so a marker could be
    # placed near the template with its future stamp overlapping the source
    # template.  That hides the intended copy operation in the demos: a learner
    # sees a marker whose stamp is partially pre-filled before the rule fires.
    occupied = {(r, c)
                for r, row in enumerate(g)
                for c, v in enumerate(row)
                if v != 0}
    for _ in range(300):
        if len(anchors) == count:
            return
        r = rng.randint(0, h - sh)
        c = rng.randint(0, w - sw)
        cells = _stamp_cells((r, c), shape)
        if g[r][c] != 0 or cells & occupied:
            continue
        if any(abs(r - ar) < sh + 1 and abs(c - ac) < sw + 1 for ar, ac in anchors):
            continue
        anchors.append((r, c))
        occupied |= cells
        g[r][c] = 1
    raise ValueError("could not place non-overlapping markers")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("height", 10, 11)
        w = ctx.draw_int("width", 12, 13)
        marker_count = ctx.draw_int("marker_count", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("height", 13, 16)
        w = ctx.draw_int("width", 15, 18)
        marker_count = ctx.draw_int("marker_count", 4, 5)
    else:
        h = ctx.draw_int("height", 10, 13)
        w = ctx.draw_int("width", 12, 15)
        marker_count = ctx.draw_int("marker_count", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    shape = rng.choice(_SHAPES)
    _place_template(g, rng, shape)
    _place_markers(g, rng, shape, marker_count)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 11, 13
    g = full_grid(h, w, 0)
    if name == "no_template":
        # No color-2 template — rule has no shape to stamp.
        g[5][8] = 1; g[7][10] = 1
        return g
    if name == "no_markers":
        # Template but no markers — rule has no anchors, output is just template.
        for dr, dc in _SHAPES[0]: g[2 + dr][2 + dc] = 2
        return g
    if name == "marker_overlaps_template":
        # Marker inside template bbox — stamp anchor is ambiguous.
        for dr, dc in _SHAPES[0]: g[2 + dr][2 + dc] = 2
        g[3][3] = 1
        return g
    return g
