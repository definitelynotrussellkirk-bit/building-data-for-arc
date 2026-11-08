"""Generator for arc_puzzle_bank_21_set23_bundle:medium_p03 — draw rectangles for exact color pairs.

Rule: for every non-zero color that appears exactly twice, draw the axis-aligned
bounding rectangle between the two cells in that same color. Colors with counts
other than two are ignored.  The generator keeps a few singletons/noise cells but
guarantees at least one useful two-cell color pair with distinct rows and cols,
so the rectangle branch is visible.

Degenerates: no_start/no_goal/walls_block_path are legacy texture names retained
as aliases; they now mean no exact pair / singleton-only / many-cell barrier.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "51d11dcced36"
VERSION = "1.2.1"  # require at least one proper exact-two color pair with distinct row and column
TASK_ID = "51d11dcced36"

SUMMARY = "Sparse colored cells with at least one exact-two color pair that expands to a rectangle."

INVARIANTS = [
    "background is 0",
    "at least one non-zero color appears exactly twice",
    "at least one exact-two color pair has distinct rows and columns",
    "colors with counts other than two act as distractors and are ignored",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_start", "no_goal", "walls_block_path")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":            {"type": "int", "default": "rng 11..13", "valid": "10..16"},
    "n_walls":           {"type": "int", "default": "rng 0..3", "valid": "0..5"},
    "use_portal":        {"type": "int", "default": "rng 0..1", "valid": "0..1"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "position_bias":     {"type": "str", "default": "start_goal_walls_portals",
                          "valid": "start_goal_walls_portals"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 11, 11)
        n_walls = ctx.draw_int("n_walls", 0, 1)
        use_portal = ctx.draw_int("use_portal", 0, 0)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 11)
        w = ctx.draw_int("grid_w", 13, 13)
        n_walls = ctx.draw_int("n_walls", 2, 3)
        use_portal = ctx.draw_int("use_portal", 1, 1)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 13)
        n_walls = ctx.draw_int("n_walls", 0, 3)
        use_portal = ctx.draw_int("use_portal", 0, 1)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        sr = rng.randint(0, h - 1); sc = rng.randint(0, w - 1)
        g[sr][sc] = 2
        for _ in range(120):
            gr = rng.randint(0, h - 1); gc = rng.randint(0, w - 1)
            if (gr, gc) == (sr, sc): continue
            if abs(gr - sr) + abs(gc - sc) < 4: continue
            g[gr][gc] = 3
            break
        else:
            continue
        for _ in range(n_walls):
            for _t in range(40):
                r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                if g[r][c] != 0: continue
                if abs(r - sr) + abs(c - sc) < 2: continue
                if abs(r - gr) + abs(c - gc) < 2: continue
                g[r][c] = 8
                break
        if use_portal:
            placed_p = 0
            portal_color = 4
            while placed_p < 2:
                for _t in range(40):
                    r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                    if g[r][c] != 0: continue
                    g[r][c] = portal_color
                    placed_p += 1
                    break
                else:
                    break
        return _ensure_pair(g, rng)
    raise ValueError("could not realize set19 p02 layout")


def _proper_exact_pair(cells):
    if len(cells) != 2:
        return False
    (r1, c1), (r2, c2) = cells
    return r1 != r2 and c1 != c2


def _ensure_pair(g, rng):
    """Guarantee at least one exact-two color pair spanning a proper rectangle.

    A same-row/same-column exact pair only draws a line; keep those as possible
    distractors, but ensure at least one pair has distinct rows and columns so
    the rectangle rule is exercised on every default instance.
    """
    from collections import defaultdict
    h, w = len(g), len(g[0])
    by_color: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r in range(h):
        for c in range(w):
            v = g[r][c]
            if v != 0:
                by_color[v].append((r, c))
    if any(_proper_exact_pair(cells) for cells in by_color.values()):
        return g
    color = next((c for c in (6, 5, 9, 1, 4, 7) if not by_color.get(c)), 6)
    empties = [(r, c) for r in range(h) for c in range(w) if g[r][c] == 0]
    rng.shuffle(empties)
    if not empties:
        return g
    r1, c1 = empties[0]
    pick = next(((r, c) for (r, c) in empties[1:] if r != r1 and c != c1), None)
    if pick is None:
        return g
    g[r1][c1] = color
    g[pick[0]][pick[1]] = color
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Require one exact-two color pair spanning both rows and columns."""
    from collections import defaultdict
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    by_color: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v != 0:
                by_color[v].append((r, c))
    if not any(len(cells) == 2 for cells in by_color.values()):
        return ["no colour appears exactly twice -> rule outputs an all-zero blank"]
    if not any(_proper_exact_pair(cells) for cells in by_color.values()):
        pairs = {color: cells for color, cells in by_color.items() if len(cells) == 2}
        return [f"exact-two colors exist only as same-row/same-column lines, not rectangles: {pairs}"]
    return []


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_start":
        # No color-2 — BFS source undefined.
        g[6][8] = 3
        g[3][3] = 8; g[5][5] = 8
        return g
    if name == "no_goal":
        # No color-3 — BFS target undefined.
        g[2][2] = 2
        g[5][5] = 8; g[6][7] = 8
        return g
    if name == "walls_block_path":
        # Walls form complete barrier separating start and goal —
        # BFS finds no path.
        g[2][2] = 2
        g[8][9] = 3
        for c in range(0, w):
            g[5][c] = 8
        return g
    return g
