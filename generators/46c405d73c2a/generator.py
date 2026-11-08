"""Generator for arc_puzzle_bank_21_set17_s:S17_H7 — color-overlap matrix.

Rule: sort the distinct non-bg colors; grow each color's cells by a 3x3
neighborhood; output an N x N matrix (N = number of colors) where cell (r,c)
is 5 on the diagonal, 8 if colors r and c's grown regions overlap, else 0.

The old docstring ("3 single-cell markers ... task-specific output") was a
lie, and the generator pinned N=3 so the output was always a 3x3 matrix with
only ~8 possible values (distinct=6). Now the COLOR COUNT N varies (2..7), so
the matrix size varies AND many more overlap subsets appear; markers sit at
varied distances so some color-pairs overlap (8) and some don't (0).

Combinatorial axes: color count N, marker positions (-> overlap pattern),
grid size.
Degenerates: too_few_markers, duplicate_colors, adjacent_markers.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "46c405d73c2a"
VERSION = "3.0.1"  # distinct=6 + lie docstring: real rule outputs an N x N color-overlap matrix (N = #colors). Gen pinned N=3 -> 3x3 matrix, <=8 values. Now N varies 2..7 (matrix 2x2..7x7) and markers sit at varied distances so overlap subsets vary widely.
TASK_ID = "46c405d73c2a"
SUMMARY = (
    "0-bg grid with N SINGLE-CELL MARKERS in N DISTINCT non-zero colors "
    "(N varies 2..7) at distinct positions and VARIED pairwise distances. "
    "Rule: grow each color's cell(s) by a 3x3 neighborhood and output the "
    "N x N overlap matrix (diagonal 5; 8 if two colors' grown regions "
    "overlap, else 0). Marker spacing controls which pairs overlap."
)

INVARIANTS = [
    "background is 0",
    "N single-cell markers in N distinct non-zero colors at distinct positions",
    "marker pairs occur at varied distances (some overlap when grown, some not)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("too_few_markers", "duplicate_colors", "adjacent_markers")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_markers":      {"type": "int", "default": "rng 2..7", "valid": "2..7"},
    "palette_size":   {"type": "int", "default": "= n_markers", "valid": "2..7"},
    "position_bias":  {"type": "str", "default": "varied_distance", "valid": "varied_distance"},
    "n_distinct_colors": {"type": "int", "default": "= n_markers", "valid": "2..7"},
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
        n = ctx.draw_int("n_markers", 2, 3); h = ctx.draw_int("grid_h", 8, 10); w = ctx.draw_int("grid_w", 8, 10)
    elif difficulty == "hard":
        n = ctx.draw_int("n_markers", 5, 7); h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 11, 14)
    else:
        n = ctx.draw_int("n_markers", 3, 5); h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 9, 12)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    colors = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], n)
    placed = []
    for color in colors:
        for _t in range(120):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if g[r][c] != 0:
                continue
            # distinct cells only; allow VARIED distances (incl. close pairs that
            # overlap when grown) so the overlap matrix varies richly.
            if (r, c) in placed:
                continue
            g[r][c] = color
            placed.append((r, c))
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "too_few_markers":
        # only 1-2 markers → 3-marker assumption violated
        g[2][2] = 3
        g[6][7] = 5
        return g
    if name == "duplicate_colors":
        # two markers share a color → "distinct colors" assumption violated
        g[1][1] = 4
        g[4][6] = 4
        g[7][3] = 7
        return g
    if name == "adjacent_markers":
        # markers placed adjacent → distance-3 separation invariant violated
        g[3][3] = 3
        g[3][4] = 5
        g[4][3] = 7
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """bg=0; >=2 distinct non-0 colors; each color appears exactly once (single-cell marker)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    from collections import Counter
    counts = Counter(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if len(counts) < 2:
        errors.append(f"expected >=2 distinct marker colors, found {len(counts)}")
        return errors
    multi = [color for color, cnt in counts.items() if cnt > 1]
    if multi:
        errors.append(f"colors {multi} appear more than once; expected single-cell markers")
    return errors
