"""Generator for arc_additional_puzzles_21_set15_bundle:E100 — Fill 0-cell with same-color diagonal neighbors.

Rule: 0-cell with both diagonal neighbors of same color → fill with
that color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_patterns,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_patterns, mismatched_diagonals, center_already_filled.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "eee9d87e516a"
VERSION = "2.0.0"  # add lone-cell + cross-ambiguous negatives (exercise the no-fill branches); non-square
TASK_ID = "eee9d87e516a"
SUMMARY = (
    "0-bg grid with several POSITIVE diagonal pairs (2 same-color cells at "
    "opposite corners of a 3x3, center 0 -> rule fills the center with that "
    "color), plus NEGATIVES: LONE cells (no diagonal partner -> no fill) and "
    "CROSS-ambiguous centers (TL/BR one color, TR/BL another -> two hits -> no "
    "fill). Rule: a 0-cell is filled iff EXACTLY ONE diagonal pair matches. "
    "Pattern counts, colors, positions and grid shape vary."
)

INVARIANTS = [
    "background is 0",
    "positive: 2 same-color cells at diagonal corners of a 3x3 with 0 center",
    "lone-cell negatives (no diagonal partner) and cross negatives (two differing "
    "diagonal pairs) exercise the no-fill branches",
    "patterns are separated so each fills independently",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_patterns", "mismatched_diagonals", "center_already_filled")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_patterns":     {"type": "int", "default": "rng 2..4 positives", "valid": "1..6"},
    "n_neg":          {"type": "int", "default": "rng 1..3 (lone/cross)", "valid": "0..5"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "spaced_diagonal_pairs",
                       "valid": "spaced_diagonal_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..3", "valid": "1..8"},
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
        h = ctx.draw_int("grid_h", 6, 8); w = ctx.draw_int("grid_w", 8, 10)
        n_pos = ctx.draw_int("n_patterns", 2, 3); n_neg = ctx.draw_int("n_neg", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 13); w = ctx.draw_int("grid_w", 11, 14)
        n_pos = ctx.draw_int("n_patterns", 3, 5); n_neg = ctx.draw_int("n_neg", 2, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 10); w = ctx.draw_int("grid_w", 9, 12)
        n_pos = ctx.draw_int("n_patterns", 2, 4); n_neg = ctx.draw_int("n_neg", 1, 3)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    placed = []
    palette = [2, 3, 4, 5, 6, 7, 8, 9]

    def free(r, c):
        return all(abs(r - pr) > 2 or abs(c - pc) > 2 for pr, pc in placed)

    # positives: one matching diagonal pair -> fills the center
    done = 0
    for _ in range(120):
        if done >= n_pos:
            break
        r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
        if free(r, c):
            color = rng.choice(palette)
            d = rng.choice([(-1, -1, 1, 1), (-1, 1, 1, -1)])
            g[r + d[0]][c + d[1]] = color
            g[r + d[2]][c + d[3]] = color
            placed.append((r, c)); done += 1

    # negatives: lone cell (no partner) or cross (two differing diagonal pairs)
    done = 0
    for _ in range(120):
        if done >= n_neg:
            break
        r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
        if not free(r, c):
            continue
        if rng.random() < 0.5:
            g[r][c] = rng.choice(palette)                 # lone cell -> no fill
        else:
            a, b = rng.sample(palette, 2)                 # cross: differing pairs -> no fill
            g[r - 1][c - 1] = a; g[r + 1][c + 1] = a
            g[r - 1][c + 1] = b; g[r + 1][c - 1] = b
        placed.append((r, c)); done += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 10
    g = full_grid(h, w, 0)
    if name == "no_patterns":
        # blank → no diagonal pairs to bridge
        return g
    if name == "mismatched_diagonals":
        # diagonal cells exist but in different colors → "same color" precondition fails
        g[1][1] = 4; g[3][3] = 6
        g[3][6] = 7; g[5][8] = 8
        return g
    if name == "center_already_filled":
        # the cell to fill is already non-bg → rule has no 0-cell to act on
        g[1][1] = 4; g[2][2] = 9; g[3][3] = 4
        g[3][6] = 6; g[4][7] = 9; g[5][8] = 6
        return g
    return g
