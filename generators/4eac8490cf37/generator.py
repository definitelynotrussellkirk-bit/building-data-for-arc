"""Generator for 9c1e755f.

Rule: a color-5 line plus an adjacent seed patch define a rectangle that gets
filled by TILING the seed pattern. For a horizontal 5-line, the seed cells in
the row beside it are tiled across the line's column span (over the seed's row
height); vertical is transposed. The rule reads (rows g)/(cols g) and finds the
5-lines dynamically, so it is fully size-generic.

The old generator hardcoded a 12x12 grid with a fixed 5-line and a fixed 2x2
seed (a,b,b,a) — shape-locked in/out. Now: vary the grid size, the line
position and span, the seed patch size and 2-color pattern, and the orientation.

Combinatorial axes: grid size, orientation, line position/span, seed
height/width + pattern, colors.
Degenerates: no_line, no_seed, full_line.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4eac8490cf37"
RULE_HASH = "30792ea72d7e"  # canonical rule this generator was written against
VERSION = "3.1.0"  # guarantee the seed patch visibly uses both colors and add executable invariants.
TASK_ID = "4eac8490cf37"
SUMMARY = (
    "0-bg grid (size varies). A full COLOR-5 LINE (horizontal or vertical) with "
    "a SEED PATCH (sh x sw, a random 2-color pattern) placed directly beside it, "
    "anchored at the line's start and narrower than the line. Rule: tile the "
    "seed pattern across the line's span (over the seed's height) to fill the "
    "rectangle beside the line. Net: the small seed pattern is repeated to fill "
    "a strip alongside the 5-line."
)

INVARIANTS = [
    "background is 0",
    "a color-5 line (full run) with a non-{0,5} seed patch adjacent to it",
    "the seed patch is narrower than the line so tiling extends it",
]

ORIENTATIONS = ("horizontal", "vertical")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_line", "no_seed", "full_line")
HELPFUL_TEXTURES = ORIENTATIONS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "10..18"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "10..18"},
    "orientation":    {"type": "str", "default": "rng", "valid": "|".join(ORIENTATIONS)},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "seed_h":         {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "seed_w":         {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "line_with_seed", "valid": "line_with_seed"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for orientation",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _transpose(g):
    return [list(row) for row in zip(*g)]


def _build_horizontal(rng, h, w, a, b):
    sh = rng.randint(1, 3)
    sw = rng.randint(2, 4)
    line_w = sw + rng.randint(2, 6)
    if line_w > w:
        line_w = w
    if sw >= line_w:
        sw = max(2, line_w - 1)
    lr = rng.randint(1, max(1, h - sh - 2))
    c1 = rng.randint(0, w - line_w)
    g = full_grid(h, w, 0)
    for c in range(c1, c1 + line_w):
        g[lr][c] = 5
    # seed patch directly below the line, anchored at c1
    cells = [a, b] + [rng.choice([a, b]) for _ in range(sh * sw - 2)]
    rng.shuffle(cells)
    it = iter(cells)
    for dr in range(sh):
        for dc in range(sw):
            g[lr + 1 + dr][c1 + dc] = next(it)
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    orientation = (overrides.get("texture") if overrides.get("texture") in ORIENTATIONS else None) or \
                  overrides.get("orientation") or rng.choice(list(ORIENTATIONS))
    a, b = ctx.draw_distinct_colors("seed_colors", n=2, exclude={0, 5})

    if difficulty == "easy":
        n1 = ctx.draw_int("grid_a", 10, 12); n2 = ctx.draw_int("grid_b", 10, 12)
    elif difficulty == "hard":
        n1 = ctx.draw_int("grid_a", 14, 18); n2 = ctx.draw_int("grid_b", 14, 18)
    else:
        n1 = ctx.draw_int("grid_a", 12, 15); n2 = ctx.draw_int("grid_b", 12, 15)

    if orientation == "horizontal":
        return _build_horizontal(rng, n1, n2, a, b)
    return _transpose(_build_horizontal(rng, n2, n1, a, b))


def _runs(values, target=5):
    runs = []
    start = None
    for i, v in enumerate(values + [None]):
        if v == target and start is None:
            start = i
        elif v != target and start is not None:
            runs.append((start, i - 1))
            start = None
    return runs


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    h, w = len(grid), len(grid[0])
    hlines = []
    for r in range(h):
        for c0, c1 in _runs(grid[r], 5):
            if c1 - c0 + 1 >= 4:
                hlines.append((r, c0, c1))
    vlines = []
    for c in range(w):
        col = [grid[r][c] for r in range(h)]
        for r0, r1 in _runs(col, 5):
            if r1 - r0 + 1 >= 4:
                vlines.append((c, r0, r1))
    if len(hlines) + len(vlines) != 1:
        errors.append(f"expected exactly one color-5 line, got h={hlines} v={vlines}")
        return errors
    seed_cells = [(r, c, grid[r][c]) for r in range(h) for c in range(w)
                  if grid[r][c] not in (0, 5)]
    seed_vals = [v for _, _, v in seed_cells]
    line_len = 0
    if hlines:
        r, c0, c1 = hlines[0]; line_len = c1 - c0 + 1
        if seed_cells:
            rs = [rr for rr, _, _ in seed_cells]; cs = [cc for _, cc, _ in seed_cells]
            if min(rs) not in (r - (max(rs) - min(rs) + 1), r + 1) and not (min(rs) <= r + 1 <= max(rs)):
                errors.append("seed patch must be adjacent to the color-5 line")
            if max(cs) - min(cs) + 1 >= line_len:
                errors.append("seed patch must be narrower than the color-5 line")
    else:
        c, r0, r1 = vlines[0]; line_len = r1 - r0 + 1
        if seed_cells:
            rs = [rr for rr, _, _ in seed_cells]; cs = [cc for _, cc, _ in seed_cells]
            if min(cs) not in (c - (max(cs) - min(cs) + 1), c + 1) and not (min(cs) <= c + 1 <= max(cs)):
                errors.append("seed patch must be adjacent to the color-5 line")
            if max(rs) - min(rs) + 1 >= line_len:
                errors.append("seed patch must be shorter than the color-5 line")
    if not seed_vals:
        errors.append("line must have an adjacent non-{0,5} seed patch")
    elif len(set(seed_vals)) < 2:
        errors.append("seed patch must visibly contain both seed colors")
    return errors


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 12, 0)
    if name == "no_line":
        g[4][2], g[4][3] = 3, 4
        return g
    if name == "no_seed":
        for c in range(2, 10):
            g[6][c] = 5
        return g
    if name == "full_line":
        for c in range(12):
            g[6][c] = 5
        g[7][0], g[7][1] = 3, 4
        return g
    return g
