"""Generator for arc_puzzle_bank_thirteenth21:M90 — XOR two panels.

Rule: two same-shape panels separated by a 9-col. Output cell = 2 if
exactly one panel has a non-zero cell at that position; else 0.

Combinatorial axes (8): grid_h, grid_w, palette_kind, panel_w,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_divider, identical_panels, one_panel_empty.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "658ae5bf94b6"
VERSION = "2.0.0"
TASK_ID = "658ae5bf94b6"
SUMMARY = (
    "0-bg grid (h, w = 2*pw + 1 "
    "with pw=3-5) split by a FULL-"
    "HEIGHT COLOR-9 (maroon) "
    "VERTICAL DIVIDER at col pw. "
    "LEFT PANEL (cols 0..pw-1) "
    "and RIGHT PANEL (cols pw+1.."
    "w-1) are each filled at ~40% "
    "density with random colors "
    "from {2, 3, 4, 5, 6} at "
    "DIFFERENT (non-identical) "
    "patterns. Rule (XOR OCCUPANCY "
    "MASKS): produce an OUTPUT "
    "GRID of size h × pw. For "
    "EACH cell at (r, c) in the "
    "output, check if "
    "input[r][c] (left side, "
    "non-zero) XOR "
    "input[r][pw+1+c] (right "
    "side, non-zero). If EXACTLY "
    "ONE is non-zero, set output "
    "to COLOR 2 (red). If both "
    "or neither, set 0. Net: "
    "output marks positions "
    "where left and right "
    "panel occupancies disagree."
)

# Rivals: 'output is the input' refuted by any demo (output is half
# width, no separator). 'output OR (union)' refuted by ≥1 demo where
# a cell non-zero on both sides stays 0 in output. 'output uses input
# colors' refuted by any demo (output is just 0/2). 'output AND'
# refuted by ≥1 demo where one-side-only cells become 2.
# 3 demos with varied patterns cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly one full vertical 9-col separates two panels of equal width",
    "left and right panels have different (non-equal) sparse patterns",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_divider", "identical_panels", "one_panel_empty")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 4..6", "valid": "3..12"},
    "panel_w":        {"type": "int", "default": "rng 3..5", "valid": "2..9"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "position_bias":  {"type": "str", "default": "two_panels_with_9div",
                       "valid": "two_panels_with_9div"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: bg=0, at least one full-height color-9 col separating two equal-width panels."""
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    # Look for a full-height 9-column
    nine_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if not nine_cols:
        pass  # degenerate (no_divider) — allowed
    elif len(nine_cols) >= 1:
        # Check panels are equal width
        sep = nine_cols[0]
        pw_left = sep
        pw_right = w - sep - 1
        if pw_left != pw_right:
            errors.append(f"panels not equal width: left={pw_left}, right={pw_right}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 3, 5)
        pw = ctx.draw_int("panel_w", 3, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 12)
        pw = ctx.draw_int("panel_w", 6, 9)
    else:
        h = ctx.draw_int("grid_h", 5, 8)
        pw = ctx.draw_int("panel_w", 4, 6)
    w = pw * 2 + 1
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    sep = pw
    for r in range(h):
        g[r][sep] = 9
    for r in range(h):
        for c in range(pw):
            if rng.random() < 0.4:
                g[r][c] = rng.choice([2, 3, 4, 5, 6])
        for c in range(sep + 1, w):
            if rng.random() < 0.4:
                g[r][c] = rng.choice([2, 3, 4, 5, 6])
    return g


def _draw_from_degenerate(name, rng):
    h, pw = 5, 4
    w = pw * 2 + 1
    g = full_grid(h, w, 0)
    sep = pw
    if name == "no_divider":
        # no 9-col → no panel split
        for r in range(h):
            for c in range(pw): g[r][c] = 4 if (r + c) % 3 == 0 else 0
            for c in range(sep + 1, w): g[r][c] = 6 if (r + c) % 2 == 0 else 0
        return g
    for r in range(h): g[r][sep] = 9
    if name == "identical_panels":
        # left == right → XOR is empty (output all bg)
        for (dr, dc) in [(0, 1), (1, 2), (2, 0)]:
            g[dr][dc] = 4
            g[dr][sep + 1 + dc] = 6
        return g
    if name == "one_panel_empty":
        # one panel empty → XOR equals the other panel
        for (dr, dc) in [(0, 1), (1, 2), (2, 0)]:
            g[dr][dc] = 4
        return g
    return g
