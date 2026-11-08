"""Generator for puzzle b9b7f026.

Rule: multiple rects; exactly one has a 0-hole inside; rule outputs
1×1 with that color.

Combinatorial axes (8): grid_h/w, n_rects, rect_size_kind,
position_bias, palette_kind, hole_position_kind, anchor_corner,
asymmetry_force.
Degenerates: no_holes, multiple_holes, single_rect.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect

GENERATOR_ID = "65b733c58db4"
VERSION = "1.2.1"  # floor large-rect lo at max_h/max_w (easy h=10/11 gave randint(4,3))
TASK_ID = "65b733c58db4"
SUMMARY = "Multiple solid rects; one has 0-hole; rule outputs 1×1 with that color."

INVARIANTS = [
    "background is 0",
    ">=2 solid colored rectangles, each >=3×3",
    "EXACTLY one rectangle has a single 0-cell hole inside",
    "rectangles non-overlapping with margin >=1",
]

RECT_SIZE_KINDS = ("small", "medium", "large", "varied")
POSITION_BIAS = ("center", "spread", "edge")
HOLE_POSITION_KINDS = ("center", "off_center", "corner")
PALETTE_KINDS = ("warm", "cool", "broad", "small")
DEGENERATE_TEXTURES = ("no_holes", "multiple_holes", "single_rect")
HELPFUL_TEXTURES = RECT_SIZE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "grid_w":            {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "n_rects":           {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "rect_size_kind":    {"type": "str", "default": "rng helpful",
                          "valid": "small|medium|large|varied"},
    "position_bias":     {"type": "str", "default": "rng spread|center|edge",
                          "valid": "spread|center|edge"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "warm|cool|broad|small"},
    "hole_position_kind": {"type": "str", "default": "rng center|off_center|corner",
                           "valid": "center|off_center|corner"},
    "anchor_corner":     {"type": "bool", "default": "false",
                          "valid": "true|false"},
    "texture":           {"type": "str", "default": "alias for rect_size_kind",
                          "valid": "small|medium|large|varied|no_holes|multiple_holes|single_rect"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 non-bg rectangle cell present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    has_rect = any(grid[r][c] != 0 for r in range(h) for c in range(w))
    if not has_rect:
        errs.append("no non-bg rectangle cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 10, 13
    elif difficulty == "hard":
        h_lo, h_hi = 17, 22
    else:
        h_lo, h_hi = 12, 18
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_rects = int(overrides.get("n_rects",
                                ctx.draw_int("n_rects", 2, 4)))
    n_rects = max(2, min(5, n_rects))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    if palette_kind == "warm":
        pool = [3, 4, 6, 9]
    elif palette_kind == "cool":
        pool = [1, 5, 7, 8]
    elif palette_kind == "small":
        pool = [1, 2, 3]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    if len(pool) < n_rects:
        extras = [c for c in range(1, 10) if c not in pool]
        rng.shuffle(extras)
        pool += extras
    palette = pool[:n_rects]
    size_kind = (overrides.get("texture") or
                 overrides.get("rect_size_kind")
                 or ctx.draw_choice("rect_size_kind",
                                    list(RECT_SIZE_KINDS)))
    bias = overrides.get("position_bias",
                         ctx.draw_choice("position_bias",
                                         ["spread", "center", "edge"]))
    g = full_grid(h, w, 0)
    placed_boxes = []
    for color in palette:
        for _try in range(20):
            rh, rw = _rect_dims(size_kind, h, w, rng)
            r0 = rng.randint(1, h - rh - 1)
            c0 = rng.randint(1, w - rw - 1)
            ok = all(not (r0 - 1 <= obr2 and r0 + rh >= obr1
                          and c0 - 1 <= obc2 and c0 + rw >= obc1)
                     for (obr1, obc1, obr2, obc2, _) in placed_boxes)
            if not ok:
                continue
            draw_rect(g, r0, c0, rh, rw, color)
            placed_boxes.append((r0, c0, r0 + rh - 1, c0 + rw - 1, color))
            break
    if len(placed_boxes) < 2:
        return _draw_from_degenerate("single_rect", h, w, rng)
    candidates = [b for b in placed_boxes
                  if (b[2] - b[0]) >= 2 and (b[3] - b[1]) >= 2]
    if not candidates:
        return _draw_from_degenerate("no_holes", h, w, rng)
    chosen = rng.choice(candidates)
    rr, rc, rr2, rc2, _ = chosen
    hole_kind = overrides.get("hole_position_kind",
                              ctx.draw_choice("hole_position_kind",
                                              list(HOLE_POSITION_KINDS)))
    if hole_kind == "center":
        hr = (rr + rr2) // 2
        hc = (rc + rc2) // 2
    elif hole_kind == "corner":
        hr = rr + 1
        hc = rc + 1
    else:
        hr = rng.randint(rr + 1, rr2 - 1)
        hc = rng.randint(rc + 1, rc2 - 1)
    g[hr][hc] = 0
    return g


def _rect_dims(kind, h, w, rng):
    max_h = max(3, h // 3)
    max_w = max(3, w // 3)
    if kind == "small":
        return 3, 3
    if kind == "medium":
        return rng.randint(3, 4), rng.randint(3, 4)
    if kind == "large":
        # max_h/max_w = max(3, dim//3) collapse to 3 on the easy band's smallest
        # grids (h=10/11 → 3) → randint(4,3) empty. Floor the lo at the max; a 3×3
        # rect still satisfies the ≥3×3 invariant (it just isn't "large" there).
        return rng.randint(min(4, max_h), max_h), rng.randint(min(4, max_w), max_w)
    return rng.randint(3, max_h), rng.randint(3, max_w)


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    palette = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(palette)
    if name == "no_holes":
        if h >= 5 and w >= 10:
            draw_rect(g, 1, 1, 3, 3, palette[0])
            draw_rect(g, 1, 5, 3, 3, palette[1])
        return g
    if name == "multiple_holes":
        if h >= 5 and w >= 10:
            draw_rect(g, 1, 1, 3, 3, palette[0])
            draw_rect(g, 1, 5, 3, 3, palette[1])
            g[2][2] = 0
            g[2][6] = 0
        return g
    if name == "single_rect":
        if h >= 5 and w >= 5:
            draw_rect(g, 1, 1, 3, 3, palette[0])
            g[2][2] = 0
        return g
    return g
