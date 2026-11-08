"""Generator for arc_puzzle_bank_21_set17_bundle:easy_p03.

Rule: four equal diagonal neighbors around a zero center fill that center.

Combinatorial axes (8): grid_h, grid_w, palette_kind, motif_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs, partial_diagonals, mismatched_diagonals.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "04400a6b6096"
VERSION = "1.2.1"
TASK_ID = "04400a6b6096"
SUMMARY = (
    "Separated X-corner motifs (4 equal diagonal corners around an "
    "empty center, which the rule fills) plus optional near-miss "
    "motifs the rule must skip: 3-corner Xs, mismatched-color Xs, and "
    "Xs whose center is already occupied."
)

# Rivals: 'fill any cell with diagonal neighbors' refuted by 3-corner
# near-misses that stay empty. 'colors may differ' refuted by
# mismatched Xs. 'overwrite the center' refuted by filled-center Xs.
# 3 demos incl. >=1 near-miss motif.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    ">=1 complete X motif (four same-color diagonals, empty center)",
    "near-miss motifs (when present) stay unchanged",
    "3x3 neighborhoods are separated",
]

NEAR_MISSES = ("partial", "mismatched", "filled_center")
DEGENERATE_TEXTURES = ("no_motifs",)
HELPFUL_TEXTURES = ("plain",) + NEAR_MISSES

AXES = {
    "grid_h":      {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":      {"type": "int", "default": "rng 7..11", "valid": "5..14"},
    "motif_count": {"type": "int", "default": "rng 2..4", "valid": "1..6",
                    "doc": "Complete X motifs (centers filled by the rule)."},
    "texture":     {"type": "str", "default": "rng helpful",
                    "valid": "plain|partial|mismatched|filled_center|no_motifs",
                    "doc": "Adds one near-miss motif of the named kind."},
}


def _block(r, c):
    return {(rr, cc) for rr in range(r - 1, r + 2) for cc in range(c - 1, c + 2)}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "partial", "mismatched", "filled_center"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        motif_count = ctx.draw_int("motif_count", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 11)
        motif_count = ctx.draw_int("motif_count", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 11)
        motif_count = ctx.draw_int("motif_count", 2, 4)
    colors = ctx.draw_distinct_colors("colors", n=motif_count, exclude={0})
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    occupied = set()
    for color in colors:
        for _ in range(300):
            r = rng.randint(1, h - 2)
            c = rng.randint(1, w - 2)
            block = _block(r, c)
            if block & occupied:
                continue
            for rr, cc in [(r - 1, c - 1), (r - 1, c + 1), (r + 1, c - 1), (r + 1, c + 1)]:
                g[rr][cc] = color
            occupied |= block
            break

    if texture in NEAR_MISSES:
        # one motif the rule must NOT fill
        nm_color = ctx.draw_color("near_miss_color", exclude={0})
        for _ in range(300):
            r = rng.randint(1, h - 2)
            c = rng.randint(1, w - 2)
            block = _block(r, c)
            if block & occupied:
                continue
            corners = [(r - 1, c - 1), (r - 1, c + 1), (r + 1, c - 1), (r + 1, c + 1)]
            if texture == "partial":
                drop = rng.randrange(4)
                for i, (rr, cc) in enumerate(corners):
                    if i != drop:
                        g[rr][cc] = nm_color
            elif texture == "mismatched":
                other = next(v for v in range(1, 10) if v != nm_color)
                for i, (rr, cc) in enumerate(corners):
                    g[rr][cc] = nm_color if i % 2 == 0 else other
            else:  # filled_center: complete X but the center is occupied
                for rr, cc in corners:
                    g[rr][cc] = nm_color
                g[r][c] = next(v for v in range(1, 10) if v != nm_color)
            occupied |= block
            break
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """bg=0; >=1 complete X motif: four same-color diagonal corners around
    an empty (0) center cell."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    found = False
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] != 0:
                continue
            corners = [grid[r - 1][c - 1], grid[r - 1][c + 1],
                       grid[r + 1][c - 1], grid[r + 1][c + 1]]
            if corners[0] != 0 and len(set(corners)) == 1:
                found = True
                break
        if found:
            break
    if not found:
        errors.append("no complete X motif found (4 same-color diagonals around empty center)")
    return errors


def _draw_from_degenerate(name, ctx):
    """no_motifs — blank grid: identity output. rng-varied dims.
    (partial/mismatched were PROMOTED to helpful near-miss textures.)"""
    h = ctx.draw_int("grid_h", 7, 10)
    w = ctx.draw_int("grid_w", 7, 11)
    return full_grid(h, w, 0)
