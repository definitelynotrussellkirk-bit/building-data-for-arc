"""Generator for c803e39c — template + layout self-tile.

Rule (re-derived):
  1. Find color-5 separator columns; expect three → four panels.
  2. Panel 1: color-1 cells form the template (bbox-cropped binary mask).
  3. Panel 2: color-2 cells form the layout (read at template's bbox size).
  4. Panel 3 row-1: color_a; Panel 4 row-1: color_b.
  5. Output is (tmpl_h² × tmpl_w²): each layout-1 cell expands to a
     template-shaped block painted color_a (template-1) / color_b
     (template-0); each layout-0 cell expands to a solid color_b block.

v1.1.0 used a fixed 6×23 grid + 3 hard-coded templates (diag/corner/bar)
all with bbox 2×2 or 1×3 → only 2 distinct output bboxes (4×4 and 1×9).
v1.2.0:
  * variable grid height (rule reads h dynamically)
  * variable panel widths sized to fit the chosen template
  * 8 templates spanning bboxes 2×2, 2×3, 3×2, 3×3, 1×3, 3×1, 1×4, 2×4
    → 7 distinct output bbox classes
  * layout is one of 5 patterns per template size, drawn uniformly
  * swatch row position varies within (1..h-2)
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4dc9d686082b"
VERSION = "1.3.2"  # fix solid-collapse: single-cell curated template/layout are 1x1-full and slip past the declared-bbox guard; redraw until non-collapsing (356 reviewer self_check caught seed27/si27). (1.3.1 pinned swatches to row 1 so the canonical (at g 1 c) read resolves color-a/color-b.)
TASK_ID = "4dc9d686082b"
SUMMARY = "Template + layout panel expand two color swatches into self-tiled output."

# Rivals: 'output is fixed 4×4' refuted by ≥2 demos with different
# template bboxes. 'swatch order doesn't matter' refuted by any demo
# (the rule assigns color_a to template-1 and color_b to template-0,
# so swapping swatches changes the output color pattern). 'ignore layout
# panel' refuted by ≥2 demos with different layouts but same template.
# 'always tile by template' refuted by ≥2 demos with different layouts.
# 4 demos covering 2 template sizes × 2 layouts cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "three full color-5 separator columns split four panels",
    "panel 1 contains a color-1 binary template (≥2 cells)",
    "panel 2 contains a color-2 layout sized to the template's bbox",
    "panels 3 and 4 each contain exactly one swatch cell on the same row",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_template", "no_layout", "full_grid",
                       "mismatched_bbox")  # layout bbox != template bbox
HELPFUL_TEXTURES = PALETTE_KINDS


# Templates keyed by (h, w). Each is a list of (dr, dc) cells, all
# relative to a (0, 0) top-left. Cells must be ≥2 and ≤ h*w cells.
_TEMPLATES = {
    (2, 2): [
        [(0, 0), (1, 1)],                    # diag
        [(0, 0), (0, 1), (1, 0)],            # corner
        [(0, 0), (1, 0), (1, 1)],            # corner-rot
        [(0, 1), (1, 0), (1, 1)],            # corner-rot2
    ],
    (1, 3): [
        [(0, 0), (0, 1), (0, 2)],            # bar
        [(0, 0), (0, 2)],                    # dots
        [(0, 1)],                            # mid-only
    ],
    (3, 1): [
        [(0, 0), (1, 0), (2, 0)],            # vbar
        [(0, 0), (2, 0)],                    # vdots
    ],
    (2, 3): [
        [(0, 0), (0, 2), (1, 1)],            # V
        [(0, 0), (1, 1), (1, 2)],            # rstep
        [(0, 0), (0, 1), (1, 1), (1, 2)],    # S
    ],
    (3, 2): [
        [(0, 0), (1, 0), (2, 1)],            # diag
        [(0, 1), (1, 0), (2, 0)],            # diag-flip
        [(0, 0), (1, 1), (2, 0)],            # zigzag
    ],
    (3, 3): [
        [(0, 0), (1, 1), (2, 2)],            # diag
        [(0, 1), (1, 0), (1, 2), (2, 1)],    # plus
        [(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)],  # X
    ],
    (1, 4): [
        [(0, 0), (0, 1), (0, 2), (0, 3)],    # full bar
        [(0, 0), (0, 3)],                    # endpoints
    ],
    (2, 4): [
        [(0, 0), (0, 3), (1, 1), (1, 2)],    # bowtie
        [(0, 0), (0, 1), (1, 2), (1, 3)],    # zigzag
    ],
}

# Layouts per (h, w) of template — each layout is a list of (dr, dc).
# Generated programmatically (any non-empty subset of [0..h)×[0..w)).
def _layouts_for(h, w):
    out = []
    # solid full
    out.append([(r, c) for r in range(h) for c in range(w)])
    # diagonal
    out.append([(i, i) for i in range(min(h, w))])
    # corners
    out.append(list({(0, 0), (h - 1, 0), (0, w - 1), (h - 1, w - 1)}))
    # top row
    out.append([(0, c) for c in range(w)])
    # left col
    out.append([(r, 0) for r in range(h)])
    # checkerboard
    cb = [(r, c) for r in range(h) for c in range(w) if (r + c) % 2 == 0]
    if cb:
        out.append(cb)
    return out


AXES = {
    "grid_h":         {"type": "int", "default": "by difficulty", "valid": "5..8"},
    "template_bbox":  {"type": "tuple", "default": "rng helpful",
                       "valid": "(2,2)|(1,3)|(3,1)|(2,3)|(3,2)|(3,3)|(1,4)|(2,4)"},
    "template_idx":   {"type": "int", "default": "rng",
                       "valid": "0..len(templates[bbox])-1"},
    "layout_idx":     {"type": "int", "default": "rng",
                       "valid": "0..len(layouts)-1"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "swatch_row":     {"type": "int", "default": "rng 1..h-2", "valid": "1..h-2"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "four_panels", "valid": "four_panels"},
    "n_distinct_colors": {"type": "int", "default": "5", "valid": "5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}




def _is_full(cells, h, w):
    return len(set(cells)) == h * w


def _avoid_solid_self_tile(template, layout, th, tw):
    """Avoid the one helpful-mode corner case that teaches a solid output.

    The rule fills every layout-1 block with a copy of the template coloured
    (a for template cells, b elsewhere).  If both the template and layout are
    full, every output cell is colour-a, which looks like a degenerate
    constant-output example rather than the intended self-tiling rule.
    """
    if _is_full(template, th, tw) and _is_full(layout, th, tw):
        # Keep the full layout, but make the template visibly two-toned.
        template = [(r, c) for (r, c) in template if not (r == th - 1 and c == tw - 1)]
    return template, layout


def _actual_dims(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    return (max(rs) - min(rs) + 1, max(cs) - min(cs) + 1)


def _collapses(template, layout):
    """Mirror self_check's solid-collapse condition on the ACTUAL rendered bbox
    (not the declared one): <2 template cells (violates the >=2-cell invariant),
    or template and layout share the same actual bbox AND both fill it -> the
    self-tile comes out a single solid colour.  A single-cell template is 1x1-full
    and slips past _avoid_solid_self_tile, which only tests the declared bbox."""
    if len(template) < 2 or not layout:
        return True
    th, tw = _actual_dims(template); lh, lw = _actual_dims(layout)
    return (th == lh and tw == lw
            and len(template) == th * tw and len(layout) == lh * lw)


def _safe_template(th, tw):
    """A >=2-cell pattern spanning the full th x tw bbox but NOT completely full,
    so it can never collapse against a full layout. Removes the first cell whose
    removal preserves the bbox (exists for any th*tw >= 3)."""
    full = [(r, c) for r in range(th) for c in range(tw)]
    for cell in full:
        rest = [x for x in full if x != cell]
        if rest and _actual_dims(rest) == (th, tw):
            return rest
    return full


def _difficulty_bboxes(difficulty):
    if difficulty == "easy":
        return [(2, 2), (1, 3), (3, 1)]
    if difficulty == "hard":
        return [(3, 3), (2, 4), (1, 4), (3, 2), (2, 3)]
    return list(_TEMPLATES.keys())


def _difficulty_grid_h(difficulty):
    if difficulty == "easy":
        return 5, 6
    if difficulty == "hard":
        return 7, 8
    return 6, 7


def _rand_pattern(rng, th, tw):
    """Random binary pattern over th x tw that touches all 4 edges (bbox = th x tw)."""
    dens = rng.uniform(0.3, 0.55)
    for _ in range(50):
        cells = {(r, c) for r in range(th) for c in range(tw) if rng.random() < dens}
        if not cells:
            continue
        if not any(r == 0 for r, _ in cells):
            cells.add((0, rng.randint(0, tw - 1)))
        if not any(r == th - 1 for r, _ in cells):
            cells.add((th - 1, rng.randint(0, tw - 1)))
        if not any(c == 0 for _, c in cells):
            cells.add((rng.randint(0, th - 1), 0))
        if not any(c == tw - 1 for _, c in cells):
            cells.add((rng.randint(0, th - 1), tw - 1))
        return sorted(cells)
    return [(r, c) for r in range(th) for c in range(tw)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    # template + layout: mix the curated bank with random patterns for the bbox.
    # (Output is a 2-colour Kronecker self-tile -> distinct is intrinsically
    # bounded ~50 for small tmpl; the bank is the designed-variety set.)
    h_lo, h_hi = _difficulty_grid_h(difficulty)
    bbox_pool = _difficulty_bboxes(difficulty)
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    bbox = rng.choice(bbox_pool)
    tmpl_h, tmpl_w = bbox
    if tmpl_h * tmpl_h > 30 or tmpl_w * tmpl_w > 30:
        bbox = (2, 2)
        tmpl_h, tmpl_w = bbox
    # Redraw until the (template, layout) pair can't collapse to a solid self-tile
    # (curated banks can yield single-cell patterns that are trivially bbox-full).
    template = layout = None
    for _attempt in range(60):
        template = rng.choice(_TEMPLATES[bbox]) if rng.random() < 0.5 else _rand_pattern(rng, tmpl_h, tmpl_w)
        layout = rng.choice(_layouts_for(tmpl_h, tmpl_w)) if rng.random() < 0.5 else _rand_pattern(rng, tmpl_h, tmpl_w)
        template, layout = _avoid_solid_self_tile(template, layout, tmpl_h, tmpl_w)
        if not _collapses(template, layout):
            break
    else:
        # Deterministic non-degenerate fallback: bbox-spanning non-full template
        # against a full layout — provably passes self_check.
        template = _safe_template(tmpl_h, tmpl_w)
        layout = [(r, c) for r in range(tmpl_h) for c in range(tmpl_w)]
    h = max(h, tmpl_h + 2)
    panel_w = max(5, tmpl_w + 2)
    total_w = 4 * panel_w + 3  # 3 separators

    color_a, color_b = ctx.draw_distinct_colors("colors", n=2, exclude={0, 1, 2, 5})

    g = full_grid(h, total_w, 0)
    # separators at columns panel_w, 2*panel_w+1, 3*panel_w+2
    sep_cols = [panel_w, 2 * panel_w + 1, 3 * panel_w + 2]
    for c in sep_cols:
        for r in range(h):
            g[r][c] = 5

    panel_starts = [0, panel_w + 1, 2 * panel_w + 2, 3 * panel_w + 3]

    # Place template in panel 1 (color 1). Center vertically and add a
    # small offset from left margin.
    p1_top = max(0, (h - tmpl_h) // 2)
    p1_left = panel_starts[0] + 1
    for dr, dc in template:
        g[p1_top + dr][p1_left + dc] = 1

    # Place layout in panel 2 (color 2). Same vertical center.
    p2_top = max(0, (h - tmpl_h) // 2)
    p2_left = panel_starts[1] + 1
    for dr, dc in layout:
        g[p2_top + dr][p2_left + dc] = 2

    # Swatches: panel 3 and 4, each with one cell. The canonical rule reads
    # them at ROW 1 only (it scans (at g 1 c)), so they MUST sit on row 1 —
    # otherwise color-a/color-b resolve to 0 and the output is solid-0.
    swatch_row = 1
    p3_left = panel_starts[2] + panel_w // 2
    p4_left = panel_starts[3] + panel_w // 2
    g[swatch_row][p3_left] = color_a
    g[swatch_row][p4_left] = color_b
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Three full color-5 separators, a color-1 template, a color-2 layout,
    and a swatch on ROW 1 in each of panels 3 and 4 (where the rule reads)."""
    h, w = len(grid), len(grid[0])
    issues = []
    sep_cols = [c for c in range(w) if grid[0][c] == 5]
    if len(sep_cols) != 3:
        issues.append(f"{len(sep_cols)} color-5 separator columns (expected 3)")
        return issues
    s1, s2, s3 = sep_cols
    tmpl = [(r, c) for r in range(h) for c in range(s1) if grid[r][c] == 1]
    layout = [(r, c) for r in range(h) for c in range(s1 + 1, s2) if grid[r][c] == 2]
    if not tmpl:
        issues.append("no color-1 template in panel 1")
    if not layout:
        issues.append("no color-2 layout in panel 2")
    if not any(grid[1][c] not in (0, 5) for c in range(s2 + 1, s3)):
        issues.append("no swatch on row 1 of panel 3")
    if not any(grid[1][c] not in (0, 5) for c in range(s3 + 1, w)):
        issues.append("no swatch on row 1 of panel 4")

    def bbox(cells):
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        return min(rs), max(rs), min(cs), max(cs)

    if tmpl and layout:
        tr0, tr1, tc0, tc1 = bbox(tmpl)
        lr0, lr1, lc0, lc1 = bbox(layout)
        th, tw = tr1 - tr0 + 1, tc1 - tc0 + 1
        lh, lw = lr1 - lr0 + 1, lc1 - lc0 + 1
        if th == lh and tw == lw and len(tmpl) == th * tw and len(layout) == lh * lw:
            issues.append("template and layout are both full-bbox; output collapses to solid swatch color")
    return issues


def _draw_from_degenerate(name, rng):
    g = full_grid(6, 23, 0)
    if name == "no_template":
        for c in (5, 11, 17):
            for r in range(6):
                g[r][c] = 5
        return g
    if name == "no_layout":
        for c in (5, 11, 17):
            for r in range(6):
                g[r][c] = 5
        g[1][1] = 1; g[2][1] = 1
        return g
    if name == "full_grid":
        for r in range(6):
            for c in range(23):
                g[r][c] = 5
        return g
    if name == "mismatched_bbox":
        # Template is 2x2 but layout is 3x3 — rule reads layout at
        # template's bbox so it drops the extras silently.
        for c in (5, 11, 17):
            for r in range(6):
                g[r][c] = 5
        g[1][1] = 1; g[2][2] = 1
        for r, c in [(1, 6), (1, 7), (1, 8), (2, 6), (2, 7), (2, 8), (3, 6), (3, 7), (3, 8)]:
            g[r][c] = 2
        g[1][13] = 3; g[1][19] = 4
        return g
    return g
