"""Generator for arc_puzzle_bank_21_set21_bundle:hard_p04 — adjacency matrix via dilation overlap.

Rule: connected components sorted top-left. Output N×N: diagonal = component
color, off-diagonal = 8 if their dilated (1-cell halo) cells overlap, else 0.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_components,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_components, all_isolated, all_overlap.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7781a5e94155"
VERSION = "3.0.1"  # POISON+distinct=2: docstring/gen built 'dilation overlap' with a 1-cell GAP between components, but the real rule marks CARDINAL TOUCHING (diag=5, touch=7). With a gap nothing ever touched -> output always the identity matrix (distinct=2). Rewrite: a connected distinct-colored polyomino so cells are separate objects that cardinally touch -> output = the polyomino's n x n adjacency matrix; vary n 3..8.
TASK_ID = "7781a5e94155"

SUMMARY = (
    "0-bg grid with N single-cell objects (each a DISTINCT non-zero color) arranged "
    "as a connected polyomino, so cardinally-adjacent cells are separate objects that "
    "TOUCH. Rule: sort the N objects by (col, row); output the N x N matrix with 5 on "
    "the diagonal, 7 where two objects cardinally touch, else 0 (the polyomino's "
    "adjacency graph). N (3-8) and the polyomino shape vary."
)

INVARIANTS = [
    "background is 0",
    "N single-cell objects in distinct colors form one connected (cardinal) polyomino",
    "cardinally-adjacent cells carry distinct colors so each stays a separate object",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_components", "all_isolated", "all_overlap")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 12..14", "valid": "10..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_components":   {"type": "int", "default": "rng 3..4", "valid": "3..8"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "position_bias":  {"type": "str", "default": "mixed_near_far",
                       "valid": "mixed_near_far"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: N distinct non-zero colors each appearing exactly once (single-cell polyomino objects)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    from collections import Counter
    counts = Counter(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if len(counts) < 3:
        errs.append(f"only {len(counts)} distinct non-zero color(s); expected ≥3 for a polyomino")
    non_singletons = [c for c, cnt in counts.items() if cnt != 1]
    if non_singletons:
        errs.append(f"colors {non_singletons} appear more than once; each should be a single cell")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        n = ctx.draw_int("n_components", 3, 5)
    elif difficulty == "hard":
        n = ctx.draw_int("n_components", 6, 8)
    else:
        n = ctx.draw_int("n_components", 4, 8)
    rng = ctx.draw_rng("layout")
    # connected polyomino of n cells; each cell a distinct color -> n separate
    # single-cell objects that cardinally touch along polyomino edges
    poly = _rand_poly(rng, n)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    ph = max(r for r, _ in poly) + 1
    pw = max(c for _, c in poly) + 1
    h = ph + rng.randint(2, 5)
    w = pw + rng.randint(2, 6)
    g = full_grid(h, w, 0)
    off_r = rng.randint(0, h - ph); off_c = rng.randint(0, w - pw)
    for i, (r, c) in enumerate(poly):
        g[off_r + r][off_c + c] = colors[i]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 13
    g = full_grid(h, w, 0)
    if name == "no_components":
        # Empty grid — output matrix is 0x0.
        return g
    if name == "all_isolated":
        # All components far apart — adjacency matrix is identity (diagonal only).
        g[1][1] = 4
        g[1][6] = 5
        g[6][1] = 6
        g[6][9] = 7
        return g
    if name == "all_overlap":
        # All components adjacent — adjacency matrix is fully off-diagonal 8.
        g[2][2] = 4
        g[2][4] = 5
        g[2][6] = 6
        g[4][2] = 7
        return g
    return g
