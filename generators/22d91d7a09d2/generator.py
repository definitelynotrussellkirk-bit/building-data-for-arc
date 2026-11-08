"""Generator for 9473c6fb.

Rule: a 5x5 all-in-bounds marker context triggers one recolor from the
local table.

Combinatorial axes (8): grid_h/w, grid_size, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_patch, edge_patch, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paste

GENERATOR_ID = "22d91d7a09d2"
# 2.2.0: place multiple independent local-context markers per example instead
# of a single patch.  The canonical demos are scattered marker fields; one patch
# under-exercised the cellwise lookup and tripped object-count drift.
VERSION = "2.2.0"
TASK_ID = "22d91d7a09d2"
SUMMARY = (
    "COLOR-7 (orange) background square "
    "grid (size ∈ 7-10) with: ONE 5×5 "
    "MARKER CONTEXT PATCH pasted at a "
    "random interior position (r0, "
    "c0 ∈ 1..size-6) — drawn from "
    "_PATCHES bank (3 variants of "
    "5×5 patches: all-orange-7 with "
    "ONE color-4 center marker at "
    "(2,2); same with color-6 center; "
    "or color-9 at (2,2) + color-1 "
    "at (2,4) + scattered color-9s "
    "in bottom-right corner). All "
    "patches are fully in-bounds; "
    "color-7 dominates the patch "
    "and the rest of the grid. "
    "Rule (RECOGNIZE THE 5×5 "
    "MARKER CONTEXT; APPLY A "
    "CANONICAL RADIUS-2 RECOLOR "
    "TABLE TO RECOLOR THE CENTER "
    "MARKER OR ADD A SPECIFIC "
    "DECORATION BASED ON THE "
    "PATTERN OF NON-7 CELLS WITHIN "
    "RADIUS 2 OF THE CENTER): "
    "LOCATE the patch by scanning "
    "for the 5×5 marker context. "
    "READ the non-7 cells in the "
    "Chebyshev-distance-2 window "
    "around the center. APPLY a "
    "fixed recolor table that maps "
    "the surrounding pattern to a "
    "new center color (or paints "
    "additional cells). Net: "
    "marker context decodes via a "
    "fixed local lookup table; "
    "the result is a "
    "context-dependent recolor."
)

INVARIANTS = [
    "the active 5x5 context has no out-of-bounds sentinel positions",
    "color 7 is the dominant filler",
    "the center marker is recolored by the canonical radius-2 table",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_patch", "edge_patch", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..16", "valid": "8..18"},
    "grid_w":         {"type": "int", "default": "rng 8..16", "valid": "8..18"},
    "grid_size":      {"type": "int", "default": "legacy square size", "valid": "8..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "varied", "valid": "varied"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "varied", "valid": "varied"},
    "n_patches":      {"type": "int", "default": "rng 2..5", "valid": "1..5"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_patch|edge_patch|full_grid"},
}


# Each patch is a fully-in-bounds 5x5 radius-2 window that the canonical
# recolor table maps to a DIFFERENT centre colour (verified: every one yields
# output != input across grid sizes 7..14 and all corner placements). The
# previous "isolated centre-6" patch had no table entry → identity, removed.
_PATCHES = [
    [   # centre 4 -> 5
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
        [7, 7, 4, 7, 7],
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
    ],
    [   # centre 6 (+9 marker) -> 5
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
        [7, 7, 6, 7, 7],
        [7, 7, 7, 7, 9],
        [7, 7, 7, 7, 7],
    ],
    [   # centre 9 (+1,+9s) -> 8
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
        [7, 7, 9, 7, 1],
        [7, 7, 7, 7, 7],
        [7, 9, 7, 9, 7],
    ],
    [   # centre 9 (+6s) -> 2
        [7, 7, 7, 7, 6],
        [7, 7, 7, 7, 7],
        [7, 7, 9, 7, 7],
        [7, 7, 7, 7, 6],
        [7, 7, 9, 7, 7],
    ],
    [   # centre 2 (+6 marker) -> 5
        [7, 7, 7, 7, 7],
        [6, 7, 7, 7, 7],
        [7, 7, 2, 7, 7],
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
    ],
    [   # centre 1 (+9s,+6) -> 2
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
        [9, 7, 1, 7, 1],
        [7, 7, 7, 7, 7],
        [7, 9, 7, 6, 7],
    ],
]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 8, 12)
        target = ctx.draw_int("n_patches", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 13, 18)
        target = ctx.draw_int("n_patches", 3, 5)
    else:
        h = ctx.draw_int("grid_h", 10, 16)
        w = ctx.draw_int("grid_w", 10, 16)
        target = ctx.draw_int("n_patches", 2, 4)
    g = full_grid(h, w, 7)
    placed: list[tuple[int, int]] = []
    # A pattern is read from its radius-2 5x5 window; keep windows disjoint so
    # one marker cannot corrupt another marker's signature.
    for _ in range(target):
        patch = [row[:] for row in rng.choice(_PATCHES)]
        for _attempt in range(200):
            r0 = rng.randint(0, h - 5)
            c0 = rng.randint(0, w - 5)
            if any(_rects_overlap((r0, c0), old) for old in placed):
                continue
            paste(g, patch, r0, c0)
            placed.append((r0, c0))
            break
    if not placed:
        # Should be unreachable for the dimensions above, but fail loud rather
        # than silently emitting an all-7 identity example.
        raise ValueError("could not place any recolorable 5x5 context")
    return g


def _rects_overlap(a, b):
    ar, ac = a
    br, bc = b
    return not (ar + 4 < br or br + 4 < ar or ac + 4 < bc or bc + 4 < ac)


def self_check(grid, *, difficulty=None, meta=None):
    """Generated marker fields must contain one or more full 5x5 lookup
    windows, color 7 must dominate, and every non-7 cell must belong to a
    recognized lookup patch."""
    errs = []
    H, W = len(grid), len(grid[0])
    if H < 5 or W < 5:
        return ["grid too small for a radius-2 lookup window"]
    total = H * W
    n7 = sum(1 for row in grid for v in row if v == 7)
    if n7 * 2 <= total:
        errs.append("color 7 is not the dominant filler")
    nz = {(r, c) for r in range(H) for c in range(W) if grid[r][c] != 7}
    if not nz:
        errs.append("no non-7 marker cells -> nothing to recolor (identity)")
        return errs
    hits = []
    covered = set()
    for r0 in range(H - 4):
        for c0 in range(W - 4):
            window = [row[c0:c0 + 5] for row in grid[r0:r0 + 5]]
            if any(window == p for p in _PATCHES):
                hits.append((r0, c0))
                for rr in range(5):
                    for cc in range(5):
                        if window[rr][cc] != 7:
                            covered.add((r0 + rr, c0 + cc))
    if not hits:
        errs.append("no recognized 5x5 lookup patch found")
    if nz - covered:
        errs.append("some non-7 cells are outside recognized lookup patches")
    if difficulty == "hard" and len(hits) < 3:
        errs.append(f"hard instance has only {len(hits)} lookup patches")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 8, 7)
    if name == "no_patch":
        return g
    if name == "edge_patch":
        paste(g, _PATCHES[0], 0, 0)
        return g
    if name == "full_grid":
        for r in range(8):
            for c in range(8):
                g[r][c] = 7
        return g
    return g
