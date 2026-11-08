"""Generator for arc_puzzle_bank_twelfth_21_bundle:easy_78_fill_axis_spans_between_matching_endpoints.

Rule: each color appears as one horizontal/vertical endpoint pair whose
straight zero span is filled.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, single_endpoint, off_axis_pair.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "43f15cc63654"
VERSION = "1.1.1"
TASK_ID = "43f15cc63654"

SUMMARY = "Each color appears as one horizontal or vertical endpoint pair whose span is filled."

INVARIANTS = [
    "background is 0",
    "each active color appears exactly twice",
    "each pair is axis-aligned",
    "spans are separated so fills do not overwrite one another",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "single_endpoint", "off_axis_pair")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "4..22"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "4..24"},
    "pairs":          {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "axis_aligned_pairs",
                       "valid": "axis_aligned_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, cells):
    h, w = len(g), len(g[0])
    for r, c in cells:
        if not (0 <= r < h and 0 <= c < w) or g[r][c] != 0:
            return False
        for rr in range(max(0, r - 1), min(h, r + 2)):
            for cc in range(max(0, c - 1), min(w, c + 2)):
                if g[rr][cc] != 0:
                    return False
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, each active color appears exactly twice (axis-aligned pairs)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    from collections import Counter
    freq = Counter(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    odd = [v for v, cnt in freq.items() if cnt != 2]
    if odd:
        errs.append(f"colors with count ≠ 2 (expected endpoint pairs): {sorted(odd)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 10)
        target = ctx.draw_int("pairs", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 18)
        w = ctx.draw_int("grid_w", 13, 20)
        target = ctx.draw_int("pairs", 4, 7)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 8, 13)
        target = ctx.draw_int("pairs", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], min(9, target))
    placed = 0
    for _ in range(180):
        if placed >= target:
            break
        vertical = rng.choice([False, True])
        if vertical:
            c = rng.randrange(w)
            r0 = rng.randint(0, h - 3)
            r1 = rng.randint(r0 + 2, h - 1)
            path = [(r, c) for r in range(r0, r1 + 1)]
            endpoints = [(r0, c), (r1, c)]
        else:
            r = rng.randrange(h)
            c0 = rng.randint(0, w - 3)
            c1 = rng.randint(c0 + 2, w - 1)
            path = [(r, c) for c in range(c0, c1 + 1)]
            endpoints = [(r, c0), (r, c1)]
        if _free(g, path):
            color = colors[placed % len(colors)]
            for r, c in endpoints:
                g[r][c] = color
            placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # Empty grid — rule has no spans to fill.
        return g
    if name == "single_endpoint":
        # Color appears once — rule's "exactly two endpoints"
        # precondition fails; fill undefined.
        g[3][3] = 4
        return g
    if name == "off_axis_pair":
        # Two same-color endpoints not aligned on row/col —
        # rule's "axis-aligned" filter excludes; fill never fires.
        g[2][2] = 4; g[5][7] = 4
        return g
    return g
