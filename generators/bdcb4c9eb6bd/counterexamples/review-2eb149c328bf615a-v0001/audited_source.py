"""Generator for 292dd178.

Rule: open color-1 rectangles fill their interior and beam through
the gap.

Combinatorial axes (8): grid_h/w, open_side, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias, background.
Degenerates: no_rect, no_gap, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid

GENERATOR_ID = "bdcb4c9eb6bd"
# 1.2.0: place 1-3 non-overlapping open rectangles per grid (was always
# exactly one). The rule loops over EVERY color-1 rectangle (a train demo
# uses two), so multiple rects exercise the all-objects branch and add
# size/position/open-side diversity.
VERSION = "1.3.0"
TASK_ID = "bdcb4c9eb6bd"
SUMMARY = "Open color-1 rectangles fill interior and beam through the gap."

INVARIANTS = [
    "the mode color is the background",
    "there are 1-3 4-connected color-1 rectangular outlines",
    "each outline has exactly one interior gap on exactly one side",
    "the rectangle sits with at least one cell of margin from grid borders",
]

OPEN_SIDES = ("up", "down", "left", "right")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_rect", "no_gap", "full_grid")
HELPFUL_TEXTURES = OPEN_SIDES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..13", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "rng 11..15", "valid": "9..18"},
    "open_side":      {"type": "str", "default": "rng helpful",
                       "valid": "|".join(OPEN_SIDES)},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "rng", "valid": "rng"},
    "background":     {"type": "color", "default": "rng !{1,2}",
                       "valid": "0|3|4|5|6|7|8|9"},
    "texture":        {"type": "str", "default": "alias for open_side",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    forced_side = (overrides.get("texture") if overrides.get("texture") in OPEN_SIDES else None) or \
                  overrides.get("open_side") or None
    bg = ctx.draw_color("background", exclude={1, 2})
    h = rng.randint(11, 16)
    w = rng.randint(12, 18)
    g = full_grid(h, w, bg)
    # Reserve a 1-cell margin from the borders for every rectangle, and
    # a >=1 gap between rectangles so each stays a distinct component.
    occupied = [[False] * w for _ in range(h)]

    def fits(r0, c0, rh, rw):
        for r in range(r0 - 1, r0 + rh + 1):
            for c in range(c0 - 1, c0 + rw + 1):
                if 0 <= r < h and 0 <= c < w and occupied[r][c]:
                    return False
        return True

    n_rect = rng.randint(1, 3)
    placed = 0
    for _ in range(80):
        if placed >= n_rect:
            break
        rh = rng.randint(5, 7)
        rw = rng.randint(5, 8)
        if rh > h - 2 or rw > w - 2:
            continue
        r0 = rng.randint(1, h - rh - 1)
        c0 = rng.randint(1, w - rw - 1)
        if not fits(r0, c0, rh, rw):
            continue
        draw_rect_outline(g, r0, c0, rh, rw, 1)
        for r in range(r0, r0 + rh):
            for c in range(c0, c0 + rw):
                occupied[r][c] = True
        r1, c1 = r0 + rh - 1, c0 + rw - 1
        side = forced_side or rng.choice(list(OPEN_SIDES))
        gap_r = rng.randint(r0 + 1, r1 - 1)
        gap_c = rng.randint(c0 + 1, c1 - 1)
        if side == "up":
            g[r0][gap_c] = bg
        elif side == "down":
            g[r1][gap_c] = bg
        elif side == "left":
            g[gap_r][c0] = bg
        else:
            g[gap_r][c1] = bg
        placed += 1
    if placed == 0:
        # guaranteed single fallback
        draw_rect_outline(g, 1, 1, 5, 5, 1)
        g[1][2] = bg
    return g


def _components_of_color(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
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
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append(cells)
    return out


def _mode(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _rect_gap_side(cells):
    cellset = set(cells)
    r0 = min(r for r, _ in cells); r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells); c1 = max(c for _, c in cells)
    if r1 - r0 + 1 < 4 or c1 - c0 + 1 < 4:
        return None, "outline bbox too small"
    perimeter = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                 if r in (r0, r1) or c in (c0, c1)}
    extras = cellset - perimeter
    if extras:
        return None, "component has color-1 cells inside the rectangle interior"
    missing = sorted(perimeter - cellset)
    if len(missing) != 1:
        return None, f"expected exactly one outline gap, found {len(missing)}"
    gr, gc = missing[0]
    if gr in (r0, r1) and gc in (c0, c1):
        return None, "gap is on a corner, not an open side"
    if gr == r0:
        return "up", None
    if gr == r1:
        return "down", None
    if gc == c0:
        return "left", None
    if gc == c1:
        return "right", None
    return None, "gap is not on the outline"


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    h = len(grid)
    w = len(grid[0]) if grid else 0
    bg = _mode(grid)
    if bg in (1, 2):
        errs.append(f"background/mode color {bg} conflicts with rectangle or fill color")
    if any(v not in (bg, 1) for row in grid for v in row):
        errs.append("default input should contain only background and color-1 outlines")
    comps = _components_of_color(grid, 1)
    if not (1 <= len(comps) <= 3):
        errs.append(f"expected 1-3 color-1 open rectangles, found {len(comps)}")
    for cells in comps:
        r0 = min(r for r, _ in cells); r1 = max(r for r, _ in cells)
        c0 = min(c for _, c in cells); c1 = max(c for _, c in cells)
        if r0 <= 0 or c0 <= 0 or r1 >= h - 1 or c1 >= w - 1:
            errs.append("rectangle lacks the required one-cell border margin")
            break
        side, msg = _rect_gap_side(cells)
        if msg:
            errs.append(msg)
            break
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 13, 0)
    if name == "no_rect":
        return g
    if name == "no_gap":
        draw_rect_outline(g, 2, 2, 6, 7, 1)
        return g
    if name == "full_grid":
        for r in range(11):
            for c in range(13):
                g[r][c] = 1
        return g
    return g
