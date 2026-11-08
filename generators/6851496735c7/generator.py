"""Generator for puzzle arc_additional_puzzle_bank_volume2:M14 — every
solid rectangular object is replaced by its perimeter only (same color).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_rects,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: rects_too_small, rects_overlap, no_rects.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect

GENERATOR_ID = "6851496735c7"
VERSION = "1.1.2"
TASK_ID = "6851496735c7"
SUMMARY = "Several solid rectangles; rule replaces each with its perimeter outline (same color)."

# Rivals: 'outline largest only' refuted by ≥1 demo with multiple rects.
# 'recolor outline' refuted by any demo (rule preserves per-rect color).
# 'flood interior' refuted by ≥1 demo with ≥4×4 rect (interior visibly empty).
# 3 demos with varied rect counts (1, 2, 3+) cover all refutations.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    ">=1 solid rectangle, each at least 3x3 (so the rule's effect is visible)",
    "rectangles non-overlapping with margin >= 1",
    "different rectangles can share or use distinct colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("rects_too_small", "rects_overlap", "no_rects")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "grid_w":         {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": 'default|warm|cool|varied'},
    "n_rects":        {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": 'default|warm|cool|varied|rects_too_small|rects_overlap|no_rects'},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; grid non-empty/rectangular; >=1 nonzero cell (at least one rect placed)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonzero:
        errs.append("no non-bg cells — no rectangle was placed")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 12, 14)
        w = ctx.draw_int("grid_w", 12, 14)
        n_rects = ctx.draw_int("n_rects", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 16, 18)
        w = ctx.draw_int("grid_w", 16, 18)
        n_rects = ctx.draw_int("n_rects", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 12, 18)
        w = ctx.draw_int("grid_w", 12, 18)
        n_rects = ctx.draw_int("n_rects", 2, 4)

    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("placement")
    placed = 0
    placed_boxes: list[tuple[int, int, int, int]] = []
    palette_pool = list(range(1, 10))
    for _ in range(n_rects):
        for _try in range(40):
            rh = rng.randint(3, max(3, h // 3))
            rw = rng.randint(3, max(3, w // 3))
            rr = rng.randint(1, h - rh - 1)
            rc = rng.randint(1, w - rw - 1)
            ok = True
            for (or1, oc1, or2, oc2) in placed_boxes:
                if (rr - 1 <= or2 and rr + rh >= or1
                        and rc - 1 <= oc2 and rc + rw >= oc1):
                    ok = False; break
            if not ok: continue
            color = rng.choice(palette_pool)
            draw_rect(g, rr, rc, rh, rw, color)
            placed_boxes.append((rr, rc, rr + rh - 1, rc + rw - 1))
            placed += 1
            break
    if placed == 0:
        return [[0]]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 14, 14
    g = full_grid(h, w, 0)
    if name == "rects_too_small":
        # 1x1 or 2x2 rects → perimeter equals interior, rule has no visible effect
        draw_rect(g, 2, 2, 1, 1, 4)
        draw_rect(g, 5, 5, 2, 2, 6)
        draw_rect(g, 9, 9, 1, 2, 7)
        return g
    if name == "rects_overlap":
        # overlapping rectangles → perimeter outlines also overlap, ambiguous component identity
        draw_rect(g, 2, 2, 5, 5, 4)
        draw_rect(g, 4, 4, 5, 5, 6)
        return g
    if name == "no_rects":
        # empty grid → no objects to outline, rule no-op
        return g
    return g
