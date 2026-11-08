"""Generator for arc_additional_puzzle_bank_volume3:E17 — recolor 1-border-touching components.

Rule: for each color-7 component, count the number of grid borders
its bounding box touches (top: r1=0, bottom: r2=h-1, left: c1=0,
right: c2=w-1). If exactly 1 border is touched, recolor to 8. Else
keep color 7. Output preserves all 7-cells not at exactly-1-border
bboxes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "7aba2cb70bae"
VERSION = "2.0.1"  # rewrite: old generator placed only 3 fixed components
TASK_ID = "7aba2cb70bae"
SUMMARY = (
    "0-bg grid with N (3-5) separated color-7 components, each "
    "occupying a small connected region. Each component's bounding "
    "box touches some number of grid borders (top, bottom, left, "
    "right) — 0, 1, 2, 3, or 4. Rule: for each color-7 component, "
    "count its border-touch number K. If K == 1, recolor that "
    "component's cells to color 8. Otherwise (K in {0, 2, 3, 4}), "
    "keep the component as color 7. Output is the input with "
    "exactly-1-border components recolored 8; all other cells "
    "unchanged."
)

# Rivals: 'output is input' refuted by demos with ≥1 1-border
# component. 'recolor all components to 8' refuted by demos showing
# 0-border and 2-border components stay 7. 'recolor border-touching
# (any K≥1)' refuted by demos with K=2 components staying 7.
# 'recolor only corner (K=2) components' refuted by demos showing
# K=1 components get the recolor. 'recolor by size' refuted by demos
# with same-size components getting different verdicts. 'use color 5
# for output' refuted by demos showing color 8. 4 demos with a mix
# of (K=0, K=1, K=2) components pin the rule.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "all colored components are color 7 (rule only acts on 7s)",
    "≥1 component touches exactly 1 border (KEPT recolor to 8)",
    "≥1 component touches 0 borders (interior component, stays 7) OR touches 2+ borders (corner, stays 7)",
    "components are separated by ≥1 bg cell (4-conn separation)",
]

PALETTE_KINDS = ("default", "border", "interior", "mixed")
DEGENERATE_TEXTURES = ("no_components", "all_interior", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "6..18"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "6..18"},
    "n_one_border":   {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "n_zero_border":  {"type": "int", "default": "rng 1..2", "valid": "0..3"},
    "n_two_border":   {"type": "int", "default": "rng 0..2", "valid": "0..2"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg 0, all nonzero cells are color 7, ≥1 cell present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonzero:
        errs.append("no nonzero cells (no color-7 components to classify)")
        return errs
    non_7 = [(r, c) for r, c in nonzero if grid[r][c] != 7]
    if non_7:
        errs.append(f"{len(non_7)} non-zero cell(s) not color 7 (e.g. {non_7[:2]}); all components must be color 7")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 8, 10)
        n_one, n_zero, n_two = 1, 1, 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 18)
        w = ctx.draw_int("grid_w", 14, 18)
        n_one = ctx.draw_int("n_one_border", 2, 4)
        n_zero = ctx.draw_int("n_zero_border", 1, 3)
        n_two = ctx.draw_int("n_two_border", 1, 2)
    else:
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 10, 14)
        n_one = ctx.draw_int("n_one_border", 1, 3)
        n_zero = ctx.draw_int("n_zero_border", 1, 2)
        n_two = ctx.draw_int("n_two_border", 0, 2)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    placed = []  # list of (r0, c0, bh, bw)
    def _try_place(r0, c0, bh, bw):
        for (pr, pc, pbh, pbw) in placed:
            if (r0 - (pr + pbh) < 2 and pr - (r0 + bh) < 2 and
                c0 - (pc + pbw) < 2 and pc - (c0 + pbw) < 2):
                return False
        if r0 < 0 or c0 < 0 or r0 + bh > h or c0 + bw > w:
            return False
        for r in range(r0, r0 + bh):
            for c in range(c0, c0 + bw):
                if g[r][c] != 0:
                    return False
        return True
    # Place 1-border components (touching exactly 1 border)
    for _ in range(n_one):
        for _ in range(60):
            side = rng.choice(["top", "bottom", "left", "right"])
            bh = rng.randint(1, 3); bw = rng.randint(1, 3)
            if side == "top":
                r0 = 0
                c0 = rng.randint(2, w - bw - 2)  # not at corners
            elif side == "bottom":
                r0 = h - bh
                c0 = rng.randint(2, w - bw - 2)
            elif side == "left":
                r0 = rng.randint(2, h - bh - 2)
                c0 = 0
            else:
                r0 = rng.randint(2, h - bh - 2)
                c0 = w - bw
            if _try_place(r0, c0, bh, bw):
                draw_rect(g, r0, c0, bh, bw, 7)
                placed.append((r0, c0, bh, bw))
                break
    # Place 0-border components (interior, not touching any border)
    for _ in range(n_zero):
        for _ in range(60):
            bh = rng.randint(1, 3); bw = rng.randint(1, 3)
            r0 = rng.randint(1, h - bh - 1)
            c0 = rng.randint(1, w - bw - 1)
            if _try_place(r0, c0, bh, bw):
                draw_rect(g, r0, c0, bh, bw, 7)
                placed.append((r0, c0, bh, bw))
                break
    # Place 2-border components (corner placements)
    for _ in range(n_two):
        for _ in range(60):
            corner = rng.choice(["nw", "ne", "sw", "se"])
            bh = rng.randint(1, 2); bw = rng.randint(1, 2)
            if corner == "nw":
                r0, c0 = 0, 0
            elif corner == "ne":
                r0, c0 = 0, w - bw
            elif corner == "sw":
                r0, c0 = h - bh, 0
            else:
                r0, c0 = h - bh, w - bw
            if _try_place(r0, c0, bh, bw):
                draw_rect(g, r0, c0, bh, bw, 7)
                placed.append((r0, c0, bh, bw))
                break
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 10, 0)
    if name == "no_components":
        return g
    if name == "all_interior":
        draw_rect(g, 4, 4, 2, 2, 7)
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(10):
                g[r][c] = 7
        return g
    return g
