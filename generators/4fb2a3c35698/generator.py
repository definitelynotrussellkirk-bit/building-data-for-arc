"""Generator for arc_additional_puzzle_bank_volume6:M36.

Rule: top two rows define color substitutions that apply only to rows 2
and below.

Combinatorial axes (8): grid_h, grid_w, palette_kind, pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_mapping_rows, mapping_self_loop, no_body.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.blobs import grow_blob
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4fb2a3c35698"
VERSION = "2.1.0"
TASK_ID = "4fb2a3c35698"
SUMMARY = (
    "0-bg grid (h~7-10, w~7-10) with: "
    "(a) ROW 0 SRC COLORS — at columns "
    "0..n-1 (n=3-5 pairs), row 0 holds "
    "SOURCE colors drawn from a palette "
    "of n+1 distinct non-0 values; "
    "(b) ROW 1 DST COLORS — at the same "
    "columns, row 1 holds TARGET "
    "colors (each colors[(c+1) % "
    "len(palette)] cyclically — paired "
    "src→dst mapping); (c) BODY rows "
    "2..h-1 — contain several separated "
    "small objects/line-like blobs in the "
    "SOURCE colors from the palette[:n] "
    "mapping domain, with every source "
    "color represented at least once. Rule "
    "(APPLY THE TOP-"
    "2-ROW COLOR SUBSTITUTION MAP ONLY "
    "TO ROWS 2 AND BELOW): READ row 0 "
    "and row 1 to build a SRC→DST MAP "
    "{g[0][c] → g[1][c] for c with "
    "non-0 g[0][c]}. For EACH cell in "
    "ROWS 2..h-1: if the cell's value "
    "is a SRC in the map, REPLACE it "
    "with the corresponding DST. "
    "Cells with non-mapped values stay. "
    "Rows 0 and 1 (the legend) stay "
    "unchanged. Net: the body is "
    "recolored by the top-2 legend."
)

INVARIANTS = [
    "mapping columns have nonzero source and destination colors",
    "body rows contain source colors to be replaced",
    "body content is object-like, not random dense speckle",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_mapping_rows", "mapping_self_loop", "no_body")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "pairs":          {"type": "int", "default": "rng 3..5", "valid": "1..8"},
    "body_objects":   {"type": "int", "default": "rng 4..7", "valid": "1..9"},
    "palette_size":   {"type": "int", "default": "rng 4..6", "valid": "2..9"},
    "position_bias":  {"type": "str", "default": "header_then_body",
                       "valid": "header_then_body"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..6", "valid": "2..9"},
    "density":        {"type": "str", "default": "sparse_object_body", "valid": "sparse_object_body"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: mapping rows are present and the body is object-like.

    The old generator filled ~65% of the body independently, producing many
    tiny disconnected components unlike the canonical object-recoloring task.
    Keep a bounded component count so runtime lint catches a regression back
    to random speckle.
    """
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if h < 3:
        errs.append(f"grid too short: need rows 0(src)+1(dst)+body, got h={h}")
        return errs
    # Count non-zero mapping columns
    n_src = sum(1 for c in range(w) if grid[0][c] != 0)
    if n_src < 2:
        errs.append(f"row 0 has <2 non-zero src colors (got {n_src})")
    # Row 1 should have matching non-zero at same columns
    n_dst = sum(1 for c in range(w) if grid[0][c] != 0 and grid[1][c] != 0)
    if n_dst < 2:
        errs.append(f"row 1 has <2 non-zero dst colors matching row 0 src positions (got {n_dst})")
    # Body should have >=1 source color
    src_colors = {grid[0][c] for c in range(w) if grid[0][c] != 0}
    has_body = any(grid[r][c] in src_colors for r in range(2, h) for c in range(w))
    if not has_body:
        errs.append("body (rows 2+) has no cells matching src colors from row 0")
    comps = _body_components(grid, src_colors)
    if len(comps) < 3:
        errs.append(f"body has too few source-color objects ({len(comps)})")
    if len(comps) > 12:
        errs.append(f"body has too many disconnected objects ({len(comps)}), looks like speckle")
    return errs


def _body_components(grid, colors):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(2, h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] not in colors:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (2 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        n = min(ctx.draw_int("pairs", 3, 3), w)
        n_objects = ctx.draw_int("body_objects", 4, 5)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        n = min(ctx.draw_int("pairs", 4, 5), w)
        n_objects = ctx.draw_int("body_objects", 6, 8)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 10)
        n = min(ctx.draw_int("pairs", 3, 5), w)
        n_objects = ctx.draw_int("body_objects", 5, 7)
    rng = ctx.draw_rng("layout")
    colors = list(ctx.draw_distinct_colors("colors", n=n + 1, exclude=[0]))
    g = full_grid(h, w, 0)
    legend_cols = sorted(rng.sample(range(w), n))
    for c, col in zip(legend_cols, range(n)):
        g[0][c] = colors[col]
        g[1][c] = colors[(col + 1) % len(colors)]

    # Body: object-level colored components, matching the canonical examples
    # (small blobs/segments to recolor) instead of high-density independent
    # Bernoulli speckle.  Work in body-local rows so grow_blob never paints
    # into the two legend rows.
    used: set[tuple[int, int]] = set()
    body_h = h - 2
    object_colors = [colors[i % n] for i in range(max(n, n_objects))]
    rng.shuffle(object_colors)
    placed = 0
    for color in object_colors[:n_objects]:
        size = rng.randint(2, 5)
        blob = grow_blob(rng, body_h, w, used, size, max_attempts=100)
        if blob is None:
            continue
        used |= blob
        for br, c in blob:
            g[2 + br][c] = color
        placed += 1
    if placed < 3:
        # Deterministic fallback with three separated motifs and all mapping
        # rows still intact.
        for br, c, color in ((0, 0, colors[0]), (body_h // 2, w // 2, colors[1 % n]),
                             (body_h - 1, w - 2, colors[2 % n])):
            for dc in (0, 1):
                cc = max(0, min(w - 1, c + dc))
                g[2 + br][cc] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_mapping_rows":
        # body content but no top-2-row mapping → rule has no substitutions defined
        for r in range(2, h):
            for c in range(w):
                if (r + c) % 2: g[r][c] = 4
        return g
    if name == "mapping_self_loop":
        # mapping has src == dst for every column → rule is identity on body
        for c in range(3):
            g[0][c] = 4 + c
            g[1][c] = 4 + c
        for r in range(2, h):
            for c in range(w):
                if (r + c) % 2: g[r][c] = 4 + (c % 3)
        return g
    if name == "no_body":
        # mapping rows present but body is empty → rule has nothing to substitute in
        for c in range(3):
            g[0][c] = 4 + c
            g[1][c] = 5 + c
        return g
    return g
