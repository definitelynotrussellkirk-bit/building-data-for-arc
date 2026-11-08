"""Generator for arc_puzzle_bank_sixteenth21:E106.

Each active color appears as one vertical endpoint pair to bridge.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_bridges,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_endpoints, single_endpoint, horizontal_pair.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "092f409aea2f"
VERSION = "2.0.1"
TASK_ID = "092f409aea2f"

SUMMARY = (
    "Colors with EXACTLY two same-column cells and a clean span fill "
    "vertically; 3-cell columns, blocked spans (a non-zero cell "
    "between, any color), horizontal pairs, and adjacent endpoints "
    "all stay untouched. (Was: every pair was an active clean "
    "vertical bridge - no guard was ever contested.)"
)

# Rivals: 'bridge any two same-color cells' refuted by blocked spans
# and horizontal pairs staying. 'any count works' refuted by 3-cell
# columns staying. 3 demos incl. >=1 guard case.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "each bridge color appears exactly twice",
    "the two cells for a bridge color share a column",
    "all cells between bridge endpoints are initially empty",
]

DEGENERATE_TEXTURES = ("no_endpoints", "single_endpoint", "horizontal_pair")
HELPFUL_TEXTURES = ("plain", "blocked_span", "three_cells", "adjacent")

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "4..18"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "4..18"},
    "n_bridges":      {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "texture":        {"type": "str", "default": "rng helpful",
                       "valid": "plain|blocked_span|three_cells|adjacent|"
                                "no_endpoints|single_endpoint|horizontal_pair",
                       "doc": "blocked_span: a non-zero cell between the "
                              "endpoints (column stays); three_cells: 3 "
                              "same-color cells in a column (stays); "
                              "adjacent: touching endpoints (empty span)."},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "blocked_span", "three_cells",
                        "adjacent"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        target = ctx.draw_int("n_bridges", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        target = ctx.draw_int("n_bridges", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 10)
        target = ctx.draw_int("n_bridges", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    colors = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(colors)
    reserved: set[tuple[int, int]] = set()
    placed = 0
    for color in colors:
        if placed >= target:
            break
        for _ in range(80):
            c = rng.randrange(w)
            r0 = rng.randint(0, h - 3)
            r1 = rng.randint(r0 + 2, h - 1)
            cells = {(r, c) for r in range(r0, r1 + 1)}
            if cells & reserved:
                continue
            g[r0][c] = color
            g[r1][c] = color
            reserved.update(cells)
            placed += 1
            break
    spare = [v for v in colors[target:] if v not in (0,)]
    if texture == "blocked_span" and spare:
        # a pair whose span holds a non-zero cell: the column stays
        for _ in range(80):
            c = rng.randrange(w)
            r0 = rng.randint(0, h - 4)
            r1 = rng.randint(r0 + 3, h - 1)
            cells = {(r, c) for r in range(r0, r1 + 1)}
            if cells & reserved:
                continue
            g[r0][c] = spare[0]
            g[r1][c] = spare[0]
            g[rng.randint(r0 + 1, r1 - 1)][c] = spare[1] if len(spare) > 1 else 9
            reserved.update(cells)
            break
    elif texture == "three_cells" and spare:
        for _ in range(80):
            c = rng.randrange(w)
            rows = sorted(rng.sample(range(h), 3))
            cells = {(r, c) for r in range(rows[0], rows[2] + 1)}
            if cells & reserved:
                continue
            for r in rows:
                g[r][c] = spare[0]
            reserved.update(cells)
            break
    elif texture == "adjacent" and spare:
        for _ in range(80):
            c = rng.randrange(w)
            r0 = rng.randint(0, h - 2)
            cells = {(r0, c), (r0 + 1, c)}
            if cells & reserved:
                continue
            g[r0][c] = spare[0]
            g[r0 + 1][c] = spare[0]
            reserved.update(cells)
            break
    return g


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied so each board differs.

    no_endpoints    — blank: identity.
    single_endpoint — one cell per color: identity.
    horizontal_pair — pair shares a ROW: the same-column guard fails,
                      identity.
    """
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 7, 9)
    w = ctx.draw_int("grid_w", 7, 10)
    g = full_grid(h, w, 0)
    if name == "no_endpoints":
        return g
    if name == "single_endpoint":
        for color in rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], rng.randint(2, 3)):
            g[rng.randrange(h)][rng.randrange(w)] = color
        return g
    color = rng.randint(1, 9)
    r = rng.randrange(h)
    c1, c2 = sorted(rng.sample(range(w), 2))
    g[r][c1] = color
    g[r][c2] = color
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: >=1 bridge color (exactly 2 same-column cells, span is
    clear 0s); no bridge color has adjacent endpoints (span length >=2)."""
    msgs = []
    h, w = len(grid), len(grid[0])
    from collections import defaultdict
    color_pos = defaultdict(list)
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                color_pos[grid[r][c]].append((r, c))
    bridges = []
    for color, positions in color_pos.items():
        if len(positions) != 2:
            continue
        (r1, c1), (r2, c2) = positions
        if c1 != c2:
            continue
        # Same column, span must be clear
        top, bot = (r1, r2) if r1 < r2 else (r2, r1)
        if bot - top >= 2 and all(grid[rr][c1] == 0 for rr in range(top + 1, bot)):
            bridges.append((color, top, bot, c1))
    if not bridges:
        msgs.append(
            "no valid bridge color found — rule would produce identity output "
            "(no coloring of vertical spans)"
        )
    return msgs
