"""Generator for arc_additional_puzzle_bank_volume3:E20.

Rule: every size-two color-6 object is recolored to 7.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors, marker.
Degenerates: no_dominoes, all_distractors, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "04676f3b2277"
VERSION = "3.0.0"
TASK_ID = "04676f3b2277"
SUMMARY = (
    "0-bg grid with 1-3 magenta(6) dominoes at random positions/"
    "orientations plus near-misses the rule must skip: longer 6-lines, "
    "single 6-cells, OTHER-color dominoes, and diagonal 6-pairs (two "
    "size-1 objects under 4-connectivity). Rule recolors exactly the "
    "size-2 color-6 components to orange(7)."
)

# Rivals: 'recolor all 6s' refuted by longer lines and singles that
# stay. 'recolor any domino' refuted by other-color dominoes that
# stay. 'diagonal pairs count' refuted (4-connectivity: they are two
# size-1 objects). 3 demos incl. >=2 near-miss kinds.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    ">=1 separated color-6 domino (gets recolored)",
    "near-misses (when present) stay: 6-lines len>=3, 6-singles, "
    "other-color dominoes, diagonal 6-pairs",
]

NEAR_MISSES = ("long_line", "single_six", "other_color_domino", "diagonal_pair")
DEGENERATE_TEXTURES = ("no_dominoes", "full_grid")
HELPFUL_TEXTURES = ("plain",) + NEAR_MISSES

AXES = {
    "grid_h":     {"type": "int", "default": "rng 8..11", "valid": "8..12"},
    "grid_w":     {"type": "int", "default": "rng 8..11", "valid": "8..12"},
    "n_dominoes": {"type": "int", "default": "rng 1..3", "valid": "1..4",
                   "doc": "Size-2 color-6 components (recolored)."},
    "texture":    {"type": "str", "default": "rng helpful",
                   "valid": "plain|long_line|single_six|other_color_domino|"
                            "diagonal_pair|no_dominoes|full_grid",
                   "doc": "Adds one near-miss of the named kind."},
}


def _free3(g, cells):
    h, w = len(g), len(g[0])
    return all(0 <= r < h and 0 <= c < w and all(
        g[rr][cc] == 0
        for rr in range(max(0, r - 1), min(h, r + 2))
        for cc in range(max(0, c - 1), min(w, c + 2)))
        for r, c in cells)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "long_line", "single_six",
                        "other_color_domino", "diagonal_pair"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 10, 12)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 8, 11)
    n = int(overrides.get("n_dominoes", ctx.draw_int("n_dominoes", 1, 3)))
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)

    placed = 0
    for _ in range(80):
        if placed >= n:
            break
        r, c = rng.randint(0, h - 2), rng.randint(0, w - 2)
        cells = [(r, c), (r, c + 1)] if rng.random() < 0.5 else [(r, c), (r + 1, c)]
        if _free3(g, cells):
            for rr, cc in cells:
                g[rr][cc] = 6
            placed += 1
    if placed == 0:
        g[1][1] = 6
        g[1][2] = 6

    # one near-miss object the rule must NOT recolor
    for _ in range(80):
        if texture == "long_line":
            r, c = rng.randint(0, h - 1), rng.randint(0, w - 4)
            cells = [(r, c + i) for i in range(rng.randint(3, 4))]
            color = 6
        elif texture == "single_six":
            cells = [(rng.randrange(h), rng.randrange(w))]
            color = 6
        elif texture == "other_color_domino":
            r, c = rng.randint(0, h - 2), rng.randint(0, w - 2)
            cells = [(r, c), (r, c + 1)] if rng.random() < 0.5 \
                else [(r, c), (r + 1, c)]
            color = rng.choice([1, 2, 3, 4, 5, 8, 9])
        elif texture == "diagonal_pair":
            r, c = rng.randint(0, h - 2), rng.randint(0, w - 2)
            cells = [(r, c), (r + 1, c + 1)]
            color = 6
        else:
            break
        if _free3(g, cells):
            for rr, cc in cells:
                g[rr][cc] = color
            break
    return g


def _components_color(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] != color:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append(cells)
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    six_comps = _components_color(grid, 6)
    if not any(len(cells) == 2 for cells in six_comps):
        errs.append("expected at least one 4-connected color-6 domino")
    return errs



def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied so each board differs.

    no_dominoes — only longer 6-lines: nothing recolors.
    full_grid   — one giant 6-component: size != 2.
    """
    rng = ctx.draw_rng("degenerate_layout")
    n = ctx.draw_int("grid_h", 8, 10)
    g = full_grid(n, n, 0)
    if name == "no_dominoes":
        for _ in range(rng.randint(1, 2)):
            r, c = rng.randint(0, n - 1), rng.randint(0, n - 4)
            for i in range(3):
                g[r][c + i] = 6
        return g
    for r in range(n):
        for c in range(n):
            g[r][c] = 6
    return g
