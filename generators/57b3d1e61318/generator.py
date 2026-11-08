"""Generator for arc_puzzle_bank_21_set15:S15_E6 — copy color-2 stencil from 1-anchor to 3-anchor.

Color-2 cells are copied by preserving offsets from a color-1 source
anchor to a color-3 target anchor.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_source_anchor (no color-1 → rule's source-anchor
selector returns nothing, no offsets to copy), no_target_anchor (no
color-3 → rule has nowhere to copy to), no_stencil (no color-2 cells
near 1-anchor → rule's stencil is empty, copy is no-op).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "57b3d1e61318"
VERSION = "2.0.1"
TASK_ID = "57b3d1e61318"
SUMMARY = (
    "0-bg grid (h~9-12, w~"
    "11-14) with: (a) ONE "
    "COLOR-1 SOURCE ANCHOR "
    "at (ar1, ac1) (interior) "
    "surrounded by 3-4 "
    "COLOR-2 STENCIL CELLS "
    "at one of 5 hardcoded "
    "OFFSET PATTERNS (e.g., "
    "[(-1,0),(0,1),(1,0),"
    "(1,1)] etc.); (b) ONE "
    "COLOR-3 TARGET ANCHOR "
    "at (ar3, ac3) far from "
    "the source (≥2-cell "
    "radius padding) where "
    "the same offsets fit "
    "in-bounds. Rule (COPY "
    "COLOR-2 STENCIL FROM "
    "1-ANCHOR TO 3-ANCHOR "
    "PRESERVING OFFSETS): "
    "identify the COLOR-1 "
    "SOURCE ANCHOR at (ar1, "
    "ac1) and its STENCIL "
    "OFFSETS = positions of "
    "COLOR-2 cells relative "
    "to it. Identify the "
    "COLOR-3 TARGET ANCHOR "
    "at (ar3, ac3). For EACH "
    "OFFSET (dr, dc) of "
    "color-2 cells, PAINT "
    "COLOR-2 at (ar3 + dr, "
    "ac3 + dc). Source + "
    "target anchors stay. "
    "Net: red stencil "
    "around 1-anchor "
    "replicates around 3-"
    "anchor with same "
    "shape."
)

INVARIANTS = [
    "background is 0",
    "there is exactly one color-1 source anchor",
    "there is exactly one color-3 target anchor",
    "all color-2 source cells fit when moved by the source-to-target anchor vector",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_source_anchor", "no_target_anchor", "no_stencil")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "height":            {"type": "int", "default": "rng 9..12", "valid": "7..15"},
    "width":             {"type": "int", "default": "rng 11..14", "valid": "9..17"},
    "offset_pattern":    {"type": "choice", "default": "rng centered stencil",
                          "valid": "small nonzero offset sets"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "default|warm|cool|varied"},
    "palette_size":      {"type": "int", "default": "rng 3..3", "valid": "3..3"},
    "position_bias":     {"type": "str", "default": "source_target_anchors",
                          "valid": "source_target_anchors"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..3", "valid": "3..3"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "default|warm|cool|varied|no_source_anchor|no_target_anchor|no_stencil"},
}

_OFFSET_PATTERNS = [
    [(-1, 0), (0, 1), (1, 0), (1, 1)],
    [(0, -1), (0, 1), (1, 1), (2, 1)],
    [(-1, -1), (-1, 0), (0, 1), (1, 1)],
    [(-2, 0), (-1, 0), (0, 1), (1, 1)],
    [(-1, 1), (0, -1), (0, 0), (1, -1)],
]


def _fits(h, w, anchor, offsets):
    ar, ac = anchor
    return all(0 <= ar + dr < h and 0 <= ac + dc < w for dr, dc in offsets)


def _near_nonzero(g, r, c, radius=1):
    h, w = len(g), len(g[0])
    for rr in range(max(0, r - radius), min(h, r + radius + 1)):
        for cc in range(max(0, c - radius), min(w, c + radius + 1)):
            if g[rr][cc] != 0:
                return True
    return False


def _place_source(g, rng, offsets):
    h, w = len(g), len(g[0])
    for _ in range(120):
        ar = rng.randint(2, h - 3)
        ac = rng.randint(2, w - 3)
        if not _fits(h, w, (ar, ac), offsets):
            continue
        if _near_nonzero(g, ar, ac):
            continue
        cells = [(ar + dr, ac + dc) for dr, dc in offsets]
        if all(g[r][c] == 0 for r, c in cells):
            g[ar][ac] = 1
            for r, c in cells:
                if (r, c) != (ar, ac):
                    g[r][c] = 2
            return
    raise ValueError("could not place source anchor")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, exactly one color-1 anchor, exactly one color-3 anchor, at least one color-2 stencil cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    c1 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 1)
    c2 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 2)
    c3 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 3)
    if c1 != 1:
        errs.append(f"expected exactly 1 color-1 anchor, found {c1}")
    if c3 != 1:
        errs.append(f"expected exactly 1 color-3 anchor, found {c3}")
    if c2 == 0:
        errs.append("no color-2 stencil cells found")
    return errs


def _place_target(g, rng, offsets):
    h, w = len(g), len(g[0])
    for _ in range(160):
        ar = rng.randint(1, h - 2)
        ac = rng.randint(1, w - 2)
        if not _fits(h, w, (ar, ac), offsets):
            continue
        if not _near_nonzero(g, ar, ac, radius=2):
            g[ar][ac] = 3
            return
    raise ValueError("could not place target anchor")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("height", 9, 10)
        w = ctx.draw_int("width", 11, 12)
    elif difficulty == "hard":
        h = ctx.draw_int("height", 12, 12)
        w = ctx.draw_int("width", 13, 14)
    else:
        h = ctx.draw_int("height", 9, 12)
        w = ctx.draw_int("width", 11, 14)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    offsets = rng.choice(_OFFSET_PATTERNS)
    _place_source(g, rng, offsets)
    _place_target(g, rng, offsets)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_source_anchor":
        # No color-1 — rule's source-anchor selector returns nothing.
        g[2][2] = 2; g[2][3] = 2; g[3][2] = 2
        g[6][7] = 3
        return g
    if name == "no_target_anchor":
        # No color-3 — rule has nowhere to copy to.
        g[2][2] = 1
        g[2][3] = 2; g[3][2] = 2
        return g
    if name == "no_stencil":
        # Source anchor exists but no color-2 cells — rule's stencil
        # is empty; copy is no-op.
        g[2][2] = 1
        g[6][7] = 3
        return g
    return g
