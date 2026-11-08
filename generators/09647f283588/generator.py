"""Generator for arc_puzzle_bank_fourteenth21:E93.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_frames,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_frames, frame_at_edge, overlapping_frames.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "09647f283588"
VERSION = "2.0.2"  # fix frame_at_edge degenerate: corners now share one color so the window actually completes (matched docstring)
TASK_ID = "09647f283588"

SUMMARY = (
    "3x3 windows with 4 same-color corners, an EMPTY center, and an "
    "uncontaminated border complete into rings. partial_border frames "
    "(edge cells pre-filled in the frame color) still complete; "
    "center_filled / contaminated / three_corners near-misses stay. "
    "(Was: perfect 4-corner frames only - guards never contested.)"
)

# Rivals: 'complete any 4 corners' refuted by center_filled and
# contaminated windows staying. '3 corners suffice' refuted by
# three_corners. 'edges must be empty' refuted by partial_border
# completing. 3 demos incl. >=1 near-miss.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "each active 3x3 window has four same-color corners",
    "3x3 center is zero",
    "active 3x3 windows are separated",
]

DEGENERATE_TEXTURES = ("no_frames", "frame_at_edge", "overlapping_frames")
HELPFUL_TEXTURES = ("plain", "partial_border", "center_filled",
                    "contaminated", "three_corners")
_EDGES = [(0, 1), (1, 0), (1, 2), (2, 1)]
_CORNERS = [(0, 0), (0, 2), (2, 0), (2, 2)]

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "5..16"},
    "n_frames":       {"type": "int", "default": "rng 1..3", "valid": "1..6"},
    "texture":        {"type": "str", "default": "rng helpful",
                       "valid": "plain|partial_border|center_filled|"
                                "contaminated|three_corners|no_frames|"
                                "frame_at_edge|overlapping_frames",
                       "doc": "partial_border: pre-filled same-color edge "
                              "cells (still completes); center_filled / "
                              "contaminated / three_corners: near-misses."},
}


def _free(g, r0, c0):
    h, w = len(g), len(g[0])
    for r in range(max(0, r0 - 1), min(h, r0 + 4)):
        for c in range(max(0, c0 - 1), min(w, c0 + 4)):
            if g[r][c] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "partial_border", "center_filled",
                        "contaminated", "three_corners"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 8, 8)
        target = ctx.draw_int("n_frames", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        target = ctx.draw_int("n_frames", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 8, 10)
        target = ctx.draw_int("n_frames", 2, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    placed = 0
    for _ in range(300):
        if placed >= target:
            break
        r0 = rng.randint(0, h - 3)
        c0 = rng.randint(0, w - 3)
        if not _free(g, r0, c0):
            continue
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        for r, c in _CORNERS:
            g[r0 + r][c0 + c] = color
        if texture == "partial_border" and placed == 0:
            # same-color edge cells pre-filled: the frame still completes
            for r, c in rng.sample(_EDGES, rng.randint(1, 2)):
                g[r0 + r][c0 + c] = color
        placed += 1
    if texture in ("center_filled", "contaminated", "three_corners"):
        for _try in range(120):
            r0 = rng.randint(0, h - 3)
            c0 = rng.randint(0, w - 3)
            if not _free(g, r0, c0):
                continue
            color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
            other = rng.choice([v for v in range(1, 10) if v != color])
            corners = list(_CORNERS)
            if texture == "three_corners":
                corners.remove(rng.choice(corners))
            for r, c in corners:
                g[r0 + r][c0 + c] = color
            if texture == "center_filled":
                g[r0 + 1][c0 + 1] = other
            elif texture == "contaminated":
                er, ec = rng.choice(_EDGES)
                g[r0 + er][c0 + ec] = other
            break
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=1 active 3x3 window: four same-color corners with 0 center."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    found = False
    for r0 in range(h - 2):
        for c0 in range(w - 2):
            corners = [grid[r0 + r][c0 + c] for r, c in _CORNERS]
            center = grid[r0 + 1][c0 + 1]
            if corners[0] != 0 and len(set(corners)) == 1 and center == 0:
                found = True
                break
        if found:
            break
    if not found:
        return ["no active 3x3 window found (4 same-color corners, 0 center)"]
    return []


def _draw_from_degenerate(name, ctx):
    """no_frames — blank: identity. frame_at_edge — frame hugging the
    border completes fully (window stays in-bounds). overlapping_frames
    — two frames near each other: each window checks the INPUT, both
    verdicts independent. rng-varied."""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 8, 11)
    w = ctx.draw_int("grid_w", 9, 11)
    g = full_grid(h, w, 0)
    if name == "no_frames":
        # blank -> no corners to complete
        return g
    if name == "frame_at_edge":
        r0 = rng.choice([0, h - 3])
        c0 = rng.choice([0, w - 3])
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])  # SAME color so it completes
        for r, c in _CORNERS:
            g[r0 + r][c0 + c] = color
        return g
    if name == "overlapping_frames":
        ca, cb = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 2)
        r0 = rng.randint(1, h - 4)
        for r, c in _CORNERS:
            g[r0 + r][1 + c] = ca
        for r, c in _CORNERS:
            g[r0 + r][3 + c] = cb  # shares the middle column band
        return g
    return g
