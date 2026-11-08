"""Generator for 1f35591a9a58 — bbox intersection of two objects.

Rule: sort connected components by color (asc). Take first two (A, B).
Compute bbox intersection (overlapping rows and cols of their bboxes).
If a non-empty intersection exists, output a fresh grid with that
intersection region painted color 8. Else output all-bg.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1f35591a9a58"
VERSION = "2.0.1"


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly 2 distinct non-zero colors; their bboxes overlap."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
        return errs
    colors = list({grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0})
    if len(colors) != 2:
        errs.append(f"expected exactly 2 non-zero colors, got {len(colors)}: {sorted(colors)}")
        return errs
    bboxes = []
    for color in colors:
        cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == color]
        r1 = min(r for r, c in cells); r2 = max(r for r, c in cells)
        c1 = min(c for r, c in cells); c2 = max(c for r, c in cells)
        bboxes.append((r1, c1, r2, c2))
    (r1a, c1a, r2a, c2a), (r1b, c1b, r2b, c2b) = bboxes
    if max(r1a, r1b) > min(r2a, r2b) or max(c1a, c1b) > min(c2a, c2b):
        errs.append("bboxes of the two objects do not overlap")
    return errs
TASK_ID = "1f35591a9a58"
SUMMARY = (
    "0-bg grid with EXACTLY 2 connected components in distinct non-zero "
    "colors. The two components have OVERLAPPING bounding boxes — "
    "intersection region of width ≥1 and height ≥1. Components may "
    "touch or be intertwined (e.g., L-shapes that fit together). Rule: "
    "find both objects (sorted by color). Compute the bbox intersection "
    "rectangle (max of r1s, min of r2s, max of c1s, min of c2s). Output "
    "a fresh canvas with that rectangle painted color 8. Component "
    "cells in the input are NOT preserved in output."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly 2 connected components in distinct non-zero colors",
    "the two bbox rectangles overlap (intersection has h ≥1 and w ≥1)",
    "components may or may not touch; what matters is bbox overlap",
]

# Free axes the runner may override. Keys match the keyed draw_int labels in
# generate(); defaults are the medium band, valid spans easy..hard.
AXES = {
    "grid_h": {"type": "int", "default": "rng 9..12", "valid": "7..16",
               "doc": "Grid height (easy 7..9, medium 9..12, hard 11..16)."},
    "grid_w": {"type": "int", "default": "rng 10..14", "valid": "8..18",
               "doc": "Grid width (easy 8..10, medium 10..14, hard 12..18)."},
    "a_size": {"type": "int", "default": "rng 4..5", "valid": "3..7",
               "doc": "Cell count of object A (easy 3..4, hard 5..7)."},
    "b_size": {"type": "int", "default": "rng 4..5", "valid": "3..7",
               "doc": "Cell count of object B (easy 3..4, hard 5..7)."},
}


def _build_blob(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc))
            seen.add((nr, nc))
    minr = min(r for r, _ in cells)
    minc = min(c for _, c in cells)
    return [(r - minr, c - minc) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 8, 10)
        a_size = ctx.draw_int("a_size", 3, 4)
        b_size = ctx.draw_int("b_size", 3, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 16)
        w = ctx.draw_int("grid_w", 12, 18)
        a_size = ctx.draw_int("a_size", 5, 7)
        b_size = ctx.draw_int("b_size", 5, 7)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 10, 14)
        a_size = ctx.draw_int("a_size", 4, 5)
        b_size = ctx.draw_int("b_size", 4, 5)
    color_a, color_b = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 2)

    for outer in range(80):
        g = full_grid(h, w, 0)
        cells_a = _build_blob(rng, a_size)
        cells_b = _build_blob(rng, b_size)
        ah = max(r for r, _ in cells_a) + 1
        aw = max(c for _, c in cells_a) + 1
        bh = max(r for r, _ in cells_b) + 1
        bw = max(c for _, c in cells_b) + 1
        ar0 = rng.randint(0, h - ah)
        ac0 = rng.randint(0, w - aw)
        # Place B with bbox overlap to A
        # A bbox: [ar0, ar0+ah-1] × [ac0, ac0+aw-1]
        # B bbox needs to overlap
        # Pick B's top-left in a range that creates overlap
        br_min = max(0, ar0 - bh + 1)
        br_max = min(h - bh, ar0 + ah - 1)
        bc_min = max(0, ac0 - bw + 1)
        bc_max = min(w - bw, ac0 + aw - 1)
        if br_min > br_max or bc_min > bc_max:
            continue
        br0 = rng.randint(br_min, br_max)
        bc0 = rng.randint(bc_min, bc_max)
        # Check the actual cells don't overlap (they can but rule treats them as separate components when colors differ)
        a_set = {(ar0 + dr, ac0 + dc) for dr, dc in cells_a}
        b_set = {(br0 + dr, bc0 + dc) for dr, dc in cells_b}
        if a_set & b_set:
            continue  # cells overlap → would merge into wrong component count
        # Verify bbox intersection is non-trivial
        ir_lo = max(ar0, br0)
        ir_hi = min(ar0 + ah - 1, br0 + bh - 1)
        ic_lo = max(ac0, bc0)
        ic_hi = min(ac0 + aw - 1, bc0 + bw - 1)
        if ir_lo > ir_hi or ic_lo > ic_hi:
            continue
        for r, c in a_set:
            g[r][c] = color_a
        for r, c in b_set:
            g[r][c] = color_b
        return g
    raise ValueError("could not realize bbox-overlap layout")
