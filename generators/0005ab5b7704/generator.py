"""Generator for arc_puzzle_bank_21_set5_s:S5_M3 (task 0005ab5b7704).

THE RULE (what a solver must learn to see):
  Row 0 carries color-4 (yellow) MARKERS over a proper, non-empty
  subset of columns. The output keeps only the marked columns' body
  (rows 1+) — a column-selection filter. Unmarked columns vanish.

WHAT MAKES AN INPUT TEACH THIS RULE (helpful textures):
  - markers unambiguous: color 4 never appears in the body
  - BOTH selected and unselected columns carry body content, so
    keep-vs-drop is visible in the output (enforced invariants)
  - marker count spans the full proper-subset range 1..w-2, so the
    edge cases (single survivor; all-but-one survive) are reachable
  - palette kind / color count / density vary independently, so the
    rule cannot be confused with a color- or density-based rule

WHAT HIDES IT (degenerate textures, reachable via texture=...):
  - no_markers          selection has no candidates
  - all_columns_marked  filter is trivially full (output == body)
  - no_body             markers select from emptiness

Combinatorial axes (all WIRED through ctx draws — overrides honored):
  grid_h, grid_w, palette_kind, n_selected, n_distinct_colors,
  body_density_pct, position_bias, texture.
The marker color is fixed at 4 by the rule itself and is NOT an axis.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0005ab5b7704"
VERSION = "2.1.1"
TASK_ID = "0005ab5b7704"
SUMMARY = (
    "0-bg grid (h 5-14, w 5-16): row 0 holds color-4 markers on a "
    "proper non-empty subset of columns (1..w-2 of them, placement "
    "optionally biased left/right/center); rows 1+ hold a body drawn "
    "from a palette-kind-controlled set of non-4 colors at a "
    "density-controlled rate. Rule: output = body columns under the "
    "markers, in order; unmarked columns are dropped."
)

INVARIANTS = [
    "background is 0",
    "row 0 markers are color 4 on a proper, non-empty subset of columns (helpful path)",
    "body (rows 1+) never contains color 4 — the marker is unambiguous",
    "at least one SELECTED column has a nonzero body cell (keep is visible)",
    "at least one UNSELECTED column has a nonzero body cell (drop is visible)",
]

PALETTE_KINDS = ("default", "sparse", "dense", "varied_palette")
POSITION_BIASES = ("spread", "left", "right", "center")
DEGENERATE_TEXTURES = ("no_markers", "all_columns_marked", "no_body")
HELPFUL_TEXTURES = PALETTE_KINDS

BODY_COLORS = (1, 2, 3, 5, 6, 7, 8, 9)  # everything but bg(0) and marker(4)

AXES = {
    "grid_h":            {"type": "int", "default": "rng 7..10 (easy 6..8, hard 9..14)",
                          "valid": "5..14", "doc": "Grid height incl. the marker row."},
    "grid_w":            {"type": "int", "default": "rng 8..12 (easy 6..9, hard 11..16)",
                          "valid": "5..16", "doc": "Grid width."},
    "palette_kind":      {"type": "enum", "default": "rng helpful",
                          "valid": "default|sparse|dense|varied_palette",
                          "doc": "Body palette regime: default=4-8 colors @35-55%, "
                                 "sparse=2-3 @20-30%, dense=5-8 @60-80%, "
                                 "varied_palette=2-8 random distinct colors."},
    "n_selected":        {"type": "int", "default": "rng 1..w-2 (uniform; extremes reachable)",
                          "valid": "1..14", "doc": "How many columns get a marker."},
    "n_distinct_colors": {"type": "int", "default": "rng per palette_kind",
                          "valid": "1..8", "doc": "Distinct body colors actually used."},
    "body_density_pct":  {"type": "int", "default": "rng per palette_kind",
                          "valid": "5..95", "doc": "Percent of body cells that are nonzero."},
    "position_bias":     {"type": "enum", "default": "rng",
                          "valid": "spread|left|right|center",
                          "doc": "Where markers cluster: spread (uniform), left/right/center halves."},
    "texture":           {"type": "enum", "default": "helpful",
                          "valid": "default|sparse|dense|varied_palette|no_markers|all_columns_marked|no_body",
                          "doc": "Set to a degenerate name to build a rule-hiding input."},
}


def _dims(ctx, difficulty):
    if difficulty == "easy":
        return ctx.draw_int("grid_h", 6, 8), ctx.draw_int("grid_w", 6, 9)
    if difficulty == "hard":
        return ctx.draw_int("grid_h", 9, 14), ctx.draw_int("grid_w", 11, 16)
    return ctx.draw_int("grid_h", 7, 10), ctx.draw_int("grid_w", 8, 12)


def _palette(ctx, kind):
    """Body color set + density range for the chosen palette regime."""
    if kind == "sparse":
        n = ctx.draw_int("n_distinct_colors", 2, 3)
        lo, hi = 20, 30
    elif kind == "dense":
        n = ctx.draw_int("n_distinct_colors", 5, 8)
        lo, hi = 60, 80
    elif kind == "varied_palette":
        n = ctx.draw_int("n_distinct_colors", 2, 8)
        lo, hi = 30, 65
    else:  # default
        n = ctx.draw_int("n_distinct_colors", 4, 8)
        lo, hi = 35, 55
    colors = ctx.draw_distinct_colors("body_colors", n=n, exclude={0, 4})
    density = ctx.draw_int("body_density_pct", lo, hi)
    return list(colors), density


def _marker_columns(ctx, w, n_selected, bias):
    """Choose marker columns honoring the placement bias; always a
    proper, non-empty subset so the filter has something to keep AND
    something to drop."""
    rng = ctx.draw_rng("marker_layout")
    n_selected = max(1, min(n_selected, w - 2))
    if bias == "left":
        pool = list(range(0, max(n_selected, (w + 1) // 2)))
    elif bias == "right":
        pool = list(range(min(w - n_selected, w // 2), w))
    elif bias == "center":
        span = max(n_selected, (w + 1) // 2)
        start = max(0, (w - span) // 2)
        pool = list(range(start, min(w, start + span)))
    else:  # spread
        pool = list(range(w))
    return sorted(rng.sample(pool, n_selected))


def _fill_body(g, rng, colors, density_pct):
    h = len(g)
    w = len(g[0])
    for r in range(1, h):
        for c in range(w):
            if rng.random() * 100 < density_pct:
                g[r][c] = rng.choice(colors)


def _enforce_visibility(g, rng, colors, selected):
    """Keep-vs-drop must be observable: at least one selected column and
    one unselected column each need a nonzero body cell."""
    h = len(g)
    w = len(g[0])
    unselected = [c for c in range(w) if c not in selected]

    def column_has_body(c):
        return any(g[r][c] != 0 for r in range(1, h))

    if selected and not any(column_has_body(c) for c in selected):
        g[rng.randrange(1, h)][rng.choice(selected)] = rng.choice(colors)
    if unselected and not any(column_has_body(c) for c in unselected):
        g[rng.randrange(1, h)][rng.choice(unselected)] = rng.choice(colors)


def _degenerate(ctx, name, difficulty):
    """Rule-hiding inputs — still DIVERSE (sizes, palettes, layouts vary)."""
    h, w = _dims(ctx, difficulty)
    kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    colors, density = _palette(ctx, kind)
    rng = ctx.draw_rng("degenerate_layout")
    g = full_grid(h, w, 0)
    if name == "no_markers":
        # body but zero markers: the selector has no candidates
        _fill_body(g, rng, colors, max(density, 25))
        if all(g[r][c] == 0 for r in range(1, h) for c in range(w)):
            g[rng.randrange(1, h)][rng.randrange(w)] = rng.choice(colors)
        return g
    if name == "all_columns_marked":
        # every column marked: the filter keeps everything
        for c in range(w):
            g[0][c] = 4
        _fill_body(g, rng, colors, density)
        return g
    # no_body: markers select from emptiness
    for c in _marker_columns(ctx, w, ctx.draw_int("n_selected", 1, max(1, w - 2)), "spread"):
        g[0][c] = 4
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _degenerate(ctx, texture, difficulty)

    h, w = _dims(ctx, difficulty)
    kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    colors, density = _palette(ctx, kind)
    bias = ctx.draw_choice("position_bias", POSITION_BIASES)
    # full proper-subset range: 1 marker and w-2 markers are the edge
    # cases that pin down "keep marked, drop unmarked"
    n_selected = ctx.draw_int("n_selected", 1, max(1, w - 2))
    selected = _marker_columns(ctx, w, n_selected, bias)

    g = full_grid(h, w, 0)
    for c in selected:
        g[0][c] = 4
    body_rng = ctx.draw_rng("body")
    _fill_body(g, body_rng, colors, density)
    _enforce_visibility(g, body_rng, colors, selected)
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: row-0 color-4 markers form a proper non-empty subset of columns;
    body (rows 1+) contains no color 4; both kept and dropped columns carry
    at least one nonzero body cell."""
    msgs = []
    h = len(grid)
    w = len(grid[0])
    if h < 2:
        msgs.append(f"grid height {h} < 2 (need at least a marker row and a body row)")
        return msgs
    selected = [c for c in range(w) if grid[0][c] == 4]
    unselected = [c for c in range(w) if grid[0][c] != 4]
    if not selected:
        msgs.append("row 0 has no color-4 markers")
    if not unselected:
        msgs.append("every column is marked — not a proper subset")
    # Body must not contain color 4
    body4 = [(r, c) for r in range(1, h) for c in range(w) if grid[r][c] == 4]
    if body4:
        msgs.append(f"body contains color-4 at {body4[:3]} (marker color must not bleed into body)")
    # Keep-vs-drop must be visible
    if selected and not any(grid[r][c] != 0 for c in selected for r in range(1, h)):
        msgs.append("no selected column has a nonzero body cell (keep branch invisible)")
    if unselected and not any(grid[r][c] != 0 for c in unselected for r in range(1, h)):
        msgs.append("no unselected column has a nonzero body cell (drop branch invisible)")
    return msgs
