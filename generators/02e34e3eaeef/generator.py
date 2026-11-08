"""Generator for arc_puzzle_bank_fifteenth_21_bundle:easy_104_read_singleton_colors_left_to_right.

Rule: scatter unique singleton colors; output reads them by column
then row.

Combinatorial axes (8): grid_h, grid_w, palette_kind, markers,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: empty_grid, duplicate_colors, all_one_column.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "02e34e3eaeef"
VERSION = "2.1.1"
TASK_ID = "02e34e3eaeef"
SUMMARY = (
    "Scattered colored cells (sometimes a color repeats, sometimes a "
    "marker is a small 2-3 cell blob). Rule emits a 1xN row of the "
    "DISTINCT colors in column-major scan order — a repeated color is "
    "listed once, at its first (leftmost, then topmost) occurrence."
)

# Rivals: 'output is input' refuted (output is 1-row). 'sort by row
# first' refuted by col-order demos. 'sort by color value' refuted by
# positional ordering. 'every cell gets an entry' refuted by repeated
# colors collapsing to one entry. 'markers are always single cells'
# refuted by blob markers. 3 demos incl. >=1 repeat or blob board.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    ">=2 distinct colors present",
    "repeated_color boards: a color appears 2-3 times, listed ONCE at "
    "its first column-major occurrence",
    "output is one row of distinct colors in column-major order",
]

DEGENERATE_TEXTURES = ("duplicate_colors", "all_one_column")
HELPFUL_TEXTURES = ("plain", "repeated_color", "blob_markers")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 7..10 (easy 4..7, hard 10..14)",
                "valid": "3..14", "doc": "Grid height."},
    "grid_w":  {"type": "int", "default": "rng 10..13 (easy 7..10, hard 13..18)",
                "valid": "4..18", "doc": "Grid width."},
    "markers": {"type": "int", "default": "rng 4..7 (easy 2..4, hard 7..9)",
                "valid": "1..9", "doc": "Distinct colors placed."},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|repeated_color|blob_markers|"
                         "duplicate_colors|all_one_column",
                "doc": "Marker flavor or a degenerate name."},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "repeated_color", "blob_markers"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 4, 7)
        w = ctx.draw_int("grid_w", 7, 10)
        target = ctx.draw_int("markers", 2, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 13, 18)
        target = ctx.draw_int("markers", 7, 9)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 10, 13)
        target = ctx.draw_int("markers", 4, 7)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], k=target)
    positions = rng.sample([(r, c) for r in range(h) for c in range(w)], target)
    for color, (r, c) in zip(colors, positions):
        g[r][c] = color

    if texture == "repeated_color":
        # a color appears 2-3 times — the rule lists it ONCE at its
        # first column-major occurrence (dedup was never exercised)
        color = colors[rng.randrange(len(colors))]
        free = [(r, c) for r in range(h) for c in range(w) if g[r][c] == 0]
        for r, c in rng.sample(free, min(len(free), rng.randint(1, 2))):
            g[r][c] = color
    elif texture == "blob_markers":
        # 1-2 markers grow into 2-3 cell blobs — still one entry each
        grown = 0
        for color, (r, c) in zip(colors, positions):
            if grown >= 2:
                break
            for _ in range(8):
                dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] == 0:
                    g[nr][nc] = color
                    grown += 1
                    break
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """bg=0; >=2 distinct non-zero colors present."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    errors = []
    if len(colors) < 2:
        errors.append(f"expected >=2 distinct non-zero colors, found {len(colors)}: {sorted(colors)}")
    return errors


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied so each board differs.
    (empty_grid was dropped: the rule would emit (list '()) — not a
    valid grid.)

    duplicate_colors — heavy repeats: dedup hides most of the content.
    all_one_column   — column order degenerates to row order.
    """
    h = ctx.draw_int("grid_h", 6, 9)
    w = ctx.draw_int("grid_w", 8, 12)
    rng = ctx.draw_rng("degenerate_layout")
    g = full_grid(h, w, 0)
    if name == "duplicate_colors":
        colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 2)
        for _ in range(rng.randint(4, 6)):
            g[rng.randrange(h)][rng.randrange(w)] = rng.choice(colors)
        return g
    # all_one_column
    col = rng.randrange(w)
    rows = rng.sample(range(h), min(4, h))
    for r, v in zip(rows, rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], len(rows))):
        g[r][col] = v
    return g
