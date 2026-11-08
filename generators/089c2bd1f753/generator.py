"""Generator for arc_puzzle_bank_eighteenth_21_bundle:medium_120_select_object_by_corner_legend_and_crop.

Rule: cell (0,0) holds a marker color. Output is the bbox crop of
the object that shares that color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_marker (cell (0,0) is bg → rule's marker selector
returns nothing, no target chosen), no_match (marker present but no
object shares its color → rule's selector finds nothing), tied_match
(≥2 objects share marker color → "the object" is ambiguous, tie-break
decides which is cropped).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.palette import random_palette
from puzzle_generators.helpers.blobs import bbox_overlaps

GENERATOR_ID = "089c2bd1f753"
VERSION = "3.0.1"
TASK_ID = "089c2bd1f753"
SUMMARY = (
    "0-bg grid (h~9-12, w~10-14) with: (a) "
    "cell (0, 0) holding a MARKER COLOR from "
    "a 3-color palette (the TARGET INDICATOR); "
    "(b) EXACTLY ONE TARGET OBJECT of 3-5 "
    "cells in the SAME COLOR as the (0, 0) "
    "marker, placed at a random interior "
    "position; (c) 1-2 DISTRACTOR OBJECTS in "
    "OTHER non-target colors (2-3 cells each, "
    "non-overlapping). Objects don't touch "
    "each other or (0, 0). Rule: READ marker "
    "color at (0, 0). FIND the ONE OBJECT "
    "(connected component) elsewhere that "
    "SHARES that color. CROP to that object's "
    "BOUNDING BOX and RETURN the cropped "
    "subgrid (preserving its color and shape). "
    "Distractors and marker discarded. Net: "
    "marker selects target by color; output "
    "is bbox crop of matching object."
)

INVARIANTS = [
    "background is 0",
    "(0, 0) holds the target marker color",
    "exactly one object of the marker's color elsewhere with ≥3 cells",
    "1-2 distractor objects in other colors",
    "objects don't touch each other or (0, 0)",
]

DEGENERATE_TEXTURES = ("no_marker", "no_match", "tied_match")
HELPFUL_TEXTURES = ("plain",)

AXES = {
    "grid_h":      {"type": "int", "default": "rng 9..13", "valid": "8..16"},
    "grid_w":      {"type": "int", "default": "rng 10..15", "valid": "9..18"},
    "target_size": {"type": "int", "default": "rng 3..6", "valid": "2..7"},
    "texture":     {"type": "str", "default": "plain",
                    "valid": "plain|no_marker|no_match|tied_match",
                    "doc": "tied_match: two marker-colored objects, the "
                           "scan-order FIRST is cropped."},
}

def _grow(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc))
            seen.add((r + dr, c + dc))
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _place(g, rng, shape, color, placed):
    h, w = len(g), len(g[0])
    sh = max(c[0] for c in shape) + 1
    sw = max(c[1] for c in shape) + 1
    for _ in range(100):
        r0 = rng.randint(2, h - sh - 1)
        c0 = rng.randint(2, w - sw - 1)
        bb = (r0 - 1, c0 - 1, r0 + sh, c0 + sw)
        if any(bbox_overlaps(bb, p) for p in placed):
            continue
        paint_at(g, r0, c0, shape, color)
        placed.append((r0, c0, r0 + sh - 1, c0 + sw - 1))
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 11)
        tsz = ctx.draw_int("target_size", 3, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 12, 15)
        tsz = ctx.draw_int("target_size", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 10, 15)
        tsz = ctx.draw_int("target_size", 3, 6)
    rng = ctx.draw_rng("layout")

    for _attempt in range(40):
        g = full_grid(h, w, 0)
        palette = list(random_palette(rng, rng.randint(3, 4)))
        target = palette[0]
        g[0][0] = target
        placed: list[tuple[int, int, int, int]] = [(0, 0, 0, 0)]
        if not _place(g, rng, _grow(rng, tsz), target, placed):
            continue
        for color in palette[1:]:
            _place(g, rng, _grow(rng, rng.randint(2, 4)), color, placed)
        return g
    raise ValueError("could not realize legend-crop board")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """(0,0) non-zero (marker); >=1 other cell of marker color in body."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    marker = grid[0][0]
    if marker == 0:
        errors.append("(0,0) is background (no marker)")
        return errors
    body_match = any(grid[r][c] == marker for r in range(h) for c in range(w)
                     if not (r == 0 and c == 0))
    if not body_match:
        errors.append(f"no body cell matches marker color {marker}")
    return errors


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied so each board differs.

    no_marker  — (0,0) is bg: targets empty, output [[0]].
    no_match   — marker color absent from the body: output [[0]].
    tied_match — two objects share the marker color: the FIRST in
                 discovery (scan) order is cropped — deterministic.
    """
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 9, 12)
    w = ctx.draw_int("grid_w", 10, 13)
    g = full_grid(h, w, 0)
    placed: list[tuple[int, int, int, int]] = [(0, 0, 0, 0)]
    if name == "no_marker":
        for color in rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 2):
            _place(g, rng, _grow(rng, rng.randint(2, 4)), color, placed)
        return g
    palette = list(random_palette(rng, 3))
    g[0][0] = palette[0]
    if name == "no_match":
        for color in palette[1:]:
            _place(g, rng, _grow(rng, rng.randint(2, 4)), color, placed)
        return g
    # tied_match
    for _ in range(2):
        _place(g, rng, _grow(rng, rng.randint(3, 4)), palette[0], placed)
    return g
