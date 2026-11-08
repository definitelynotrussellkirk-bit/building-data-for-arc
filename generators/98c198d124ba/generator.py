"""Generator for 98c198d124ba — gather hole regions, pack at bottom.

Rule: find all 0-cell regions enclosed by non-bg frames (not reachable
from grid border). For each region, find adjacent frame color. Paint
the region's cells in that color (on a fresh canvas matching region
bbox). Sort regions by (size DESC, height ASC, width ASC). Pack
horizontally bottom-aligned with 1-col gap.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "98c198d124ba"
VERSION = "2.0.1"
TASK_ID = "98c198d124ba"

SUMMARY = (
    "0-bg grid with 2-4 hollow rectangular FRAMES in distinct non-zero "
    "colors. Each frame is ≥3×3 (so it has an interior). Frame "
    "interiors are bg (0), forming HOLE REGIONS enclosed by the frame "
    "color. Frames don't overlap or touch. Rule: find all 0-regions "
    "(connected groups) that are ENCLOSED (not reachable from grid "
    "border through 0-cells). For each enclosed region, find its "
    "adjacent frame color. Build a small grid showing the region "
    "cells in that color. Sort regions by (size DESC, height ASC, "
    "width ASC). Pack the grids horizontally bottom-aligned with "
    "1-col gap. Output is the packed gallery."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "2-4 hollow color frames with distinct colors",
    "each frame is ≥3×3 (interior exists)",
    "frame interiors are enclosed 0-regions",
    "frames don't overlap or touch (≥1-cell buffer)",
    "the 0-cells outside frames are connected to the border (so they're not enclosed)",
]

# Free axes the runner may override. Keys match the keyed draw_int labels in
# generate(); defaults are the medium band, valid spans easy..hard. (n_frames
# is a constant 2 in the easy band, so it's only keyed in medium/hard.)
AXES = {
    "grid_h":   {"type": "int", "default": "rng 9..11", "valid": "7..16",
                 "doc": "Grid height (easy 7..9, medium 9..11, hard 11..16)."},
    "grid_w":   {"type": "int", "default": "rng 10..14", "valid": "9..18",
                 "doc": "Grid width (easy 9..11, medium 10..14, hard 13..18)."},
    "n_frames": {"type": "int", "default": "rng 2..3", "valid": "2..4",
                 "doc": "Number of hollow frames (easy 2, medium 2..3, hard 3..4)."},
}


def _free(g, r1, c1, r2, c2, buffer=1):
    h, w = len(g), len(g[0])
    for r in range(max(0, r1 - buffer), min(h, r2 + buffer + 1)):
        for c in range(max(0, c1 - buffer), min(w, c2 + buffer + 1)):
            if g[r][c] != 0:
                return False
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: 2-4 distinct non-zero non-8 colors; each forms a rectangular outline (frame)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    from collections import defaultdict
    pos: dict = defaultdict(list)
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v not in (0, 8):
                pos[v].append((r, c))
    if not pos:
        return []  # degenerate — allowed
    errs = []
    n = len(pos)
    if not (2 <= n <= 4):
        errs.append(f"expected 2-4 frame colors; found {n}")
    for color, cells in pos.items():
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
        if r1 == r2 or c1 == c2:
            continue  # degenerate — 1-cell frame
        # A frame outline has cells only on bbox border
        bbox_border = {(r1, c) for c in range(c1, c2 + 1)} | {(r2, c) for c in range(c1, c2 + 1)} | \
                      {(r, c1) for r in range(r1, r2 + 1)} | {(r, c2) for r in range(r1, r2 + 1)}
        cell_set = set(cells)
        non_border = cell_set - bbox_border
        if non_border:
            errs.append(f"color {color} has {len(non_border)} cells not on frame border")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 9, 11)
        n_frames = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 16)
        w = ctx.draw_int("grid_w", 13, 18)
        n_frames = ctx.draw_int("n_frames", 3, 4)
    else:
        # h floor is 9 (not 8): with n_frames=3, an 8-tall grid only fits one
        # vertical band of frames once any frame is 4-tall, so the 3rd never
        # places. 9 rows give two bands and placement is always feasible.
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 10, 14)
        n_frames = ctx.draw_int("n_frames", 2, 3)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], n_frames)

    # Cap frame size by how many frames must share the grid: with 3-4 frames in
    # a tight medium grid, 5x5 frames greedily eat the space and the 3rd/4th
    # can't fit. Shrinking the ceiling as n_frames grows keeps placement feasible.
    fmax = 5 if n_frames <= 2 else 4
    for outer in range(200):
        g = full_grid(h, w, 0)
        placed = 0
        for color in colors:
            for _ in range(40):
                fh = rng.randint(3, min(fmax, h - 2))
                fw = rng.randint(3, min(fmax, w - 2))
                r0 = rng.randint(1, h - fh - 1)
                c0 = rng.randint(1, w - fw - 1)
                if not _free(g, r0, c0, r0 + fh - 1, c0 + fw - 1, buffer=1):
                    continue
                draw_frame(g, r0, c0, r0 + fh - 1, c0 + fw - 1, color)
                placed += 1
                break
        if placed == n_frames:
            return g
    raise ValueError("could not realize frames")
