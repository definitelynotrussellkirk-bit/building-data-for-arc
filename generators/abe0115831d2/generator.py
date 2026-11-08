"""Generator for arc_additional_puzzle_bank_volume6:E41 — Recolor smallest 2-blob to 8.

Rule: find all 4-conn components of color 2. Sort by size ascending.
Pick the smallest (first in sorted order, tie-broken by Racket's
sort stability). Recolor its cells to color 8. Other 2-blobs stay 2.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "abe0115831d2"
VERSION = "1.3.0"
TASK_ID = "abe0115831d2"
SUMMARY = (
    "0-bg grid with N (3-5) connected color-2 components of "
    "STRICTLY DISTINCT sizes (the smallest must be unique). May "
    "include 0..1 decoration cells in other colors (e.g. color 5 in "
    "a corner). Rule: extract all color-2 components, sort by cell "
    "count ascending, take the first (smallest), recolor its cells "
    "to color 8. Other 2-blobs and decoration cells preserved."
)

# Rivals: 'output is input' refuted by demos with ≥1 smallest blob.
# 'recolor largest' refuted by demos showing smallest gets recolored.
# 'recolor every 2 to 8' refuted by demos with larger 2-blobs staying.
# 'use color 4 instead of 8' refuted. 'recolor by position (first
# top-left)' refuted by demos where size order differs from position.
# 3 demos with 3+ distinct-sized 2-blobs pin the rule.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥3 connected color-2 components",
    "STRICTLY one smallest component (unique min size, no ties)",
    "components separated by ≥1 bg cell (4-conn separation)",
    "≤1 decoration cell in a non-{0, 2, 8} color (so output is unambiguous)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_smallest", "single_blob", "no_2_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "9..18"},
    "n_blobs":        {"type": "int", "default": "rng 3..4", "valid": "3..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "2", "valid": "1..3"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "1..3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_DELTAS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _blob_of_size(rng, size, h, w):
    """Generate cells of a connected random-walk blob of exact `size` cells.

    The previous walk could give up after repeatedly sampling interior cells,
    silently returning a smaller blob.  That broke the promised distinct-size
    curriculum even when the sampled size list itself was unique.  Growing from
    the explicit frontier makes every returned blob exact.
    """
    cells = {(0, 0)}
    while len(cells) < size:
        frontier = []
        for r, c in cells:
            for dr, dc in _DELTAS4:
                p = (r + dr, c + dc)
                if p not in cells:
                    frontier.append(p)
        cells.add(rng.choice(frontier))
    minr = min(r for r, _ in cells)
    minc = min(c for _, c in cells)
    return [(r - minr, c - minc) for r, c in cells]


def _try_place(g, rng, cells, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in cells) + 1
    sw = max(c for _, c in cells) + 1
    if sh > h or sw > w:
        return False
    for _ in range(120):
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        # Check the cells AND a 1-cell margin are free.
        ok = True
        for r in range(max(0, r0 - 1), min(h, r0 + sh + 1)):
            for c in range(max(0, c0 - 1), min(w, c0 + sw + 1)):
                if g[r][c] != 0:
                    ok = False
                    break
            if not ok:
                break
        if not ok:
            continue
        for dr, dc in cells:
            g[r0 + dr][c0 + dc] = color
        return True
    return False


def _components_of_color(grid, color):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            q = [(r, c)]
            seen.add((r, c))
            cells = []
            while q:
                rr, cc = q.pop()
                cells.append((rr, cc))
                for dr, dc in _DELTAS4:
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0]:
        return ["grid is empty"]
    comps = _components_of_color(grid, 2)
    if len(comps) < 3:
        msgs.append("expected at least three connected color-2 components")
    sizes = [len(cells) for cells in comps]
    if len(set(sizes)) != len(sizes):
        msgs.append("color-2 component sizes are not strictly distinct")
    decorations = sum(1 for row in grid for v in row if v not in (0, 2))
    if decorations > 1:
        msgs.append("more than one non-0/non-2 decoration cell")
    if any(v == 8 for row in grid for v in row):
        msgs.append("input contains output color 8")
    return msgs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 12)
        n_blobs = ctx.draw_int("n_blobs", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 13, 18)
        n_blobs = ctx.draw_int("n_blobs", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 11, 14)
        n_blobs = ctx.draw_int("n_blobs", 3, 4)
    rng = ctx.draw_rng("layout")

    for _attempt in range(200):
        g = full_grid(h, w, 0)
        # Generate N strictly distinct sizes.
        sizes = sorted(rng.sample(range(1, 10), n_blobs))
        ok = True
        for size in sizes:
            placed = False
            for _ in range(20):
                blob = _blob_of_size(rng, size, h, w)
                if _try_place(g, rng, blob, 2):
                    placed = True
                    break
            if not placed:
                ok = False
                break
        if not ok:
            continue
        # Optional decoration cell.
        if rng.random() < 0.5:
            for _ in range(20):
                r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                if g[r][c] == 0:
                    g[r][c] = rng.choice([3, 4, 5, 6, 7, 9])
                    break
        if not self_check(g, difficulty=difficulty):
            return g
    raise RuntimeError("could not place distinct color-2 blobs without invariant violations")


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    if name == "tied_smallest":
        for r, c in [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2)]: g[r][c] = 2
        for r, c in [(5, 4), (6, 4)]: g[r][c] = 2
        for r, c in [(7, 8), (8, 8)]: g[r][c] = 2
        g[h - 1][w - 1] = 5
        return g
    if name == "single_blob":
        for r, c in [(3, 3), (3, 4), (4, 3), (4, 4)]: g[r][c] = 2
        g[h - 1][w - 1] = 5
        return g
    if name == "no_2_blobs":
        for r, c in [(2, 2), (4, 5), (6, 8)]:
            g[r][c] = 4
        g[h - 1][w - 1] = 5
        return g
    return g
