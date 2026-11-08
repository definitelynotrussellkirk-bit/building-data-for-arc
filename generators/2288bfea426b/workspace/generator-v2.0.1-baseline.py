"""Generator for next_b:hard_13 — multi-marker rotated stamping.

Rule: template = color-2 component. For each cell with value v in
{1, 3, 4, 6}, stamp the template rotated by k = mapped(v) at that
cell, painted color 8. Mapping: 1→0, 3→1 (CW), 4→2 (180), 6→3 (CCW).

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_template (no color-2 → rule's template selector
returns nothing), no_markers (template present but no {1,3,4,6}
markers → rule has nothing to stamp), rot_symmetric_template
(template is rotationally symmetric → all 4 rotations identical, no
contrast).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2288bfea426b"
VERSION = "2.0.1"


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=2 color-2 template cells; >=2 distinct marker colors from {1,3,4,6}."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
        return errs
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if len(twos) < 2:
        errs.append(f"expected >=2 color-2 template cells, got {len(twos)}")
    markers = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] in {1, 3, 4, 6}}
    if len(markers) < 2:
        errs.append(f"expected >=2 distinct marker colors from {{1,3,4,6}}, got {len(markers)}")
    return errs
TASK_ID = "2288bfea426b"

SUMMARY = (
    "0-bg grid (h~11-14, w~"
    "12-14) with: (a) ONE "
    "COLOR-2 (red) TEMPLATE "
    "drawn from 4 hardcoded "
    "ASYMMETRIC SHAPES (3-4 "
    "cells, max bbox 3×3) at "
    "a random non-touching "
    "position; (b) 2-3 "
    "MARKER cells with "
    "DISTINCT codes from "
    "{1, 3, 4, 6} placed far "
    "from the template and "
    "each other (with room "
    "for max(sh, sw) bounding "
    "box). Markers map to "
    "rotation codes: 1→0 "
    "(identity), 3→1 (90° "
    "CW), 4→2 (180°), 6→3 "
    "(270° CW). Rule (STAMP "
    "ROTATED TEMPLATE AT "
    "EACH MARKER IN COLOR "
    "8): identify the "
    "COLOR-2 TEMPLATE cells. "
    "For EACH MARKER at "
    "(r, c) with code v ∈ "
    "{1, 3, 4, 6}: COMPUTE "
    "rotation k = {1:0, 3:1, "
    "4:2, 6:3}[v]. ROTATE "
    "the template by k×90° "
    "CW. STAMP the rotated "
    "shape at (r, c) (as "
    "anchor or offset, "
    "task-specific) in "
    "COLOR-8 (cyan). The "
    "template + markers "
    "stay (or markers may "
    "be overwritten). Net: "
    "each marker stamps a "
    "rotated red template "
    "in cyan."
)

INVARIANTS = [
    "background is 0",
    "exactly one color-2 multi-cell template (3-4 cells)",
    "2-3 isolated marker cells with distinct values from {1, 3, 4, 6}",
    "each marker has space for the rotated template (max(sh, sw) bound) to fit",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_template", "no_markers", "rot_symmetric_template")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 11..14", "valid": "10..18"},
    "grid_w":            {"type": "int", "default": "rng 12..14", "valid": "11..18"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 4..5", "valid": "3..5"},
    "position_bias":     {"type": "str", "default": "template_plus_rotation_markers",
                          "valid": "template_plus_rotation_markers"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..5", "valid": "3..5"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_SHAPES = [
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 1)],
    [(0, 0), (1, 0), (2, 0), (2, 1)],
]


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _too_close(g, r, c) -> bool:
    h, w = len(g), len(g[0])
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0:
                return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 12, 13)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 14)
        w = ctx.draw_int("grid_w", 13, 14)
    else:
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 12, 14)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    shape = rng.choice(_SHAPES)
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    bound = max(sh, sw)
    placed = False
    for _ in range(40):
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = 2
        placed = True; break
    if not placed:
        raise ValueError("could not place template")
    n_markers = rng.randint(2, 3)
    marker_codes = rng.sample([1, 3, 4, 6], n_markers)
    placed = 0; attempts = 0
    while placed < n_markers and attempts < 80:
        attempts += 1
        r = rng.randint(0, h - bound); c = rng.randint(0, w - bound)
        if g[r][c] != 0 or _too_close(g, r, c): continue
        bad = False
        for rr in range(r, r + bound):
            for cc in range(c, c + bound):
                if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0:
                    bad = True; break
            if bad: break
        if bad: continue
        g[r][c] = marker_codes[placed]
        placed += 1
    if placed < n_markers:
        raise ValueError(f"could only place {placed}/{n_markers} markers")
    return g


def _draw_from_degenerate(name, rng):
    h, w = 12, 13
    g = full_grid(h, w, 0)
    if name == "no_template":
        # No color-2 — rule's template selector returns nothing.
        g[3][3] = 1
        g[7][8] = 4
        return g
    if name == "no_markers":
        # Template present but no {1,3,4,6} markers.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[3 + dr][3 + dc] = 2
        return g
    if name == "rot_symmetric_template":
        # Template rotationally symmetric (2x2) — all 4 rotations identical.
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            g[2 + dr][2 + dc] = 2
        g[7][3] = 1
        g[8][9] = 4
        return g
    return g
