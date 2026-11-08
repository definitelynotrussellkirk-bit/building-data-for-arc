"""Generator for d753a70b.

Rule: red diamond outlines shrink, gray diamond outlines grow on
orange background.

Combinatorial axes (8): grid_h/w, red_radius, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
gray_radius.
Degenerates: no_red, no_gray, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "388e9ae29018"
VERSION = "3.0.1"  # shape-locked-in/out (fixed 15x15, exactly 1 red + 1 gray diamond): rule reads h,w dynamically and processes EVERY red(shrink)/gray(grow) diamond. Now grid 12..20 (incl non-square) + 1-2 red AND 1-2 gray diamonds at varied radii/positions, separated >=2 (objects-8). bg stays 7 (rule hardcodes bg=7).
TASK_ID = "388e9ae29018"
SUMMARY = (
    "Fixed 15×15 color-7 (orange) bg grid with: (a) a "
    "RED DIAMOND OUTLINE — color 2 cells at all positions "
    "where Manhattan distance from a center (red_r, "
    "red_c) equals red_radius (2 or 3); (b) a GRAY "
    "DIAMOND OUTLINE — color 5 cells at all positions "
    "where Manhattan distance from a center (gray_r, "
    "gray_c) equals gray_radius (1 or 2). Diamonds are "
    "positioned with margin so growth/shrink stays "
    "in-bounds. Rule: detect each diamond. RED diamond "
    "SHRINKS by 1 (replace red cells with bg, redraw at "
    "red_radius - 1). GRAY diamond GROWS by 1 (redraw "
    "at gray_radius + 1). Output: bg + shrunk red "
    "diamond + grown gray diamond."
)

INVARIANTS = [
    "the background is orange",
    "red and gray objects are Manhattan-distance diamond outlines",
    "red objects shrink one radius while gray objects grow one radius",
    "diamonds sit clear of grid borders so growth/shrink stays in-bounds",
]

RED_RADII = ("r2", "r3")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_red", "no_gray", "full_grid")
HELPFUL_TEXTURES = RED_RADII

AXES = {
    "grid_h":         {"type": "int", "default": "rng 13..18", "valid": "12..20"},
    "grid_w":         {"type": "int", "default": "rng 13..18", "valid": "12..20"},
    "red_radius":     {"type": "str", "default": "rng helpful",
                       "valid": "|".join(RED_RADII)},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "gray_radius":    {"type": "int", "default": "rng 1..2", "valid": "1..2"},
    "texture":        {"type": "str", "default": "alias for red_radius",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _draw_diamond(g, cr, cc, radius, color):
    for r in range(len(g)):
        for c in range(len(g[0])):
            if abs(r - cr) + abs(c - cc) == radius:
                g[r][c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        H = ctx.draw_int("grid_h", 12, 14); W = ctx.draw_int("grid_w", 12, 14)
        n_red = 1; n_gray = 1
    elif difficulty == "hard":
        H = ctx.draw_int("grid_h", 16, 20); W = ctx.draw_int("grid_w", 16, 20)
        n_red = rng.randint(1, 2); n_gray = rng.randint(1, 2)
    else:
        H = ctx.draw_int("grid_h", 13, 18); W = ctx.draw_int("grid_w", 13, 18)
        n_red = rng.randint(1, 2); n_gray = rng.randint(1, 2)
    tx = overrides.get("texture")
    # Rule coverage requires at least one red shrinker AND one gray grower.
    # The old greedy placement silently accepted partial layouts (often red-only)
    # when a large early diamond consumed the small canvas.  Keep the radii inside
    # the documented axes and restart the whole layout until every promised object
    # lands.
    forced_red = int(tx[1]) if tx in RED_RADII else None
    red_radii = [forced_red if (i == 0 and forced_red) else rng.choice([2, 3])
                 for i in range(n_red)]
    gray_radii = [rng.choice([1, 2]) for _ in range(n_gray)]

    def realize_once():
        g = full_grid(H, W, 7)
        placed = []  # (cr, cc, radius)

        def try_place(radius, color, margin):
            if margin > H - 1 - margin or margin > W - 1 - margin:
                return False
            for _ in range(120):
                cr = rng.randint(margin, H - 1 - margin)
                cc = rng.randint(margin, W - 1 - margin)
                if all(abs(cr - pr) + abs(cc - pc) >= radius + prad + 3
                       for (pr, pc, prad) in placed):
                    _draw_diamond(g, cr, cc, radius, color)
                    placed.append((cr, cc, radius))
                    return True
            return False

        # Place larger rings first; this dramatically reduces restart pressure.
        objects = [(r, 2, r + 1) for r in red_radii] + [(r, 5, r + 2) for r in gray_radii]
        for radius, color, margin in sorted(objects, reverse=True):
            if not try_place(radius, color, margin):
                return None
        return g

    for _ in range(120):
        g = realize_once()
        if g is not None:
            return g

    # Deterministic last resort for the rare tight hard layouts: use four corners
    # with the same documented radius ranges rather than emitting a partial rule.
    H = max(H, 18); W = max(W, 18)
    g = full_grid(H, W, 7)
    slots = [(4, 4), (4, W - 5), (H - 5, W - 5), (H - 5, 4)]
    objects = [(r, 2) for r in red_radii] + [(r, 5) for r in gray_radii]
    for (radius, color), (cr, cc) in zip(objects, slots):
        _draw_diamond(g, cr, cc, radius, color)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(15, 15, 7)
    if name == "no_red":
        _draw_diamond(g, 7, 7, 2, 5)
        return g
    if name == "no_gray":
        _draw_diamond(g, 7, 7, 2, 2)
        return g
    if name == "full_grid":
        for r in range(15):
            for c in range(15):
                g[r][c] = 7
        return g
    return g


def _selfcheck_diamond_outlines(grid, color):
    h, w = len(grid), len(grid[0])
    cells = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    candidates = []
    for cr in range(h):
        for cc in range(w):
            for radius in range(1, 7):
                outline = set()
                for dr in range(-radius, radius + 1):
                    dc = radius - abs(dr)
                    for cdelta in ({-dc, dc} if dc else {0}):
                        rr, cc2 = cr + dr, cc + cdelta
                        if 0 <= rr < h and 0 <= cc2 < w:
                            outline.add((rr, cc2))
                if len(outline) == 4 * radius and outline <= cells:
                    candidates.append((radius, cr, cc, outline))
    used = set()
    count = 0
    for radius, cr, cc, outline in sorted(candidates, reverse=True):
        if not (outline & used):
            used |= outline
            count += 1
    return count, cells - used


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    bad = sorted({v for row in grid for v in row if v not in (2, 5, 7)})
    if bad:
        errors.append(f"unexpected colors outside {{2,5,7}}: {bad}")
    red_n, red_left = _selfcheck_diamond_outlines(grid, 2)
    gray_n, gray_left = _selfcheck_diamond_outlines(grid, 5)
    if red_n < 1:
        errors.append("expected at least one red diamond outline")
    if gray_n < 1:
        errors.append("expected at least one gray diamond outline")
    if red_left:
        errors.append(f"red cells not covered by complete diamond outlines: {len(red_left)}")
    if gray_left:
        errors.append(f"gray cells not covered by complete diamond outlines: {len(gray_left)}")
    return errors

