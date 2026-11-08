"""Generator for arc_puzzle_bank_thirteenth_21_bundle:easy_86_fill_diagonal_spans_between_matching_endpoints.

Rule: each color appearing exactly twice along a diagonal pair fills
the diagonal span between them.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, pairs, texture.
Degenerates: no_pairs, axis_aligned, single_endpoint.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9968c63eab81"
VERSION = "1.1.1"
TASK_ID = "9968c63eab81"

SUMMARY = "Same-color diagonal endpoint pairs define filled diagonal spans."

INVARIANTS = [
    "background is 0",
    "each color appears exactly twice",
    "matching cells lie on one diagonal",
    "diagonal span interiors are initially blank",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "axis_aligned", "single_endpoint")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "5..20"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "5..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "pairs":          {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "palette_size":   {"type": "int", "default": "= pairs", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "scattered_diagonal_pairs",
                       "valid": "scattered_diagonal_pairs"},
    "n_distinct_colors": {"type": "int", "default": "= pairs", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _clear(g, cells):
    h, w = len(g), len(g[0])
    for r, c in cells:
        for rr in range(max(0, r - 1), min(h, r + 2)):
            for cc in range(max(0, c - 1), min(w, c + 2)):
                if g[rr][cc] != 0:
                    return False
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: each non-bg color appears exactly twice; each pair has |Δr| == |Δc| > 0 (diagonal)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    from collections import defaultdict
    pos: dict = defaultdict(list)
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v != 0:
                pos[v].append((r, c))
    if not pos:
        return []  # degenerate — allowed
    errs = []
    for color, cells in pos.items():
        if len(cells) != 2:
            errs.append(f"color {color} appears {len(cells)} times; expected 2")
            continue
        (r0, c0), (r1, c1) = cells
        dr, dc = abs(r1 - r0), abs(c1 - c0)
        if dr != dc or dr == 0:
            errs.append(f"color {color} pair not diagonal: |Δr|={dr}, |Δc|={dc}")
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
        h = ctx.draw_int("grid_h", 11, 16)
        w = ctx.draw_int("grid_w", 12, 18)
        target = ctx.draw_int("pairs", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 8, 12)
        target = ctx.draw_int("pairs", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], min(9, target))
    placed = 0
    for _ in range(180):
        if placed >= target:
            break
        length = rng.randint(3, min(5, h, w))
        dr = rng.choice([-1, 1])
        dc = rng.choice([-1, 1])
        r0 = rng.randint(max(0, -(length - 1) * dr), min(h - 1, h - 1 - (length - 1) * dr))
        c0 = rng.randint(max(0, -(length - 1) * dc), min(w - 1, w - 1 - (length - 1) * dc))
        cells = [(r0, c0), (r0 + (length - 1) * dr, c0 + (length - 1) * dc)]
        if _clear(g, cells):
            color = colors[placed % len(colors)]
            for r, c in cells:
                g[r][c] = color
            placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # Empty grid — rule has no diagonal pairs to span.
        return g
    if name == "axis_aligned":
        # Same color appears twice but along a horizontal or vertical
        # line, not diagonal — rule's diagonal-span filter doesn't fire.
        g[3][2] = 4; g[3][7] = 4
        g[2][6] = 6; g[6][6] = 6
        return g
    if name == "single_endpoint":
        # Color appears only once — rule's "exactly two endpoints"
        # check excludes it.
        g[2][2] = 4
        return g
    return g
