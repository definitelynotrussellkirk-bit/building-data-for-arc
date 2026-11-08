"""Generator for arc_additional_puzzles_21_set8:E51 — connect 2 same-color cells aligned in row or col.

Rule: each color with exactly 2 cells; if cells share row/col, fill
segment between them with that color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, not_aligned, single_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6d374c3846bf"
VERSION = "1.1.1"
TASK_ID = "6d374c3846bf"
SUMMARY = "2-3 colors each with 2 cells aligned in row or col."

INVARIANTS = [
    "≥2 colors with exactly 2 cells each",
    "each pair shares a row or col, separated by gap",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "not_aligned", "single_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_pairs":        {"type": "int", "default": "rng 2..3", "valid": "2..5"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "axis_aligned_pairs",
                       "valid": "axis_aligned_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥2 colors each with exactly 2 cells; skip degenerate textures."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    from collections import Counter
    counts = Counter(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    pairs = [c for c, n in counts.items() if n == 2]
    if len(pairs) < 2:
        errs.append(f"expected ≥2 colors with exactly 2 cells; got pairs={pairs}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 10, 13)
    else:
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 8, 10)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    n = rng.randint(2, 3)
    pal = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], n)
    used_rows = set()
    used_cols = set()
    for color in pal:
        for _ in range(20):
            if rng.random() < 0.5:
                r = rng.randint(0, h - 1)
                if r in used_rows: continue
                cs = sorted(rng.sample(range(w), 2))
                if cs[1] - cs[0] >= 3 and g[r][cs[0]] == 0 and g[r][cs[1]] == 0:
                    g[r][cs[0]] = color; g[r][cs[1]] = color
                    used_rows.add(r)
                    break
            else:
                c = rng.randint(0, w - 1)
                if c in used_cols: continue
                rs = sorted(rng.sample(range(h), 2))
                if rs[1] - rs[0] >= 3 and g[rs[0]][c] == 0 and g[rs[1]][c] == 0:
                    g[rs[0]][c] = color; g[rs[1]][c] = color
                    used_cols.add(c)
                    break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # Singletons only — no pair to connect, rule is a no-op.
        g[1][2] = 3; g[3][6] = 4; g[5][1] = 5
        return g
    if name == "not_aligned":
        # Pairs exist but neither shares row nor column — rule fills nothing.
        g[1][1] = 3; g[3][4] = 3
        g[2][6] = 4; g[5][2] = 4
        return g
    if name == "single_color":
        # Only one color present — at minimum the rule needs the canonical 2+
        # so a single color produces a degenerate non-multi-color signal.
        g[1][1] = 4; g[1][6] = 4
        return g
    return g
