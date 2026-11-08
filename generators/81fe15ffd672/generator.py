"""Generator for arc_puzzle_bank_21_set19_bundle:hard_p01 — transform-by-marker-count.

Rule: (0, 0) is the key color. Row 0 contains color-9 markers; their count is
the transform code. Take all key-color cells outside row 0 as a shape; output
the shape transformed by code.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_markers,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_key, no_markers, no_body_shape.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "81fe15ffd672"
VERSION = "2.0.0"
TASK_ID = "81fe15ffd672"

SUMMARY = (
    "0-bg grid with: (a) one KEY color cell at (0, 0) in some "
    "non-{0, 9} color; (b) 1-3 color-9 markers at distinct columns in "
    "row 0 (the count determines the transform code); (c) body (rows "
    "1+) holds one connected SHAPE in the key color (3-5 cells). "
    "Rule: read key color from (0, 0). Count color-9 markers in row 0 "
    "= code. Collect key-colored cells outside row 0 as the shape. "
    "Crop to bbox and apply transform code (1=identity, 2=rot90, "
    "3=rot180, 4=rot270, ...). Output is the transformed shape grid "
    "in the key color."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "(0, 0) holds a key color (non-{0, 9})",
    "row 0 has 1-3 color-9 markers at distinct columns",
    "body (rows 1..h-1) holds a connected shape in the key color (3-5 cells)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_key", "no_markers", "no_body_shape")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_markers":      {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "key_at_origin_plus_9_markers_plus_body",
                       "valid": "key_at_origin_plus_9_markers_plus_body"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
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
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 9, 10)
        n_markers = ctx.draw_int("n_markers", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 11)
        n_markers = ctx.draw_int("n_markers", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 11)
        n_markers = ctx.draw_int("n_markers", 1, 3)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    key_color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])
    g[0][0] = key_color
    cols = rng.sample(range(1, w), n_markers)
    for c in cols:
        g[0][c] = 9
    # body shape (3-5 cells)
    cells = [(2, 2)]
    seen = {(2, 2)}
    target = rng.randint(3, 5)
    while len(cells) < target:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if 1 <= nr < h and 0 <= nc < w and (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    for r, c in cells:
        g[r][c] = key_color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_key":
        # markers + body but no key at (0,0)
        for c in [3, 5]: g[0][c] = 9
        g[3][3] = 4; g[3][4] = 4
        return g
    if name == "no_markers":
        # key + body but no 9-markers (count=0 → no transform code)
        g[0][0] = 4
        g[3][3] = 4; g[3][4] = 4; g[4][3] = 4
        return g
    if name == "no_body_shape":
        # key + markers but no body
        g[0][0] = 4
        for c in [2, 4, 6]: g[0][c] = 9
        return g
    return g


def _components_of_color(grid, color, *, skip_row0=False):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    start_r = 1 if skip_row0 else 0
    for r in range(start_r, h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if start_r <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    key = grid[0][0]
    if key in (0, 9):
        return [f"bad key color: {key}"]
    markers = [c for c in range(1, w) if grid[0][c] == 9]
    if not (1 <= len(markers) <= 3):
        msgs.append(f"marker count outside 1..3: {len(markers)}")
    comps = _components_of_color(grid, key, skip_row0=True)
    if len(comps) != 1:
        msgs.append(f"body shape component count {len(comps)} != 1")
    elif not (3 <= len(comps[0]) <= 5):
        msgs.append(f"body shape size {len(comps[0])} outside 3..5")
    return msgs
