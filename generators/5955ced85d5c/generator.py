"""Generator for 2bcee788.

Rule: the main-color shape is REFLECTED across the red(2) fold line; then
every cell of (main shape ∪ red fold ∪ reflected shape) is painted the main
color and every OTHER cell becomes 3. The rule reads (rows g)/(cols g) and
computes the fold axis from the red/main centroids, so it is fully
size-generic.

The old generator hardcoded an 11×11 grid AND a single fixed 5-cell L shape
(only the main color + a tiny offset varied) -> shape-locked in/out, 48% dup.
It also let main_color be 3, which collides with the rule's background fill
(-> all-3 outputs). Now: vary the GRID SIZE, use a RANDOM connected shape, a
random fold distance/extent, and exclude main_color 3.

Combinatorial axes: grid size, orientation, the shape, the fold distance,
the main color.
Degenerates: no_shape, no_fold, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5955ced85d5c"
VERSION = "3.0.0"  # shape-locked in/out + 48% dup: gen hardcoded 11x11 + a single fixed L shape (only colour/offset varied); also allowed main_color=3 (== rule's bg fill -> all-3). Rule is size-generic (centroid-reflection across red fold). Now vary grid size + random connected shape + fold distance + exclude main_color 3.
TASK_ID = "5955ced85d5c"
SUMMARY = (
    "0-bg grid (size varies). (a) a RANDOM connected SHAPE (4-8 cells) in one "
    "main color (not 0/2/3) in the upper/left region; (b) a color-2 (red) FOLD "
    "LINE parallel to the shape and offset by a small distance, perpendicular "
    "to the reflection axis, with room for the reflected copy. Rule: detect "
    "the main-color shape + the red fold line; REFLECT the shape across the "
    "fold (axis from the red cells); paint (shape ∪ fold ∪ reflection) the "
    "main color and every other cell 3. Output dims = input dims (now vary). "
    "Net: the shape folds across the red line, red merges into the main color, "
    "background becomes 3."
)

INVARIANTS = [
    "there is exactly one main nonzero color besides red (not 0, 2, or 3)",
    "red cells form a fold line on one side of the main shape",
    "the reflection of the shape across the fold lands fully in-bounds",
    "the shape and its reflection sit clear of each other (fold between them)",
]

ORIENTATIONS = ("horizontal", "vertical")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_shape", "no_fold", "full_grid")
HELPFUL_TEXTURES = ORIENTATIONS

SHAPE = [(0, 0), (0, 1), (1, 0), (2, 0), (2, 1)]

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "9..18"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..18"},
    "orientation":    {"type": "str", "default": "rng helpful",
                       "valid": "|".join(ORIENTATIONS)},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "fold_distance":  {"type": "int", "default": "rng 2..4", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "rng", "valid": "rng"},
    "main_color":     {"type": "color", "default": "rng !{0,2,3}",
                       "valid": "1|4|5|6|7|8|9"},
    "texture":        {"type": "str", "default": "alias for orientation",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _rand_shape(rng):
    """Random connected polyomino, 4-8 cells, bbox within 4x4, normalized."""
    n = rng.randint(4, 8)
    cells = {(rng.randint(0, 3), rng.randint(0, 3))}
    guard = 0
    while len(cells) < n and guard < 200:
        guard += 1
        r, c = rng.choice(tuple(cells))
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if 0 <= nr < 4 and 0 <= nc < 4:
            cells.add((nr, nc))
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r0, c0 = min(rs), min(cs)
    return [(r - r0, c - c0) for (r, c) in cells]


def _transpose(g):
    return [list(row) for row in zip(*g)]


def _build_horizontal(rng, H, W, mc):
    """Shape in the top region, a horizontal red fold below it, reflected copy
    further below. Returns a grid or None if it couldn't fit."""
    shape = _rand_shape(rng)
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    for _ in range(40):
        r0 = rng.randint(1, max(1, H // 2 - sh))
        c0 = rng.randint(1, W - sw - 1)
        d = rng.randint(2, 4)                 # gap from shape bottom to fold
        fold_r = r0 + sh - 1 + d
        axis2 = 2 * fold_r - 1
        refl = [(axis2 - (r0 + dr), c0 + dc) for dr, dc in shape]
        if fold_r >= H or any(not (0 <= rr < H) for rr, _ in refl):
            continue
        g = full_grid(H, W, 0)
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = mc
        cl = max(0, c0 - 1)
        cr = min(W - 1, c0 + sw)
        for c in range(cl, cr + 1):
            g[fold_r][c] = 2
        return g
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    orientation = (overrides.get("texture") if overrides.get("texture") in ORIENTATIONS else None) or \
                  overrides.get("orientation") or \
                  ctx.draw_choice("orientation", list(ORIENTATIONS))
    main_color = ctx.draw_color("main_color", exclude={0, 2, 3})

    if difficulty == "easy":
        a = ctx.draw_int("grid_a", 11, 13)
        b = ctx.draw_int("grid_b", 9, 11)
    elif difficulty == "hard":
        a = ctx.draw_int("grid_a", 15, 18)
        b = ctx.draw_int("grid_b", 13, 16)
    else:
        a = ctx.draw_int("grid_a", 12, 15)
        b = ctx.draw_int("grid_b", 11, 14)

    # build horizontally on (rows=a, cols=b); transpose for the vertical fold.
    g = _build_horizontal(rng, a, b, main_color)
    if g is None:                              # fall back to a roomy grid
        g = _build_horizontal(rng, 18, 14, main_color)
    if orientation == "vertical":
        g = _transpose(g)
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the red-fold reflection setup."""
    errs = []
    if not grid or not isinstance(grid[0], list):
        return ["grid is empty or not rectangular"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        errs.append("grid rows have inconsistent widths")
        return errs
    colors = sorted({v for row in grid for v in row})
    main_colors = [c for c in colors if c not in (0, 2)]
    if len(main_colors) != 1:
        return [f"expected exactly one main color besides red, found {main_colors}"]
    mc = main_colors[0]
    if mc == 3:
        errs.append("main color must not be 3 (the rule's output background fill)")
    reds = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    mains = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == mc]
    if not reds:
        errs.append("missing red fold line")
    if not mains:
        errs.append("missing main-color shape")
    if not reds or not mains:
        return errs
    red_rows = {r for r, _ in reds}
    red_cols = {c for _, c in reds}
    if not (len(red_rows) == 1 or len(red_cols) == 1):
        errs.append("red fold cells are not a straight row/column line")
    mr = sum(r for r, _ in mains) / len(mains)
    mc_col = sum(c for _, c in mains) / len(mains)
    rr = sum(r for r, _ in reds) / len(reds)
    rc = sum(c for _, c in reds) / len(reds)
    dr, dc = rr - mr, rc - mc_col
    vertical_fold = dr * dr > dc * dc
    if vertical_fold:
        if len(red_rows) != 1:
            errs.append("vertical reflection branch needs a horizontal red fold row")
        axis2 = (2 * min(red_rows) - 1) if dr > 0 else (2 * max(red_rows) + 1)
        reflected = [(axis2 - r, c) for r, c in mains]
    else:
        if len(red_cols) != 1:
            errs.append("horizontal reflection branch needs a vertical red fold column")
        axis2 = (2 * min(red_cols) - 1) if dc > 0 else (2 * max(red_cols) + 1)
        reflected = [(r, axis2 - c) for r, c in mains]
    if any(not (0 <= r < h and 0 <= c < w) for r, c in reflected):
        errs.append("reflected main shape lands out of bounds")
    if set(reflected) & set(mains):
        errs.append("reflected main shape overlaps the source shape")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 11, 0)
    if name == "no_shape":
        for c in range(2, 8):
            g[5][c] = 2
        return g
    if name == "no_fold":
        for dr, dc in SHAPE:
            g[2 + dr][3 + dc] = 4
        return g
    if name == "full_grid":
        for r in range(11):
            for c in range(11):
                g[r][c] = 2
        return g
    return g
