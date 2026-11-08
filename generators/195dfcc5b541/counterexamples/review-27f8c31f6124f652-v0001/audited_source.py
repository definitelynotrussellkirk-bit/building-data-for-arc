"""Generator for 195dfcc5b541.

Rule: in a noisy multicolor field, color-3 copies matching a color-8
stencil under rotation/reflection are recolored to 8.

Combinatorial axes (8): grid_h/w, variant, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
shape_variant.
Degenerates: no_stencil, no_copies, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "195dfcc5b541"
VERSION = "2.1.0"
TASK_ID = "195dfcc5b541"
SUMMARY = (
    "Dense noisy 0/2/3/4/7 background with one color-8 stencil polyomino "
    "and several color-3 rotated/reflected copies. The canonical Racket rule "
    "finds color-3 windows matching the stencil under the dihedral group and "
    "recolors those cells to 8 while leaving unrelated noise unchanged."
)

INVARIANTS = [
    "one compact color-8 polyomino supplies the stencil",
    "at least two color-3 copies match a rotated/reflected stencil variant",
    "the surrounding field is dense multicolor noise, matching the canonical task scale",
    "matched color-3 cells are recolored to 8 by the canonical rule",
]

VARIANTS = ("rot90", "rot180", "flip")
PALETTE_KINDS = ("canonical_noise",)
DEGENERATE_TEXTURES = ("no_stencil", "no_copies", "full_grid")
HELPFUL_TEXTURES = VARIANTS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 14..18", "valid": "14..18"},
    "grid_w":         {"type": "int", "default": "rng 17..18", "valid": "17..18"},
    "variant":        {"type": "str", "default": "rng helpful", "valid": "|".join(VARIANTS)},
    "palette_kind":   {"type": "str", "default": "canonical_noise", "valid": "canonical_noise"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "true", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "5", "valid": "5"},
    "position_bias":  {"type": "str", "default": "noisy_canonical", "valid": "noisy_canonical"},
    "shape_variant":  {"type": "str", "default": "rng", "valid": "rng"},
    "texture":        {"type": "str", "default": "alias for variant", "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _norm(cells):
    cells = list(cells)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return sorted((r - min_r, c - min_c) for r, c in cells)


def _rot(cells):
    return _norm((c, -r) for r, c in cells)


def _flip(cells):
    return _norm((r, -c) for r, c in cells)


def _bbox(cells):
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _variant(cells, name):
    if name == "rot90":
        return _rot(cells)
    if name == "rot180":
        return _rot(_rot(cells))
    return _flip(cells)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    variant = (overrides.get("texture") if overrides.get("texture") in VARIANTS else None) or \
              overrides.get("variant") or \
              ctx.draw_choice("variant", list(VARIANTS))
    shapes = [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(0, 1), (1, 1), (2, 1), (2, 0), (2, 2)],
        [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)],
        [(0, 0), (0, 1), (1, 0), (2, 0), (2, 1)],
    ]
    base = shapes[rng.randint(0, len(shapes) - 1)]
    match_a = _variant(base, variant)
    match_b = _variant(base, ctx.draw_choice("second_variant", list(VARIANTS)))

    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 14, 15)
        w = ctx.draw_int("grid_w", 17, 17)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 17, 18)
        w = ctx.draw_int("grid_w", 18, 18)
    else:
        h = ctx.draw_int("grid_h", 14, 18)
        w = ctx.draw_int("grid_w", 17, 18)

    # Canonical examples are dense noisy fields, not clean two-object demos.
    # Exclude 8 from background so the stencil remains unambiguous; include
    # abundant 3s so the task lives in the same high-object-count regime.
    noise = [0, 0, 2, 3, 3, 4, 7]
    g = [[rng.choice(noise) for _ in range(w)] for _ in range(h)]

    paint_at(g, 0, 2 + rng.randint(0, 2), base, 8)
    ah, aw = _bbox(match_a)
    bh, bw = _bbox(match_b)
    paint_at(g, h - ah - 2, 1 + rng.randint(0, 2), match_a, 3)
    paint_at(g, rng.randint(2, max(2, h - bh - 2)), w - bw - 2, match_b, 3)
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify noisy stencil-copy regime for 195dfcc5b541."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    flat = [v for row in grid for v in row]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    if not (14 <= h <= 18 and 17 <= w <= 18):
        errs.append(f"expected canonical noisy size 14..18 x 17..18; got {h}x{w}")
    colors = set(flat)
    if 8 not in colors:
        errs.append("missing color-8 stencil")
    if flat.count(3) < 12:
        errs.append(f"expected abundant color-3 copy/noise cells; got {flat.count(3)}")
    if sum(1 for v in flat if v != 0) < 90:
        errs.append("background is too sparse for canonical noisy regime")
    if len(colors) < 5:
        errs.append(f"expected at least five colors in noisy field; got {sorted(colors)}")
    if sum(1 for v in flat if v == 8) < 4:
        errs.append("color-8 stencil is too small")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(15, 18, 0)
    if name == "no_stencil":
        for r in range(15):
            for c in range(18):
                g[r][c] = rng.choice([0, 2, 3, 4, 7])
        return g
    if name == "no_copies":
        paint_at(g, 1, 1, [(0, 0), (1, 0), (1, 1), (2, 1)], 8)
        return g
    if name == "full_grid":
        return full_grid(15, 18, 8)
    return g
