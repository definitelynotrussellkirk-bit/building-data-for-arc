"""Generator for f8b3ba0a.

Rule: count colors. Sort desc. Output [3rd, 4th, 5th] most common as
3×1 column.

Combinatorial axes (8): grid_h/w, palette_size, count_distribution,
position_layout, palette_kind, anchor_corner, asymmetry_force,
spread_kind.
Degenerates: too_few_colors, equal_counts, all_one_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.place import random_free_cell

GENERATOR_ID = "427be9c8dedb"
VERSION = "2.1.0"  # distinct=90, out 3x1 intrinsic (rule outputs the 3rd/4th/5th most-common colors): palette was only 5-7 colors so ranks 3-5 had few candidates. Widened palette to 6-9 colors (pool auto-expanded to all 9 when needed) -> more mid-rank variety. out 3x1 is intrinsic to the rule.
TASK_ID = "427be9c8dedb"
SUMMARY = (
    "0-bg grid (h ∈ 11-16, w ∈ 8-14) with "
    "5-7 NON-ZERO COLORS at SCATTERED "
    "POSITIONS: palette drawn from one of "
    "{warm (3,4,6,9), cool (1,5,7,8), "
    "small (1..5), broad (1..9)}, expanded "
    "to ≥5 colors if needed. Counts drawn "
    "via _draw_counts using one of: "
    "default (random 22,12,6,4,2,2,2), "
    "wide_spread (30%, 15%, 7%, 4%, 2 "
    "cells), tight_spread (15% ± 5%), "
    "ascending (5%, 10%, 15%, ...). All "
    "5+ NON-ZERO COUNTS are STRICTLY "
    "DISTINCT (no ties); bg=0 has the "
    "largest count overall. Cells placed "
    "at random free positions via "
    "random_free_cell. Rule (COUNT EACH "
    "NON-ZERO COLOR'S CELL FREQUENCY, "
    "SORT DESCENDING, OUTPUT THE 3RD, "
    "4TH, 5TH MOST-COMMON COLORS AS A "
    "3×1 COLUMN GRID): COUNT cells of "
    "each non-zero color. SORT colors "
    "by count DESCENDING. SELECT the "
    "3RD, 4TH, 5TH entries (skipping "
    "the top-2). OUTPUT a 3-ROW × "
    "1-COLUMN grid: row 0 = 3rd "
    "most-common color, row 1 = 4th, "
    "row 2 = 5th. Net: a frequency-"
    "based selection extracts the "
    "mid-tier colors and emits them "
    "as a vertical color triple."
)

INVARIANTS = [
    ">=6 distinct colors total (incl. bg=0)",
    "5+ non-zero colors with STRICTLY distinct counts",
    "bg=0 has the largest count overall",
    "the 3rd, 4th, 5th distinct (by count) colors are unambiguous",
]

POSITION_LAYOUTS = ("scattered", "blob", "stripes", "checker")
COUNT_DISTRIBUTIONS = ("default", "wide_spread", "tight_spread", "ascending")
PALETTE_KINDS = ("warm", "cool", "broad", "small")
DEGENERATE_TEXTURES = ("too_few_colors", "equal_counts", "all_one_color")
HELPFUL_TEXTURES = POSITION_LAYOUTS

AXES = {
    "grid_h":             {"type": "int", "default": "rng 11..16", "valid": "9..20"},
    "grid_w":             {"type": "int", "default": "rng 8..14", "valid": "7..16"},
    "palette_size":       {"type": "int", "default": "rng 5..7", "valid": "5..9"},
    "count_distribution": {"type": "str", "default": "rng helpful",
                           "valid": "|".join(COUNT_DISTRIBUTIONS)},
    "position_layout":    {"type": "str", "default": "rng helpful",
                           "valid": "|".join(POSITION_LAYOUTS)},
    "palette_kind":       {"type": "str", "default": "rng helpful",
                           "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":      {"type": "bool", "default": "false",
                           "valid": "true|false"},
    "asymmetry_force":    {"type": "bool", "default": "false",
                           "valid": "true|false"},
    "texture":            {"type": "str", "default": "alias for position_layout",
                           "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 9, 12, 7, 10
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 15, 20, 13, 16
    else:
        h_lo, h_hi, w_lo, w_hi = 11, 16, 8, 14
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    if palette_kind == "warm":
        pool = [3, 4, 6, 9]
    elif palette_kind == "cool":
        pool = [1, 5, 7, 8]
    elif palette_kind == "small":
        pool = [1, 2, 3, 4, 5]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    # output = the 3rd/4th/5th most-common colors (a 3x1 column, intrinsically
    # 3x1). More colors -> more candidates for ranks 3-5 -> more distinct.
    n_palette = int(overrides.get("palette_size",
                                  ctx.draw_int("palette_size", 6, 9)))
    n_palette = max(5, n_palette)
    if len(pool) < n_palette:                     # widen pool to fit larger palettes
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]; rng.shuffle(pool)
    palette = pool[:n_palette]
    if len(palette) < 5:
        extras = [c for c in [1, 2, 3, 4, 5, 6, 7, 8, 9] if c not in palette]
        rng.shuffle(extras)
        palette += extras[:5 - len(palette)]
    palette = palette[:n_palette]
    dist = overrides.get("count_distribution",
                         ctx.draw_choice("count_distribution",
                                         list(COUNT_DISTRIBUTIONS)))
    counts = _draw_counts(dist, len(palette), h, w, rng)
    g = full_grid(h, w, 0)
    for color, count in zip(palette, counts):
        for _ in range(count):
            cell = random_free_cell(g, rng, max_tries=40)
            if cell is not None:
                g[cell[0]][cell[1]] = color
    return g


def _draw_counts(dist, n, h, w, rng):
    """Draw a strict foreground-count ladder.

    The Racket rule asks for the 3rd/4th/5th most-common colors, so the
    generator must not create ties at those ranks.  The original sampler also
    let foreground colors outrank the zero background on compact grids, which
    sent the rule down a different branch and caused parity crashes.  Keep
    every nonzero count distinct and keep background as the unique largest
    region.
    """
    n = max(5, min(9, n))
    total = h * w
    # A strict descending ladder with enough colors for ranks 3, 4, and 5.
    ladder = list(range(n, 0, -1))
    base_sum = sum(ladder)

    # We may raise every foreground count together, but leave enough cells for
    # background to remain strictly larger than the largest foreground count.
    boost_max = max(0, (total - base_sum - n - 1) // (n + 1))

    if dist == "wide_spread":
        boost = max(0, boost_max - 1)
        counts = [c + boost for c in ladder]
        counts[0] += min(boost_max, 4)
    elif dist == "tight_spread":
        boost = min(boost_max, max(1, total // 24))
        counts = [c + boost for c in ladder]
    elif dist == "ascending":
        boost = min(boost_max, max(1, total // 30))
        counts = [c + boost for c in ladder]
        # Still descending by count; the palette-order variation comes from
        # the shuffled color choice, not ambiguous equal-size blobs.
    else:
        boost = min(boost_max, rng.randint(0, max(0, min(4, boost_max))))
        counts = [c + boost for c in ladder]

    # Defensive repair for very small override grids.
    while sum(counts) >= total - counts[0]:
        counts[0] -= 1
        counts = sorted(counts, reverse=True)
    assert len(set(counts)) == len(counts)
    assert (total - sum(counts)) > counts[0]
    return counts[:n]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the count-rank task."""
    errors: list[str] = []
    if not grid or not grid[0]:
        return ["grid must be non-empty"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        errors.append("grid must be rectangular")
        return errors

    counts = {}
    for row in grid:
        for cell in row:
            counts[cell] = counts.get(cell, 0) + 1

    if 0 not in counts:
        errors.append("background color 0 must be present")
    if len(counts) < 6:
        errors.append("need background plus at least five foreground colors")
    fg = [(color, count) for color, count in counts.items() if color != 0]
    if len(fg) < 5:
        errors.append("need five nonzero colors so ranks 3/4/5 exist")
        return errors

    if 0 in counts:
        bg_count = counts[0]
        max_fg = max(count for _, count in fg)
        if bg_count <= max_fg:
            errors.append("background must be the unique most common color")

    fg_counts = [count for _, count in fg]
    if len(set(fg_counts)) != len(fg_counts):
        errors.append("foreground color counts must be strictly distinct")

    ranked = sorted(fg, key=lambda kv: (-kv[1], kv[0]))
    answer_colors = [color for color, _ in ranked[2:5]]
    if len(answer_colors) != 3 or len(set(answer_colors)) != 3:
        errors.append("3rd/4th/5th colors must be unambiguous")
    return errors


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "too_few_colors":
        # only 3 colors
        from puzzle_generators.helpers.place import random_free_cell as rfc
        for color, count in zip([1, 2, 3], [10, 6, 3]):
            for _ in range(count):
                cell = rfc(g, rng, max_tries=20)
                if cell:
                    g[cell[0]][cell[1]] = color
        return g
    if name == "equal_counts":
        from puzzle_generators.helpers.place import random_free_cell as rfc
        for color in [1, 2, 3, 4, 5]:
            for _ in range(5):
                cell = rfc(g, rng, max_tries=20)
                if cell:
                    g[cell[0]][cell[1]] = color
        return g
    if name == "all_one_color":
        for r in range(h):
            for c in range(w):
                if rng.random() < 0.4:
                    g[r][c] = 1
        return g
    return g
