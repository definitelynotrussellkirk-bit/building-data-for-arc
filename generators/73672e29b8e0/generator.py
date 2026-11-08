"""Generator for puzzle 31aa019c.

Rule: find the color appearing exactly once. Output: empty grid; that
cell stays its color, its 8 neighbors become 2.

Combinatorial axes (8): grid_h/w, n_common_colors, common_count_min,
common_count_max, unique_position, palette_kind, anchor_corner,
asymmetry_force.
Degenerates: no_unique, multiple_unique, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "73672e29b8e0"
VERSION = "1.2.0"
TASK_ID = "73672e29b8e0"
SUMMARY = "Common colors + 1 unique-color cell; rule outputs unique + halo of 2."

INVARIANTS = [
    "background is 0",
    "exactly 1 color has count 1 (the unique)",
    "other non-bg colors have count >=2",
    "unique cell at interior (so halo fits)",
]

UNIQUE_POSITIONS = ("center", "near_edge", "diagonal", "corner_adj",
                    "spread")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_unique", "multiple_unique", "full_grid")
HELPFUL_TEXTURES = UNIQUE_POSITIONS

AXES = {
    "grid_h":          {"type": "int", "default": "rng 5..9", "valid": "4..12"},
    "grid_w":          {"type": "int", "default": "rng 9..13", "valid": "7..16"},
    "n_common_colors": {"type": "int", "default": "rng 3..4", "valid": "2..6"},
    "common_count_min":{"type": "int", "default": "2", "valid": "2..5"},
    "common_count_max":{"type": "int", "default": "rng 3..4", "valid": "2..6"},
    "unique_position": {"type": "str", "default": "rng helpful",
                        "valid": "|".join(UNIQUE_POSITIONS)},
    "palette_kind":    {"type": "str", "default": "rng helpful",
                        "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":   {"type": "bool", "default": "false",
                        "valid": "true|false"},
    "texture":         {"type": "str", "default": "alias for unique_position",
                        "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 4, 6
    elif difficulty == "hard":
        h_lo, h_hi = 9, 12
    else:
        h_lo, h_hi = 5, 9
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo + 4, h_hi + 4)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_common = int(overrides.get("n_common_colors",
                                 ctx.draw_int("n_common_colors", 3, 4)))
    n_common = max(2, min(6, n_common))
    c_min = int(overrides.get("common_count_min", 2))
    c_max = int(overrides.get("common_count_max",
                              ctx.draw_int("common_count_max", 3, 4)))
    pos = (overrides.get("texture") or
           overrides.get("unique_position")
           or ctx.draw_choice("unique_position",
                              list(UNIQUE_POSITIONS)))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    palette = _build_palette(palette_kind, n_common + 1, rng)
    common = palette[:n_common]
    unique = palette[n_common] if len(palette) > n_common else 8
    g = full_grid(h, w, 0)
    ur, uc = _pick_unique_position(pos, h, w, rng)
    cells = [(r, c) for r in range(h) for c in range(w) if (r, c) != (ur, uc)]
    rng.shuffle(cells)
    idx = 0
    for color in common:
        cnt = rng.randint(c_min, c_max)
        placed = 0
        while placed < cnt and idx < len(cells):
            r, c = cells[idx]; idx += 1
            if g[r][c] == 0:
                g[r][c] = color
                placed += 1
        if placed < max(2, c_min):
            raise ValueError("could not place enough common-color cells")
    g[ur][uc] = unique
    return g


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    if len(pool) < n:
        for c in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            if c not in pool:
                pool.append(c)
            if len(pool) >= n:
                break
    return pool[:n]


def _pick_unique_position(pos, h, w, rng):
    if pos == "center":
        return h // 2, w // 2
    if pos == "near_edge":
        side = rng.choice(["top", "bottom", "left", "right"])
        if side == "top":
            return 1, rng.randint(1, w - 2)
        if side == "bottom":
            return h - 2, rng.randint(1, w - 2)
        if side == "left":
            return rng.randint(1, h - 2), 1
        return rng.randint(1, h - 2), w - 2
    if pos == "diagonal":
        i = rng.randint(1, min(h, w) - 2)
        return i, i
    if pos == "corner_adj":
        return rng.choice([(1, 1), (1, w - 2), (h - 2, 1),
                           (h - 2, w - 2)])
    return rng.randint(1, h - 2), rng.randint(1, w - 2)


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "no_unique":
        # All colors have >=2 cells
        common = rng.sample([3, 4, 5, 6, 7], 3)
        for color in common:
            for _ in range(3):
                r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                if g[r][c] == 0:
                    g[r][c] = color
        return g
    if name == "multiple_unique":
        # 2 colors each with count 1
        for color, (r, c) in zip([4, 8], [(2, 2), (h - 3, w - 3)]):
            g[r][c] = color
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 3
        g[h // 2][w // 2] = 8
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    from collections import Counter
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    counts = Counter(v for row in grid for v in row if v != 0)
    uniques = [c for c, n in counts.items() if n == 1]
    if len(uniques) != 1:
        errors.append("expected exactly one color with count 1")
    for c, n in counts.items():
        if c not in uniques and n < 2:
            errors.append("non-unique color has fewer than two cells")
    if uniques:
        locs = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == uniques[0]]
        if len(locs) == 1:
            r, c = locs[0]
            if r in (0, h - 1) or c in (0, w - 1):
                errors.append("unique cell must be interior so the halo fits")
    return errors
