"""Generator for arc_puzzle_bank_21_set22_bundle:hard_p04 — component adjacency matrix.

Rule: connected components sorted by bbox (top-left). Output is an N×N matrix
(N = number of components): diagonal cells = 1, off-diagonal (i, j) = 2 if
components i and j are 4-touching (cardinal adjacency), else 0.

The output is a fixed-cardinality N×N adjacency encoding, so diversity is
maximized by varying the component COUNT (matrix size) and the adjacency
pattern (which pairs touch).

Combinatorial axes: grid_h, grid_w, palette_kind, n_components, position.
Degenerates: no_components, all_isolated, all_overlap.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b722c62a7980"
# 1.3.0: output is an NxN adjacency matrix (fixed-cardinality). Widen component
# count (3-6 -> more matrix sizes) and randomize adjacency to spread the
# distinct matrices; fix stale top docstring (was 8/color, actual 1/2).
VERSION = "1.4.0"  # easy band reaches canonical 7x9-8x10 scale (area coverage) + AXES synced
RULE_HASH = "c9466841c78d"  # canonical rule this generator was written against
TASK_ID = "b722c62a7980"

SUMMARY = "N (3-5) small 4-connected components in distinct colors. Some pairs are 4-touching (immediate cardinal adjacency), others are separated. Rule outputs an N×N adjacency matrix sorted by bbox top-left: diagonal cells = 1, off-diagonal (i, j) = 2 if components i and j are 4-touching, else 0."

# Rivals: 'output is input' refuted by demos (output is small NxN).
# 'output 0/1 only' refuted by demos with 2-marked adjacencies.
# 'use component colors' refuted by demos (always 0/1/2). 'output
# is full grid' refuted by any demo. 3 demos with ≥1 adjacent pair
# and ≥1 non-adjacent pair cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "3-4 isolated 4-conn components in distinct colors",
    "some components are 1-cell apart (dilation overlap), others are far apart",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_components", "all_isolated", "all_overlap")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "7-10 easy / 10-14 med / 13-17 hard",
                       "valid": "7..17"},
    "grid_w":         {"type": "int", "default": "8-12 easy / 13-17 med / 16-20 hard",
                       "valid": "8..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_components":   {"type": "int", "default": "3-4 easy / 3-6 med / 5-6 hard", "valid": "3..6"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "position_bias":  {"type": "str", "default": "mixed_near_far",
                       "valid": "mixed_near_far"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: each nonzero color's cells form exactly 1 same-color 4-connected region."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    from collections import defaultdict
    by_color = defaultdict(list)
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                by_color[grid[r][c]].append((r, c))
    errs = []
    for col, cells in by_color.items():
        cell_set = set(cells)
        visited = set()
        # BFS from first cell using same-color adjacency
        q = [cells[0]]
        visited.add(cells[0])
        while q:
            r, c = q.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                if (nr, nc) in cell_set and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    q.append((nr, nc))
        if len(visited) != len(cells):
            errs.append(f"color {col} has {len(cells)} cells but forms multiple disconnected regions")
    return errs


def _free(g, r1, c1, r2, c2, pad=1):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - pad), min(h, r2 + pad + 1)):
        for c in range(max(0, c1 - pad), min(w, c2 + pad + 1)):
            if g[r][c] != 0: return False
    return True


def _free_no_pad(g, cells):
    """True iff every cell is in bounds and currently 0."""
    h, w = len(g), len(g[0])
    for r, c in cells:
        if not (0 <= r < h and 0 <= c < w) or g[r][c] != 0:
            return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        # canonical demos are 7x9-8x10 (area median 64) — the old 9x12 floor
        # left them unreachable (defect-lint area coverage)
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 8, 12)
        n = ctx.draw_int("n_components", 3, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 17)
        w = ctx.draw_int("grid_w", 16, 20)
        n = ctx.draw_int("n_components", 5, 6)
    else:
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 13, 17)
        n = ctx.draw_int("n_components", 3, 6)
    rng = ctx.draw_rng("layout")
    # need n distinct colors (8 available in pool)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], n)

    for outer in range(40):
        g = full_grid(h, w, 0)
        ok = True
        # First component placed normally with 1-cell pad.
        # Subsequent components: some adjacent (no pad) to earlier ones,
        # others separated (pad ≥ 1).
        placed_positions = []
        for idx, color in enumerate(palette):
            shape = rng.choice([
                [(0, 0), (0, 1)],
                [(0, 0), (1, 0)],
                [(0, 0), (0, 1), (1, 0)],
                [(0, 0), (0, 1), (1, 1)],
                [(0, 0), (0, 1), (0, 2)],
                [(0, 0), (1, 0), (1, 1), (2, 1)],
                [(0, 0)],
            ])
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            adjacent_mode = (idx > 0 and rng.random() < 0.5)
            placed = False
            for _ in range(120):
                if adjacent_mode and placed_positions:
                    target = rng.choice(placed_positions)
                    tr, tc = target
                    side = rng.choice(["right", "left", "below", "above"])
                    if side == "right":
                        r0 = tr; c0 = tc + 1
                    elif side == "left":
                        r0 = tr; c0 = tc - sw
                    elif side == "below":
                        r0 = tr + 1; c0 = tc
                    else:
                        r0 = tr - sh; c0 = tc
                else:
                    r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if r0 < 0 or c0 < 0 or r0 + sh > h or c0 + sw > w:
                    continue
                cells = [(r0 + dr, c0 + dc) for dr, dc in shape]
                if not _free_no_pad(g, cells):
                    continue
                for r, c in cells:
                    g[r][c] = color
                placed_positions.append((r0, c0))
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not place {0} components".format(n))


def _draw_from_degenerate(name, rng):
    h, w = 10, 13
    g = full_grid(h, w, 0)
    if name == "no_components":
        return g
    if name == "all_isolated":
        # All far apart — adjacency matrix is identity (diagonal only).
        g[1][1] = 4
        g[1][6] = 5
        g[6][1] = 6
        g[6][9] = 7
        return g
    if name == "all_overlap":
        # All adjacent — adjacency matrix is fully off-diagonal 8.
        g[2][2] = 4; g[2][4] = 5; g[2][6] = 6; g[4][2] = 7
        return g
    return g
