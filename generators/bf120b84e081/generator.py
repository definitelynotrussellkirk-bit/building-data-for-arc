"""Generator for 10b:m68 — connect matching markers with elbows.

Rule: for each color appearing exactly twice, paint an elbow path
between the two cells in that color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, single_endpoint, three_cells_per_color.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bf120b84e081"
VERSION = "2.1.1"
TASK_ID = "bf120b84e081"

SUMMARY = (
    "0-bg grid (h~8-10, w~9-11) with 2-3 distinct "
    "non-bg colors. For EACH color, EXACTLY TWO "
    "isolated single cells (the MARKERS) are placed at "
    "random non-adjacent positions (8-connectivity "
    "isolation between any two cells, so each cell is "
    "its own 4-component). Rule: for each color that "
    "appears in exactly TWO cells, treat the two cells "
    "as endpoints. PAINT an ELBOW PATH between them — "
    "an L-shaped 2-segment path going through some "
    "corner point (typically the cell at "
    "(r1, c2) or (r2, c1)) — in that color. The two "
    "endpoint cells stay. Net: each colored pair gets "
    "connected by an L-shaped path of its own color."
)

INVARIANTS = [
    "background is 0",
    "2-3 distinct non-bg colors are present",
    "each color appears in exactly 2 cells",
    "all 4-6 cells are pairwise non-adjacent (4-conn) so each is its own component",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "single_endpoint", "three_cells_per_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "isolated_marker_pairs",
                       "valid": "isolated_marker_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..3"},
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


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; each non-zero color appears exactly twice (marker pairs)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    from collections import Counter
    counts: Counter = Counter()
    for row in grid:
        for v in row:
            if v != 0:
                counts[v] += 1
    if not counts:
        errs.append("no non-zero cells found")
        return errs
    bad_colors = [c for c, n in counts.items() if n != 2]
    if bad_colors:
        errs.append(f"colors not appearing exactly twice: {sorted(bad_colors)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 8, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 12, 14)
    else:
        h = ctx.draw_int("grid_h", 7, 14)
        w = ctx.draw_int("grid_w", 8, 14)
    rng = ctx.draw_rng("layout")
    n_colors = rng.randint(2, 3)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_colors)
    for _ in range(40):
        g = full_grid(h, w, 0)
        ok = True
        for color in palette:
            placed = 0
            for _ in range(60):
                if placed == 2: break
                r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                if g[r][c] != 0 or _too_close(g, r, c):
                    continue
                g[r][c] = color
                placed += 1
            if placed != 2:
                ok = False; break
        if not ok:
            continue
        cnt = Counter(v for row in g for v in row if v != 0)
        if all(v == 2 for v in cnt.values()) and len(cnt) == n_colors:
            return g
    raise ValueError(
        f"could not place {n_colors} non-adjacent color-pairs in 40 outer attempts")


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # Empty grid — rule has no markers to connect.
        return g
    if name == "single_endpoint":
        # Color appears once — rule's "exactly two cells per
        # color" filter excludes; elbow path undefined.
        g[3][3] = 4
        return g
    if name == "three_cells_per_color":
        # Color appears three times — rule's "exactly two" filter
        # excludes; rule's connect branch never fires.
        g[2][2] = 4; g[2][6] = 4; g[5][4] = 4
        return g
    return g
