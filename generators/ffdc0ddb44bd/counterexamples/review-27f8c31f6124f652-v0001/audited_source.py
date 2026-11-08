"""Generator for arc_puzzle_bank_21_set15:S15_M6 — most-frequent normalized shape.

Rule: among candidate objects, find the most-frequent normalized shape;
crop and recolor it.

Combinatorial axes (8): grid_h, grid_w, palette_kind, majority_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: tied_counts, single_object, all_distinct_shapes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.selfcheck import components, components_have_clearance, color_counts, has_row_gap, interior_cells, is_full_frame_component, norm

GENERATOR_ID = "ffdc0ddb44bd"
VERSION = "2.1.0"
TASK_ID = "ffdc0ddb44bd"
SUMMARY = (
    "0-bg grid (h~12-15, w~16-19) with multiple CANDIDATE "
    "objects in colors {2, 3, 4, 5, 6}, isolated from each "
    "other. ONE normalized shape (the MAJORITY shape) "
    "appears 3-4 times, each in a distinct color. 1-2 "
    "DECOY objects have different shapes (also in colors "
    "from {2..6}). Rule: extract all objects with colors in "
    "{2..6}. Compute their normalized cell-set signatures. "
    "Sort signatures by (count desc, then shape-size asc as "
    "tiebreaker). Take the winning signature. Find the first "
    "object matching that signature. Crop it to bbox, "
    "recolor every non-bg cell to 8 (cyan). Output is that "
    "small grid."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "candidate objects use colors 2 through 6",
    "one normalized shape appears strictly more often than every other candidate shape",
    "candidate objects are separated from one another",
    "≥1 decoy shape present (so the rule's selector is non-trivial)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_counts", "single_object", "all_distinct_shapes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "height":         {"type": "int", "default": "rng 12..15", "valid": "10..18"},
    "width":          {"type": "int", "default": "rng 16..19", "valid": "14..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "majority_count": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "position_bias":  {"type": "str", "default": "majority_shape_with_decoys",
                       "valid": "majority_shape_with_decoys"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|tied_counts|single_object|all_distinct_shapes"},
}

MAJORITY_OPTIONS = [
    [(0, 0), (1, 0), (1, 1), (2, 1)],          # S-tetromino
    [(0, 0), (0, 1), (1, 1), (1, 2)],          # Z-tetromino
    [(0, 0), (0, 1), (0, 2), (1, 1)],          # T-tetromino
    [(0, 1), (1, 0), (1, 1), (1, 2)],          # ⊥
    [(0, 0), (1, 0), (1, 1), (2, 0)],          # T-rotated
    [(0, 0), (1, 0), (2, 0), (2, 1)],          # L-tetromino
    [(0, 1), (1, 0), (1, 1), (2, 1)],          # ⊥-rotated
]
ODD_OPTIONS = [
    [(0, 0), (0, 1), (1, 1)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 0)],
    [(0, 1), (1, 0), (1, 1), (1, 2)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (1, 0), (2, 0)],
]

# Aliases for the degenerate path (previously referenced undefined names).
MAJORITY = MAJORITY_OPTIONS[0]
ODD_A = ODD_OPTIONS[0]
ODD_B = ODD_OPTIONS[2]


def _norm(cells):
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def _rand_poly(rng, size):
    """Random connected polyomino of `size` cells inside a 3x3 box."""
    cells = [(rng.randint(0, 2), rng.randint(0, 2))]
    guard = 0
    while len(cells) < size and guard < 200:
        guard += 1
        gr, gc = rng.choice(cells)
        for dr, dc in rng.sample([(-1, 0), (1, 0), (0, -1), (0, 1)], 4):
            nr, nc = gr + dr, gc + dc
            if 0 <= nr <= 2 and 0 <= nc <= 2 and (nr, nc) not in cells:
                cells.append((nr, nc))
                break
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _draw_decoy(rng, exclude):
    """A decoy shape whose translation-normalized form is not in `exclude`."""
    for _ in range(200):
        s = _rand_poly(rng, rng.randint(3, 5))
        if _norm(s) not in exclude:
            return s
    for s in ODD_OPTIONS:
        if _norm(s) not in exclude:
            return s
    return ODD_OPTIONS[0]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("height", 12, 13)
        w = ctx.draw_int("width", 16, 17)
        majority_count = ctx.draw_int("majority_count", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("height", 14, 15)
        w = ctx.draw_int("width", 18, 19)
        majority_count = ctx.draw_int("majority_count", 4, 4)
    else:
        h = ctx.draw_int("height", 12, 15)
        w = ctx.draw_int("width", 16, 19)
        majority_count = ctx.draw_int("majority_count", 3, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # Randomly drawn majority/decoy shapes (≤3x3 box) keep the fixed, isolated
    # anchor layout while widening shape -> output diversity. Decoys are
    # translation-normalized-distinct from the majority (the rule compares
    # shapes by translation only), so the majority stays strictly most frequent.
    majority_shape = _rand_poly(rng, rng.randint(4, 6))
    m_norm = _norm(majority_shape)
    odd_shape = _draw_decoy(rng, {m_norm})

    anchors = [(1, 1), (1, 6), (h - 5, 1), (h - 5, 6)]
    for color, (r, c) in zip(range(2, 2 + majority_count), anchors):
        paint_at(g, r, c, majority_shape, color)
    paint_at(g, 1, w - 5, odd_shape, 6)
    if majority_count < 4:
        odd_shape2 = _draw_decoy(rng, {m_norm, _norm(odd_shape)})
        paint_at(g, h - 4, w - 5, odd_shape2, 5)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 13, 17
    g = full_grid(h, w, 0)
    if name == "tied_counts":
        # 2 distinct shapes each appearing 2 times → "most frequent" is tied
        paint_at(g, 1, 1, MAJORITY, 2)
        paint_at(g, 1, 6, MAJORITY, 3)
        paint_at(g, h - 4, 1, ODD_A, 4)
        paint_at(g, h - 4, 6, ODD_A, 5)
        return g
    if name == "single_object":
        # only 1 candidate → "most frequent" trivially that one
        paint_at(g, 4, 4, MAJORITY, 2)
        return g
    if name == "all_distinct_shapes":
        # all candidates have distinct shapes → no shape has count > 1
        paint_at(g, 1, 1, [(0, 0), (0, 1), (0, 2)], 2)            # line
        paint_at(g, 1, 6, MAJORITY, 3)                              # S
        paint_at(g, h - 5, 1, ODD_A, 4)                             # corner
        paint_at(g, h - 5, 6, ODD_B, 5)                             # T
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    comps = components(grid, colors={2, 3, 4, 5, 6})
    if len(comps) < 4:
        errs.append("expected majority objects plus at least one decoy")
    if not components_have_clearance(grid, comps):
        errs.append("candidate objects should be isolated")
    counts = color_counts(grid)
    if any(v != 0 and v not in {2, 3, 4, 5, 6} for row in grid for v in row):
        errs.append("candidate grid should only use colors 2..6 on 0 background")
    shape_counts = {}
    for comp in comps:
        shape_counts[comp["norm"]] = shape_counts.get(comp["norm"], 0) + 1
    if shape_counts:
        ordered = sorted(shape_counts.values(), reverse=True)
        if len(ordered) < 2 or ordered[0] <= ordered[1]:
            errs.append("one normalized shape must be a strict majority")
        if len(shape_counts) < 2:
            errs.append("at least one decoy normalized shape should be present")
    return errs
