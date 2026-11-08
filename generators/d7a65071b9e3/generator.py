"""Generator for arc_additional_puzzle_bank_volume5:H29.

Rule: a direction marker makes every non-control object slide rigidly
until stacked against the wall or another object.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_objects,
palette_size, position_bias, n_distinct_colors, marker_dir, texture.
Degenerates: no_direction_marker, no_objects, ambiguous_direction.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "d7a65071b9e3"
VERSION = "1.2.0"  # uniq 56%: 3 FIXED shapes at fixed positions/colors; only marker direction + dims varied. Rule slides all non-marker components in the marker direction. Now random shapes (2-5 cells), counts (2-4), positions, colors -> more distinct outputs.
TASK_ID = "d7a65071b9e3"
SUMMARY = "A direction marker makes every non-control object slide rigidly until stacked against the wall or another object."

INVARIANTS = [
    "one marker from 1 through 4 selects direction",
    "sliding objects use colors outside 1 through 4",
    "objects begin away from their landing wall",
    "at least two objects slide in the selected direction",
]

PALETTE_KINDS = ("default", "dir_up", "dir_down", "dir_lr")
DEGENERATE_TEXTURES = ("no_direction_marker", "no_objects", "ambiguous_direction")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..14", "valid": "8..24"},
    "grid_w":         {"type": "int", "default": "rng 10..14", "valid": "8..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_objects":      {"type": "int", "default": "3", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4"},
    "marker_dir":     {"type": "str", "default": "rng", "valid": "rng"},
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
        h = ctx.draw_int("grid_h", 10, 11); w = ctx.draw_int("grid_w", 10, 11)
        n = ctx.draw_int("n_objects", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18); w = ctx.draw_int("grid_w", 13, 18)
        n = ctx.draw_int("n_objects", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 10, 14); w = ctx.draw_int("grid_w", 10, 14)
        n = ctx.draw_int("n_objects", 2, 4)
    rng = ctx.draw_rng("layout")
    # marker direction + dims varied, but the 3 sliding shapes were FIXED -> uniq 56%.
    # Now random shapes/positions/colors/count (rule slides all of them in the marker dir).
    g = full_grid(h, w, 0)
    mr, mc = rng.randrange(h), rng.randrange(w)
    g[mr][mc] = rng.choice([1, 2, 3, 4])
    used = {(mr + dr, mc + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
    colors = rng.sample([5, 6, 7, 8, 9], n)
    for color in colors:
        shape = _poly(rng, rng.randint(2, 5))
        sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
        for _ in range(120):
            r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
            cells = [(r0 + r, c0 + c) for r, c in shape]
            if any((r, c) in used for r, c in cells):
                continue
            for r, c in cells:
                g[r][c] = color
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        used.add((r + dr, c + dc))
            break
    return g


def _poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]




def self_check(grid, *, difficulty=None, meta=None):
    """Executable default-path invariants for the direction-marker sliding scene."""
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if sum(1 for row in grid for v in row if v == 0) <= h * w // 2:
        errs.append("background must be dominantly 0")

    markers = [(r, c, grid[r][c]) for r in range(h) for c in range(w)
               if grid[r][c] in (1, 2, 3, 4)]
    if len(markers) != 1:
        errs.append("expected exactly one direction marker in 1..4")
        marker_pos = None
    else:
        marker_pos = markers[0][:2]

    object_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] >= 5]
    if not object_cells:
        errs.append("expected at least one non-control object")
    if any(grid[r][c] in (1, 2, 3, 4) for r, c in object_cells):
        errs.append("object uses a reserved marker color")

    seen = set()
    comps = 0
    for r, c in object_cells:
        if (r, c) in seen:
            continue
        comps += 1
        color = grid[r][c]
        stack = [(r, c)]
        seen.add((r, c))
        while stack:
            cr, cc = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = cr + dr, cc + dc
                if ((nr, nc) not in seen and 0 <= nr < h and 0 <= nc < w
                        and grid[nr][nc] == color):
                    seen.add((nr, nc))
                    stack.append((nr, nc))
    if comps < 2:
        errs.append("expected at least two separate sliding objects")

    if marker_pos is not None:
        mr, mc = marker_pos
        if any(abs(r - mr) <= 1 and abs(c - mc) <= 1 for r, c in object_cells):
            errs.append("object touches marker exclusion zone")
    return errs

def _draw_from_degenerate(name, rng):
    h, w = 11, 11
    g = full_grid(h, w, 0)
    if name == "no_direction_marker":
        # objects exist but no 1-4 marker → slide direction undefined
        paint_at(g, 2, 2, [(0, 0), (1, 0), (1, 1)], 6)
        paint_at(g, 2, w - 4, [(0, 0), (0, 1), (1, 0), (1, 1)], 7)
        paint_at(g, h - 5, w // 2, [(0, 0), (0, 1), (1, 1), (2, 1)], 9)
        return g
    if name == "no_objects":
        # marker exists but nothing to slide → rule is no-op
        g[0][0] = 2
        return g
    if name == "ambiguous_direction":
        # multiple direction markers (1 and 4) → which direction wins?
        g[0][0] = 1
        g[0][w - 1] = 4
        paint_at(g, 2, 2, [(0, 0), (1, 0), (1, 1)], 6)
        paint_at(g, h - 5, w // 2, [(0, 0), (0, 1), (1, 1), (2, 1)], 9)
        return g
    return g
