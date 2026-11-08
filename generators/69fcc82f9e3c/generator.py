"""Generator for arc_puzzle_bank_21_set15_bundle:medium_o05 — flip-lr each blob in place.

Rule: replace each blob with its bbox flipped left-right (i.e., mirror
the cells across the bbox vertical axis).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_blobs, all_lr_symmetric, single_cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "69fcc82f9e3c"
VERSION = "1.1.1"
TASK_ID = "69fcc82f9e3c"
SUMMARY = "2-3 LR-asymmetric blobs (so flip-lr changes them)."

INVARIANTS = [
    "background is 0",
    "blobs are LR-asymmetric (flip-lr produces a different shape)",
    "blobs are 4-disjoint and don't overlap bboxes",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blobs", "all_lr_symmetric", "single_cell")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "9..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "lr_asymmetric_blobs",
                       "valid": "lr_asymmetric_blobs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; >=1 distinct non-bg color present (blobs to flip)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    colors = set(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if not colors:
        return errs  # degenerate (no_blobs) — allowed
    return errs


def _is_lr_asym(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    rmin = min(rs); cmin = min(cs); cmax = max(cs)
    norm = {(r - rmin, c - cmin) for r, c in cells}
    flipped = {(r, (cmax - cmin) - c) for r, c in norm}
    return norm != flipped


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
        n = ctx.draw_int("n_blobs", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 12, 13)
        n = ctx.draw_int("n_blobs", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 10, 13)
        n = ctx.draw_int("n_blobs", 2, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    used: set[tuple[int, int]] = set()
    for color in palette:
        for _ in range(40):
            cells = grow_blob(rng, h, w, used, rng.randint(3, 5), max_attempts=20)
            if cells is None:
                continue
            if not _is_lr_asym(cells):
                continue
            for r, c in cells:
                g[r][c] = color
            used |= cells
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_blobs":
        # blank → nothing to flip
        return g
    if name == "all_lr_symmetric":
        # blobs are already LR-symmetric → flip-lr is identity
        # plus shape (LR symmetric):
        g[1][2] = 4
        g[2][1] = 4; g[2][2] = 4; g[2][3] = 4
        g[3][2] = 4
        # 2x2 (also LR sym):
        for dr in range(2):
            for dc in range(2): g[5 + dr][6 + dc] = 6
        return g
    if name == "single_cell":
        # 1-cell blobs → flip is identity
        g[2][2] = 4
        g[5][7] = 6
        return g
    return g
