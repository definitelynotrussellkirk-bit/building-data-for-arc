"""Generator for 17b:m113 — select object by legend and transform.

Rule: key color at (0,0), transform code at (0, w-1). Find shape with
matching key color; output is its crop transformed per code.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_shapes,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_key, no_match_shape, no_code.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a4580cf49290"
VERSION = "2.2.0"  # retry until all keyed/distractor shapes are placed; stronger self_check
TASK_ID = "a4580cf49290"
SUMMARY = (
    "0-bg grid (h~10-12, w~11-13) with: (a) KEY COLOR "
    "at (0, 0) — a single non-bg cell choosing which "
    "shape to operate on; (b) TRANSFORM CODE at "
    "(0, w-1) — a single cell with value ∈ {1, 2, 3, "
    "4, 5} encoding 1=identity, 2=rotate-CW, "
    "3=rotate-180, 4=rotate-CCW, 5=flip-LR; (c) 3 "
    "MULTI-CELL SHAPES placed at random positions in "
    "rows 2..h-1, each in a distinct non-bg color from "
    "a 3-color palette — EXACTLY ONE of those shapes "
    "uses the KEY COLOR from (0, 0). Shapes are "
    "4-conn isolated. Rule: find the shape whose "
    "color matches the KEY color. CROP it to its "
    "bounding box. APPLY the TRANSFORM encoded by the "
    "code. Output: the small transformed crop, in the "
    "key color. Net: top-left key picks the shape, "
    "top-right code picks the dihedral op; output is "
    "the resulting transformed crop."
)

INVARIANTS = [
    "background is 0",
    "cell (0,0) is the key color (some non-bg)",
    "cell (0, w-1) is a transform code (small integer)",
    "2-3 multi-cell shapes elsewhere; one is in the key color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_key", "no_match_shape", "no_code")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..12", "valid": "9..16"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "10..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_shapes":       {"type": "int", "default": "3 (med) / 3-4 (hard)", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "3-4", "valid": "2..4"},
    "shape_size":     {"type": "int", "default": "3-4 easy / 4-6 med / 5-8 hard", "valid": "3..9"},
    "position_bias":  {"type": "str", "default": "header_corners_shapes_below",
                       "valid": "header_corners_shapes_below"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "3..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_key|no_match_shape|no_code"},
}

_SHAPES = [
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 1)],
    [(0, 0), (1, 0), (1, 1), (2, 1)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (1, 0), (1, 1)],
]


def _rand_shape(rng, k):
    """Random connected (4-conn) polyomino of k cells, normalised."""
    cells = [(0, 0)]; seen = {(0, 0)}; tries = 0
    while len(cells) < k and tries < 60:
        tries += 1
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nc = (r + dr, c + dc)
        if nc not in seen:
            cells.append(nc); seen.add(nc)
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _place(g, rng, shape, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    for _ in range(40):
        r0 = rng.randint(2, h - sh); c0 = rng.randint(1, w - sw - 1)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = color
        return True
    return False


def _body_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(2, h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 2 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify key/code headers and the full keyed-shape candidate set."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if (meta or {}).get("texture") in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    key = grid[0][0]
    if key == 0:
        errs.append("cell (0,0) is 0 (no key color)")
    code = grid[0][w - 1]
    if code not in (1, 2, 3, 4, 5):
        errs.append(f"cell (0,w-1) is {code} (expected transform code 1-5)")
    comps = _body_components(grid)
    min_shapes = 4 if difficulty == "hard" else 3
    if len(comps) < min_shapes:
        errs.append(f"expected at least {min_shapes} isolated body shapes, found {len(comps)}")
    key_comps = [cells for color, cells in comps if color == key]
    if len(key_comps) != 1:
        errs.append(f"expected exactly one body shape in the key color {key}, found {len(key_comps)}")
    if comps and min(len(cells) for _color, cells in comps) < 3:
        errs.append("body contains a too-small shape; expected multi-cell objects")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 11, 12)
        n_shapes, k_lo, k_hi = 3, 3, 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 16)
        w = ctx.draw_int("grid_w", 14, 16)
        n_shapes, k_lo, k_hi = 4, 5, 8
    else:
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 12, 14)
        n_shapes, k_lo, k_hi = 3, 4, 6
    rng = ctx.draw_rng("layout")
    palette = rng.sample([3, 4, 6, 7, 8, 9], n_shapes)
    key = palette[0]
    code = rng.choice([1, 2, 3, 4, 5])
    for _layout in range(100):
        g = full_grid(h, w, 0)
        g[0][0] = key
        g[0][w - 1] = code
        placed = 0
        for color in palette:
            # random connected shape (was 1 of 5 fixed); easy may use a canonical one
            shape = rng.choice(_SHAPES) if (difficulty == "easy" and rng.random() < 0.5) \
                else _rand_shape(rng, rng.randint(k_lo, k_hi))
            if not _place(g, rng, shape, color):
                break
            placed += 1
        if placed == n_shapes:
            return g
    raise ValueError(f"could not place all {n_shapes} keyed/distractor shapes")


def _draw_from_degenerate(name, rng):
    h, w = 11, 12
    g = full_grid(h, w, 0)
    if name == "no_key":
        # No key color at (0,0) — rule has no shape selector.
        g[0][w - 1] = 2
        for r, c in [(2, 2), (3, 2), (4, 2)]: g[r][c] = 4
        for r, c in [(6, 6), (6, 7), (7, 7)]: g[r][c] = 5
        return g
    if name == "no_match_shape":
        # Key set but no shape in key color — rule selects nothing.
        g[0][0] = 4
        g[0][w - 1] = 2
        for r, c in [(2, 2), (3, 2), (4, 2)]: g[r][c] = 5
        for r, c in [(6, 6), (6, 7), (7, 7)]: g[r][c] = 6
        return g
    if name == "no_code":
        # Key set but no transform code — rule has no transformation to apply.
        g[0][0] = 4
        for r, c in [(2, 2), (3, 2), (4, 2)]: g[r][c] = 4
        for r, c in [(6, 6), (6, 7), (7, 7)]: g[r][c] = 5
        return g
    return g
