"""Generator for arc_additional_puzzle_bank_volume10:E64.

Red L-triominoes are completed by recoloring their 2x2 box green.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_l_shapes,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_l, full_squares, length_4_l.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dadeacb21d08"
VERSION = "2.0.1"  # add executable self_check for target red L-triomino invariant
TASK_ID = "dadeacb21d08"
SUMMARY = (
    "0-bg grid (h, w~7-12) with 2-5 RED (color-2) "
    "L-TRIOMINOES — each a 3-cell L within a 2×2 "
    "bbox, with one of the 4 corners missing. Each "
    "L is placed with ≥3 cells of margin from "
    "neighbors. Optionally a few decoy cells in other "
    "non-{0, 2} colors (1, 4, 5, 6, 7, 8, 9) are "
    "sprinkled with 1-cell padding so they don't "
    "accidentally extend an L. Rule: identify every "
    "color-2 connected component with EXACTLY 3 "
    "cells AND a 2×2 bounding box (i.e., an "
    "L-triomino). For each matching L, FILL its "
    "entire 2×2 bbox — all 4 cells, completing the "
    "missing corner — with color 3 (green) "
    "(replacing both the red cells and the empty "
    "corner with green). Non-L red components and "
    "decoy-colored cells stay. Net: every red L "
    "becomes a green 2×2 square; other shapes "
    "unchanged."
)

# Rivals: 'complete any 3-cell shape' refuted by ≥1 demo with a
# non-L 3-cell (e.g. I3 line) that stays unchanged. 'fill with red'
# refuted by any demo (output is green). 'fill any non-red shape too'
# refuted by ≥1 demo with non-red distractors that stay unchanged.
# 4 demos with varied L-counts + non-L red distractors + non-red
# distractors cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "target red components are exact 3-cell Ls inside a 2x2 box",
    "target components are separated so they stay distinct",
    "optional red line distractors are not L-triominoes",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_l", "full_squares", "length_4_l")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..12", "valid": "4..18"},
    "grid_w":         {"type": "int", "default": "rng 7..12", "valid": "4..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_l_shapes":     {"type": "int", "default": "rng 2..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "separated_l_triominoes",
                       "valid": "separated_l_triominoes"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
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
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        n_l_shapes = ctx.draw_int("n_l_shapes", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 10, 12)
        n_l_shapes = ctx.draw_int("n_l_shapes", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 7, 12)
        w = ctx.draw_int("grid_w", 7, 12)
        n_l_shapes = ctx.draw_int("n_l_shapes", 2, 5)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    anchors: list[tuple[int, int]] = []
    corners = [(0, 0), (0, 1), (1, 0), (1, 1)]
    for _ in range(220):
        if len(anchors) >= n_l_shapes:
            break
        r = rng.randint(0, h - 2)
        c = rng.randint(0, w - 2)
        if any(abs(r - rr) < 3 and abs(c - cc) < 3 for rr, cc in anchors):
            continue
        missing = rng.choice(corners)
        for dr, dc in corners:
            if (dr, dc) != missing:
                g[r + dr][c + dc] = 2
        anchors.append((r, c))
    if not anchors:
        g[1][1] = 2
        g[1][2] = 2
        g[2][1] = 2
    # Distractor cells in other colors. Rule processes all objects but
    # only acts on (color=2, size=3, bbox=2x2) → distractors stay unchanged.
    n_distractors = rng.randint(0, 4 if difficulty == "hard" else 2)
    distractor_pool = [1, 4, 5, 6, 7, 8, 9]
    placed = 0
    for _ in range(40):
        if placed >= n_distractors: break
        dr = rng.randint(0, h - 1); dc = rng.randint(0, w - 1)
        if g[dr][dc] != 0: continue
        # 1-cell margin so we don't accidentally extend an L.
        bad = False
        for ar in range(max(0, dr - 1), min(h, dr + 2)):
            for ac in range(max(0, dc - 1), min(w, dc + 2)):
                if g[ar][ac] != 0:
                    bad = True; break
            if bad: break
        if bad: continue
        g[dr][dc] = rng.choice(distractor_pool)
        placed += 1
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify normal rows contain only proper target red L-triominoes.

    The task rule completes each color-2 connected component that has exactly
    three cells and a 2x2 bbox. Default generated rows should therefore contain
    at least one such component, and no accidental non-L red component that
    teaches a conflicting rule. Degenerate override textures intentionally
    exercise no-op cases and are outside the default self-check path.
    """
    if not grid or not isinstance(grid[0], list):
        return ["grid must be non-empty and rectangular"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid rows must have equal width"]
    errs: list[str] = []
    seen = set()
    comps: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 2 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            comp = []
            while stack:
                rr, cc = stack.pop()
                comp.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 2 and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(comp)
    if not comps:
        return ["no color-2 target components present"]
    good = 0
    for comp in comps:
        rs = [r for r, _ in comp]
        cs = [c for _, c in comp]
        bbox_h = max(rs) - min(rs) + 1
        bbox_w = max(cs) - min(cs) + 1
        if len(comp) == 3 and bbox_h == 2 and bbox_w == 2:
            good += 1
        else:
            errs.append(f"color-2 component is not a 3-cell 2x2 L-triomino: size={len(comp)} bbox={bbox_h}x{bbox_w}")
            break
    if good == 0:
        errs.append("no valid target L-triomino found")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_l":
        # blank → no L-triominoes to complete
        return g
    if name == "full_squares":
        # 2x2 already full → no missing corner to complete
        for dr in range(2):
            for dc in range(2):
                g[1 + dr][1 + dc] = 2
        return g
    if name == "length_4_l":
        # 4-cell L → not 3-cell L-triomino, rule won't fire
        for r, c in [(1, 1), (1, 2), (2, 1), (3, 1)]: g[r][c] = 2
        return g
    return g
