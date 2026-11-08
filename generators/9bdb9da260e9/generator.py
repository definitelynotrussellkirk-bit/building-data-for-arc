"""Generator for arc_puzzle_bank_21_set3:S3_H1 — colored legend recolors gray copies.

Rule: the top band is a color/shape legend. The lower band contains
gray copies of those shapes that should be recolored by matching the
legend shape.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_shapes,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_legend, no_targets, missing_match.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9bdb9da260e9"
VERSION = "2.1.0"  # distinct 93 / shape-locked: fixed 12x15 + 3-shape bank + fixed cols. Rule picks the separator row generically (canonical 12x12, 13x13). Vary grid size + random distinct-normalized-shape legend + gray copies below."
TASK_ID = "9bdb9da260e9"
SUMMARY = "Colored legend shapes in a top band, an all-zero separator row, then gray(5) copies below; the rule recolors each gray copy to the legend color whose normalized shape it matches. Grid size, shapes and colors vary."

INVARIANTS = [
    "one all-zero row separates legend and target bands",
    "legend shapes have distinct normalized forms and colors",
    "target shapes are gray copies of legend shapes",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_legend", "no_targets", "missing_match")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..16", "valid": "11..16"},
    "grid_w":         {"type": "int", "default": "square (= grid_h)", "valid": "11..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_shapes":       {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "position_bias":  {"type": "str", "default": "two_band_legend_with_targets",
                       "valid": "two_band_legend_with_targets"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_SHAPES = [
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 1), (2, 1)],
    [(0, 1), (1, 0), (1, 1), (1, 2)],
]


def _paint(g, top, left, cells, color):
    for r, c in cells:
        g[top + r][left + c] = color


def _normalize(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def _rand_poly(rng, k):
    """Random connected polyomino, normalized, bbox <= 3x3."""
    for _ in range(60):
        cells = [(0, 0)]; seen = {(0, 0)}
        while len(cells) < k:
            r, c = rng.choice(cells)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            if (r + dr, c + dc) not in seen:
                cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
        norm = list(_normalize(cells))
        if max(r for r, _ in norm) <= 2 and max(c for _, c in norm) <= 2:
            return norm
    return [(0, 0), (1, 0), (1, 1)]


def _place_row(g, shapes, colors, top, n):
    """Place shapes left-to-right with a 1-col gap; returns True if all fit."""
    left = 0
    for s, col in zip(shapes, colors):
        sw = max(c for _, c in s) + 1
        if left + sw > n:
            return False
        _paint(g, top, left, s, col)
        left += sw + 1
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        n = ctx.draw_int("grid_h", 11, 12); n_shapes = ctx.draw_int("n_shapes", 2, 2)
    elif difficulty == "hard":
        n = ctx.draw_int("grid_h", 13, 16); n_shapes = ctx.draw_int("n_shapes", 3, 3)
    else:
        n = ctx.draw_int("grid_h", 12, 14); n_shapes = ctx.draw_int("n_shapes", 2, 3)
    # K distinct-normalized small shapes (bbox <= 3x3) so each gray copy matches
    # exactly one legend shape.
    shapes = []; seen = set()
    for _ in range(60):
        if len(shapes) >= n_shapes:
            break
        s = _rand_poly(rng, rng.randint(3, 5))
        key = _normalize(s)
        if key not in seen:
            seen.add(key); shapes.append(s)
    n_shapes = len(shapes)
    colors = rng.sample([2, 3, 4, 6, 7, 8, 9], n_shapes)
    g = full_grid(n, n, 0)
    # Legend band at rows 1..3; gray copies at rows n-4.. ; the all-zero middle
    # is the separator the rule detects. Gray copies use a shuffled order.
    _place_row(g, shapes, colors, 1, n)
    order = list(range(n_shapes)); rng.shuffle(order)
    _place_row(g, [shapes[i] for i in order], [5] * n_shapes, n - 4, n)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 15, 0)
    if name == "no_legend":
        # gray targets but no legend → no recolor mapping
        _paint(g, 7, 2, _SHAPES[0], 5)
        _paint(g, 7, 7, _SHAPES[1], 5)
        return g
    if name == "no_targets":
        # legend present but no gray targets → rule has nothing to recolor
        _paint(g, 1, 1, _SHAPES[0], 4)
        _paint(g, 1, 6, _SHAPES[1], 6)
        return g
    if name == "missing_match":
        # target shape doesn't match any legend shape → lookup fails
        _paint(g, 1, 1, _SHAPES[0], 4)
        _paint(g, 1, 6, _SHAPES[1], 6)
        # Target is shape 2 (plus), but no legend entry for that
        _paint(g, 7, 2, _SHAPES[2], 5)
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify the two-band legend/gray-copy layout used by the recolor rule."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    msgs = []
    legend_rows = [r for r in range(h) for c in range(w) if grid[r][c] not in (0, 5)]
    target_rows = [r for r in range(h) for c in range(w) if grid[r][c] == 5]
    legend_colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] not in (0, 5)}
    if not legend_rows:
        msgs.append("no colored (non-{0,5}) legend cells found")
    if not target_rows:
        msgs.append("no gray(5) target cells found")
    if legend_rows and target_rows:
        if max(legend_rows) >= min(target_rows):
            msgs.append(
                f"legend not fully above targets: legend max row={max(legend_rows)}, "
                f"target min row={min(target_rows)}"
            )
        sep_rows = [r for r in range(max(legend_rows) + 1, min(target_rows))
                    if all(grid[r][c] == 0 for c in range(w))]
        if not sep_rows:
            msgs.append("missing all-zero separator row between legend and targets")
    expected = 2 if difficulty == "easy" else 3 if difficulty == "hard" else None
    if expected is not None and len(legend_colors) != expected:
        msgs.append(f"expected {expected} legend colors for difficulty={difficulty}, got {len(legend_colors)}")
    elif expected is None and not (2 <= len(legend_colors) <= 3):
        msgs.append(f"expected 2-3 legend colors, got {len(legend_colors)}")
    return msgs
