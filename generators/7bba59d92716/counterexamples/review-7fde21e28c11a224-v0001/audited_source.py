"""Generator for arc_additional_puzzle_bank_volume23:E155 — Mark middle of vertical 1-line of length 5 with 2.

Rule: each 1-blob that is a vertical line of size 5 → middle cell to 2.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_lines,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_length5, all_length5, horizontal_lines.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7bba59d92716"
# 1.2.0: when two color-1 vertical lines landed in ADJACENT columns with
# overlapping rows they 4-connect into one non-line blob -> no length-5 vertical
# line qualifies -> rule marks nothing -> output == input. Enforce >=2 column gap
# between all color-1 lines and verify >=1 qualifies. Adds self_check.
VERSION = "1.2.0"
TASK_ID = "7bba59d92716"
SUMMARY = "2 vertical 1-lines of length 5 + a few non-line 1s as decoration."

INVARIANTS = [
    "exactly 2 vertical 1-lines of length 5",
    "1-2 short vertical 1-lines of other lengths (won't qualify)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_length5", "all_length5", "horizontal_lines")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..9", "valid": "8..12"},
    "grid_w":         {"type": "int", "default": "rng 10..12", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_lines":        {"type": "int", "default": "2", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..2"},
    "position_bias":  {"type": "str", "default": "vertical_lines",
                       "valid": "vertical_lines"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 10, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 11, 12)
    else:
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 12)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    # choose 3 columns for color-1 lines, pairwise >=2 apart so adjacent vertical
    # lines never merge into a single non-line blob.
    one_cols = _spaced_columns(rng, w, 3, min_gap=2)
    c1, c2, c3 = one_cols
    r1 = rng.randint(0, h - 5)
    r2 = rng.randint(0, h - 5)
    for dr in range(5):
        g[r1 + dr][c1] = 1
        g[r2 + dr][c2] = 1
    rs = rng.randint(0, h - 4)
    for dr in range(rng.randint(2, 3)):     # short decoy line (length 2-3, won't qualify)
        g[rs + dr][c3] = 1
    # color-6 marker in a column not used by any 1-line (different color anyway)
    free_cols = [c for c in range(w) if c not in one_cols]
    if free_cols:
        g[h - 1][rng.choice(free_cols)] = 6
    return g


def _spaced_columns(rng, w, n, min_gap):
    """Pick n columns in [0,w) that are pairwise >= min_gap apart."""
    for _ in range(200):
        chosen = []
        cols = list(range(w)); rng.shuffle(cols)
        for c in cols:
            if all(abs(c - x) >= min_gap for x in chosen):
                chosen.append(c)
            if len(chosen) == n:
                return chosen
    # deterministic fallback: evenly spaced
    return [min(w - 1, i * min_gap) for i in range(n)]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """At least one color-1 component must be a vertical line of exactly 5 cells,
    so the rule (mark its middle with 2) actually fires -> output != input."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != 1 or seen[sr][sc]:
                continue
            stack = [(sr, sc)]; seen[sr][sc] = True; cells = []
            while stack:
                r, c = stack.pop(); cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] and grid[nr][nc] == 1:
                        seen[nr][nc] = True; stack.append((nr, nc))
            comps.append(cells)

    def is_vline5(cells):
        if len(cells) != 5:
            return False
        cs = {c for _, c in cells}; rs = sorted(r for r, _ in cells)
        return len(cs) == 1 and rs == list(range(rs[0], rs[0] + 5))

    if not any(is_vline5(c) for c in comps):
        return ["no vertical color-1 line of length 5 — the rule marks nothing "
                "(output == input, identity)"]
    return []


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_length5":
        # all vertical 1-lines have other lengths (3, 4) → no qualifying targets, rule no-op
        for dr in range(3):
            g[1 + dr][2] = 1
        for dr in range(4):
            g[1 + dr][6] = 1
        return g
    if name == "all_length5":
        # every column has length-5 → every column gets middle marked, no contrast across blobs
        for c in [1, 4, 7]:
            for dr in range(5):
                g[2 + dr][c] = 1
        return g
    if name == "horizontal_lines":
        # 1-blobs are horizontal not vertical → "vertical line" condition never matches, rule no-op
        for dc in range(5):
            g[2][1 + dc] = 1
        for dc in range(5):
            g[5][3 + dc] = 1
        return g
    return g
