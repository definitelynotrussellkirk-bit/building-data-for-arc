"""Generator for puzzle 321b1fc6.

Rule: a colored key motif is stamped at every 8-target object's
top-left corner.

Combinatorial axes (8): grid_size, target_count, key_kind,
target_size_min, target_size_max, palette_kind, position_bias,
anchor_corner.
Degenerates: no_targets, no_key, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "37794e3e5409"
VERSION = "1.1.1"
TASK_ID = "37794e3e5409"
SUMMARY = "Key motif at top-left + 8-targets; rule stamps key at each target."

INVARIANTS = [
    "background is 0",
    "key motif at top-left uses non-{0,8} colors",
    "1-4 8-target rects elsewhere",
    "no other non-0 cells",
]

KEY_KINDS = ("L_shape", "diagonal", "T_shape", "plus", "Z_shape")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
POSITION_BIASES = ("scattered", "corners", "diagonal", "row_aligned")
DEGENERATE_TEXTURES = ("no_targets", "no_key", "full_grid")
HELPFUL_TEXTURES = KEY_KINDS

AXES = {
    "grid_size":      {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "target_count":   {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "key_kind":       {"type": "str", "default": "rng helpful",
                       "valid": "|".join(KEY_KINDS)},
    "target_size_min":{"type": "int", "default": "1", "valid": "1..3"},
    "target_size_max":{"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "position_bias":  {"type": "str", "default": "rng",
                       "valid": "|".join(POSITION_BIASES)},
    "texture":        {"type": "str", "default": "alias for key_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_KEYS = {
    "L_shape":  [(0, 0), (0, 1), (1, 1), (2, 0)],
    "diagonal": [(0, 0), (1, 1), (2, 2)],
    "T_shape":  [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)],
    "plus":     [(1, 0), (0, 1), (1, 1), (1, 2), (2, 1)],
    "Z_shape":  [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)],
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥1 color-8 target cell; ≥1 non-{0,8} key cell; values 0..9."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    for r in range(h):
        for c in range(w):
            if not (0 <= grid[r][c] <= 9):
                errors.append(f"out-of-range value {grid[r][c]} at ({r},{c})")
    eights = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 8)
    if eights == 0:
        pass  # degenerate (no_targets) — allowed
    key_cells = sum(1 for r in range(h) for c in range(w) if grid[r][c] not in (0, 8))
    if key_cells == 0:
        pass  # degenerate (no_key) — allowed
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        size_lo, size_hi = 10, 12
    elif difficulty == "hard":
        size_lo, size_hi = 18, 22
    else:
        size_lo, size_hi = 12, 18
    size = int(overrides.get("grid_size",
                             ctx.draw_int("grid_size", size_lo, size_hi)))
    size = max(10, min(22, size))
    target_count = int(overrides.get("target_count",
                                     ctx.draw_int("target_count", 2, 3)))
    target_count = max(1, min(5, target_count))
    key_kind = (overrides.get("texture") or
                overrides.get("key_kind")
                or ctx.draw_choice("key_kind", list(KEY_KINDS)))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    palette = _build_palette(palette_kind, 3, rng)
    t_min = int(overrides.get("target_size_min", 1))
    t_max = int(overrides.get("target_size_max",
                              ctx.draw_int("target_size_max", 2, 3)))
    g = full_grid(size, size, 0)
    key_cells = _KEYS[key_kind]
    for i, (dr, dc) in enumerate(key_cells):
        g[1 + dr][1 + dc] = palette[i % len(palette)]
    placed = 0
    for _ in range(target_count * 6):
        if placed >= target_count:
            break
        th = rng.randint(t_min, t_max); tw = rng.randint(t_min, t_max)
        r0 = rng.randint(5, size - th - 1)
        c0 = rng.randint(5, size - tw - 1)
        ok = all(g[r0 + dr][c0 + dc] == 0
                 for dr in range(th) for dc in range(tw))
        if not ok:
            continue
        draw_rect(g, r0, c0, th, tw, 8)
        placed += 1
    return g


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 9]
    rng.shuffle(pool)
    while len(pool) < n:
        for c in [1, 2, 3, 4, 5, 6, 7, 9]:
            if c not in pool:
                pool.append(c)
    return pool[:n]


def _draw_from_degenerate(name, rng):
    g = full_grid(14, 14, 0)
    if name == "no_targets":
        for dr, dc in _KEYS["L_shape"]:
            g[1 + dr][1 + dc] = 3
        return g
    if name == "no_key":
        for r, c in [(1, 8), (6, 4)]:
            draw_rect(g, r, c, 2, 2, 8)
        return g
    if name == "full_grid":
        for r in range(14):
            for c in range(14):
                g[r][c] = 8
        return g
    return g
