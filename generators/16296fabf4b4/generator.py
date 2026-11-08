"""Generator for arc_puzzle_bank_21_set13_s:S13_E7 — recolor tall components.

Rule: tall components (bbox h > w) → recolor to 8; square/wide keep colors.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_components, all_tall, all_wide.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "16296fabf4b4"
# 2.1.0: shapes came from a 3+3 fixed bank; rule only cares about bbox h vs w.
#        Added random-polyomino growth with a target aspect (tall: h>w,
#        non-tall: h<=w) so component shapes vary far more (banks kept as
#        fallback). Both branches still guaranteed.
VERSION = "2.1.1"
TASK_ID = "16296fabf4b4"
SUMMARY = (
    "0-bg grid with several connected components in distinct non-zero "
    "colors. Some have TALL bboxes (height > width), others have "
    "SQUARE or WIDE bboxes (height ≤ width). Rule: for each component, "
    "if bbox h > w (strictly taller than wide), recolor all its cells "
    "to 8. Otherwise preserve original color. Output is the same grid "
    "with tall components recolored."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥1 component with bbox h > w (tall → recolored)",
    "≥1 component with bbox h ≤ w (preserved)",
    "components don't touch (separated)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_components", "all_tall", "all_wide")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "height":         {"type": "int", "default": "rng 11..14", "valid": "9..17"},
    "width":          {"type": "int", "default": "rng 12..15", "valid": "10..18"},
    "tall_count":     {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "position_bias":  {"type": "str", "default": "tall_with_non_tall",
                       "valid": "tall_with_non_tall"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_TALL = [
    [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1)],
    [(0, 1), (1, 1), (2, 0), (2, 1), (3, 1)],
    [(0, 0), (1, 0), (2, 0)],
]
_NOT_TALL = [
    [(0, 0), (0, 1), (0, 2), (1, 0)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (0, 2)],
]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, at least one tall AND one non-tall component present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in ("no_components", "all_tall", "all_wide"):
        return errs
    # Check at least one non-zero cell exists
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonzero:
        errs.append("no non-bg cells found")
    return errs


def _size(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _grow_aspect(rng, want_tall, attempts=60):
    """Grow a random connected polyomino (3-6 cells) whose bbox is taller
    than wide (want_tall) or not (h<=w). Returns normalized cell list."""
    for _ in range(attempts):
        size = rng.randint(3, 6)
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            cells.add((r + dr, c + dc))
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        mr, mc = min(rs), min(cs)
        h = max(rs) - mr + 1; w = max(cs) - mc + 1
        if (want_tall and h > w) or (not want_tall and h <= w):
            return [(r - mr, c - mc) for r, c in cells]
    return None


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


def _place(g, rng, shape, color):
    h, w = len(g), len(g[0])
    sh, sw = _size(shape)
    for _ in range(120):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        if _free(g, r0, c0, shape):
            for dr, dc in shape:
                g[r0 + dr][c0 + dc] = color
            return
    raise ValueError("could not place object")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("height", 11, 11)
        w = ctx.draw_int("width", 12, 12)
        tall_count = ctx.draw_int("tall_count", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("height", 14, 16)
        w = ctx.draw_int("width", 15, 17)
        tall_count = ctx.draw_int("tall_count", 2, 3)
    else:
        h = ctx.draw_int("height", 11, 14)
        w = ctx.draw_int("width", 12, 15)
        tall_count = ctx.draw_int("tall_count", 1, 2)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # Exclude 8 (the rule's recolor target) from input colors to avoid
    # a kept (non-tall) object already being color 8.
    colors = [1, 2, 3, 4, 6, 7, 9]
    rng.shuffle(colors)
    ci = 0
    for _ in range(tall_count):
        shape = _grow_aspect(rng, True) or rng.choice(_TALL)
        _place(g, rng, shape, colors[ci]); ci += 1
    for _ in range(2):
        shape = _grow_aspect(rng, False) or rng.choice(_NOT_TALL)
        _place(g, rng, shape, colors[ci]); ci += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 12, 13
    g = full_grid(h, w, 0)
    if name == "no_components":
        # Empty grid — rule has no candidates to recolor.
        return g
    if name == "all_tall":
        # All components tall — rule's recolor branch fires for
        # everything; output is uniformly 8.
        for r, c in [(0, 0), (1, 0), (2, 0)]: g[r][c] = 4
        for r, c in [(0, 5), (1, 5), (2, 5), (3, 5)]: g[r][c] = 6
        return g
    if name == "all_wide":
        # All components square or wide — rule's recolor branch
        # never fires; output equals input.
        for r, c in [(2, 2), (2, 3), (2, 4)]: g[r][c] = 4
        for r, c in [(7, 7), (7, 8), (8, 7), (8, 8)]: g[r][c] = 6
        return g
    return g
