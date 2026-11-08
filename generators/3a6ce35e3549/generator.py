"""Generator for puzzle 3de23699.

Rule: minority color is "dot" (4 corners of a rect). Majority is "big"
shape inside. Output: shape recolored big→dot, cropped to rect interior.

Combinatorial axes (8): grid_h/w, rect_h, rect_w, blob_density,
palette_kind, position_bias, anchor_corner, asymmetry_force.
Degenerates: no_blob, no_dots, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.palette import random_palette

GENERATOR_ID = "3a6ce35e3549"
VERSION = "2.0.1"
TASK_ID = "3a6ce35e3549"
SUMMARY = (
    "0-bg grid (h, w ~10-16) with: (a) FOUR DOTS at the "
    "corners of an axis-aligned rect (rh × rw, "
    "rh, rw ~5-8) in a MINORITY color; (b) a BLOB of "
    "5+ cells strictly INSIDE the rect in a MAJORITY "
    "color. Two distinct non-bg colors total. Rule: "
    "identify the 4 corner-dot cells (minority color = "
    "dot color). Find the rectangle they define. "
    "Crop the rect's INTERIOR (strictly inside the 4 "
    "corner positions). Recolor the blob from majority "
    "(big) color to MINORITY (dot) color. Output: the "
    "cropped interior with the recolored blob."
)

INVARIANTS = [
    "background is 0",
    "exactly 2 distinct non-zero colors",
    "minority color: 4 cells at axis-aligned rect corners",
    "majority color: >=5 cells strictly inside the rect",
]

POSITION_BIASES = ("scattered", "centered", "corner", "spread")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_blob", "no_dots", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..16", "valid": "8..20"},
    "grid_w":         {"type": "int", "default": "rng 10..16", "valid": "8..20"},
    "rect_h":         {"type": "int", "default": "rng 5..8", "valid": "4..10"},
    "rect_w":         {"type": "int", "default": "rng 5..8", "valid": "4..10"},
    "blob_density":   {"type": "float", "default": "rng 0.4..0.7",
                       "valid": "0.2..1"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly 2 distinct nonzero colors (4 corner dots + blob); values 0..9."""
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
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if not colors:
        pass  # degenerate (no_blob/no_dots) — allowed
    elif len(colors) != 2:
        errors.append(f"expected exactly 2 nonzero colors (dots+blob), found {len(colors)}: {sorted(colors)}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 8, 11
    elif difficulty == "hard":
        h_lo, h_hi = 16, 20
    else:
        h_lo, h_hi = 10, 16
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    rh = int(overrides.get("rect_h",
                           ctx.draw_int("rect_h", 5, min(8, h - 1))))
    rw = int(overrides.get("rect_w",
                           ctx.draw_int("rect_w", 5, min(8, w - 1))))
    rh = max(4, min(h - 1, rh))
    rw = max(4, min(w - 1, rw))
    blob_d = float(overrides.get("blob_density",
                                 ctx.draw_rng("blob_density")
                                 .uniform(0.4, 0.7)))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias",
                               list(POSITION_BIASES)))
    palette = _build_palette(palette_kind, 2, rng)
    big, dot = palette
    g = full_grid(h, w, 0)
    r0, c0 = _pick_position(bias, h, w, rh, rw, rng)
    g[r0][c0] = dot
    g[r0][c0 + rw - 1] = dot
    g[r0 + rh - 1][c0] = dot
    g[r0 + rh - 1][c0 + rw - 1] = dot
    cells_pool = [(r, c) for r in range(r0 + 1, r0 + rh - 1)
                  for c in range(c0 + 1, c0 + rw - 1)]
    n_big = max(5, int(len(cells_pool) * blob_d))
    n_big = min(n_big, len(cells_pool))
    chosen = rng.sample(cells_pool, n_big)
    for r, c in chosen:
        g[r][c] = big
    return g


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        return random_palette(rng, n)
    rng.shuffle(pool)
    return pool[:n]


def _pick_position(bias, h, w, rh, rw, rng):
    if bias == "centered":
        return max(0, (h - rh) // 2), max(0, (w - rw) // 2)
    if bias == "corner":
        return rng.choice([(0, 0), (0, w - rw),
                           (h - rh, 0), (h - rh, w - rw)])
    if bias == "spread":
        return rng.randint(0, h - rh), rng.randint(0, w - rw)
    return rng.randint(0, h - rh), rng.randint(0, w - rw)


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "no_blob":
        # 4 dots at rect corners but no blob → rule has nothing to crop
        g[1][1] = 3
        g[1][6] = 3
        g[5][1] = 3
        g[5][6] = 3
        return g
    if name == "no_dots":
        # Blob without rect corners → rule can't find rect
        for r in range(2, 5):
            for c in range(3, 7):
                if rng.random() < 0.6:
                    g[r][c] = 5
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 5
        return g
    return g
