"""Generator for arc_puzzle_bank_twentythird21:H159.

Rule: row 0 has k=1-4 color-1 markers (rotation count). Body (rows 1+)
has one color-9 anchor + several non-{0,1,9} object cells. Rule
preserves row 0 + anchor, then for each object cell at offset (dr,dc)
relative to anchor, paints up to k rotations around the anchor.

Combinatorial axes (8): grid_h, grid_w, palette_kind, k_markers,
n_objects, palette_size, position_bias, n_distinct_colors, texture.
Degenerates: no_markers, no_anchor, no_objects.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b9d914a60205"
# 1.4.0: k=1 marker means the rule paints only the object's ORIGINAL position
# (rels[:1]) -> output == input (identity). Draw k>=2 so every default instance
# performs a real rotation, and guarantee >=1 object is actually placed. Adds
# self_check.
VERSION = "1.4.0"
TASK_ID = "b9d914a60205"

SUMMARY = "Row 0 holds k color-1 markers (rotation count, 1-4). Body has one maroon(9) anchor + non-{0,1,9} object cells. Rule rotates each object cell up to k times around the anchor."

# Rivals: 'rotate full grid' refuted by ≥1 demo with anchor off-center.
# 'rotate without k limit' refuted by ≥2 demos with k=1 (no rotation
# beyond identity). 'use marker color for rotation' refuted by any
# demo (object colors preserved). 'erase anchor in output' refuted
# by any demo (anchor visible in output).
# 4 demos with varied k + object layouts cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "row 0 has 1-4 color-1 marker cells",
    "body has exactly one color-9 anchor + ≥1 non-{0,1,9} object cell",
    "object cells' rotations land in-bounds within body",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_markers", "no_anchor", "no_objects")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "7..18"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "7..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "k_markers":      {"type": "int", "default": "rng 1..4", "valid": "1..4"},
    "n_objects":      {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "2..7"},
    "position_bias":  {"type": "str", "default": "row0_markers_body_anchor",
                       "valid": "row0_markers_body_anchor"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "2..7"},
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
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 8, 10)
        k = ctx.draw_int("k_markers", 2, 2)   # k>=2: k=1 rotates nothing (identity)
        n_objects = ctx.draw_int("n_objects", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 13, 18)
        k = ctx.draw_int("k_markers", 2, 4)
        n_objects = ctx.draw_int("n_objects", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 10, 13)
        k = ctx.draw_int("k_markers", 2, 3)
        n_objects = ctx.draw_int("n_objects", 2, 4)

    g = full_grid(h, w, 0)
    # Row 0: place k color-1 cells at random distinct positions.
    marker_positions = rng.sample(range(w), k)
    for c in marker_positions:
        g[0][c] = 1
    # Body (rows 1+): anchor in the middle-ish, with room for rotations.
    # Anchor relative to body: at body[ar][ac].
    # In absolute grid coords: g[1+ar][ac]
    ar = rng.randint(2, h - 3)  # absolute row
    ac = rng.randint(2, w - 3)
    g[ar][ac] = 9
    # Place object cells whose all k rotations around anchor land in body.
    # rotation k applied to (dr, dc) yields (dr, dc), (dc, -dr), (-dr, -dc), (-dc, dr).
    obj_colors = rng.sample([2, 3, 4, 5, 6, 7, 8], n_objects)
    body_top = 1  # in-bounds row in body is g[1..h-1]
    placed = 0
    used = {(ar, ac)} | {(0, c) for c in marker_positions}
    for color in obj_colors:
        for _ in range(60):
            dr = rng.randint(-3, 3); dc = rng.randint(-3, 3)
            if dr == 0 and dc == 0:
                continue
            r0 = ar + dr; c0 = ac + dc
            # All k rotation positions must land in-bounds in body (row >=1).
            rots = [(dr, dc), (dc, -dr), (-dr, -dc), (-dc, dr)][:k]
            # Also reject if the *input* placement falls in row 0
            if r0 < body_top or r0 >= h or c0 < 0 or c0 >= w:
                continue
            ok = True
            new_used = set()
            for rdr, rdc in rots:
                rr = ar + rdr; cc = ac + rdc
                if not (body_top <= rr < h and 0 <= cc < w):
                    ok = False; break
                if (rr, cc) in used or (rr, cc) in new_used:
                    ok = False; break
                if g[rr][cc] != 0:
                    ok = False; break
                new_used.add((rr, cc))
            if not ok:
                continue
            # Place input cell at first rotation (just the original obj cell).
            g[r0][c0] = color
            used.add((r0, c0))
            placed += 1
            break
        if placed >= n_objects:
            break

    # Guarantee >=1 object so the rotation actually produces new cells (no
    # identity). The 4 cardinal neighbours of the anchor are always in-bounds
    # (anchor is inset >=2) and rotate into each other.
    if placed == 0:
        for dr, dc in ((-1, 0), (0, 1), (1, 0), (0, -1)):
            rots = [(dr, dc), (dc, -dr), (-dr, -dc), (-dc, dr)][:k]
            cells = [(ar + rr, ac + cc) for rr, cc in rots]
            if all(1 <= r < h and 0 <= c < w and (r, c) not in used
                   and g[r][c] == 0 for r, c in cells):
                g[ar + dr][ac + dc] = 2
                placed = 1
                break
    return g


def _apply_rule(g):
    """Simulate the canonical rule (k rotations of each body object about the
    color-9 anchor) so we can verify output != input."""
    h, w = len(g), len(g[0])
    k = sum(1 for v in g[0] if v != 0)
    anchor = None
    for r in range(1, h):
        for c in range(w):
            if g[r][c] == 9:
                anchor = (r - 1, c); break
        if anchor:
            break
    out = [[0] * w for _ in range(h)]
    out[0] = list(g[0])
    if anchor is None:
        return out
    ar, ac = anchor
    out[ar + 1][ac] = 9
    for r in range(1, h):
        for c in range(w):
            v = g[r][c]
            if v in (0, 1, 9):
                continue
            dr = (r - 1) - ar; dc = c - ac
            rels = [(dr, dc), (dc, -dr), (-dr, -dc), (-dc, dr)][:min(k, 4)]
            for rr, cc in rels:
                pr = 1 + ar + rr; pc = ac + cc
                if 0 <= pr < h and 0 <= pc < w:
                    out[pr][pc] = v
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Row 0 has >=2 color-1 markers (k>=2 = a real rotation), exactly one anchor,
    >=1 object, and the simulated rotation changes the grid (no identity)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    k = sum(1 for v in grid[0] if v == 1)
    errors = []
    if k < 2:
        errors.append(f"row 0 has {k} markers; k>=2 needed (k=1 rotates nothing)")
    anchors = sum(1 for r in range(1, h) for c in range(w) if grid[r][c] == 9)
    if anchors != 1:
        errors.append(f"expected exactly one color-9 anchor, found {anchors}")
    objs = sum(1 for r in range(1, h) for c in range(w)
               if grid[r][c] not in (0, 1, 9))
    if objs < 1:
        errors.append("no object cells to rotate")
    if not errors and _apply_rule(grid) == grid:
        errors.append("rotation leaves the grid unchanged (identity)")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    if name == "no_markers":
        g[3][5] = 9
        g[5][3] = 4
        return g
    if name == "no_anchor":
        g[0][2] = 1; g[0][5] = 1
        g[5][3] = 4
        return g
    if name == "no_objects":
        g[0][2] = 1; g[0][5] = 1
        g[3][5] = 9
        return g
    return g
