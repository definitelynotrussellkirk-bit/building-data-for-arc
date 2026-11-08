"""Generator for puzzle a699fb00.

Rule: for each row, find positions of 1s (blue dots). If ≥2 dots,
paint each bg(0) cell strictly between leftmost and rightmost dot
with 2 (red). Other cells unchanged.

Combinatorial axes (8):
  * grid_h / grid_w        — outer canvas size
  * n_rows_with_dots       — how many rows get the fill treatment
  * dots_per_row_dist      — sparse_2 / cluster_3plus / dense_5plus / mixed
  * dot_layout_per_row     — endpoints / scattered / regular_spacing /
                             triple_anchors
  * gap_between_endpoints  — controls span of the fill (small / medium / large)
  * row_distribution       — top_only / bottom_only / spread / alternating
  * decoy_palette_size     — non-1 non-2 cells in non-trigger rows
  * caller-opt-in degenerates: no_dots, single_dot_per_row,
                              dots_at_adjacent_cells (no fill).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "955305c16146"
VERSION = "2.0.0"
TASK_ID = "955305c16146"
SUMMARY = (
    "0-bg grid (h, w~4-18) with "
    "n_rows_with_dots active rows "
    "containing COLOR-1 (blue) "
    "DOTS in one of 4 LAYOUTS "
    "(endpoints / scattered / "
    "regular_spacing / "
    "triple_anchors), with "
    "DOT_COUNT distribution "
    "sparse_2/cluster_3plus/"
    "dense_5plus/mixed. Row "
    "distribution: top_only/"
    "bottom_only/spread/"
    "alternating/all_rows. Plus "
    "optional 0-3 DECOY COLORS in "
    "non-trigger rows. At least "
    "one row has ≥2 dots with bg "
    "between them. Rule (PAINT "
    "RED BETWEEN BLUE DOTS PER "
    "ROW): for EACH ROW, find "
    "the COLUMNS of all COLOR-1 "
    "cells. If ≥2 dots, find "
    "LEFTMOST and RIGHTMOST. "
    "PAINT every BG (0) CELL "
    "strictly BETWEEN them in "
    "that row with COLOR 2 (red). "
    "Rows with <2 dots stay. "
    "Decoys (non-1) cells stay. "
    "Net: each row with ≥2 blue "
    "dots fills its bg span "
    "between leftmost and "
    "rightmost dots with red."
)

INVARIANTS = [
    "bg = 0",
    "≥1 row has ≥2 blue(1) cells with at least one bg cell between them",
]

DOTS_PER_ROW_DISTS = ("sparse_2", "cluster_3plus", "dense_5plus", "mixed")
DOT_LAYOUTS = ("endpoints", "scattered", "regular_spacing", "triple_anchors")
ROW_DISTRIBUTIONS = ("top_only", "bottom_only", "spread", "alternating", "all_rows")
DEGENERATE_TEXTURES = ("no_dots", "single_dot_per_row", "adjacent_dots_only")
HELPFUL_TEXTURES = DOT_LAYOUTS

AXES = {
    "grid_h":               {"type": "int", "default": "rng 4..18", "valid": "3..25"},
    "grid_w":               {"type": "int", "default": "rng 5..18", "valid": "4..25"},
    "n_rows_with_dots":     {"type": "int", "default": "rng 1..h/2", "valid": "1..h"},
    "dots_per_row_dist":    {"type": "str", "default": "rng helpful",
                             "valid": "|".join(DOTS_PER_ROW_DISTS)},
    "dot_layout":           {"type": "str", "default": "rng helpful",
                             "valid": "|".join(DOT_LAYOUTS)},
    "gap_size":             {"type": "str", "default": "rng small|medium|large",
                             "valid": "small|medium|large"},
    "row_distribution":     {"type": "str", "default": "rng helpful",
                             "valid": "|".join(ROW_DISTRIBUTIONS)},
    "decoy_palette_size":   {"type": "int", "default": "rng 0..3", "valid": "0..6"},
    "texture":              {"type": "str", "default": "alias for dot_layout",
                             "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 4, 7, 5, 8
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 14, 18, 14, 18
    else:
        h_lo, h_hi, w_lo, w_hi = 4, 18, 5, 18
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_rows = int(overrides.get("n_rows_with_dots",
                               ctx.draw_int("n_rows_with_dots", 1, max(1, h // 2))))
    n_rows = max(1, min(h, n_rows))
    dots_dist = overrides.get("dots_per_row_dist",
                              ctx.draw_choice("dots_per_row_dist", list(DOTS_PER_ROW_DISTS)))
    layout = (overrides.get("texture") or overrides.get("dot_layout")
              or ctx.draw_choice("dot_layout", list(DOT_LAYOUTS)))
    gap = overrides.get("gap_size",
                        ctx.draw_choice("gap_size", ["small", "medium", "large"]))
    row_dist = overrides.get("row_distribution",
                             ctx.draw_choice("row_distribution", list(ROW_DISTRIBUTIONS)))
    n_decoy = int(overrides.get("decoy_palette_size",
                                ctx.draw_int("decoy_palette_size", 0, 3)))
    decoy_palette = [c for c in range(3, 10)]
    rng.shuffle(decoy_palette)
    decoy_palette = decoy_palette[:max(0, n_decoy)]
    g = full_grid(h, w, 0)
    target_rows = _select_rows(row_dist, h, n_rows, rng)
    for r in target_rows:
        n_dots = _pick_dot_count(dots_dist, w, rng)
        positions = _dot_positions(layout, w, n_dots, gap, rng)
        for c in positions:
            g[r][c] = 1
    if decoy_palette:
        for r in range(h):
            if r in target_rows:
                continue
            for c in range(w):
                if rng.random() < 0.15:
                    g[r][c] = rng.choice(decoy_palette)
    # Ensure ≥1 valid trigger row. If the row previously held decoys, clear it
    # first so the teaching row is an unambiguous blue-dot span with a bg gap.
    if not _has_valid_trigger(g):
        g[0] = [0] * w
        g[0][0] = 1
        g[0][w - 1] = 1
    return g


def _select_rows(dist, h, n, rng):
    if dist == "top_only":
        return list(range(min(h, n)))
    if dist == "bottom_only":
        return list(range(max(0, h - n), h))
    if dist == "alternating":
        return list(range(0, h, 2))[:n]
    if dist == "all_rows":
        return list(range(h))
    rows = list(range(h))
    rng.shuffle(rows)
    return rows[:n]


def _pick_dot_count(dist, w, rng):
    max_dots = max(2, w // 2)
    if dist == "sparse_2":
        return 2
    if dist == "cluster_3plus":
        return rng.randint(3, max(3, max_dots // 2))
    if dist == "dense_5plus":
        return min(max_dots, rng.randint(5, max(5, max_dots)))
    return rng.randint(2, max_dots)


def _dot_positions(layout, w, n, gap, rng):
    n = max(2, n)
    if layout == "endpoints":
        # Just first and last positions in a sub-range.
        left = rng.randint(0, max(0, w // 4))
        right = rng.randint(max(left + 2, w * 3 // 4), w - 1)
        positions = [left, right]
        if n > 2:
            for _ in range(n - 2):
                positions.append(rng.randint(left + 1, max(left + 1, right - 1)))
        return positions
    if layout == "scattered":
        return rng.sample(range(w), min(n, w))
    if layout == "regular_spacing":
        gap_size = {"small": 2, "medium": 3, "large": 4}.get(gap, 2)
        positions = list(range(0, w, gap_size))[:n]
        if len(positions) < 2:
            positions = [0, w - 1]
        return positions
    if layout == "triple_anchors":
        return [0, w // 2, w - 1] + rng.sample(range(1, w - 1),
                                                min(max(0, n - 3), w - 2))
    return sorted(rng.sample(range(w), min(n, w)))


def _has_valid_trigger(g):
    # The rule fills bg (0) cells STRICTLY BETWEEN the first and last blue dot
    # with red. A row only teaches that if such a bg gap actually exists -- an
    # all-blue or decoy-filled span between endpoints fills nothing. (The old
    # `ones[-1]-ones[0] >= 2` span check let those no-op rows pass.)
    h = len(g); w = len(g[0])
    for r in range(h):
        ones = [c for c in range(w) if g[r][c] == 1]
        if len(ones) >= 2 and any(g[r][c] == 0
                                  for c in range(ones[0] + 1, ones[-1])):
            return True
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    has_trigger = False
    for row in grid:
        if any(v not in range(10) for v in row):
            errors.append("grid values must be digits 0..9")
        if 2 in row:
            errors.append("input must not already contain output fill color 2")
        ones = [c for c, v in enumerate(row) if v == 1]
        if ones:
            if any(v not in (0, 1) for v in row):
                errors.append("rows containing blue dots should not contain decoy colors")
            if len(ones) >= 2 and any(row[c] == 0 for c in range(ones[0] + 1, ones[-1])):
                has_trigger = True
    if not has_trigger:
        errors.append("expected >=1 row with >=2 blue dots and a bg gap between endpoints")
    return errors


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "no_dots":
        # No 1s in input — rule is no-op.
        # Add some non-1 decoys.
        for r in range(h):
            for c in range(w):
                if rng.random() < 0.2:
                    g[r][c] = rng.choice([3, 4, 5, 6, 7, 8, 9])
        return g
    if name == "single_dot_per_row":
        for r in range(h):
            g[r][rng.randint(0, w - 1)] = 1
        return g
    if name == "adjacent_dots_only":
        # Rows with 2+ dots but adjacent — no bg between → no fill.
        for r in range(h):
            if rng.random() < 0.5:
                c = rng.randint(0, w - 2)
                g[r][c] = 1
                g[r][c + 1] = 1
        return g
    return g
