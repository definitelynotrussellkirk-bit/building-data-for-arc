"""Generator for 17b:hard_115 — overlay monotone staircases into count map.

Rule: each color with exactly 2 cells produces a staircase path
between them. Output is a per-cell count map (encoded by `s17b-encode-count`).

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, single_endpoint, no_overlap.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ca5dcbac0e83"
VERSION = "2.1.0"  # require a visible path-overlap count witness and add self_check
TASK_ID = "ca5dcbac0e83"

SUMMARY = (
    "0-bg grid (h~8-10, w~9-11) with 3-4 distinct non-zero "
    "COLORS, each appearing in exactly 2 isolated cells "
    "(8-conn non-adjacent). Rule: for each color with exactly "
    "2 cells, compute a STAIRCASE PATH between them (monotone "
    "diagonal/L-step path). Collect all path cells across all "
    "color pairs. For each output cell (r, c), encode the "
    "count of how many path cells map to (r, c) via "
    "s17b-encode-count — a per-cell count map painted with "
    "specific colors per count level."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "3-4 distinct non-bg colors are present",
    "each color appears in exactly 2 isolated single cells",
    "all cells pairwise non-adjacent",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "single_endpoint", "no_overlap")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "position_bias":  {"type": "str", "default": "isolated_color_pairs",
                       "valid": "isolated_color_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _too_close(g, r, c) -> bool:
    h, w = len(g), len(g[0])
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0:
                return True
    return False


def _stair_cells(p0, p1):
    tr, tc = p1
    r, c = p0
    acc = [(r, c)]
    while (r, c) != (tr, tc):
        r2 = r if r == tr else r + (1 if tr > r else -1)
        if r2 != r:
            acc.append((r2, c))
        c2 = c if c == tc else c + (1 if tc > c else -1)
        if c2 != c:
            acc.append((r2, c2))
        r, c = r2, c2
    return acc


def _path_counts(grid):
    by_color = {}
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v != 0:
                by_color.setdefault(v, []).append((r, c))
    counts = Counter()
    for cells in by_color.values():
        if len(cells) == 2:
            counts.update(_stair_cells(cells[0], cells[1]))
    return counts


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 11, 13)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 11)
    rng = ctx.draw_rng("layout")
    n_colors = rng.randint(3, 4)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_colors)
    for _ in range(120):
        g = full_grid(h, w, 0)
        ok = True
        for color in palette:
            placed = 0
            for _ in range(80):
                if placed == 2: break
                r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                if g[r][c] != 0 or _too_close(g, r, c): continue
                g[r][c] = color
                placed += 1
            if placed != 2: ok = False; break
        if ok:
            cnt = Counter(v for row in g for v in row if v != 0)
            if (all(v == 2 for v in cnt.values()) and len(cnt) == n_colors
                    and max(_path_counts(g).values(), default=0) >= 2):
                return g
    raise ValueError("could not place required color-pairs")


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # Empty grid — rule has no pairs to compute staircases for.
        return g
    if name == "single_endpoint":
        # Color appears once — rule's "exactly 2 cells per color"
        # filter excludes; staircase undefined.
        g[3][3] = 4
        return g
    if name == "no_overlap":
        # Multiple pairs whose staircases don't intersect — rule's
        # count map degenerates: no cells with count > 1.
        g[1][1] = 4; g[1][3] = 4
        g[7][6] = 6; g[7][8] = 6
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be a non-empty rectangle"]
    by_color = {}
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v != 0:
                by_color.setdefault(v, []).append((r, c))
    if not (3 <= len(by_color) <= 4):
        errs.append(f"expected 3-4 endpoint colors, found {len(by_color)}")
    for color, cells in by_color.items():
        if len(cells) != 2:
            errs.append(f"color {color} should have exactly two endpoints, found {len(cells)}")
    endpoints = [p for cells in by_color.values() for p in cells]
    for i, (r1, c1) in enumerate(endpoints):
        for r2, c2 in endpoints[i + 1:]:
            if max(abs(r1 - r2), abs(c1 - c2)) <= 1:
                errs.append("endpoints should be pairwise 8-neighbor isolated")
                break
    if max(_path_counts(grid).values(), default=0) < 2:
        errs.append("expected at least one overlapping staircase cell with count >= 2")
    return errs
