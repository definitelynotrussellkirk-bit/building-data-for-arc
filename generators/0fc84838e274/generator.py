"""Generator for 18b:m124 — connect color pairs with clear elbows.

Rule: for each color appearing exactly twice, paint the elbow path
between them — provided at least one of the two L-shaped routes
doesn't cross another pair's cells.

Object-graph family: same validate-after-place tactic as m80.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: single_pair (only 1 pair → rule paints just one
elbow, no graph effect); colinear_pair (pair endpoints share row
or column → "elbow" degenerates to a straight line, both routes
identical); no_clear_elbow (every pair's both elbows pass through
another pair's cells → rule's clear-elbow precondition fails).
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0fc84838e274"
VERSION = "2.1.1"  # +self_check
TASK_ID = "0fc84838e274"

SUMMARY = (
    "0-bg grid (h×w, ~9-11 by ~10-12) with 2-3 COLOR PAIRS: each "
    "of 2-3 distinct non-zero colors appears EXACTLY 2 times as "
    "single-cell markers (not 4-adjacent), positioned NON-"
    "COLINEARLY (different rows AND different cols). For each "
    "pair, at least one of the two L-elbow routes between the "
    "two endpoints is clear of other pair-cells. Rule: for each "
    "color, find its 2 endpoints. Try both L-elbow paths (via "
    "(r1, c2) corner or (r2, c1) corner). Pick the one whose "
    "interior cells don't pass through any other pair's "
    "endpoint cells. Paint that elbow path with the pair's "
    "color. Output: each pair connected by its clear elbow."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "2-3 distinct non-zero colors, each appearing exactly 2 times",
    "endpoints non-adjacent (4-conn) and non-colinear per pair",
    "for each pair, ≥1 of 2 elbow routes is clear",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("single_pair", "colinear_pair", "no_clear_elbow")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":            {"type": "int", "default": "rng 10..12", "valid": "9..14"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "position_bias":     {"type": "str", "default": "non_colinear_pairs",
                          "valid": "non_colinear_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
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


def _line(p, q):
    if p[0] == q[0]:
        c1, c2 = sorted([p[1], q[1]])
        return [(p[0], c) for c in range(c1, c2 + 1)]
    if p[1] == q[1]:
        r1, r2 = sorted([p[0], q[0]])
        return [(r, p[1]) for r in range(r1, r2 + 1)]
    return []


def _elbow_clear(a, b, others) -> bool:
    for e in [(a[0], b[1]), (b[0], a[1])]:
        path = set(_line(a, e)) | set(_line(e, b))
        if all(p not in others for p in path):
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 10, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 11, 12)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 10, 12)
    rng = ctx.draw_rng("layout")
    n_colors = rng.randint(2, 3)
    # color 5 is the WALL/obstacle color, never a connectable pair color
    palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], n_colors)
    for _ in range(80):
        g = full_grid(h, w, 0)
        cells_by_color: dict = {}
        ok = True
        for color in palette:
            placed = []
            for _ in range(80):
                if len(placed) == 2: break
                r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                if g[r][c] != 0 or _too_close(g, r, c):
                    continue
                if placed and (placed[0][0] == r or placed[0][1] == c):
                    continue
                g[r][c] = color
                placed.append((r, c))
            if len(placed) != 2:
                ok = False; break
            cells_by_color[color] = placed
        if not ok:
            continue
        pair_cells = {p for pair in cells_by_color.values() for p in pair}
        # Add a few short 5-wall segments in empty cells (obstacles the rule
        # routes around). They go on cells not occupied by any pair endpoint.
        wall_cells: set = set()
        n_walls = rng.randint(1, 4)
        for _ in range(n_walls):
            wr = rng.randint(0, h - 1); wc = rng.randint(0, w - 1)
            length = rng.randint(2, 4)
            horiz = rng.random() < 0.5
            seg = [(wr, wc + i) if horiz else (wr + i, wc) for i in range(length)]
            if all(0 <= r < h and 0 <= c < w and g[r][c] == 0 and (r, c) not in pair_cells
                   for r, c in seg):
                for r, c in seg:
                    g[r][c] = 5
                    wall_cells.add((r, c))
        # Validate: for each pair, >=1 elbow route avoids other pair cells AND
        # all 5-walls (mirrors the canonical clear-elbow precondition).
        good = True
        for color, pair in cells_by_color.items():
            blockers = (pair_cells - set(pair)) | wall_cells
            if not _elbow_clear(pair[0], pair[1], blockers):
                good = False; break
        if good:
            cnt = Counter(v for row in g for v in row if v not in (0, 5))
            if all(v == 2 for v in cnt.values()) and len(cnt) == n_colors:
                return g
    raise ValueError(
        f"could not place {n_colors} non-colinear color-pairs with clear elbows in 80 attempts")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Every non-zero, non-5 color appears exactly twice (endpoint pairs)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    from collections import Counter
    counts = Counter(grid[r][c] for r in range(len(grid)) for c in range(len(grid[0]))
                     if grid[r][c] not in (0, 5))
    errors = []
    if not counts:
        errors.append("no endpoint-pair cells (non-{0,5}) found")
        return errors
    bad = [c for c, n in counts.items() if n != 2]
    if bad:
        errors.append(f"colors with count != 2: {sorted(bad)}")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    if name == "single_pair":
        # Only 1 color pair — graph effect collapses to a single elbow.
        g[2][2] = 1; g[7][8] = 1
        return g
    if name == "colinear_pair":
        # Pair endpoints share a row — "elbow" is a straight line, no L bend.
        g[3][1] = 1; g[3][9] = 1
        g[6][2] = 2; g[8][8] = 2
        return g
    if name == "no_clear_elbow":
        # Both elbows of each pair pass through another pair's cell.
        g[2][2] = 1; g[8][8] = 1
        g[2][8] = 2; g[8][2] = 2
        return g
    return g
