"""Generator for arc_puzzle_bank_21_set14_s:S14_E1.

Rule: connected components have per-row holes that are closed into horizontal spans.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_components, no_row_gap, single_cell_objects.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import components, components_have_clearance, color_counts, has_row_gap, interior_cells, is_full_frame_component, norm

GENERATOR_ID = "5f8201e3482c"
VERSION = "2.1.0"  # fix disconnected no-fire shape, hard-count color cap, and placement retries
TASK_ID = "5f8201e3482c"
SUMMARY = (
    "0-bg grid (h×w, ~9-14 by ~12-17) with 2-5 connected motifs "
    "in distinct non-zero colors. Each motif is placed with ≥1-"
    "cell buffer. At least one motif has rows where its cells are "
    "non-contiguous (a gap between the leftmost and rightmost "
    "cell in some row). Rule: for each connected component, "
    "iterate over its rows. If a row has the component's color "
    "at multiple positions with at least one 0 between leftmost "
    "and rightmost, fill the entire span [leftmost..rightmost] "
    "with that component's color. Rows with no gap stay "
    "unchanged. Other components (no gaps) are preserved."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "2-5 connected motifs in distinct non-zero colors",
    "motifs are ≥1-cell isolated (no 8-conn touch)",
    "every helpful motif is 4-connected and has at least one row with a horizontal gap (rule fires on every component)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_components", "no_row_gap", "single_cell_objects")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "height":         {"type": "int", "default": "rng 9..12", "valid": "7..15"},
    "width":          {"type": "int", "default": "rng 12..15", "valid": "9..18"},
    "component_count":{"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "rng 2..5", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "scattered_with_row_gaps",
                       "valid": "scattered_with_row_gaps"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..5", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_components|no_row_gap|single_cell_objects"},
}

_SHAPES = [
    [(0, 0), (0, 2), (1, 0), (1, 1), (1, 2)],
    [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)],
    [(0, 0), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)],
    # Keep every helpful motif 4-connected AND row-gap-bearing. The old
    # variant ``[(0,0),(0,2),(1,0),(1,1),(2,1),(2,2)]`` left the
    # top-right cell disconnected, so the canonical per-component row-span rule
    # often had no component row with a gap and output==input.
    [(0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)],
]


def _size(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _free(g, r0, c0, shape, pad=1):
    h, w = len(g), len(g[0])
    sh, sw = _size(shape)
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


def _place(g, rng, shape, color):
    h, w = len(g), len(g[0])
    sh, sw = _size(shape)
    for _ in range(160):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        if _free(g, r0, c0, shape):
            _paint(g, r0, c0, shape, color)
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("height", 9, 9)
        w = ctx.draw_int("width", 12, 13)
        count = ctx.draw_int("component_count", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("height", 12, 14)
        w = ctx.draw_int("width", 15, 17)
        count = ctx.draw_int("component_count", 4, 5)
    else:
        h = ctx.draw_int("height", 9, 12)
        w = ctx.draw_int("width", 12, 15)
        count = ctx.draw_int("component_count", 2, 4)

    # Five colors for the hard-band count=5 case; the old 4-color list silently
    # capped a requested 5-motif example at 4 motifs.
    base_colors = [2, 3, 4, 6, 7]
    for attempt in range(24):
        rng = ctx.draw_rng("layout" if attempt == 0 else f"layout_retry_{attempt}")
        g = full_grid(h, w, 0)
        colors = base_colors[:]
        rng.shuffle(colors)
        ok = True
        for color in colors[:count]:
            if not _place(g, rng, rng.choice(_SHAPES), color):
                ok = False
                break
        if ok:
            return g

    # Deterministic, rule-firing fallback rather than raising and dropping the
    # episode. Grid sizes are at least 9x12, so these two motifs fit with room.
    g = full_grid(h, w, 0)
    _paint(g, 1, 1, _SHAPES[0], base_colors[0])
    _paint(g, h - 4, w - 5, _SHAPES[1], base_colors[1])
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 13
    g = full_grid(h, w, 0)
    if name == "no_components":
        # Empty grid — rule has no rows to span-fill.
        return g
    if name == "no_row_gap":
        # Solid contiguous components — every row is already a
        # solid run; rule's "fill row gap" branch never fires.
        for r in range(2, 4):
            for c in range(2, 5): g[r][c] = 4
        for r in range(6, 8):
            for c in range(8, 11): g[r][c] = 6
        return g
    if name == "single_cell_objects":
        # 1-cell objects — rule's per-row span has no gap to fill.
        g[2][2] = 4; g[5][7] = 6; g[8][3] = 7
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    comps = components(grid)
    if not (2 <= len(comps) <= 5):
        errs.append(f"expected 2-5 motifs, got {len(comps)}")
    if len({c["color"] for c in comps}) != len(comps):
        errs.append("motifs should use distinct colors")
    if not components_have_clearance(grid, comps):
        errs.append("motifs should have a 1-cell moat")
    if comps and not all(has_row_gap(c["cells"]) for c in comps):
        errs.append("every helpful motif should contain a row gap for the span-fill rule")
    return errs
