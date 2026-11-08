"""Generator for 77fdfe62.

Rule: corners hold 4 colors. Interior (rows 2..h-3, cols 2..w-3): each
non-zero cell takes the color of the corner of its quadrant.

Combinatorial axes (8): grid_h/w, palette_kind, interior_density,
interior_layout, frame_color, anchor_quadrants, asymmetry_force,
include_decoy.
Degenerates: empty_interior, full_interior, missing_corner.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a48ffccce86c"
VERSION = "1.1.0"
TASK_ID = "a48ffccce86c"
SUMMARY = "4 corner colors + interior; rule recolors interior by quadrant."

INVARIANTS = [
    "h, w both >=6 and even",
    "4 corners have 4 distinct non-{0,1} colors",
    "border (row 0, h-1, col 0, w-1) is 1s except at corners",
    "interior (rows 2..h-3, cols 2..w-3) has >=1 non-zero cell",
    "non-zero interior cells != 1 (rule treats 0 as bg)",
]

INTERIOR_LAYOUTS = ("scattered", "blob", "diagonal", "checker",
                    "frame", "cross", "stripes")
PALETTE_KINDS = ("warm", "cool", "broad", "pastel")
DEGENERATE_TEXTURES = ("empty_interior", "full_interior", "missing_corner")
HELPFUL_TEXTURES = INTERIOR_LAYOUTS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 6..10 even",
                          "valid": "6..14 even"},
    "grid_w":            {"type": "int", "default": "rng 6..10 even",
                          "valid": "6..14 even"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "interior_density":  {"type": "float", "default": "rng 0.3..0.7",
                          "valid": "0.1..1"},
    "interior_layout":   {"type": "str", "default": "rng helpful",
                          "valid": "|".join(INTERIOR_LAYOUTS)},
    "interior_color":    {"type": "color", "default": "8", "valid": "1..9 (≠1)"},
    "anchor_quadrants":  {"type": "bool", "default": "true",
                          "valid": "true|false"},
    "asymmetry_force":   {"type": "bool", "default": "false",
                          "valid": "true|false"},
    "texture":           {"type": "str", "default": "alias for interior_layout",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_choices = [6, 8]
    elif difficulty == "hard":
        h_choices = [10, 12, 14]
    else:
        h_choices = [6, 8, 10]
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        h = rng.choice(h_choices)
        w = rng.choice(h_choices)
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    h = int(overrides.get("grid_h", rng.choice(h_choices)))
    w = int(overrides.get("grid_w", rng.choice(h_choices)))
    if h % 2 == 1: h += 1
    if w % 2 == 1: w += 1
    h = max(6, min(14, h))
    w = max(6, min(14, w))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    if palette_kind == "warm":
        pool = [3, 4, 6, 9]
    elif palette_kind == "cool":
        pool = [5, 7, 8]
    elif palette_kind == "pastel":
        pool = [2, 3, 5]
    else:
        pool = [2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    pal = pool[:4]
    if len(pal) < 4:
        extras = [c for c in [2, 3, 4, 5, 6, 7, 8, 9] if c not in pal]
        rng.shuffle(extras)
        pal += extras[:4 - len(pal)]
    pal = pal[:4]
    layout = (overrides.get("texture") or
              overrides.get("interior_layout")
              or ctx.draw_choice("interior_layout",
                                 list(INTERIOR_LAYOUTS)))
    interior_color = int(overrides.get("interior_color", 8))
    if interior_color == 1 or interior_color in pal:
        interior_color = next((c for c in [8, 7, 6, 5, 4, 3, 2]
                               if c != 1 and c not in pal), 8)
    density = float(overrides.get("interior_density",
                                  ctx.draw_rng("interior_density")
                                  .uniform(0.3, 0.7)))
    g = full_grid(h, w, 0)
    g[0][0] = pal[0]; g[0][w - 1] = pal[1]
    g[h - 1][0] = pal[2]; g[h - 1][w - 1] = pal[3]
    for c in range(1, w - 1):
        g[0][c] = 1; g[h - 1][c] = 1
    for r in range(1, h - 1):
        g[r][0] = 1; g[r][w - 1] = 1
    for c in range(1, w - 1):
        g[1][c] = 1; g[h - 2][c] = 1
    for r in range(1, h - 1):
        g[r][1] = 1; g[r][w - 2] = 1
    _fill_interior(g, layout, h, w, interior_color, density, rng)
    has_interior = any(g[r][c] not in (0, 1)
                       for r in range(2, h - 2)
                       for c in range(2, w - 2))
    if not has_interior and h >= 6 and w >= 6:
        g[2][2] = interior_color
    return g


def _fill_interior(g, layout, h, w, color, density, rng):
    cells = [(r, c) for r in range(2, h - 2) for c in range(2, w - 2)]
    if layout == "blob":
        if cells:
            cr, cc = rng.choice(cells)
            for r, c in cells:
                if abs(r - cr) + abs(c - cc) <= 2 and rng.random() < density + 0.2:
                    g[r][c] = color
        return
    if layout == "diagonal":
        for k in range(min(h - 4, w - 4)):
            r = 2 + k; c = 2 + k
            if 2 <= r < h - 2 and 2 <= c < w - 2:
                g[r][c] = color
        return
    if layout == "checker":
        for r, c in cells:
            if (r + c) % 2 == 0 and rng.random() < density + 0.2:
                g[r][c] = color
        return
    if layout == "frame":
        for r, c in cells:
            if r in (2, h - 3) or c in (2, w - 3):
                g[r][c] = color
        return
    if layout == "cross":
        mr = h // 2; mc = w // 2
        for r, c in cells:
            if r == mr or c == mc:
                g[r][c] = color
        return
    if layout == "stripes":
        for r, c in cells:
            if r % 2 == 0 and rng.random() < density + 0.2:
                g[r][c] = color
        return
    for r, c in cells:
        if rng.random() < density:
            g[r][c] = color


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    pal = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], 4)
    g[0][0] = pal[0]; g[0][w - 1] = pal[1]
    g[h - 1][0] = pal[2]; g[h - 1][w - 1] = pal[3]
    for c in range(1, w - 1):
        g[0][c] = 1; g[h - 1][c] = 1
    for r in range(1, h - 1):
        g[r][0] = 1; g[r][w - 1] = 1
    for c in range(1, w - 1):
        g[1][c] = 1; g[h - 2][c] = 1
    for r in range(1, h - 1):
        g[r][1] = 1; g[r][w - 2] = 1
    if name == "empty_interior":
        return g
    if name == "full_interior":
        for r in range(2, h - 2):
            for c in range(2, w - 2):
                g[r][c] = 8
        return g
    if name == "missing_corner":
        g[0][0] = 1
        for r in range(2, h - 2):
            for c in range(2, w - 2):
                if rng.random() < 0.4:
                    g[r][c] = 8
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if h % 2 or w % 2 or not (6 <= h <= 14 and 6 <= w <= 14):
        msgs.append("grid should be even-sized with h,w in 6..14")
    corners = [grid[0][0], grid[0][w - 1], grid[h - 1][0], grid[h - 1][w - 1]]
    if len(set(corners)) != 4 or any(v in (0, 1) for v in corners):
        msgs.append("four corners should be distinct non-background/non-frame colors")
    if any(grid[0][c] != 1 or grid[h - 1][c] != 1 for c in range(1, w - 1)):
        msgs.append("top/bottom outer frame should be color 1 except corners")
    if any(grid[r][0] != 1 or grid[r][w - 1] != 1 for r in range(1, h - 1)):
        msgs.append("left/right outer frame should be color 1 except corners")
    if h >= 6 and w >= 6:
        if any(grid[1][c] != 1 or grid[h - 2][c] != 1 for c in range(1, w - 1)):
            msgs.append("inner horizontal frame should be color 1")
        if any(grid[r][1] != 1 or grid[r][w - 2] != 1 for r in range(1, h - 1)):
            msgs.append("inner vertical frame should be color 1")
    interior = [grid[r][c] for r in range(2, h - 2) for c in range(2, w - 2)]
    marked = [v for v in interior if v != 0]
    if not marked:
        msgs.append("normal instance should include at least one marked interior cell")
    marked_colors = set(marked)
    if 1 in marked_colors:
        msgs.append("interior cue cells should not use frame color 1")
    if marked_colors & set(corners):
        msgs.append("interior cue color should be distinct from all corner output colors")
    if len(marked_colors - {1}) > 1:
        msgs.append("normal instance should use a single interior cue color")
    return sorted(set(msgs))
