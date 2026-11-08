"""Generator for arc_additional_puzzles_21_set10_bundle:H68 — XOR two binary panels split by 5-col.

Rule: a 5-filled column splits grid; left/right panels' non-zero
patterns are normalized to bbox crops, OR'd to 1; output = bbox-aligned
XOR painted as 7.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_separator, empty_panel, identical_panels.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0261c073ae3f"
VERSION = "1.3.2"
TASK_ID = "0261c073ae3f"
SUMMARY = (
    "Grid split by a single full color-5 column into 2 panels. Each "
    "panel holds a non-zero compact object pattern in some non-bg, non-5 "
    "color. Rule: extract left panel and right panel (as subgrids). "
    "Normalize each: crop to bbox of non-zero cells, then convert to "
    "binary mask. Take XOR of the two binary masks (aligned at (0,0), "
    "padded by 0 where dims differ). Output is the bbox-sized XOR "
    "with 7 wherever the masks differ, 0 wherever they match."
)

# Rivals: 'output is input' refuted by demos (output is small).
# 'output is AND' refuted by demos showing XOR (cells where exactly
# one panel has content). 'output is OR' refuted similarly. 'use
# panel colors (not 7)' refuted by demos showing color 7. 'output
# is left panel only' refuted. 3 demos with mixed XOR patterns pin
# the rule.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "exactly one full-height col of 5s (the separator)",
    "left panel has ≥1 non-zero cell",
    "right panel has ≥1 non-zero cell",
    "the two NORMALIZED binary patterns differ (so XOR is non-empty)",
    "left and right colors are distinct so the panels are visually distinguishable",
]

DEGENERATE_TEXTURES = ("empty_panel", "identical_panels")
HELPFUL_TEXTURES = ("plain", "off_center", "mixed_colors")
RULE_HIDING_TEXTURES = ("same_color",)

AXES = {
    "grid_h":  {"type": "int", "default": "rng 5..7 (hard 7..9)",
                "valid": "5..10", "doc": "Grid height."},
    "grid_w":  {"type": "int", "default": "rng 11..15 (hard 15..17)",
                "valid": "9..18", "doc": "Grid width."},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|off_center|mixed_colors|same_color|"
                         "empty_panel|identical_panels",
                "doc": "off_center: unequal panel widths; mixed_colors: a "
                       "panel mixes 2 colors (rule binarizes); same_color: "
                       "both panels share one color."},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "off_center", "mixed_colors"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 5)
        w = ctx.draw_int("grid_w", 11, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 15, 17)
    else:
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 11, 15)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    # the rule finds ANY full 5-column — panels need not be equal width
    if texture == "off_center":
        sep = rng.choice([3, 4, w - 5, w - 4])
    else:
        sep = w // 2 + rng.randint(-1, 1)
    sep = max(3, min(w - 4, sep))
    for r in range(h):
        g[r][sep] = 5
    pool = [2, 3, 4, 6, 7, 8]
    if texture == "same_color":
        palette_l = palette_r = rng.choice(pool)
    else:
        palette_l, palette_r = rng.sample(pool, 2)
    # Canonical demos contain one compact, connected object per side.  The
    # old sampler scattered 3-5 independent cells over each panel, inflating
    # object counts and drifting away from the task distribution while still
    # passing rule parity.
    while True:
        cells_l_local = _sample_compact_mask(rng, h, sep)
        cells_r_local = _sample_compact_mask(rng, h, w - sep - 1)
        if _norm_binary_global(cells_l_local) != _norm_binary_global(cells_r_local):
            break
    cells_l = {(r, c) for r, c in cells_l_local}
    cells_r = {(r, c + sep + 1) for r, c in cells_r_local}

    second_l = rng.choice([v for v in pool if v not in (palette_l, palette_r)])
    accent = set()
    if texture == "mixed_colors":
        top = min(r for r, _ in cells_l)
        accent = {(r, c) for r, c in cells_l if r == top}
        if len(accent) == len(cells_l):
            accent = {min(cells_l)}
    for r, c in cells_l:
        # mixed_colors: a panel mixes two colors — the rule binarizes,
        # so the XOR is unchanged by the color split.  Keep the accent
        # contiguous instead of alternating every other cell; otherwise the
        # generic object-count linter sees several artificial objects.
        g[r][c] = second_l if (r, c) in accent else palette_l
    for r, c in cells_r:
        g[r][c] = palette_r
    return g


def _normalize_local(cells):
    if not cells:
        return frozenset()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _maybe_mirror(cells, rng):
    out = set(cells)
    if rng.random() < 0.5:
        max_c = max(c for _, c in out)
        out = {(r, max_c - c) for r, c in out}
    if rng.random() < 0.5:
        max_r = max(r for r, _ in out)
        out = {(max_r - r, c) for r, c in out}
    return _normalize_local(out)


def _sample_compact_mask(rng, h, panel_w):
    """Return local panel cells for one compact connected object.

    The canonical H68 train set has two low-object-count operands plus the
    separator.  Sampling from compact templates keeps generated structure
    close to that support but still varies translation, reflection and shape.
    """
    templates = (
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
        ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
        ((0, 1), (1, 1), (2, 1), (2, 0), (2, 2)),
        ((0, 0), (0, 1), (1, 1), (2, 1), (3, 1)),
        ((0, 0), (1, 0), (1, 1), (1, 2)),
    )
    candidates = []
    for tmpl in templates:
        cells = _maybe_mirror(tmpl, rng)
        max_r = max(r for r, _ in cells)
        max_c = max(c for _, c in cells)
        if max_r < h and max_c < panel_w:
            candidates.append(cells)
    if not candidates:
        # Defensive fallback for very narrow override panels: a connected bar.
        n = max(1, min(h, 3))
        candidates.append(frozenset((r, 0) for r in range(n)))
    cells = set(rng.choice(candidates))
    height = max(r for r, _ in cells) + 1
    width = max(c for _, c in cells) + 1
    r0 = rng.randint(0, h - height)
    # Canonical objects tend to sit near the separator but not flush with it.
    slack = panel_w - width
    if slack <= 0:
        c0 = 0
    elif rng.random() < 0.65:
        c0 = max(0, slack - rng.randint(0, min(2, slack)))
    else:
        c0 = rng.randint(0, slack)
    return {(r + r0, c + c0) for r, c in cells}


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied, rule-safe (separator always
    present; no_separator was dropped: the rule crashes at (first '())
    when no full 5-column exists).

    empty_panel      — one side blank: XOR degenerates to the other mask.
    identical_panels — normalized panels match: XOR is empty.
    """
    h = ctx.draw_int("grid_h", 5, 7)
    w = ctx.draw_int("grid_w", 11, 14)
    rng = ctx.draw_rng("degenerate_layout")
    g = full_grid(h, w, 0)
    sep = w // 2
    for r in range(h):
        g[r][sep] = 5
    color_a, color_b = rng.sample([2, 3, 4, 6, 7, 8], 2)
    if name == "empty_panel":
        for _ in range(rng.randint(2, 4)):
            g[rng.randrange(h)][rng.randint(0, sep - 1)] = color_a
        return g
    # identical_panels: same normalized pattern both sides
    cells = set()
    for _ in range(rng.randint(3, 4)):
        cells.add((rng.randint(0, h - 1), rng.randint(0, min(sep - 1, 3))))
    for r, c in cells:
        g[r][c] = color_a
        if c + sep + 1 < w:
            g[r][c + sep + 1] = color_b
    return g


def _nonzero_cells(panel, col0=0):
    return {(r, c + col0) for r, row in enumerate(panel) for c, v in enumerate(row) if v != 0}


def _norm_binary_global(cells):
    if not cells:
        return frozenset()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def self_check(grid, *, difficulty=None, meta=None):
    """Executable invariants for normalized-XOR split-panel inputs."""
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    h, w = len(grid), len(grid[0])
    full_sep_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(full_sep_cols) != 1:
        errs.append("expected exactly one full-height color-5 separator column")
        return errs
    sep = full_sep_cols[0]
    if sep == 0 or sep == w - 1:
        errs.append("separator must leave non-empty panels on both sides")
        return errs

    left_cells = {(r, c) for r in range(h) for c in range(sep) if grid[r][c] not in (0, 5)}
    right_cells = {(r, c) for r in range(h) for c in range(sep + 1, w) if grid[r][c] not in (0, 5)}
    if not left_cells:
        errs.append("left panel must contain at least one non-zero non-separator cell")
    if not right_cells:
        errs.append("right panel must contain at least one non-zero non-separator cell")
    if left_cells and right_cells:
        left_norm = _norm_binary_global(left_cells)
        right_norm = _norm_binary_global(right_cells)
        if left_norm == right_norm:
            errs.append("normalized left and right binary masks must differ so XOR is non-empty")

    left_colors = {grid[r][c] for r, c in left_cells}
    right_colors = {grid[r][c] for r, c in right_cells}
    if left_colors & right_colors:
        errs.append("default panels should use disjoint non-zero colors so the two operands are visually separable")

    bad_values = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v < 0 or v > 9]
    if bad_values:
        errs.append("grid values must be digits 0..9")
    return errs
