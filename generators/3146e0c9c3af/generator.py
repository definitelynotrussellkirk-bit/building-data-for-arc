"""Generator for arc_additional_puzzles_21_set3:H16.

Rule: among the nested color-1 frames, recolor each 0-cell to (depth + 1)
where depth = the number of frame interiors enclosing it.

Combinatorial axes: grid size, the number of nested frames, and their
per-side insets / position.
Degenerates: no_frames, single_frame, frames_at_edges.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "3146e0c9c3af"
VERSION = "3.1.0"  # diversity: random grid + N nested frames + per-side insets (was centered, ~9 configs)
TASK_ID = "3146e0c9c3af"
SUMMARY = (
    "0-bg grid (size varies). 2-5 NESTED color-1 (blue) RECTANGULAR "
    "FRAMES, each inset >=2 on every side from the one outside it (so "
    "they are separate components; insets vary per side, not necessarily "
    "concentric). Rule: for each empty cell, count how many frame "
    "interiors enclose it (depth); if depth > 0, recolor it to depth+1 "
    "(depth-1 -> color 2, depth-2 -> color 3, ...). The frames stay "
    "color 1 and outside cells stay 0. The grid size, the number of "
    "frames and their per-side insets all vary freely, so the depth "
    "gradient (the output) varies too (was centered concentric frames + "
    "grid padding)."
)

INVARIANTS = [
    "2-5 nested color-1 frames, each at least 3x3",
    "frames are inset >=2 so each is a separate component",
    "the interior fills with a depth-encoded color gradient",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "single_frame", "frames_at_edges")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..22"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "8..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_frames":       {"type": "int", "default": "rng 2..5", "valid": "2..5"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "nested", "valid": "nested"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "density":        {"type": "str", "default": "frames", "valid": "frames"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_frames|single_frame|frames_at_edges"},
}


def _frame(g, r0, c0, r1, c1):
    for c in range(c0, c1 + 1):
        g[r0][c] = 1
        g[r1][c] = 1
    for r in range(r0, r1 + 1):
        g[r][c0] = 1
        g[r][c1] = 1


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        nr, fr = (9, 11), (2, 3)
    elif difficulty == "hard":
        nr, fr = (16, 22), (4, 5)
    else:
        nr, fr = (11, 16), (3, 4)

    target = rng.randint(*fr)
    min_outer = 3 + 4 * (target - 1)
    h = rng.randint(max(nr[0], min_outer), nr[1])
    w = rng.randint(max(nr[0], min_outer), nr[1])

    # Pick an outer box large enough that repeated 2-cell insets leave a
    # nonempty innermost frame.  The old randomized per-side shrink could stop
    # after two frames, then silently return a fallback 2-frame task even for
    # hard examples that had promised 4-5 nested frames.
    oh = rng.randint(min_outer, h)
    ow = rng.randint(min_outer, w)
    r0 = rng.randint(0, h - oh)
    c0 = rng.randint(0, w - ow)
    r1 = r0 + oh - 1
    c1 = c0 + ow - 1
    frames = []
    for _ in range(target):
        frames.append((r0, c0, r1, c1))
        r0 += 2; c0 += 2; r1 -= 2; c1 -= 2

    g = full_grid(h, w, 0)
    for fr0, fc0, fr1, fc1 in frames:
        _frame(g, fr0, fc0, fr1, fc1)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "no_frames":
        return g
    if name == "single_frame":
        for c in range(2, 8): g[2][c] = 1; g[7][c] = 1
        for r in range(2, 8): g[r][2] = 1; g[r][7] = 1
        return g
    if name == "frames_at_edges":
        for c in range(0, w): g[0][c] = 1; g[h - 1][c] = 1
        for r in range(0, h): g[r][0] = 1; g[r][w - 1] = 1
        return g
    return g


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 1 or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == 1:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append(cells)
    return comps


def _bbox(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _is_frame(cells):
    r0, c0, r1, c1 = _bbox(cells)
    if r1 - r0 < 2 or c1 - c0 < 2:
        return False
    expected = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                if r in (r0, r1) or c in (c0, c1)}
    return set(cells) == expected


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(v not in (0, 1) for row in grid for v in row):
        errors.append("normal input should contain only 0 background and color-1 frames")
    comps = _components(grid)
    n = len(comps)
    if difficulty == "easy":
        lo, hi = 2, 3
    elif difficulty == "hard":
        lo, hi = 4, 5
    else:
        lo, hi = 3, 4
    if not (lo <= n <= hi):
        errors.append(f"expected {lo}..{hi} nested frames, got {n}")
    boxes = []
    for cells in comps:
        if not _is_frame(cells):
            errors.append("color-1 component is not a one-cell-thick rectangular frame")
            continue
        boxes.append(_bbox(cells))
    boxes.sort(key=lambda b: (b[2] - b[0]) * (b[3] - b[1]), reverse=True)
    for outer, inner in zip(boxes, boxes[1:]):
        r0, c0, r1, c1 = outer; ir0, ic0, ir1, ic1 = inner
        if not (ir0 - r0 >= 2 and ic0 - c0 >= 2 and r1 - ir1 >= 2 and c1 - ic1 >= 2):
            errors.append("nested frames are not inset by at least two cells on every side")
    return errors

