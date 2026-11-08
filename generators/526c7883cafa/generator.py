"""Generator for arc_puzzle_bank_21_set19_bundle:medium_p02 — bbox-fill every object.

Rule: for each connected non-zero object, fill its bbox with that
object's color. Output replaces every blob by its solid bbox.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_rectangular, single_blob, bboxes_overlap.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "526c7883cafa"
VERSION = "2.0.1"
TASK_ID = "526c7883cafa"
SUMMARY = (
    "0-bg grid (h~8-11, w~10-13) with 2-4 ISOLATED 4-conn "
    "BLOBS (3-5 cells each) in distinct colors, with "
    "NON-RECTANGULAR shapes (so bbox-fill is non-trivial) "
    "and non-overlapping bboxes. Rule: extract every "
    "4-conn non-bg blob. For each blob, find its "
    "BOUNDING BOX. FILL every cell in that bbox with the "
    "blob's color (solid rectangle fill). Net: each blob "
    "expands from its sparse shape to a SOLID FILLED "
    "RECTANGLE matching its bbox dimensions."
)

INVARIANTS = [
    "background is 0",
    "every blob has a non-rectangular shape (so bbox-fill differs from input)",
    "blobs (and their bboxes) don't overlap",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_rectangular", "single_blob", "bboxes_overlap")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "position_bias":  {"type": "str", "default": "bbox_isolated",
                       "valid": "bbox_isolated"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; at least one non-bg component; grid is rectangular."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    non_bg = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not non_bg:
        errors.append("no non-background cells found")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 12, 13)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 10, 13)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    used: set[tuple[int, int]] = set()
    n = rng.randint(2, 4)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    for color in palette:
        for _ in range(40):
            cells = grow_blob(rng, h, w, used, rng.randint(3, 5), max_attempts=20)
            if cells is None:
                continue
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            bb_h = max(rs) - min(rs) + 1
            bb_w = max(cs) - min(cs) + 1
            if bb_h * bb_w == len(cells):
                continue
            bbox_cells = {(r, c) for r in range(min(rs), max(rs) + 1) for c in range(min(cs), max(cs) + 1)}
            if bbox_cells & used:
                continue
            for r, c in cells:
                g[r][c] = color
            used |= bbox_cells
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "all_rectangular":
        # all blobs already solid rectangles → bbox-fill = input, rule is identity
        for r in range(2, 5):
            for c in range(2, 5):
                g[r][c] = 4
        for r in range(6, 8):
            for c in range(7, 10):
                g[r][c] = 6
        return g
    if name == "single_blob":
        # one blob → no comparison among objects, rule still works trivially
        for r, c in [(3, 3), (3, 4), (4, 3), (5, 4), (6, 4)]:
            g[r][c] = 5
        return g
    if name == "bboxes_overlap":
        # blobs whose bboxes overlap → bbox-fill paints over each other, ambiguous result
        for r, c in [(2, 2), (2, 3), (3, 4)]:
            g[r][c] = 4
        for r, c in [(3, 5), (4, 4), (5, 3)]:
            g[r][c] = 6
        return g
    return g
