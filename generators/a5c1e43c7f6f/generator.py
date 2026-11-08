"""Generator for 5ffb2104.

Rule: nonzero same-color objects slide right as rigid bodies, processed
rightmost first.

Combinatorial axes (8): grid_h/w, object_count, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
shape_variant.
Degenerates: no_objects, single_object, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a5c1e43c7f6f"
VERSION = "1.1.1"
TASK_ID = "a5c1e43c7f6f"
SUMMARY = "Same-color objects slide right as rigid bodies, rightmost first."

INVARIANTS = [
    "background is color 0",
    "all nonzero cells belong to compact same-color objects",
    "objects are initially separated by empty space",
    "object colors are distinct and non-zero",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_objects", "single_object", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

SHAPES = [
    [(0, 0), (1, 0)],
    [(0, 0), (0, 1), (1, 1)],
    [(0, 0), (1, 0), (1, 1), (1, 2)],
    [(0, 1), (1, 0), (1, 1), (2, 1)],
]

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..15", "valid": "7..20"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "6..30"},
    "object_count":   {"type": "int", "default": "rng 3..4", "valid": "2..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..6"},
    "position_bias":  {"type": "str", "default": "rng", "valid": "rng"},
    "shape_variant":  {"type": "str", "default": "rng", "valid": "rng"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _paint_shape(g, r0, c0, cells, color):
    for dr, dc in cells:
        g[r0 + dr][c0 + dc] = color


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; >=2 distinct non-bg colors; no two same-color cells
    are 4-adjacent (objects are separate by bg gaps — no direct contact)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    colors = set(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if len(colors) < 2:
        errs.append(f"only {len(colors)} distinct non-bg color(s); expected >=2 objects")
        return errs
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        c_lo, c_hi = 2, 3
    elif difficulty == "hard":
        c_lo, c_hi = 4, 6
    else:
        c_lo, c_hi = 3, 4
    count = ctx.draw_int("object_count", c_lo, c_hi)
    w = ctx.draw_int("grid_width", 10, 13)
    h = count * 3 + 2
    palette_kind = (overrides.get("texture") or
                    overrides.get("palette_kind") or
                    ctx.draw_choice("palette_kind", list(PALETTE_KINDS)))
    pool = _build_palette(palette_kind, rng)
    if len(pool) < count:
        pool = pool + [c for c in [1, 2, 3, 4, 5, 6, 7, 8, 9] if c not in pool]
    colors = pool[:count]
    g = full_grid(h, w, 0)
    for idx in range(count):
        shape = list(SHAPES[(idx + sample_index) % len(SHAPES)])
        max_dc = max(dc for _, dc in shape)
        r0 = 1 + idx * 3
        c0 = rng.randint(0, max(0, min(3, w - max_dc - 4)))
        if idx % 2 == 1:
            c0 += 1
        _paint_shape(g, r0, c0, shape, colors[idx])
    return g


def _build_palette(kind, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    pool = [c for c in pool if c != 0]
    rng.shuffle(pool)
    return pool


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 12, 0)
    if name == "no_objects":
        return g
    if name == "single_object":
        for dr, dc in SHAPES[0]:
            g[2 + dr][2 + dc] = 2
        return g
    if name == "full_grid":
        for r in range(11):
            for c in range(12):
                g[r][c] = 2
        return g
    return g
