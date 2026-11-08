"""Generator for arc_puzzle_bank_21_set7:medium_g11 — bar chart of object sizes.

Rule: each blob's area = bar height. Bars side-by-side with 1-col gap.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: tied_sizes, single_blob, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "4c5a96f13170"
VERSION = "3.0.0"  # out-shape-locked (out width always 2*3-1=5): n_blobs was pinned at 3 so the bar-chart output width never varied. Rule sets out width = 2*ncomps-1 and height = max area, so VARYING the blob count (2..5) and the size pool (1..5) unlocks output-shape diversity (widths 3/5/7/9).
TASK_ID = "4c5a96f13170"
SUMMARY = (
    "0-bg grid (h~5-9, w~8-14) with 2-5 NON-TOUCHING "
    "connected BLOBS of STRICTLY DISTINCT sizes "
    "(drawn from a per-difficulty size pool without replacement), "
    "each in a distinct non-zero color from "
    "{1..9}. Blobs are 4-connectivity-isolated "
    "(no cell of one blob is orthogonally "
    "adjacent to another). Rule: count each "
    "blob's AREA (cell count). Render an OUTPUT "
    "BAR CHART: each blob becomes a VERTICAL "
    "BAR of the same color whose HEIGHT EQUALS "
    "the blob's area; bars are arranged "
    "SIDE-BY-SIDE with a 1-column gap between "
    "them, aligned along a common baseline "
    "(rows oriented bottom-up). Output grid "
    "size matches the bar count and max-area. "
    "Net: input has 2-5 colored blobs of "
    "different sizes; output is an n-bar bar "
    "chart of those sizes."
)

INVARIANTS = [
    "background is 0",
    "2-5 distinct-color blobs with strictly distinct sizes",
    "blobs don't 4-touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_sizes", "single_blob", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 4..6", "valid": "3..10"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "6..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "rng 2..5", "valid": "2..5"},
    "palette_size":   {"type": "int", "default": "= n_blobs", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "non_touching",
                       "valid": "non_touching"},
    "n_distinct_colors": {"type": "int", "default": "= n_blobs", "valid": "2..5"},
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
        n_blobs = ctx.draw_int("n_blobs", 2, 3)
        h = ctx.draw_int("grid_h", 5, 7); w = ctx.draw_int("grid_w", 8, 11)
    elif difficulty == "hard":
        n_blobs = ctx.draw_int("n_blobs", 4, 5)
        h = ctx.draw_int("grid_h", 7, 9); w = ctx.draw_int("grid_w", 11, 14)
    else:
        n_blobs = ctx.draw_int("n_blobs", 3, 4)
        h = ctx.draw_int("grid_h", 6, 8); w = ctx.draw_int("grid_w", 10, 13)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # distinct sizes (so the bars have distinct heights) from a pool wide
    # enough for n_blobs; max area drives output height, count drives width.
    sizes = rng.sample(range(1, max(6, n_blobs + 2)), n_blobs)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_blobs)
    used: set[tuple[int, int]] = set()
    for size, color in zip(sizes, palette):
        cells = grow_blob(rng, h, w, used, size, max_attempts=80)
        if cells is None:
            continue
        for r, c in cells:
            g[r][c] = color
        used |= cells
    return g


def _draw_from_degenerate(name, rng):
    h, w = 5, 8
    g = full_grid(h, w, 0)
    if name == "tied_sizes":
        # two blobs same area → bar heights tie, ordering ambiguous
        g[0][0] = 3; g[1][0] = 3
        g[0][3] = 5; g[1][3] = 5
        for r, c in [(3, 1), (3, 2), (4, 1)]:
            g[r][c] = 7
        return g
    if name == "single_blob":
        # one blob → bar chart degenerates to one bar
        for r, c in [(2, 2), (2, 3), (3, 2)]:
            g[r][c] = 6
        return g
    if name == "no_blobs":
        # empty grid → no bars to draw
        return g
    return g



def _nonzero_components(grid):
    h, w = len(grid), len(grid[0])
    cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0}
    seen = set(); comps = []
    for start in sorted(cells):
        if start in seen:
            continue
        stack = [start]; seen.add(start); comp = set()
        while stack:
            r, c = stack.pop(); comp.add((r, c))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (r + dr, c + dc)
                if nb in cells and nb not in seen:
                    seen.add(nb); stack.append(nb)
        comps.append(comp)
    return comps



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    if not grid or not grid[0]:
        return ["empty grid"]
    comps = _nonzero_components(grid)
    if not (2 <= len(comps) <= 5):
        errors.append(f"expected 2-5 blobs, got {len(comps)}")
    sizes = [len(c) for c in comps]
    colors = []
    for comp in comps:
        comp_colors = {grid[r][c] for r, c in comp}
        if len(comp_colors) != 1:
            errors.append("component has mixed colors; blobs touched")
        colors.extend(comp_colors)
    if len(set(sizes)) != len(sizes):
        errors.append("blob sizes are not strictly distinct")
    if len(set(colors)) != len(colors):
        errors.append("blob colors are not distinct")
    return errors
