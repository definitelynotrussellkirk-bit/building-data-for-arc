"""Generator for arc_puzzle_bank_seventeenth21:M113 — recolor from 2-row legend.

Rule: top 2 rows hold (src, dst) pairs at the same column. Below row 1,
each non-zero cell with value v becomes dst if v matches some src.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_legend, no_content, content_color_not_in_legend.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "0cf12bd584ef"
VERSION = "3.0.0"  # diversity: variable n_pairs (1..4) + multiple varied body blobs (was fixed 2 pairs / 2 blobs)
TASK_ID = "0cf12bd584ef"
SUMMARY = (
    "0-bg grid (h ∈ 7-9, w ∈ 8-10) "
    "with: (a) A 2-ROW LEGEND at "
    "TOP — for each of 2 DISTINCT "
    "COLUMNS (cols sorted, drawn from "
    "range(w)): row 0 holds a SRC "
    "color, row 1 holds the matching "
    "DST color. The 4 colors (src1, "
    "dst1, src2, dst2) are drawn "
    "distinct from {2..9}; (b) BELOW "
    "ROW 1 (row 2 is buffer): TWO "
    "BLOBS, each in one of the SRC "
    "colors (src1 or src2), built "
    "via grow_blob of 2-3 cells, "
    "placed at non-overlapping "
    "interior positions. Rule (READ "
    "THE 2-ROW LEGEND TO BUILD A "
    "RECOLOR MAP SRC→DST; FOR EACH "
    "NON-BG BODY CELL (R ≥ 2) WITH "
    "COLOR V: IF V IS A SRC: PAINT "
    "g[R][C] = MAP[V]; ELSE: KEEP "
    "AS-IS): PARSE the top 2 rows "
    "to build (src1→dst1, "
    "src2→dst2) map. For EACH cell "
    "(r, c) below row 1: IF g[r][c] "
    "∈ map: PAINT g[r][c] = "
    "map[g[r][c]]. Legend rows "
    "preserved (or per demos, "
    "zeroed). Net: src-colored "
    "blobs are recolored to their "
    "corresponding dst colors per "
    "the legend."
)

INVARIANTS = [
    "background is 0",
    "row 0 has 2 distinct src colors at 2 distinct cols",
    "row 1 has 2 dst colors at the same cols",
    "below row 1: blobs in src colors (so legend remap is non-trivial)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_legend", "no_content", "content_color_not_in_legend")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "6..12"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_pairs":        {"type": "int", "default": "rng 1..4", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "2*n_pairs", "valid": "2..8"},
    "position_bias":  {"type": "str", "default": "two_row_legend_top",
                       "valid": "two_row_legend_top"},
    "n_distinct_colors": {"type": "int", "default": "2*n_pairs", "valid": "2..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_legend|no_content|content_color_not_in_legend"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 9)
        n_pairs = ctx.draw_int("n_pairs", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 10, 13)
        n_pairs = ctx.draw_int("n_pairs", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 8, 12)
        n_pairs = ctx.draw_int("n_pairs", 1, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)

    # Legend: n_pairs (src,dst) columns. 2*n_pairs distinct colors, capped to
    # the available width.
    n_pairs = max(1, min(n_pairs, w, 4))
    pal = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], min(2 * n_pairs, 8))
    pairs = [(pal[2 * i], pal[2 * i + 1]) for i in range(len(pal) // 2)]
    n_pairs = len(pairs)
    cols = sorted(rng.sample(range(w), n_pairs))
    srcs = []
    for (src, dst), c in zip(pairs, cols):
        g[0][c] = src
        g[1][c] = dst
        srcs.append(src)

    # Reserve the full legend rows plus one buffer row.  The old generator only
    # marked the populated legend cells as used, so grow_blob could place body
    # cells into row 0/1 at other columns, corrupting the two-row legend.
    used = {(r, c) for r in (0, 1, 2) for c in range(w)}

    # Body: several blobs in src colors (so the legend remap is non-trivial),
    # varied count and size. Each blob is its own color from srcs.
    n_blobs = rng.randint(n_pairs, max(n_pairs, n_pairs + 2))
    placed_body = 0
    for _ in range(n_blobs):
        src = rng.choice(srcs)
        cells = grow_blob(rng, h, w, used, rng.randint(1, 4), max_attempts=120)
        if cells:
            for r, c in cells:
                g[r][c] = src
            used |= cells
            placed_body += len(cells)
    if placed_body == 0:
        # Fail constructive, not silent: one source-colored body cell is enough
        # to make the legend remap non-trivial, and the rule will recolor it.
        for r in range(3, h):
            for c in range(w):
                if g[r][c] == 0:
                    g[r][c] = srcs[0]
                    return g
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 8
    g = full_grid(h, w, 0)
    if name == "no_legend":
        # content but no top-row src/dst pairs → no remap dictionary
        for r, c in [(4, 2), (4, 3), (5, 3)]: g[r][c] = 4
        return g
    if name == "no_content":
        # only legend, no content below row 1 → identity output
        g[0][1] = 4; g[1][1] = 6
        g[0][5] = 7; g[1][5] = 8
        return g
    if name == "content_color_not_in_legend":
        # content uses a color not declared in legend → no remap applies
        g[0][1] = 4; g[1][1] = 6
        g[0][5] = 7; g[1][5] = 8
        for r, c in [(4, 2), (4, 3), (5, 3)]: g[r][c] = 9  # 9 not in legend
        return g
    return g



def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if h < 4 or w < 2:
        msgs.append("grid too small for legend plus body")
    legend_cols = [c for c in range(w) if grid[0][c] != 0 or grid[1][c] != 0]
    if not legend_cols:
        msgs.append("missing two-row legend")
        return msgs
    srcs = []
    dsts = []
    for c in legend_cols:
        src, dst = grid[0][c], grid[1][c]
        if src == 0 or dst == 0:
            msgs.append("legend column is only half populated")
            break
        if src == dst:
            msgs.append("legend src maps to itself")
            break
        srcs.append(src); dsts.append(dst)
    if len(srcs) != len(set(srcs)):
        msgs.append("legend source colors are not distinct")
    if set(srcs) & set(dsts):
        msgs.append("legend src/dst palettes overlap")
    if not any(grid[r][c] in set(srcs) for r in range(2, h) for c in range(w)):
        msgs.append("no body cell uses a legend source color")
    if any(grid[r][c] != 0 for r in (0, 1) for c in range(w) if c not in legend_cols):
        msgs.append("non-legend color leaked into legend rows")
    return msgs
