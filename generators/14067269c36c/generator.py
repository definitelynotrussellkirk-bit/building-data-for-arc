"""Generator for arc_puzzle_bank_21_set16_s:S16_M5 — crop object hit by 1-1 connector.

Rule: two color-1 cells define a span (Bresenham). Find the non-1
object whose cells intersect the span. Output is that object cropped
to its bbox, painted in 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_endpoints (fewer than 2 color-1 cells → rule's span
is undefined), no_hit_object (no non-1 object intersects the span →
rule's selector finds nothing to crop), tied_hits (≥2 non-1 objects
intersect the span → "the hit object" is ambiguous).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "14067269c36c"
# 2.1.0: reverse-diversity -- span was ALWAYS horizontal; the rule's span-cells
# handles vertical too. Now pick span orientation (H or V) per grid, doubling
# positional variety. 82 -> more distinct.
# 2.2.0: keep the hit object's input color distinct from the output color 8,
# so every normal example teaches the recolor-to-cyan operation as well as crop.
VERSION = "2.2.1"
TASK_ID = "14067269c36c"
SUMMARY = (
    "0-bg grid (h~9-12, w~10-13) with: (a) exactly TWO color-1 "
    "(blue) cells aligned horizontally or vertically — these "
    "define a SPAN (Bresenham line, but here a straight line); "
    "(b) several non-1 blobs of distinct colors. EXACTLY ONE "
    "blob has cells that intersect the span (the target); the "
    "rest are distractors. Rule: take the first non-1 object "
    "whose cells touch the span. Crop it to its bbox and recolor "
    "ALL its non-bg cells to 8 (cyan), 0 elsewhere. Output is a "
    "small grid of just the target object's silhouette in cyan."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly 2 color-1 cells aligned horiz or vert (orientation varies per grid)",
    "exactly one other blob has cells on the span (the target)",
    "≥1 distractor blob does NOT intersect the span",
    "target blob is non-empty and not the same color as 1",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_endpoints", "no_hit_object", "tied_hits")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "grid_w":            {"type": "int", "default": "rng 10..13", "valid": "8..16"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 4..4", "valid": "4..4"},
    "position_bias":     {"type": "str", "default": "1_1_span_plus_blobs",
                          "valid": "1_1_span_plus_blobs"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..4", "valid": "4..4"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _line_cells(r1, c1, r2, c2):
    if r1 == r2:
        return {(r1, c) for c in range(min(c1, c2), max(c1, c2) + 1)}
    return {(r, c1) for r in range(min(r1, r2), max(r1, r2) + 1)}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; has exactly 2 color-1 cells; has other non-1 blobs."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    ones = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    if not ones:
        return errors  # degenerate (no_endpoints) — allowed
    if len(ones) != 2:
        errors.append(f"expected exactly 2 color-1 cells, got {len(ones)}")
    others = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 1)]
    if not others:
        return errors  # degenerate (no_hit_object) — allowed
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 12)
        w = ctx.draw_int("grid_w", 13, 13)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 10, 13)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    vertical = rng.choice([False, True])  # span orientation per grid
    if vertical:
        span_col = rng.randint(2, w - 3)
        r1 = rng.randint(0, h // 3)
        r2 = rng.randint(2 * h // 3, h - 1)
        g[r1][span_col] = 1
        g[r2][span_col] = 1
        line = _line_cells(r1, span_col, r2, span_col)
        used = {(r1, span_col), (r2, span_col)}
        # anchor cells along the vertical span (between the endpoints)
        anchors = [(r, span_col) for r in range(r1 + 1, r2)]
    else:
        span_row = rng.randint(2, h - 3)
        c1 = rng.randint(0, w // 3)
        c2 = rng.randint(2 * w // 3, w - 1)
        g[span_row][c1] = 1
        g[span_row][c2] = 1
        line = _line_cells(span_row, c1, span_row, c2)
        used = {(span_row, c1), (span_row, c2)}
        anchors = [(span_row, c) for c in range(c1 + 1, c2)]
    target_color = rng.choice([2, 3, 4, 5, 6, 7, 9])  # exclude output color 8
    distractor_colors = rng.sample([c for c in [2, 3, 4, 5, 6, 7, 8, 9]
                                    if c != target_color], 2)
    palette = [target_color] + distractor_colors
    # Grow a random blob anchored on the span line (so it touches it).
    target_placed = False
    for _ in range(60):
        if not anchors:
            break
        anchor = rng.choice(anchors)
        if g[anchor[0]][anchor[1]] != 0:
            continue
        size = rng.randint(4, 8)  # larger target blobs -> more distinct silhouettes
        # Seed grow_blob from the anchor — pass used minus anchor so it can start here.
        seed_cell = anchor
        cells = {seed_cell}
        for _step in range(size - 1):
            frontier = []
            for r, c in cells:
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w
                            and (nr, nc) not in cells
                            and (nr, nc) not in used):
                        frontier.append((nr, nc))
            if not frontier:
                break
            cells.add(rng.choice(frontier))
        if len(cells) >= 3:
            for r, c in cells:
                g[r][c] = palette[0]
            used |= cells
            target_placed = True
            break
    if not target_placed:
        raise ValueError("could not place target blob touching span")
    for color in palette[1:]:
        for _ in range(40):
            blob = grow_blob(rng, h, w, used, rng.randint(2, 4), max_attempts=20)
            if blob is None:
                continue
            if blob & line:
                continue
            for r, c in blob:
                g[r][c] = color
            used |= blob
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 11, 12
    g = full_grid(h, w, 0)
    if name == "no_endpoints":
        # Only one color-1 cell — rule's span is undefined.
        g[5][2] = 1
        for r, c in [(5, 7), (5, 8), (6, 7)]: g[r][c] = 4
        return g
    if name == "no_hit_object":
        # Span exists but no non-1 object intersects it.
        g[5][1] = 1
        g[5][10] = 1
        for r, c in [(2, 5), (2, 6), (3, 5)]: g[r][c] = 4
        for r, c in [(8, 5), (8, 6), (9, 6)]: g[r][c] = 6
        return g
    if name == "tied_hits":
        # Two non-1 objects intersect the span — "the hit object" is
        # ambiguous.
        g[5][0] = 1
        g[5][11] = 1
        # both objects have cells on row 5
        g[5][3] = 4; g[6][3] = 4
        g[5][8] = 6; g[6][8] = 6
        return g
    return g
