"""Generator for arc_additional_puzzle_bank_volume21:M142.

Rule: for each color in {2,3,4}, if it has exactly 2 cells and they are
aligned (same row or same column), fill the segment between them with
that color. Other colors / counts are left unchanged.

This generator places 2-3 aligned endpoint PAIRS (one per color), each
with its line footprint reserved so the drawn lines do not cross.

Combinatorial axes: grid size, which colors are used, each pair's
orientation, length and position.
Degenerates: no_pairs, three_aligned, non_aligned_pairs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bf8e1d3e9c4c"
VERSION = "2.0.2"
TASK_ID = "bf8e1d3e9c4c"
SUMMARY = (
    "0-bg grid (size varies). 2-3 colors from {2,3,4}, each with exactly 2 "
    "ENDPOINT cells aligned in a row or column (the cells between them are "
    "empty). Rule: fill the segment between each aligned same-color pair "
    "with that color. Line footprints are reserved so they don't cross. The "
    "grid size, which colors are used, and each pair's "
    "orientation/length/position vary freely (was a fixed layout, ~13 "
    "distinct)."
)

INVARIANTS = [
    "each used color (from 2,3,4) has exactly 2 cells, aligned in a row or column",
    "the two endpoints are >=2 apart with an empty span between them",
    "line footprints are disjoint (drawn lines do not overlap)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "three_aligned", "non_aligned_pairs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "9..20"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..22"},
    "n_pairs":        {"type": "int", "default": "varies", "valid": "2..3"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "pairs_apart", "valid": "pairs_apart"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "2..3"},
    "density":        {"type": "str", "default": "pairs", "valid": "pairs"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_pairs|three_aligned|non_aligned_pairs"},
}


def _reserve(occ, cells, h, w):
    cset = set(cells)
    for (r, c) in cells:
        if not (0 <= r < h and 0 <= c < w) or occ[r][c]:
            return False
    for (r, c) in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if (rr, cc) in cset:
                    continue
                if 0 <= rr < h and 0 <= cc < w and occ[rr][cc]:
                    return False
    for (r, c) in cells:
        occ[r][c] = True
    return True


def _line_path(a, b):
    (r1, c1), (r2, c2) = a, b
    if r1 == r2:
        step = 1 if c2 >= c1 else -1
        return [(r1, c) for c in range(c1, c2 + step, step)]
    if c1 == c2:
        step = 1 if r2 >= r1 else -1
        return [(r, c1) for r in range(r1, r2 + step, step)]
    return []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify line-endpoint scenes match the executable rule assumptions."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    from collections import defaultdict
    by_color: dict = defaultdict(list)
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v != 0:
                by_color[v].append((r, c))
                if v not in {2, 3, 4}:
                    errs.append(f"unexpected color {v} at {(r, c)}")
    if not (2 <= len(by_color) <= 3):
        errs.append(f"expected 2..3 endpoint colors, got {len(by_color)}")
    used_path_cells = set()
    for color, cells in sorted(by_color.items()):
        if len(cells) != 2:
            errs.append(f"color {color} appears {len(cells)} times (expected 2)")
            continue
        (r1, c1), (r2, c2) = cells
        if r1 != r2 and c1 != c2:
            errs.append(f"color {color} endpoints not aligned")
            continue
        dist = abs(r1 - r2) + abs(c1 - c2)
        if dist < 2:
            errs.append(f"color {color} endpoints are too close")
        path = _line_path(cells[0], cells[1])
        if any(grid[r][c] != 0 and (r, c) not in cells for r, c in path[1:-1]):
            errs.append(f"color {color} span interior is not empty")
        overlap = used_path_cells & set(path)
        if overlap:
            errs.append(f"color {color} line footprint overlaps another color at {sorted(overlap)[:3]}")
        used_path_cells.update(path)
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)

    if difficulty == "easy":
        hr, wr, pr, lr = (9, 11), (9, 12), (2, 2), (3, 5)
    elif difficulty == "hard":
        hr, wr, pr, lr = (14, 20), (15, 22), (3, 3), (3, 9)
    else:
        hr, wr, pr, lr = (11, 16), (12, 18), (2, 3), (3, 7)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        colors = rng.sample([2, 3, 4], rng.randint(*pr))
        placed = 0
        for color in colors:
            for _t in range(40):
                horiz = rng.random() < 0.5
                L = rng.randint(*lr)
                if horiz:
                    if L > w:
                        continue
                    r = rng.randint(0, h - 1); c0 = rng.randint(0, w - L)
                    cells = [(r, c0 + i) for i in range(L)]
                else:
                    if L > h:
                        continue
                    c = rng.randint(0, w - 1); r0 = rng.randint(0, h - L)
                    cells = [(r0 + i, c) for i in range(L)]
                if _reserve(occ, cells, h, w):
                    g[cells[0][0]][cells[0][1]] = color
                    g[cells[-1][0]][cells[-1][1]] = color    # endpoints only
                    placed += 1
                    break
        if placed >= 2:
            return g

    # Fallback (rare): deterministic valid two-pair scene in the current grid.
    g = full_grid(h, w, 0)
    g[1][1] = 2
    g[1][4] = 2
    g[4][6] = 3
    g[7][6] = 3
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 13, 0)
    if name == "no_pairs":
        g[2][2] = 2          # single cell -> count 1, no line
        return g
    if name == "three_aligned":
        g[2][2] = 2; g[2][5] = 2; g[2][8] = 2   # count 3 -> unchanged
        return g
    if name == "non_aligned_pairs":
        g[2][2] = 3; g[5][7] = 3                 # not aligned -> unchanged
        return g
    return g
