"""Generator for arc_puzzle_bank_fifteenth21:M101 — repeat body by 9-marker count.

Rule: top-row 9 markers give the repeat count. The nonzero object below
is cropped and repeated horizontally with one blank spacer column.

Combinatorial axes (8): grid_h, grid_w, palette_kind, repeat_count, shape,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_markers, no_body, K_equals_one.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c7bee0c68969"
VERSION = "2.4.0"  # honor grid_h/grid_w axes for the variable-size canonical layout
TASK_ID = "c7bee0c68969"
SUMMARY = (
    "A small 0-bg grid with 2-4 maroon-9 markers in row 0 and one "
    "single-color connected body object below. The marker count k drives "
    "horizontal repetition of the cropped body with one blank spacer column."
)

INVARIANTS = [
    "row 0 has two to four color-9 markers",
    "all nonzero body cells belong to one compact object",
    "the object crop is not empty",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_markers", "no_body", "K_equals_one")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "6-7 easy / 7-9 med / 8-10 hard", "valid": "6..10"},
    "grid_w":         {"type": "int", "default": "9-10 easy / 10-12 med / 11-13 hard", "valid": "9..13"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "repeat_count":   {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "shape":          {"type": "int", "default": "rng 0..3", "valid": "0..3"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "position_bias":  {"type": "str", "default": "row0_9_markers_with_body",
                       "valid": "row0_9_markers_with_body"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_markers|no_body|K_equals_one"},
}

_SHAPES = [
    [(0, 0, 2), (1, 0, 2), (1, 1, 3), (2, 1, 3)],
    [(0, 1, 4), (1, 0, 4), (1, 1, 5), (1, 2, 5)],
    [(0, 0, 6), (0, 1, 6), (1, 1, 7), (2, 1, 7), (2, 2, 8)],
    [(0, 0, 3), (1, 0, 3), (2, 0, 4), (2, 1, 4)],
]


def _rand_obj(rng, k, color):
    """Random connected single-color object.  The canonical task's body is a
    single foreground object; color variation comes from the sampled body color,
    not from splitting the body into color-islands."""
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin, color) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        k = ctx.draw_int("repeat_count", 2, 2)
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 9, 10)
        o_lo, o_hi = 3, 4
    elif difficulty == "hard":
        k = ctx.draw_int("repeat_count", 3, 4)
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 11, 13)
        o_lo, o_hi = 4, 6
    else:
        k = ctx.draw_int("repeat_count", 2, 4)
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 10, 12)
        o_lo, o_hi = 3, 5
    # object whose bbox width keeps the hstack output (k*ow + k-1) within 30 cols
    body_color = rng.randint(2, 8)
    cells = None
    for _ in range(30):
        cand = _rand_obj(rng, rng.randint(o_lo, o_hi), body_color)
        ow = max(c for _, c, _ in cand) + 1
        if k * ow + (k - 1) <= 30:
            cells = cand; break
    if cells is None:
        cells = _rand_obj(rng, 3, body_color)
    oh = max(r for r, _, _ in cells) + 1; ow = max(c for _, c, _ in cells) + 1
    g = full_grid(h, w, 0)
    for c in sorted(rng.sample(range(1, w - 1), k)):
        g[0][c] = 9
    top = rng.randint(1, max(1, h - oh - 1))
    left = rng.randint(1, max(1, w - ow - 1))
    for r, c, v in cells:
        g[top + r][left + c] = v
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 12, 0)
    cells = _SHAPES[0]
    if name == "no_markers":
        # row 0 empty → K=0, no copies to make
        for r, c, v in cells: g[3 + r][3 + c] = v
        return g
    if name == "no_body":
        # markers but no body → K copies of nothing
        for c in [2, 5, 8]: g[0][c] = 9
        return g
    if name == "K_equals_one":
        # only 1 marker → output is single copy (no observable repetition)
        g[0][3] = 9
        for r, c, v in cells: g[3 + r][3 + c] = v
        return g
    return g



def _nonzero_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(1, h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 1 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] != 0:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["empty or ragged grid"]
    k = sum(1 for v in grid[0] if v == 9)
    if not (2 <= k <= 4):
        errs.append(f"row 0 must contain 2..4 marker-9 cells, saw {k}")
    if any(v not in (0, 9) for v in grid[0]):
        errs.append("row 0 contains non-marker foreground")
    comps = _nonzero_components(grid)
    if len(comps) != 1:
        errs.append(f"expected exactly one body component below row 0, saw {len(comps)}")
    elif len(comps[0]) < 3:
        errs.append("body object too small to teach repetition")
    body_colors = {grid[r][c] for comp in comps for r, c in comp}
    if len(body_colors) != 1:
        errs.append(f"body should be one single-color object, found colors {sorted(body_colors)}")
    if 9 in body_colors:
        errs.append("body uses marker color 9")
    return errs
