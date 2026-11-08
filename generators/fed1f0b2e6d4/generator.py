"""Generator for 4b:m26 — crop and vstack by area.

Rule: sort blobs by area, vstack their bbox crops.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: tied_sizes, single_blob, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "fed1f0b2e6d4"
VERSION = "3.0.0"  # variable blob count (2-6), wider size range, auto-sized canvas
TASK_ID = "fed1f0b2e6d4"
SUMMARY = (
    "0-bg grid with 2-6 BLOBS, each a random 4-connected "
    "shape in a DISTINCT COLOR from {1..9} and a STRICTLY "
    "DISTINCT SIZE (so the area-sort is unambiguous). "
    "Blobs are placed at NON-TOUCHING positions (1-cell "
    "orthogonal gap). Rule (CROP EACH BLOB TO ITS BBOX, "
    "VSTACK SORTED BY AREA, ASCENDING): find all "
    "4-CONNECTED non-0 COMPONENTS (color-blind "
    "connectivity). Compute each component's BBOX CROP and "
    "AREA (cell count). SORT crops by area ascending, "
    "tiebreaking by bbox top-row then left-col. VERTICALLY "
    "STACK the bbox crops top-to-bottom in that order, "
    "left-aligned, with a 1-row gap between them; width = "
    "max crop width (0-padded). Net: blobs are gathered "
    "into a vertical gallery sorted small-to-large."
)

INVARIANTS = [
    "background is 0",
    "2-6 distinct-color blobs with strictly distinct sizes",
    "blobs don't 4-touch (1-cell orthogonal gap between all blobs)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_sizes", "single_blob", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "auto-sized to fit blobs", "valid": "7..30"},
    "grid_w":         {"type": "int", "default": "auto-sized to fit blobs", "valid": "8..30"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "2-3 easy / 3-5 med / 4-6 hard", "valid": "2..6"},
    "blob_size":      {"type": "int", "default": "2..6 easy / 2..9 med / 2..12 hard (distinct)",
                       "valid": "2..12"},
    "palette_size":   {"type": "int", "default": "= n_blobs", "valid": "2..9"},
    "position_bias":  {"type": "str", "default": "non_touching",
                       "valid": "non_touching"},
    "n_distinct_colors": {"type": "int", "default": "= n_blobs", "valid": "2..9"},
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
        n_blobs = ctx.draw_int("n_blobs", 2, 3)
        size_pool = range(2, 7)
        base_h, base_w = 8, 9
    elif difficulty == "hard":
        n_blobs = ctx.draw_int("n_blobs", 4, 6)
        size_pool = range(2, 13)
        base_h, base_w = 12, 14
    else:
        n_blobs = ctx.draw_int("n_blobs", 3, 5)
        size_pool = range(2, 10)
        base_h, base_w = 9, 12
    rng = ctx.draw_rng("layout")

    # The rule sorts ALL non-0 components by AREA and vstacks their crops, so it
    # handles ANY blob count — n_blobs was hardcoded at 3. Vary the count (more
    # rows in the gallery) and widen the size pool (taller/wider crops). Sizes stay
    # STRICTLY DISTINCT so the area-sort is unambiguous; colors distinct for clarity
    # (the rule's connectivity is color-blind, so the 1-cell gap is what keeps each
    # blob a separate component).
    n_blobs = min(n_blobs, len(size_pool), 9)
    sizes = rng.sample(list(size_pool), n_blobs)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_blobs)

    # Auto-floor the canvas so all blobs + isolation gaps fit comfortably while
    # keeping drawn dimensions varied (≈5× the raw cell budget as an area floor).
    total_cells = sum(sizes)
    need_side = int((total_cells * 5) ** 0.5) + 1
    h = min(30, max(ctx.draw_int("grid_h", base_h, base_h + 5), need_side))
    w = min(30, max(ctx.draw_int("grid_w", base_w, base_w + 5), need_side))

    g = full_grid(h, w, 0)
    used: set[tuple[int, int]] = set()
    for size, color in zip(sizes, palette):
        cells = grow_blob(rng, h, w, used, size, max_attempts=120)
        if cells is None: continue
        for r, c in cells: g[r][c] = color
        used |= cells
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "tied_sizes":
        # blobs with equal sizes → sort key tie, vstack order ambiguous
        for r, c in [(1, 1), (1, 2)]: g[r][c] = 3
        for r, c in [(4, 5), (4, 6)]: g[r][c] = 5
        for r, c in [(7, 1), (7, 2), (8, 1)]: g[r][c] = 7
        return g
    if name == "single_blob":
        # one blob → stacking trivial
        for r, c in [(3, 3), (3, 4), (4, 3)]: g[r][c] = 6
        return g
    if name == "no_blobs":
        # empty grid → nothing to stack
        return g
    return g
