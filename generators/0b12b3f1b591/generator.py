"""Generator for arc_puzzle_bank_nineteenth21:E131.

Rule: paint color = MAX value in row 0. Output rebuilds: every 1-cell
in rows 1+ becomes that color; EVERYTHING else (row 0, body decoys,
row-0 1s) is erased.

Combinatorial axes: grid_h/w, markers, texture
(plain|multi_legend|body_decoy|row0_one).
Degenerates: no_legend (max=0, blank output), no_markers.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0b12b3f1b591"
VERSION = "3.0.1"
TASK_ID = "0b12b3f1b591"
SUMMARY = (
    "Row-0 legend recolors the body 1s; the paint color is the MAX of "
    "row 0, so multi_legend boards with several legend cells use the "
    "largest (promoted from a mislabeled 'ambiguous' degenerate). "
    "body_decoy boards scatter non-1 colors below (erased); row0_one "
    "boards put a 1 IN row 0 (erased, not recolored - the rule only "
    "recolors rows 1+)."
)

# Rivals: 'first/only legend cell' refuted by multi_legend (max
# wins). 'non-1 body survives' refuted by body_decoy. 'all 1s
# recolor' refuted by row0_one. 3 demos.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "main-path row 0 has >=1 legend cell in 2..9",
    "multi_legend boards: >=2 row-0 values, max is the paint color",
    "body 1s present on every non-degenerate board",
]

DEGENERATE_TEXTURES = ("no_legend", "no_markers")
HELPFUL_TEXTURES = ("plain", "multi_legend", "body_decoy", "row0_one")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 4..9", "valid": "3..14"},
    "grid_w":  {"type": "int", "default": "rng 5..11", "valid": "3..16"},
    "markers": {"type": "int", "default": "rng 3..7", "valid": "1..20"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|multi_legend|body_decoy|row0_one|"
                         "no_legend|no_markers",
                "doc": "multi_legend: several row-0 colors, MAX paints; "
                       "body_decoy: non-1 body colors erased; row0_one: "
                       "a 1 in row 0 is erased, not recolored."},
}


def _mirror(g):
    h, w = len(g), len(g[0])
    color = max(g[0])
    return [[color if r > 0 and g[r][c] == 1 else 0 for c in range(w)]
            for r in range(h)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain",
                                              "multi_legend", "body_decoy",
                                              "row0_one"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 4, 6)
        w = ctx.draw_int("grid_w", 5, 8)
        target = ctx.draw_int("markers", 2, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 9, 11)
        target = ctx.draw_int("markers", 5, 8)
    else:
        h = ctx.draw_int("grid_h", 4, 9)
        w = ctx.draw_int("grid_w", 5, 11)
        target = ctx.draw_int("markers", 3, 7)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    if texture == "multi_legend":
        for c in rng.sample(range(w), min(w, rng.randint(2, 3))):
            g[0][c] = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
    else:
        g[0][rng.randrange(w)] = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
    if texture == "row0_one":
        free = [c for c in range(w) if g[0][c] == 0]
        if free:
            g[0][rng.choice(free)] = 1
    body = [(r, c) for r in range(1, h) for c in range(w)]
    rng.shuffle(body)
    for r, c in body[:target]:
        g[r][c] = 1
    if texture == "body_decoy":
        rest = [p for p in body[target:]]
        for r, c in rest[:rng.randint(2, 4)]:
            g[r][c] = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: row 0 has >=1 legend cell (value 2..9); rows 1+ have >=1
    color-1 body marker."""
    msgs = []
    h, w = len(grid), len(grid[0])
    legend = [grid[0][c] for c in range(w) if 2 <= grid[0][c] <= 9]
    if not legend:
        msgs.append("row 0 has no legend cell (value 2..9) — output would be blank")
    body_ones = [(r, c) for r in range(1, h) for c in range(w) if grid[r][c] == 1]
    if not body_ones:
        msgs.append("no color-1 marker in rows 1+ — rule has nothing to recolor")
    return msgs


def _draw_from_degenerate(name, ctx):
    """no_legend — row 0 all zero: max = 0, the 1s erase, output is
    blank. no_markers — legend only: blank body output. rng-varied."""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 4, 8)
    w = ctx.draw_int("grid_w", 5, 10)
    g = full_grid(h, w, 0)
    if name == "no_legend":
        for _ in range(rng.randint(2, 4)):
            g[rng.randint(1, h - 1)][rng.randrange(w)] = 1
        return g
    g[0][rng.randrange(w)] = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
    return g
