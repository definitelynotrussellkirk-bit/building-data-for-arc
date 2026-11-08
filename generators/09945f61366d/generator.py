"""Generator for arc_puzzle_bank_twentysecond21:E154 — plus per cell.

Rule: output rebuilds on a BLANK grid; every non-zero input cell
paints a plus (itself + 4 cardinal neighbors, in-bounds clipped) in
its color, in row-major scan order — on overlap the LATER plus
overwrites the earlier one, including the earlier marker's center.

Combinatorial axes: grid_h/w, n_cells, texture
(plain|edge|overlap|dense|same_color).
Degenerates: no_cells (blank in, blank out).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "09945f61366d"
VERSION = "2.0.1"
TASK_ID = "09945f61366d"
SUMMARY = (
    "Scattered markers each stamp a plus in their color. edge boards "
    "put markers on borders/corners (arms clip); overlap boards put "
    "two markers 1-2 apart so the scan-order LATER plus overwrites "
    "the earlier one (even its center); same_color repeats a color; "
    "dense packs 5-9 markers. (Was: always-interior markers separated "
    "by >=4 - clipping and overlap never fired on the main path, and "
    "the overlap degenerate mislabeled last-wins as 'ambiguous'.)"
)

# Rivals: 'markers keep their cell, arms only added' refuted by
# overlap boards where an earlier CENTER is repainted by a later
# plus. 'pluses always complete' refuted by edge boards. 'colors are
# distinct' refuted by same_color. 3-4 demos incl. >=1 overlap or
# edge board.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0; markers are single non-zero cells",
    "overlap boards: >=2 markers within Manhattan distance 2",
    "edge boards: >=1 marker on the border (arm clips off-grid)",
]

DEGENERATE_TEXTURES = ("no_cells",)
HELPFUL_TEXTURES = ("plain", "edge", "overlap", "dense", "same_color")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 5..12", "valid": "4..16"},
    "grid_w":  {"type": "int", "default": "rng 5..12", "valid": "4..16"},
    "n_cells": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|edge|overlap|dense|same_color|no_cells",
                "doc": "overlap: markers 1-2 apart, the row-major LATER "
                       "plus overwrites the earlier (center included); "
                       "edge: border markers with clipped arms."},
}

_COLORS = (1, 2, 3, 4, 5, 6, 7, 8, 9)


def _mirror(g):
    h, w = len(g), len(g[0])
    out = [[0] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            v = g[r][c]
            if v == 0:
                continue
            for dr, dc in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w:
                    out[rr][cc] = v
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain", "edge",
                                              "overlap", "dense",
                                              "same_color"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 5, 7)
        n = ctx.draw_int("n_cells", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 9, 12)
        n = ctx.draw_int("n_cells", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 5, 12)
        w = ctx.draw_int("grid_w", 5, 12)
        n = ctx.draw_int("n_cells", 2, 4)
    rng = ctx.draw_rng("layout")
    if texture == "dense":
        n = rng.randint(5, 9)
    g = full_grid(h, w, 0)
    placed = []

    if texture == "same_color":
        color = rng.choice(_COLORS)
        colors = [color] * n
    else:
        colors = [rng.choice(_COLORS) for _ in range(n)]
        if n >= 2 and len(set(colors)) == 1:
            colors[-1] = rng.choice([v for v in _COLORS
                                     if v != colors[0]])

    if texture == "overlap":
        # a deliberate close pair first: 1-2 apart, distinct colors
        ca, cb = rng.sample(_COLORS, 2)
        for _t in range(150):
            r = rng.randint(1, h - 2)
            c = rng.randint(1, w - 2)
            dr, dc = rng.choice([(0, 1), (1, 0), (1, 1), (0, 2), (2, 0),
                                 (1, -1)])
            r2, c2 = r + dr, c + dc
            if 0 <= r2 < h and 0 <= c2 < w:
                g[r][c] = ca
                g[r2][c2] = cb
                placed += [(r, c), (r2, c2)]
                break
        colors = colors[2:]
    elif texture == "edge":
        # >=1 marker on the border (corner-biased)
        edge_spots = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1),
                      (0, rng.randint(1, w - 2)),
                      (h - 1, rng.randint(1, w - 2)),
                      (rng.randint(1, h - 2), 0),
                      (rng.randint(1, h - 2), w - 1)]
        r, c = rng.choice(edge_spots)
        g[r][c] = colors[0]
        placed.append((r, c))
        colors = colors[1:]

    min_gap = 1 if texture == "dense" else 3
    for color in colors:
        for _t in range(150):
            r = rng.randint(0, h - 1)
            c = rng.randint(0, w - 1)
            if g[r][c] != 0:
                continue
            if any(abs(r - pr) + abs(c - pc) < min_gap
                   for pr, pc in placed):
                continue
            g[r][c] = color
            placed.append((r, c))
            break
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=1 non-zero marker cell in the grid."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    nz = sum(1 for row in grid for v in row if v != 0)
    if nz == 0:
        return ["no non-zero cell — blank input, blank output (degenerate)"]
    return []


def _draw_from_degenerate(name, ctx):
    """no_cells — blank grid: the rebuilt output is also blank
    (identity). rng-varied dims."""
    h = ctx.draw_int("grid_h", 5, 10)
    w = ctx.draw_int("grid_w", 5, 10)
    return full_grid(h, w, 0)
