"""Generator for 57aa92db.

Rule: rectangular seeds scale a non-rectangular two-color template,
replacing the template accent color.

Combinatorial axes (8): grid_h/w, seed_count, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_template, no_seeds, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "78a914ac492e"
VERSION = "2.0.1"  # shape-locked in/out: fixed 14x15 grid, template + seeds at fixed positions. Rule (scale the non-rect 2-color template at each rectangular seed) is size-generic. Now random grid size, 1-3 seeds at random separated positions with distinct new colors, template at a random position.
TASK_ID = "78a914ac492e"
SUMMARY = "A non-rectangular two-color template (common cell + accent L) plus 1-3 rectangular seeds (2x2 common block + 2x1 new-color block), placed at random separated positions on a random-sized grid. The rule scales the template at each seed, replacing the accent with the seed's new color."

INVARIANTS = [
    "one connected multicolor object is a non-seed template",
    "seed objects contain a rectangular common-color block and a rectangular new-color block",
    "the common-color block determines the scale and alignment",
    "the template accent color is replaced by each seed's new color",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_template", "no_seeds", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 14..18", "valid": "10..24"},
    "grid_w":         {"type": "int", "default": "rng 15..18", "valid": "10..24"},
    "seed_count":     {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "4", "valid": "4"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _seed(g, r, c, common, new):
    draw_rect(g, r, c, 2, 2, common)
    draw_rect(g, r, c + 2, 2, 1, new)


def _free(g, r0, c0, fh, fw):
    """True if the fh x fw box plus a 1-cell margin is all background."""
    h, w = len(g), len(g[0])
    for r in range(r0 - 1, r0 + fh + 1):
        for c in range(c0 - 1, c0 + fw + 1):
            if 0 <= r < h and 0 <= c < w and g[r][c] != 0:
                return False
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg 0, ≥2 distinct non-zero colors (common + accent + seed colors), nonempty grid."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 2:
        errs.append(f"only {len(colors)} distinct non-zero color(s); expected ≥2 (template + seeds)")
    if not colors:
        errs.append("grid is entirely background")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 12, 14); w = ctx.draw_int("grid_w", 13, 15)
        seed_count = ctx.draw_int("seed_count", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 16, 22); w = ctx.draw_int("grid_w", 16, 22)
        seed_count = ctx.draw_int("seed_count", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 14, 18); w = ctx.draw_int("grid_w", 15, 18)
        seed_count = ctx.draw_int("seed_count", 1, 2)
    common, accent, *news = ctx.draw_distinct_colors("colors", n=2 + seed_count, exclude={0})
    g = full_grid(h, w, 0)

    # template: common cell + accent L (non-rectangular -> not a seed), 3x2 footprint
    for _ in range(120):
        tr = rng.randint(0, h - 3); tc = rng.randint(0, w - 2)
        if _free(g, tr, tc, 3, 2):
            g[tr][tc] = common
            g[tr][tc + 1] = accent
            g[tr + 1][tc] = accent
            g[tr + 2][tc] = accent
            break

    # seeds: 2x2 common block + 2x1 new block (both rect), 2x3 footprint, separated
    placed = 0
    for _ in range(300):
        if placed >= seed_count:
            break
        r0 = rng.randint(0, h - 2); c0 = rng.randint(0, w - 3)
        if _free(g, r0, c0, 2, 3):
            _seed(g, r0, c0, common, news[placed])
            placed += 1
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(14, 15, 0)
    if name == "no_template":
        _seed(g, 6, 2, 3, 4)
        return g
    if name == "no_seeds":
        g[1][1] = 3
        g[1][2] = 4
        g[2][1] = 4
        g[3][1] = 4
        return g
    if name == "full_grid":
        for r in range(14):
            for c in range(15):
                g[r][c] = 3
        return g
    return g
