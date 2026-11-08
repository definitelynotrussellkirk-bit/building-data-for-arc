"""Generator for arc_puzzle_bank_sixth_21_bundle:easy_38_keep_bottommost_component.

Rule: among the connected non-bg components, keep only the one whose
bbox bottom row is strictly the lowest; clear the rest.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, components, texture.
Degenerates: no_components, single_component, tied_bottom.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7160d1eda94b"
VERSION = "2.0.1"
TASK_ID = "7160d1eda94b"

SUMMARY = (
    "0-bg grid (h ∈ 8-20, w ∈ 7-18, "
    "by difficulty) with: TARGET ∈ "
    "2-9 COMPONENTS, each in a "
    "DISTINCT color drawn from "
    "{1..9}, where: (a) the BOTTOM-"
    "MOST COMPONENT is placed at "
    "br = h - sh (bottom-aligned) "
    "with sh × sw drawn from "
    "bottom_shapes bank (L-tromino, "
    "corner, 2×2, L-tet, I-tro "
    "horizontal/vertical), painted "
    "in colors[0]; (b) OTHER "
    "components placed STRICTLY "
    "ABOVE br (rows ≤ br - 1) with "
    "1-cell padding, drawn from a "
    "wider other_shapes bank. "
    "Guaranteed: ONE component has "
    "STRICTLY LOWEST bottom row. "
    "Rule (KEEP ONLY THE COMPONENT "
    "WHOSE BBOX BOTTOM ROW IS "
    "STRICTLY THE LOWEST; ERASE "
    "ALL OTHER COMPONENTS TO 0; "
    "KEPT COMPONENT PRESERVES "
    "SHAPE AND COLOR): EXTRACT "
    "every 4-connected non-bg "
    "component. For each: COMPUTE "
    "bbox-bottom-row. FIND the "
    "MAXIMUM bottom row (strictly "
    "unique). PRODUCE a fresh "
    "same-size grid of 0s. PAINT "
    "only the bottommost "
    "component's cells in its "
    "original color. Net: the "
    "lowest component wins; "
    "others vanish."
)

# Rivals: 'keep largest component' refuted by ≥1 demo where bottommost
# is smaller than another. 'keep topmost' refuted by any demo (we keep
# bottommost). 'keep by color' refuted by ≥2 demos with same bottommost
# color but different shapes. 'keep rightmost' refuted by ≥1 demo where
# the bottommost is not the rightmost.
# 4 demos with varied component layouts cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "components are separated by background",
    "one component has a strictly greatest bottom row",
    "kept component preserves its original shape and color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_components", "single_component", "tied_bottom")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "5..22"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "5..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "components":     {"type": "int", "default": "rng 3..5", "valid": "2..10"},
    "palette_size":   {"type": "int", "default": "= components", "valid": "2..10"},
    "position_bias":  {"type": "str", "default": "scattered_with_one_lowest",
                       "valid": "scattered_with_one_lowest"},
    "n_distinct_colors": {"type": "int", "default": "= components", "valid": "2..10"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥2 distinct non-zero colors; skip degenerate textures."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 2:
        errs.append(f"expected ≥2 distinct non-zero colors (components), found {colors}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 7, 10)
        target = ctx.draw_int("components", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 20)
        w = ctx.draw_int("grid_w", 13, 18)
        target = ctx.draw_int("components", 5, 9)
    else:
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 9, 13)
        target = ctx.draw_int("components", 3, 6)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    colors = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(colors)
    # Bottommost component — random shape from a small bank.
    bottom_shapes = [
        [(0, 0), (1, 0), (1, 1)],            # L-tromino
        [(0, 0), (0, 1), (1, 0)],            # corner
        [(0, 0), (0, 1), (1, 1), (1, 0)],    # 2x2
        [(0, 0), (1, 0), (1, 1), (1, 2)],    # L-tet
        [(0, 0), (0, 1), (0, 2)],            # I-tro horizontal
        [(0, 0), (1, 0), (2, 0)],            # I-tro vertical
    ]
    shape = rng.choice(bottom_shapes)
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    br = h - sh
    bc = rng.randint(0, w - sw)
    for dr, dc in shape:
        g[br + dr][bc + dc] = colors[0]
    placed = 1
    attempts = 0
    # Other components must end strictly above br.
    max_top = max(0, br - 1)
    other_shapes = bottom_shapes + [
        [(0, 0), (0, 1)], [(0, 0), (1, 0)], [(0, 0)],
        [(0, 0), (0, 1), (1, 1)], [(0, 0), (1, 0), (1, 1), (2, 1)],
    ]
    while placed < target and attempts < 600:
        attempts += 1
        s = rng.choice(other_shapes)
        sh2 = max(r for r, _ in s) + 1
        sw2 = max(c for _, c in s) + 1
        if sh2 > max_top:
            continue
        r0 = rng.randint(0, max_top - sh2)
        c0 = rng.randint(0, w - sw2)
        ok = True
        for r in range(max(0, r0 - 1), min(h, r0 + sh2 + 1)):
            for c in range(max(0, c0 - 1), min(w, c0 + sw2 + 1)):
                if g[r][c] != 0:
                    ok = False
                    break
            if not ok:
                break
        if not ok:
            continue
        col = colors[placed % len(colors)]
        for dr, dc in s:
            g[r0 + dr][c0 + dc] = col
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 9
    g = full_grid(h, w, 0)
    if name == "no_components":
        # Empty grid — rule has no components to choose between.
        return g
    if name == "single_component":
        # Only one component exists — rule's "keep bottommost" is
        # trivially that one; rule's effect is invisible.
        for r, c in [(3, 3), (3, 4), (4, 3)]: g[r][c] = 4
        return g
    if name == "tied_bottom":
        # Multiple components share the same bottom row — rule's
        # strictly-lowest tiebreak has no entry.
        for r, c in [(7, 1), (7, 2), (8, 1)]: g[r][c] = 4
        for r, c in [(7, 6), (7, 7), (8, 7)]: g[r][c] = 6
        return g
    return g
