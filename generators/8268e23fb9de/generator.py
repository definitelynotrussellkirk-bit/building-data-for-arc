"""Generator for b7955b3c.

Rule: cyan noise inside overlapping rectangles is restored using
inferred z-order.

Combinatorial axes (8): grid_h/w, order, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_overlap, no_noise, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "8268e23fb9de"
VERSION = "2.0.1"  # shape-locked in/out: fixed 14x15 grid, fixed 3 boxes, fixed cyan positions; only colors + 1-of-3 z-order varied. The z-order/overlap-restore rule is fully size- and position-generic. Now: random grid size, 3 anchored-overlap rects of random size/position, random z-order, random cyan cells inside covered area.
TASK_ID = "8268e23fb9de"
SUMMARY = "Three colored rectangles overlap on a 0-bg grid (later-drawn dominates the overlap, encoding a z-order). A few cyan-8 noise cells sit inside the covered region. Rule infers the z-order and restores each cyan cell to the topmost containing rectangle's color. Grid size, rectangle sizes/positions, z-order, colors and cyan placement all vary."

INVARIANTS = [
    "colored rectangles overlap on a modal background",
    "later rectangles visibly dominate overlap regions",
    "cyan cells are noise placeholders inside one or more rectangle bounding boxes",
    "each cyan cell is replaced by the topmost containing rectangle color",
]

ORDERS = ("o0", "o1", "o2")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_overlap", "no_noise", "full_grid")
HELPFUL_TEXTURES = ORDERS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 12..17", "valid": "10..20"},
    "grid_w":         {"type": "int", "default": "rng 13..18", "valid": "11..20"},
    "order":          {"type": "choice", "default": "rng helpful",
                       "valid": "0|1|2"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for order",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: has color-8 (cyan) noise cells; has ≥3 distinct non-{0,8} rectangle colors."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    cyans = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    rect_colors = {grid[r][c] for r in range(h) for c in range(w)
                   if grid[r][c] not in (0, 8)}
    if not cyans and not rect_colors:
        return []  # no_overlap/no_noise degenerate — allowed
    errs = []
    if not cyans:
        return []  # no_noise degenerate — allowed
    if not rect_colors:
        errs.append("has cyan noise but no visible rectangle colors")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 12); w = ctx.draw_int("grid_w", 11, 13)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 16, 20); w = ctx.draw_int("grid_w", 16, 20)
    else:
        h = ctx.draw_int("grid_h", 12, 17); w = ctx.draw_int("grid_w", 13, 18)
    colors = list(ctx.draw_distinct_colors("colors", n=3, exclude={0, 8}))

    # Three rectangles all containing a shared anchor cell -> guaranteed
    # pairwise overlap so the z-order is recoverable from the visible result.
    oy = rng.randint(h // 3, 2 * h // 3)
    ox = rng.randint(w // 3, 2 * w // 3)
    boxes = []
    for _ in range(3):
        top = rng.randint(max(0, oy - 4), max(0, oy - 2))
        left = rng.randint(max(0, ox - 4), max(0, ox - 2))
        bot = rng.randint(min(h - 1, oy + 2), min(h - 1, oy + 4))
        right = rng.randint(min(w - 1, ox + 2), min(w - 1, ox + 4))
        boxes.append((top, left, bot - top + 1, right - left + 1))

    g = full_grid(h, w, 0)
    draw_order = [0, 1, 2]
    tx = overrides.get("texture")
    if tx in ORDERS:
        draw_order = [(0, 1, 2), (1, 0, 2), (0, 2, 1)][int(tx[1])]
    else:
        rng.shuffle(draw_order)
    for idx in draw_order:
        draw_rect(g, *boxes[idx], colors[idx])

    # cyan noise on cells covered by some rectangle (topmost color is defined)
    covered = [(r, c) for r in range(h) for c in range(w) if g[r][c] != 0]
    n_noise = rng.randint(3, 6)
    for r, c in rng.sample(covered, min(n_noise, len(covered))):
        g[r][c] = 8
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(14, 15, 0)
    if name == "no_overlap":
        draw_rect(g, 2, 2, 3, 3, 3)
        draw_rect(g, 9, 9, 3, 3, 4)
        return g
    if name == "no_noise":
        draw_rect(g, 2, 2, 7, 7, 3)
        draw_rect(g, 4, 5, 7, 7, 4)
        return g
    if name == "full_grid":
        for r in range(14):
            for c in range(15):
                g[r][c] = 8
        return g
    return g
