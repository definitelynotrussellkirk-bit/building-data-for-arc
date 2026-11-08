"""Generator for arc_puzzle_bank_fourth21:M24 — slide every blob to top border.

Rule: each blob shifts vertically so its bbox top row = 0.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: blobs_already_at_top, single_blob, blobs_share_cols.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "0fce75f9162a"
VERSION = "1.2.1"  # +self_check
TASK_ID = "0fce75f9162a"
SUMMARY = (
    "0-bg grid with N (2-4) connected non-bg components ('blobs'), "
    "each in its own color, occupying disjoint column ranges so they "
    "can each slide up independently without collision. Rule: for "
    "each blob, compute its bbox top row r0. Shift the blob UP by r0 "
    "rows (so its new bbox top is at row 0), preserving columns and "
    "shape. Output is a fresh grid with all blobs slid to touch the "
    "top border."
)

# Rivals: 'output is input' refuted by demos where some blob's bbox
# top row > 0. 'slide all to bottom' refuted by demos showing blobs
# at row 0. 'slide single blob (the lowest)' refuted by demos with
# all blobs shifted up. 'slide horizontally to left' refuted by demos
# preserving column position. 'gravity-down' refuted by demos showing
# upward motion. 'all blobs collapse to single point' refuted by demos
# preserving shapes. 3 demos with blobs at varied starting depths
# pin the per-blob upward slide.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥2 connected non-bg components (rule's per-blob slide invisible with only 1 already at top)",
    "every blob's bbox top row ≥ 1 (so there's room to slide)",
    "blobs occupy DISJOINT column ranges (so shifted blobs don't overlap)",
    "each blob has a single distinct color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("blobs_already_at_top", "single_blob", "blobs_share_cols")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "below_top_row",
                       "valid": "below_top_row"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..9"},
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
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 8, 10)
        n = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 13, 16)
        n = ctx.draw_int("n_blobs", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 10, 13)
        n = ctx.draw_int("n_blobs", 2, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    used: set[tuple[int, int]] = set()
    for c in range(w):
        used.add((0, c))
    if n is None:
        n = rng.randint(2, 3)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    cols_used: list[range] = []
    for color in palette:
        for _ in range(40):
            cells = grow_blob(rng, h, w, used, rng.randint(2, 4), max_attempts=20)
            if cells is None:
                continue
            cs = [c for _, c in cells]
            cmin, cmax = min(cs), max(cs)
            if any(set(range(cmin, cmax + 1)) & set(cu) for cu in cols_used):
                continue
            for r, c in cells:
                g[r][c] = color
            used |= cells
            cols_used.append(range(cmin, cmax + 1))
            break
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=2 non-zero components; every non-zero cell is NOT in row 0 (so sliding is visible)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    from collections import Counter
    h, w = len(grid), len(grid[0])
    errors = []
    colors = Counter(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if len(colors) < 2:
        errors.append(f"need >=2 distinct blob colors, got {len(colors)}")
    all_at_top = all(grid[0][c] != 0 or True for c in range(w))
    # Check that every blob has its top row >= 1 (sliding room exists)
    for color in colors:
        top_row = min(r for r in range(h) for c in range(w) if grid[r][c] == color)
        if top_row == 0:
            errors.append(f"blob color {color} already at row 0 — slide is identity")
            break
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "blobs_already_at_top":
        # blobs already touch row 0 → sliding is identity, rule effect invisible
        for (r, c) in [(0, 1), (0, 2), (1, 1)]: g[r][c] = 4
        for (r, c) in [(0, 5), (1, 5), (1, 6)]: g[r][c] = 6
        return g
    if name == "single_blob":
        # one blob → sliding works but no comparison across blobs
        for (r, c) in [(4, 5), (4, 6), (5, 5), (5, 6)]: g[r][c] = 4
        return g
    if name == "blobs_share_cols":
        # two blobs share a column → sliding both to row 0 would collide; INVARIANT violated
        for (r, c) in [(2, 4), (2, 5), (3, 4)]: g[r][c] = 4
        for (r, c) in [(6, 4), (6, 5), (7, 5)]: g[r][c] = 6   # same col 4-5
        return g
    return g
