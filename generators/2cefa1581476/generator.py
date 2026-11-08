"""Generator for 2cefa1581476 — pack objects horizontally, bottom-aligned.

Rule: extract all 4-connected non-bg components. Sort by bbox height
desc (or some order). Crop each. Pack horizontally with 1-col gap,
bottom-aligned (so all crops align to output bottom row).
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2cefa1581476"
VERSION = "2.2.1"  # strengthen non-bg component/separation self_check
TASK_ID = "2cefa1581476"
SUMMARY = (
    "0-bg grid with N (3-5) connected components in distinct non-zero "
    "colors at scattered positions. Each component is a small 4-conn "
    "blob (3-5 cells) with varied bbox shape. Components are spaced "
    "≥1-cell apart. Rule: extract each component. Crop to bbox. Sort "
    "by height descending (then color asc for ties). Pack the cropped "
    "pieces horizontally with 1-col gap between, ALL bottom-aligned. "
    "Output height = max cropped height; output width = sum cropped "
    "widths + (N-1) gaps."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "3-5 connected components in distinct non-zero colors",
    "each component is 4-conn, 3-5 cells, with varied bbox shape",
    "components don't touch (≥1-cell buffer)",
]

# Free axes the runner may override. Keys match the keyed draw_int labels in
# generate(); defaults are the medium band, valid spans easy..hard.
AXES = {
    "grid_h": {"type": "int", "default": "rng 9..12", "valid": "8..16",
               "doc": "Grid height (easy 8..10, medium 9..12, hard 12..16)."},
    "grid_w": {"type": "int", "default": "rng 11..14", "valid": "10..18",
               "doc": "Grid width (easy 10..12, medium 11..14, hard 14..18)."},
    "n":      {"type": "int", "default": "rng 3..4", "valid": "3..5",
               "doc": "Number of components to pack (easy 3, hard 4..5)."},
}


def _free(g, cells, h, w):
    cell_set = set(cells)
    for r, c in cells:
        if not (0 <= r < h and 0 <= c < w):
            return False
        if g[r][c] != 0:
            return False
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    if g[nr][nc] != 0 and (nr, nc) not in cell_set:
                        return False
    return True


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
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 10, 12)
        n = ctx.draw_int("n", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 14, 18)
        n = ctx.draw_int("n", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 11, 14)
        n = ctx.draw_int("n", 3, 4)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)

    for outer in range(80):
        g = full_grid(h, w, 0)
        ok = True
        placed_heights = []
        for color in colors:
            cells = _build_blob(rng, rng.randint(3, 5))
            sh = max(r for r, _ in cells) + 1
            sw = max(c for _, c in cells) + 1
            placed = False
            for _ in range(80):
                r0 = rng.randint(0, h - sh)
                c0 = rng.randint(0, w - sw)
                cells_abs = [(r0 + dr, c0 + dc) for dr, dc in cells]
                if not _free(g, cells_abs, h, w):
                    continue
                for r, c in cells_abs:
                    g[r][c] = color
                placed_heights.append(sh)
                placed = True
                break
            if not placed:
                ok = False
                break
        if ok and len(set(placed_heights)) >= 2:
            return g
    raise ValueError("could not realize layout")


def _components4(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == 0:
                continue
            color = grid[r][c]
            q = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            out.append({"color": color, "cells": cells,
                        "bbox": (min(r for r, _ in cells), min(c for _, c in cells),
                                 max(r for r, _ in cells), max(c for _, c in cells))})
    return out



def _components_nonzero(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == 0:
                continue
            q = deque([(r, c)]); seen.add((r, c)); cells = []
            while q:
                rr, cc = q.popleft(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] != 0:
                        seen.add((nr, nc)); q.append((nr, nc))
            out.append(cells)
    return out

def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be a non-empty rectangle"]
    comps = _components4(grid)
    expected = (3, 3) if difficulty == "easy" else ((4, 5) if difficulty == "hard" else (3, 4))
    if not (expected[0] <= len(comps) <= expected[1]):
        errs.append(f"expected {expected[0]}-{expected[1]} components for difficulty={difficulty}, found {len(comps)}")
    colors = [c["color"] for c in comps]
    if len(colors) != len(set(colors)):
        errs.append("components should use distinct colors")
    nonzero_comps = _components_nonzero(grid)
    if len(nonzero_comps) != len(comps):
        errs.append("different-colored objects touch 4-connectedly; rule extracts non-bg components, not color components")
    occupied = {(r, c) for comp in comps for r, c in comp["cells"]}
    for comp in comps:
        own = set(comp["cells"])
        for r, c in own:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == dc == 0:
                        continue
                    nb = (r + dr, c + dc)
                    if nb in occupied and nb not in own:
                        errs.append("components should have a one-cell buffer and not touch diagonally")
                        return errs
    for comp in comps:
        if not (3 <= len(comp["cells"]) <= 5):
            errs.append(f"component size outside 3-5: {len(comp['cells'])}")
            break
    heights = [c["bbox"][2] - c["bbox"][0] + 1 for c in comps]
    if len(set(heights)) < 2:
        errs.append(f"all component bbox heights are identical; pack order witness is weak: {heights}")
    return errs
