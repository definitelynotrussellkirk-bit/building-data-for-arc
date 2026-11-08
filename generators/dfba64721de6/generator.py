"""Generator for 11dc524f.

Rule: a red shape slides toward a gray target and the gray output
becomes the reflected red shape docked beside it.

Combinatorial axes (8): grid_h/w, direction, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_red, no_gray, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dfba64721de6"
VERSION = "2.1.0"  # was FIXED 15x15 (shape-locked-in/out). Rule (slide red->gray, dock, reflect) is size-agnostic; now vary dims 12-22 with edge-relative placement. bg=7 kept (rule-required)."
TASK_ID = "dfba64721de6"
SUMMARY = (
    "FIXED 15×15 grid with "
    "COLOR-7 (orange) "
    "BACKGROUND. (a) ONE "
    "ASYMMETRIC RED(2) "
    "SHAPE drawn from a "
    "shape bank of 4-cell "
    "tetrominoes (L, J, T, "
    "S, Z, etc.); (b) ONE "
    "2×2 GRAY(5) BLOCK. "
    "The two are separated "
    "along ONE DOMINANT "
    "AXIS (horizontal: red "
    "and gray on same "
    "rows, different "
    "columns; vertical: "
    "same columns, "
    "different rows) with "
    "the SLIDE DIRECTION "
    "from red toward gray "
    "being one of {right, "
    "left, down, up}. "
    "Rule (SLIDE RED "
    "TOWARD GRAY, DOCK; "
    "REPLACE GRAY WITH "
    "REFLECTED RED): "
    "DETECT slide axis "
    "(red position vs "
    "gray position). "
    "SLIDE the red shape "
    "as a rigid group "
    "toward gray until "
    "they are adjacent "
    "(red's leading cell "
    "touches gray's bbox)"
    ". REPLACE the gray "
    "block with a "
    "REFLECTED COPY of "
    "the red shape (LR "
    "reflection if "
    "sliding horizontally, "
    "UD reflection if "
    "vertically) painted "
    "in red. Bg-7 "
    "preserved. Net: red "
    "shape docks beside "
    "gray, gray "
    "transforms into the "
    "red's mirror image."
)

# Rivals: 'output is input' refuted by demos (red moves). 'red stays
# put, gray moves' refuted by demos. 'gray becomes a red copy (not
# reflected)' refuted by demos showing reflection. 'use color 5 for
# docked shape' refuted by demos showing color 5 → color 5 for the
# adjacent reflected shape. 'red slides past gray' refuted by demos
# showing red stops adjacent. 4 demos covering all 4 directions pin
# the slide-and-dock rule.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is color 7",
    "exactly one red (color 2) connected shape — asymmetric",
    "exactly one gray (color 5) 2×2 block",
    "red and gray separated along ONE dominant axis (same row OR same col centroid)",
    "red can slide toward gray without leaving the grid",
    "red shape is asymmetric so its reflection is visibly distinct",
]

DIRECTIONS = ("right", "left", "down", "up")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_red", "no_gray", "full_grid")
HELPFUL_TEXTURES = DIRECTIONS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 13..18", "valid": "12..24"},
    "grid_w":         {"type": "int", "default": "rng 13..18", "valid": "12..24"},
    "direction":      {"type": "str", "default": "rng helpful",
                       "valid": "|".join(DIRECTIONS)},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for direction",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_RED_SHAPES = [
    [(0, 0), (1, 0), (2, 0), (2, 1)],                   # L-tetromino
    [(0, 1), (1, 1), (2, 1), (2, 0)],                   # J-tetromino
    [(0, 0), (0, 1), (1, 0), (2, 0)],                   # J flipped
    [(0, 0), (1, 0), (1, 1), (1, 2)],                   # T-rotated
    [(0, 0), (0, 1), (0, 2), (1, 0)],                   # J flat
    [(0, 0), (1, 0), (1, 1), (2, 1)],                   # S-tetromino
    [(0, 0), (0, 1), (1, 1), (1, 2)],                   # Z-tetromino
    [(0, 0), (0, 1), (0, 2), (1, 2)],                   # L flat
]


def _components(cells):
    cells = set(cells)
    comps = []
    while cells:
        stack = [cells.pop()]
        comp = []
        while stack:
            r, c = stack.pop()
            comp.append((r, c))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (r + dr, c + dc)
                if q in cells:
                    cells.remove(q)
                    stack.append(q)
        comps.append(comp)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Check the slide-to-gray setup: bg=7, one red tetromino, one gray 2x2."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs: list[str] = []
    vals = {v for row in grid for v in row}
    bad = vals - {2, 5, 7}
    if bad:
        errs.append(f"unexpected colors in input: {sorted(bad)}")
    if sum(v == 7 for row in grid for v in row) == 0:
        errs.append("missing color-7 background")
    red = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    gray = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 5]
    if len(red) != 4:
        errs.append(f"expected 4 red cells, found {len(red)}")
    elif len(_components(red)) != 1:
        errs.append("red cells are not one connected shape")
    if len(gray) != 4:
        errs.append(f"expected 4 gray cells, found {len(gray)}")
    else:
        rs = sorted({r for r, _ in gray})
        cs = sorted({c for _, c in gray})
        if len(rs) != 2 or len(cs) != 2 or rs[1] != rs[0] + 1 or cs[1] != cs[0] + 1:
            errs.append("gray cells are not a 2x2 block")
    if red and gray:
        red_r = sum(r for r, _ in red) / len(red)
        red_c = sum(c for _, c in red) / len(red)
        gray_r = sum(r for r, _ in gray) / len(gray)
        gray_c = sum(c for _, c in gray) / len(gray)
        if abs(red_r - gray_r) == abs(red_c - gray_c):
            errs.append("red/gray axis is ambiguous")
    return errs


def _paint(g, cells, r0, c0, color):
    for dr, dc in cells:
        g[r0 + dr][c0 + dc] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    direction = (overrides.get("texture") if overrides.get("texture") in DIRECTIONS else None) or \
                overrides.get("direction") or \
                ctx.draw_choice("direction", list(DIRECTIONS))
    # Grid is NOT fixed: the rule (slide red toward gray, dock, reflect) is
    # size-agnostic, so vary dims for diversity (bg stays color 7).
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 12, 13); w = ctx.draw_int("grid_w", 12, 13)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 16, 22); w = ctx.draw_int("grid_w", 16, 22)
    else:
        h = ctx.draw_int("grid_h", 13, 18); w = ctx.draw_int("grid_w", 13, 18)
    red_shape = _RED_SHAPES[rng.randrange(len(_RED_SHAPES))]
    g = full_grid(h, w, 7)
    rh = max(r for r, _ in red_shape) + 1
    rw = max(c for _, c in red_shape) + 1
    gray = [(0, 0), (0, 1), (1, 0), (1, 1)]
    # Randomize the row (for horizontal slide) or column (for vertical)
    if direction == "right":
        r0 = rng.randint(0, h - max(rh, 2))
        red_c = rng.randint(0, max(0, w // 5))
        gray_c = rng.randint(max(red_c + rw + 2, w * 3 // 5), w - 2)
        _paint(g, red_shape, r0, red_c, 2)
        _paint(g, gray, r0, gray_c, 5)
    elif direction == "left":
        r0 = rng.randint(0, h - max(rh, 2))
        gray_c = rng.randint(0, max(0, w // 5))
        red_c = rng.randint(max(gray_c + 4, w * 3 // 5), w - rw)
        _paint(g, red_shape, r0, red_c, 2)
        _paint(g, gray, r0, gray_c, 5)
    elif direction == "down":
        c0 = rng.randint(0, w - max(rw, 2))
        red_r = rng.randint(0, max(0, h // 5))
        gray_r = rng.randint(max(red_r + rh + 2, h * 3 // 5), h - 2)
        _paint(g, red_shape, red_r, c0, 2)
        _paint(g, gray, gray_r, c0, 5)
    else:  # up
        c0 = rng.randint(0, w - max(rw, 2))
        gray_r = rng.randint(0, max(0, h // 5))
        red_r = rng.randint(max(gray_r + 4, h * 3 // 5), h - rh)
        _paint(g, red_shape, red_r, c0, 2)
        _paint(g, gray, gray_r, c0, 5)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(15, 15, 7)
    if name == "no_red":
        _paint(g, [(0, 0), (0, 1), (1, 0), (1, 1)], 6, 11, 5)
        return g
    if name == "no_gray":
        _paint(g, _RED_SHAPES[0], 6, 1, 2)
        return g
    if name == "full_grid":
        for r in range(15):
            for c in range(15):
                g[r][c] = 2
        return g
    return g
