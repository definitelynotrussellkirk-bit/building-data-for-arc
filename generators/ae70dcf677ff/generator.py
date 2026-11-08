"""Generator for 9841fdad.

Rule: objects in left framed panel project as stretched bars into
matching right panel.

Combinatorial axes (8): grid_h, panel_w, palette_kind, frame_color,
n_objects, anchor_corner, asymmetry_force, palette_size.
Degenerates: no_objects, no_frame, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ae70dcf677ff"
VERSION = "3.0.1"  # shape-locked in+out + wrong-bg: fixed panel size + bg=0 both panels + fixed left shapes. Rule projects left objects into the uniform right panel; now nonzero left-bg/right-bg, random left objects, varied panel size."
TASK_ID = "ae70dcf677ff"
SUMMARY = (
    "0-bg framed grid (h~7-12, w = 2*panel_w+3 "
    "with panel_w=5) containing TWO PANELS "
    "separated by a vertical FRAME-COLOR "
    "divider, plus a full FRAME-COLOR outer "
    "border. LEFT PANEL contains 1-2 small "
    "colored OBJECTS (each 2-3 cells, in "
    "distinct non-frame colors c1, c2) placed "
    "at distinct row spans. RIGHT PANEL is "
    "initially blank (the projection canvas). "
    "NOTE: object positions are currently "
    "hardcoded — diversity is mid. Rule: for "
    "EACH OBJECT in the LEFT PANEL, determine "
    "its ROW SPAN (rmin..rmax) and color c. "
    "PROJECT a stretched HORIZONTAL BAR of "
    "color c into the RIGHT PANEL spanning "
    "those same rows, filling the entire "
    "right-panel column range (with horizontal "
    "margin convention). Net: left-panel "
    "shapes become projected colored bars in "
    "the right panel."
)

INVARIANTS = [
    "one frame color forms the outer border and the vertical separator",
    "the left panel has a background and separated colored objects",
    "the right panel is the projection canvas",
    "projected objects preserve row span and horizontal margin convention",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_objects", "no_frame", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "9", "valid": "7..14"},
    "panel_width":    {"type": "int", "default": "5", "valid": "3..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "frame_color":    {"type": "color", "default": "rng !0",
                       "valid": "1..9"},
    "n_objects":      {"type": "int", "default": "2", "valid": "1..3"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: grid has at least 2 distinct colors (frame color + objects)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_objects", "no_frame"):
        return []
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    colors = set(grid[r][c] for r in range(h) for c in range(w))
    if len(colors) < 2:
        errs.append(f"expected >=2 distinct colors (frame+objects); found {len(colors)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    # Rule: left panel objects are projected (as filled bboxes, margin-aligned)
    # into the uniform right panel. v1.x used bg=0 both panels + FIXED left shapes
    # at fixed panel size (shape-locked + wrong bg vs canonical's nonzero panel
    # backgrounds). Now: nonzero left-bg + right-bg, random left objects, and
    # varied panel size.
    pal = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 5)
    frame, left_bg, right_bg = pal[0], pal[1], pal[2]
    obj_colors = pal[3:]                    # 2 object colors, distinct from bgs
    if difficulty == "easy":
        panel_w = ctx.draw_int("panel_width", 5, 6); h = ctx.draw_int("grid_h", 7, 9)
    elif difficulty == "hard":
        panel_w = ctx.draw_int("panel_width", 8, 11); h = ctx.draw_int("grid_h", 11, 14)
    else:
        panel_w = ctx.draw_int("panel_width", 5, 9); h = ctx.draw_int("grid_h", 8, 12)
    w = 2 * panel_w + 3
    sep = panel_w + 1
    g = full_grid(h, w, frame)
    # left + right interior backgrounds
    for r in range(1, h - 1):
        for c in range(1, sep):
            g[r][c] = left_bg
        for c in range(sep + 1, w - 1):
            g[r][c] = right_bg
    # random objects in the left panel (rows 1..h-2, cols 1..sep-1), separated
    occupied = set()

    def _free(cells):
        for (r, c) in cells:
            if not (1 <= r <= h - 2 and 1 <= c <= sep - 1):
                return False
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if (r + dr, c + dc) in occupied:
                        return False
        return True

    n_obj = rng.randint(2, 4)
    for i in range(n_obj):
        shape = _poly(rng, rng.randint(2, 5))
        sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
        for _ in range(60):
            r0 = rng.randint(1, h - 1 - sh); c0 = rng.randint(1, sep - sw)
            cells = [(r0 + dr, c0 + dc) for dr, dc in shape]
            if _free(cells):
                col = obj_colors[i % len(obj_colors)]
                for (r, c) in cells:
                    g[r][c] = col
                    occupied.add((r, c))
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


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    if len(pool) < n:
        for c in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            if c not in pool:
                pool.append(c)
            if len(pool) >= n:
                break
    return pool[:n]


def _draw_from_degenerate(name, rng):
    h, w = 9, 13
    g = full_grid(h, w, 0)
    if name == "no_objects":
        for c in range(w):
            g[0][c] = 5
            g[h - 1][c] = 5
        for r in range(h):
            g[r][0] = 5
            g[r][6] = 5
            g[r][w - 1] = 5
        return g
    if name == "no_frame":
        g[3][3] = 2
        g[5][8] = 3
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 5
        return g
    return g
