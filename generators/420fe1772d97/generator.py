"""Generator for arc_puzzle_bank_21_set19_s:S19_M6.

A top template is stamped at each color-3 marker in the lower panel.

Combinatorial axes (8): grid_h, grid_w, palette_kind, shape,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_template, no_markers, no_divider.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "420fe1772d97"
VERSION = "3.1.0"  # guarantee template has at least 3 cells and add executable invariants.
TASK_ID = "420fe1772d97"
SUMMARY = (
    "Variable two-panel grid. A full color-9 divider separates a top "
    "template panel from an equal-sized bottom marker panel. Top panel: "
    "a TEMPLATE shape in color 2 — a small connected blob (3-5 cells) "
    "anchored at top-left. Bottom panel: 2-4 color-3 ANCHOR markers "
    "at distinct positions where the "
    "template can fit. Rule: extract template's offset cells from its "
    "top-left anchor. For each color-3 marker in the bottom panel, "
    "stamp the template (in color 8) at the marker's position. Output "
    "is the bottom panel only, filled with 8-stamps."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "grid has two equal-height panels separated by one full color-9 divider row",
    "top panel has a color-2 template (3-5 cells)",
    "bottom panel has 2-4 color-3 markers at positions where template fits",
    "no other non-bg colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_template", "no_markers", "no_divider")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "2*panel_h+1", "valid": "9..17"},
    "grid_w":         {"type": "int", "default": "panel_w rng 4..8", "valid": "4..8"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": 'default|warm|cool|varied'},
    "shape":          {"type": "int", "default": "rng 0..3", "valid": "0..3"},
    "n_markers":      {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "template_plus_markers",
                       "valid": "template_plus_markers"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": 'default|warm|cool|varied|no_template|no_markers|no_divider'},
}

_SHAPES = [
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 1), (2, 1)],
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
]


def _size(cells):
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _rand_poly(rng, n, maxh, maxw):
    cells = [(0, 0)]; seen = {(0, 0)}
    tries = 0
    while len(cells) < n and tries < 200:
        tries += 1
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) in seen:
            continue
        rs = [x for x, _ in cells] + [nr]; cs = [y for _, y in cells] + [nc]
        if max(rs) - min(rs) + 1 <= maxh and max(cs) - min(cs) + 1 <= maxw:
            cells.append((nr, nc)); seen.add((nr, nc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    # output = bottom-panel size -> vary the panel dims (was fixed 5x5 panels)
    if difficulty == "easy":
        ph = ctx.draw_int("panel_h", 4, 5); pw = ctx.draw_int("panel_w", 4, 5)
        n_markers = ctx.draw_int("n_markers", 2, 2); k_hi = 4
    elif difficulty == "hard":
        ph = ctx.draw_int("panel_h", 5, 8); pw = ctx.draw_int("panel_w", 5, 8)
        n_markers = ctx.draw_int("n_markers", 3, 5); k_hi = 5
    else:
        ph = ctx.draw_int("panel_h", 4, 7); pw = ctx.draw_int("panel_w", 4, 7)
        n_markers = ctx.draw_int("n_markers", 2, 4); k_hi = 5
    # random template shape that fits within roughly half the panel (so anchored
    # stamps have placement room)
    shape = _rand_poly(rng, rng.randint(3, k_hi), max(2, ph - 1), max(2, pw - 1))
    shape_h, shape_w = _size(shape)
    g = full_grid(2 * ph + 1, pw, 0)
    for r, c in shape:
        g[r][c] = 2                      # template in top panel
    for c in range(pw):
        g[ph][c] = 9                     # full color-9 divider row
    # anchors (color 3) in the bottom panel, at positions where the shape fits
    spots = [(r, c) for r in range(0, ph - shape_h + 1)
             for c in range(0, pw - shape_w + 1)]
    rng.shuffle(spots)
    for r, c in spots[:n_markers]:
        g[ph + 1 + r][c] = 3
    return g


def _comp_count(cells):
    cells = set(cells)
    if not cells:
        return 0
    n = 0
    while cells:
        n += 1
        todo = [next(iter(cells))]
        cells.remove(todo[0])
        while todo:
            r, c = todo.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (r + dr, c + dc)
                if q in cells:
                    cells.remove(q); todo.append(q)
    return n


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    h, w = len(grid), len(grid[0])
    div_rows = [r for r in range(h) if all(v == 9 for v in grid[r])]
    if len(div_rows) != 1:
        errors.append(f"expected exactly one full color-9 divider row, got {div_rows}")
        return errors
    ph = div_rows[0]
    if ph < 4 or h != 2 * ph + 1:
        errors.append("top and bottom panels should have equal height >=4")
    template = [(r, c) for r in range(ph) for c in range(w) if grid[r][c] == 2]
    if not (3 <= len(template) <= 5):
        errors.append(f"template must contain 3-5 cells, got {len(template)}")
    if _comp_count(template) != 1:
        errors.append("template cells must be 4-connected")
    markers = [(r, c) for r in range(ph + 1, h) for c in range(w) if grid[r][c] == 3]
    min_markers = 3 if difficulty == "hard" else 2
    if len(markers) < min_markers:
        errors.append(f"expected at least {min_markers} bottom-panel markers, got {len(markers)}")
    if any(v not in (0, 2, 3, 9) for row in grid for v in row):
        errors.append("normal input must contain only colors 0/2/3/9")
    return errors


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 5, 0)
    if name == "no_template":
        # markers without template → no shape to stamp
        for c in range(5):
            g[5][c] = 9
        g[7][1] = 3
        g[8][3] = 3
        return g
    if name == "no_markers":
        # template alone, no markers in lower panel → nothing to stamp around
        for r, c in _SHAPES[0]:
            g[r][c] = 2
        for c in range(5):
            g[5][c] = 9
        return g
    if name == "no_divider":
        # template + markers but no 9-divider → no panel separation
        for r, c in _SHAPES[0]:
            g[r][c] = 2
        g[7][1] = 3
        g[8][3] = 3
        return g
    return g
