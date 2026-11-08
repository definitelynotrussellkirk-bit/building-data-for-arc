"""Generator for arc_puzzle_bank_thirteenth_21_bundle:hard_91_overlay_three_shapes_to_count_map.

Rule: overlay three aligned 5x5 panels and encode per-cell occupancy counts.

Combinatorial axes (8): variant, palette_kind,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: identical_panels, no_overlap, single_panel.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7017b91a367d"
VERSION = "2.0.0"  # distinct=4: 3 panels came from a 4-entry _PANEL_SETS bank -> only 4 overlap-count outputs. Rule output (5x5 cell = count of panels nonzero at (r,c): 0/2/4/8) is overlap-count; output 5x5 is rule-intrinsic. Randomize the 3 panel patterns -> overlap-count output varies widely.
TASK_ID = "7017b91a367d"
SUMMARY = "Overlay three aligned 5x5 panels and encode per-cell occupancy counts."

INVARIANTS = [
    "the input has three 5-column panels at offsets 0, 6, and 12",
    "panel colors are arbitrary and ignored by the rule",
    "all three panels use the same local coordinate system",
    "the output maps occupancy counts 1, 2, and 3 to colors 2, 4, and 8",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("identical_panels", "no_overlap", "single_panel")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "variant":        {"type": "int", "default": "rng 0..3", "valid": "0..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "three_aligned_panels",
                       "valid": "three_aligned_panels"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_PANEL_SETS = [
    ([(1, 2), (2, 1), (2, 2), (2, 3), (3, 2)],
     [(1, 1), (1, 2), (1, 3), (2, 2), (3, 2)],
     [(1, 3), (2, 3), (3, 2), (3, 3), (3, 4)]),
    ([(1, 1), (2, 1), (3, 1), (3, 2)],
     [(1, 1), (1, 2), (2, 2), (3, 2)],
     [(2, 1), (2, 2), (2, 3), (3, 3)]),
    ([(0, 2), (1, 2), (2, 1), (2, 2)],
     [(1, 1), (1, 2), (1, 3), (2, 3)],
     [(2, 1), (2, 2), (3, 2), (3, 3)]),
    ([(1, 0), (1, 1), (2, 1), (3, 1)],
     [(0, 2), (1, 2), (2, 2), (2, 3)],
     [(2, 0), (2, 1), (2, 2), (3, 2)]),
]


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: input is 5x17 (three 5x5 panels at offsets 0, 6, 12 separated by 1-col gaps)."""
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    if h != 5:
        errors.append(f"expected 5 rows, got {h}")
    if w != 17:
        errors.append(f"expected 17 cols (3x5 panels + 2 gaps), got {w}")
    # Columns 5 and 11 should be all-zero (the separators)
    if h == 5 and w == 17:
        for sep_col in (5, 11):
            if not all(grid[r][sep_col] == 0 for r in range(5)):
                errors.append(f"separator column {sep_col} is not all-zero")
    return errors


def _paint(g, panel, cells, color):
    left = panel * 6
    for r, c in cells:
        g[r][left + c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        lo, hi = 4, 10
    elif difficulty == "hard":
        lo, hi = 8, 18
    else:
        lo, hi = 5, 15
    colors = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], 3)
    spots = [(r, c) for r in range(5) for c in range(5)]
    g = full_grid(5, 17, 0)
    # three random 5x5 panel patterns; the rule overlays them by per-cell count
    for panel in range(3):
        cells = rng.sample(spots, rng.randint(lo, hi))
        _paint(g, panel, cells, colors[panel])
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(5, 17, 0)
    if name == "identical_panels":
        # all 3 panels share same shape → output is uniformly count-3 (no count-1 or count-2 cells)
        cells = [(1, 2), (2, 1), (2, 2), (2, 3), (3, 2)]
        for panel in range(3):
            _paint(g, panel, cells, [4, 6, 3][panel])
        return g
    if name == "no_overlap":
        # 3 panels with disjoint positions → output has only count-1 cells
        _paint(g, 0, [(0, 0), (0, 1)], 4)
        _paint(g, 1, [(2, 2), (2, 3)], 6)
        _paint(g, 2, [(4, 4)], 3)
        return g
    if name == "single_panel":
        # only first panel populated → other panels empty, only count-1 cells in output
        _paint(g, 0, [(1, 2), (2, 1), (2, 2), (2, 3), (3, 2)], 4)
        return g
    return g
