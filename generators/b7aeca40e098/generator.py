"""Generator for arc_additional_puzzles_21_set3:M16.

Rule: for each closed color-1 rectangular frame, if its interior holds
exactly one non-{0,1} color, recolor the frame's cells to that color.

Combinatorial axes: grid size, number of frames, their sizes/positions,
the interior marker colors, optional empty-interior decoy frames.
Degenerates: no_frames, no_marker, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "b7aeca40e098"
VERSION = "2.1.1"
TASK_ID = "b7aeca40e098"
SUMMARY = (
    "0-bg grid (size varies). Several closed COLOR-1 (blue) RECTANGULAR "
    "FRAMES (hollow outlines, >=3x3), placed clear of one another. Each "
    "frame's interior holds 1-3 cells of a SINGLE distinct non-{0,1} "
    "marker color (frames use different colors); optional decoy frames "
    "have an empty interior. Rule: for every hollow color-1 frame whose "
    "interior contains exactly ONE non-{0,1} color, recolor the frame's "
    "cells to that color; frames with no interior color (or more than "
    "one) stay blue. The grid size, the number / size / position of the "
    "frames and their marker colors all vary freely (was 2 hardcoded "
    "frames, ~6 configs)."
)

INVARIANTS = [
    "closed color-1 rectangular frames at least 3x3",
    "each active frame has exactly one non-{0,1} color cell inside",
    "frames sit clear of each other so each is a separate component",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_frames", "no_marker", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "9..20"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "11..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "3..9"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "varies", "valid": "3..9"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_frames|no_marker|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: every color-1 cell has ≥1 color-1 4-neighbor (frames are closed outlines)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 1:
                continue
            nbrs = [grid[r + dr][c + dc]
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                    if 0 <= r + dr < h and 0 <= c + dc < w]
            if not any(v == 1 for v in nbrs):
                errs.append(f"isolated color-1 cell at ({r},{c})")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  task_id=TASK_ID, version=VERSION,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, nf, smax, ndecoy = (9, 11), (11, 13), (2, 2), 4, 0
    elif difficulty == "hard":
        hr, wr, nf, smax, ndecoy = (15, 20), (15, 20), (3, 5), 6, 1
    else:
        hr, wr, nf, smax, ndecoy = (11, 14), (12, 15), (2, 3), 5, 0

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        occ = [[False] * w for _ in range(h)]
        g = full_grid(h, w, 0)
        colors = rng.sample(range(2, 10), 8)
        ci = 0

        def _reserve(top, left, bh, bw):
            for r in range(top - 1, top + bh + 1):
                for c in range(left - 1, left + bw + 1):
                    if 0 <= r < h and 0 <= c < w and occ[r][c]:
                        return False
            for r in range(top, top + bh):
                for c in range(left, left + bw):
                    occ[r][c] = True
            return True

        def _place_frame(kind):
            # kind: "active" (1 interior color -> recolor),
            #       "empty"  (no interior -> stay blue),
            #       "multi"  (>=2 interior colors -> stay blue)
            nonlocal ci
            for _t in range(30):
                bh = rng.randint(3, min(smax, h)); bw = rng.randint(3, min(smax, w))
                top = rng.randint(0, h - bh); left = rng.randint(0, w - bw)
                if _reserve(top, left, bh, bw):
                    draw_frame(g, top, left, top + bh - 1, left + bw - 1, 1)
                    cells = [(r, c) for r in range(top + 1, top + bh - 1)
                             for c in range(left + 1, left + bw - 1)]
                    if kind == "active" and cells:
                        color = colors[ci]; ci += 1
                        k = rng.randint(1, min(3, len(cells)))
                        for r, c in rng.sample(cells, k):
                            g[r][c] = color
                    elif kind == "multi" and len(cells) >= 2:
                        c1 = colors[ci]; ci += 1
                        c2 = colors[ci]; ci += 1
                        (r1, k1), (r2, k2) = rng.sample(cells, 2)
                        g[r1][k1] = c1; g[r2][k2] = c2
                    return True
            return False

        placed = 0
        for _ in range(rng.randint(*nf)):
            if _place_frame("active"):
                placed += 1
        for _ in range(ndecoy):
            _place_frame("empty")           # empty-interior decoy (stays blue)
        # 0-2 multi-color-interior decoys (>=2 distinct interior colors -> blue)
        if ci <= 6:
            for _ in range(rng.randint(0, 2)):
                _place_frame("multi")
        if placed >= 1:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 12, 0)
    if name == "no_frames":
        g[3][3] = 4; g[6][8] = 6
        return g
    if name == "no_marker":
        draw_frame(g, 1, 1, 4, 5, 1)
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(12):
                g[r][c] = 1
        return g
    return g
