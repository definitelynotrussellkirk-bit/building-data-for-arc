"""Generator for arc_puzzle_bank_21_set17_s:S17_E3.

Rule: every non-zero cell grows a clipped 3x3 square; the union is
painted color 8 on a blank canvas (input colors are irrelevant).

Combinatorial axes: grid_h/w, seed_count, texture
(plain|edge_seeds|blob|eight_seed).
Degenerates: no_seeds (blank identity), full_grid (all 8, not identity).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "067f6e037e97"
VERSION = "3.3.0"
TASK_ID = "067f6e037e97"
SUMMARY = (
    "Every non-zero cell grows a 3x3 Chebyshev neighborhood, clipped "
    "at the borders; the output is the UNION of all neighborhoods "
    "painted UNIFORMLY in color 8 on a blank canvas — seed colors are "
    "irrelevant and do NOT survive. (Old doc claimed each seed grows "
    "in its own color with overlap tie-breaks: fiction. Seeds were "
    "also always colors 4/5/6 and always isolated cells.)"
)

# Rivals: 'stamps keep seed colors' refuted by every demo (all 8).
# 'seeds must be special colors' refuted by random palettes incl. 8.
# 'one stamp per object' refuted by blob boards where each CELL of a
# 2-3 cell blob grows (union is bigger than one 3x3). 'stamps fit'
# refuted by edge seeds whose squares clip. 3 demos.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "output is the union of clipped 3x3 squares around every non-zero INPUT cell, all color 8",
    ">=1 seed on every main-path board",
]

DEGENERATE_TEXTURES = ("no_seeds", "full_grid")
HELPFUL_TEXTURES = ("plain", "edge_seeds", "blob", "eight_seed")

AXES = {
    "grid_h":     {"type": "int", "default": "rng 6..11", "valid": "5..14"},
    "grid_w":     {"type": "int", "default": "rng 6..11", "valid": "5..14"},
    "seed_count": {"type": "int", "default": "rng 1..5", "valid": "1..6"},
    "texture":    {"type": "str", "default": "rng helpful",
                   "valid": "plain|edge_seeds|blob|eight_seed|no_seeds|full_grid",
                   "doc": "edge_seeds: seeds on borders/corners (clipped "
                          "squares); blob: a 2-3 cell component (every cell "
                          "grows); eight_seed: a seed already colored 8."},
}


def _draw_axis_int(ctx, label, default_lo, default_hi, valid_lo, valid_hi):
    """Honor the full advertised range for explicit overrides.

    Default lessons keep their narrower pedagogical bands; an explicit axis
    override is validated against the declared AXES range instead of the
    current difficulty band.
    """
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")

    texture_options = (
        "plain", "edge_seeds", "blob", "eight_seed", "no_seeds", "full_grid"
    )
    if overrides.get("texture") is not None:
        texture = ctx.draw_choice("texture", texture_options)
    else:
        # Every three consecutive default examples contain a connected blob,
        # so the lesson necessarily distinguishes "grow every cell" from
        # "stamp once per connected object".
        schedule = ("blob", "plain", "edge_seeds", "blob", "eight_seed", "plain")
        texture = ctx.draw_choice("texture", (schedule[sample_index % len(schedule)],))

    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)

    if difficulty == "easy":
        h_band, w_band, n_band = (6, 7), (6, 7), (1, 3)
    elif difficulty == "hard":
        h_band, w_band, n_band = (9, 11), (9, 11), (3, 5)
    else:
        h_band, w_band, n_band = (6, 11), (6, 11), (1, 5)

    h = _draw_axis_int(ctx, "grid_h", *h_band, 5, 14)
    w = _draw_axis_int(ctx, "grid_w", *w_band, 5, 14)
    # Default blob lessons need at least two adjacent cells, while an explicit
    # seed_count override remains exact across the full advertised 1..6 range.
    n_lo = max(2, n_band[0]) if texture == "blob" else n_band[0]
    n = _draw_axis_int(ctx, "seed_count", n_lo, n_band[1], 1, 6)
    g = full_grid(h, w, 0)

    palette = [1, 2, 3, 4, 5, 6, 7, 9]
    if texture == "eight_seed":
        palette = [8] + palette  # input color is irrelevant to the rule

    if texture == "edge_seeds":
        border = ([(0, c) for c in range(w)] + [(h - 1, c) for c in range(w)] +
                  [(r, 0) for r in range(h)] + [(r, w - 1) for r in range(h)])
        spots = rng.sample(sorted(set(border)), min(n, len(set(border))))
    elif texture == "blob":
        # One same-colour connected 2-3 cell blob plus optional scattered
        # cells.  Explicit seed_count=1 is still exact and yields the lawful
        # one-cell boundary case; default blob lessons draw at least two cells.
        target_count = n
        br = rng.randint(1, h - 2)
        bc = rng.randint(1, w - 3)
        blob = [(br, bc)]
        if target_count >= 2:
            blob.append((br, bc + 1))
        if target_count >= 3 and rng.random() < 0.5:
            blob.append((br + 1, bc))
        all_cells = [(r, c) for r in range(h) for c in range(w)
                     if (r, c) not in blob]
        spots = blob + rng.sample(all_cells, target_count - len(blob))
    else:
        cells = [(r, c) for r in range(h) for c in range(w)]
        spots = rng.sample(cells, n)

    blob_size = len(blob) if texture == "blob" else 0
    for i, (r, c) in enumerate(spots):
        if texture == "blob" and i < blob_size:
            g[r][c] = palette[0]
        else:
            g[r][c] = palette[i % len(palette)] if i or texture != "eight_seed" \
                else 8
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=1 non-zero cell (rule needs seeds; blank input = blank output)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    seeds = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not seeds:
        return ["no seed cells found (blank input = blank output, not interesting)"]
    return []


def _draw_from_degenerate(name, ctx):
    """no_seeds — blank: blank output (identity). full_grid — every
    cell non-zero: the union covers the whole grid, output all 8
    (NOT identity: colors are replaced). rng-varied."""
    rng = ctx.draw_rng("degenerate_layout")
    h = _draw_axis_int(ctx, "grid_h", 6, 9, 5, 14)
    w = _draw_axis_int(ctx, "grid_w", 6, 9, 5, 14)
    if name == "no_seeds":
        return full_grid(h, w, 0)
    return full_grid(h, w, rng.choice((1, 2, 3, 4, 5, 6, 7, 9)))
