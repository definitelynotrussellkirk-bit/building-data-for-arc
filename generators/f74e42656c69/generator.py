"""Generator for arc_puzzle_bank_21_set7_s:S7_E7.

Rule: count disconnected color-1 components → 1xN bar of 1s.

Combinatorial axes (8): grid_h, grid_w, palette_kind, component_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_components, single_blob, components_touching.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "f74e42656c69"
VERSION = "2.0.0"  # wider component-count range (was 2-6 -> out_shapes 5) + varied multi-cell blobs + bigger grids
TASK_ID = "f74e42656c69"
SUMMARY = (
    "0-bg grid (size varies) holding N isolated color-1 components (count "
    "varies widely, ~2-15). Each component is a singleton OR a small varied "
    "blob (any shape counts as ONE component); components are spaced so each "
    "is a distinct 4-connected piece. Rule: count the color-1 components and "
    "emit a single row of that many 1s. Net: output width = component count. "
    "(Was: 2-6 isolated singletons -> only 5 distinct output widths.)"
)

INVARIANTS = [
    "background is 0; only color 1 is used (matches canonical)",
    "components are isolated (1-cell gap) so each is a distinct 4-connected piece",
    "output is a single row whose width equals the component count",
    "component count varies widely so output widths are diverse",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_components", "single_blob", "components_touching")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "6-9 easy / 9-14 med / 13-20 hard", "valid": "4..22"},
    "grid_w":         {"type": "int", "default": "7-10 easy / 10-15 med / 14-22 hard", "valid": "5..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "component_count": {"type": "int", "default": "2-4 easy / 3-8 med / 6-15 hard", "valid": "1..16"},
    "blob_size":      {"type": "int", "default": "1-5 cells per component", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "isolated", "valid": "isolated"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        hr, wr, cr = (6, 9), (7, 10), (2, 4)
    elif difficulty == "hard":
        hr, wr, cr = (13, 20), (14, 22), (6, 15)
    else:
        hr, wr, cr = (9, 14), (10, 15), (3, 8)
    rng = ctx.draw_rng("layout")

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        used = set()
        target = rng.randint(*cr)
        placed = 0
        for _ in range(target * 5):
            if placed >= target:
                break
            blob = grow_blob(rng, h, w, used, rng.randint(1, 5), max_attempts=20)
            if blob is None:
                continue
            for r, c in blob:
                g[r][c] = 1
            used |= blob
            placed += 1
        if placed >= 1:
            return g

    # deterministic fallback: 3 singletons
    g = full_grid(6, 8, 0)
    for r, c in [(1, 1), (1, 5), (4, 3)]:
        g[r][c] = 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "no_components":
        # zero color-1 cells → output bar has length 0, ambiguous shape
        return g
    if name == "single_blob":
        # one large connected blob → count is 1, no comparison signal across multiple objects
        for r, c in [(2, 3), (2, 4), (3, 3), (3, 4), (4, 3)]:
            g[r][c] = 1
        return g
    if name == "components_touching":
        # adjacent cells form one component, not two → counting under "isolated" invariant breaks
        for r, c in [(2, 2), (2, 3), (4, 5), (4, 6), (4, 7)]:
            g[r][c] = 1
        return g
    return g
