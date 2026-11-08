"""Generator for puzzle 1e0a9b12.

Rule: gravity-down per column. For each column c: collect non-zero
values in row order; place them at rows (h-n)..(h-1) of output column c
(stacked at bottom).

Combinatorial axes (8):
  * grid_h / grid_w        — outer canvas size
  * fg_palette_size        — distinct fg colors
  * fg_density             — fraction of non-bg cells
  * fg_layout              — random / clustered / row_band / column_band /
                             diagonal / scattered / blob
  * row_bias               — top / bottom / mid / spread
                             (where the fg cells start)
  * column_distribution    — uniform / sparse_cols / dense_cols / one_col
  * value_distribution     — same_color / per_column / random
  * caller-opt-in degenerates: all_bg, all_filled (output equals input),
                              already_at_bottom (rule no-op).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6a1a8be1f042"
VERSION = "1.1.0"
TASK_ID = "6a1a8be1f042"
SUMMARY = "Sparse cells on bg=0; rule applies gravity-down per column (stack at bottom)."

INVARIANTS = [
    "background is 0",
    "≥1 non-bg cell with at least one bg cell below it",
]

FG_LAYOUTS = ("random", "clustered", "row_band", "column_band",
              "diagonal", "scattered", "blob")
ROW_BIASES = ("top", "bottom", "mid", "spread")
COLUMN_DISTRIBUTIONS = ("uniform", "sparse_cols", "dense_cols", "one_col")
VALUE_DISTRIBUTIONS = ("same_color", "per_column", "random")
DEGENERATE_TEXTURES = ("all_bg", "all_filled", "already_at_bottom")
HELPFUL_TEXTURES = FG_LAYOUTS

AXES = {
    "grid_h":              {"type": "int", "default": "rng 4..18", "valid": "3..25"},
    "grid_w":              {"type": "int", "default": "rng 4..18", "valid": "3..25"},
    "fg_palette_size":     {"type": "int", "default": "rng 1..5", "valid": "1..9"},
    "fg_density":          {"type": "float", "default": "rng 0.15..0.4", "valid": "0..0.7"},
    "fg_layout":           {"type": "str", "default": "rng helpful",
                            "valid": "|".join(FG_LAYOUTS)},
    "row_bias":            {"type": "str", "default": "rng helpful",
                            "valid": "|".join(ROW_BIASES)},
    "column_distribution": {"type": "str", "default": "rng helpful",
                            "valid": "|".join(COLUMN_DISTRIBUTIONS)},
    "value_distribution":  {"type": "str", "default": "rng helpful",
                            "valid": "|".join(VALUE_DISTRIBUTIONS)},
    "texture":             {"type": "str", "default": "alias for fg_layout",
                            "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 4, 7
    elif difficulty == "hard":
        h_lo, h_hi = 14, 18
    else:
        h_lo, h_hi = 4, 18
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_palette = int(overrides.get("fg_palette_size",
                                  ctx.draw_int("fg_palette_size", 1, 5)))
    palette = list(ctx.draw_distinct_colors("palette", n=max(1, n_palette), exclude={0}))
    density = float(overrides.get("fg_density",
                                  ctx.draw_rng("fg_density").uniform(0.15, 0.4)))
    layout = (overrides.get("texture") or overrides.get("fg_layout")
              or ctx.draw_choice("fg_layout", list(FG_LAYOUTS)))
    row_bias = overrides.get("row_bias",
                             ctx.draw_choice("row_bias", list(ROW_BIASES)))
    col_dist = overrides.get("column_distribution",
                             ctx.draw_choice("column_distribution",
                                             list(COLUMN_DISTRIBUTIONS)))
    val_dist = overrides.get("value_distribution",
                             ctx.draw_choice("value_distribution",
                                             list(VALUE_DISTRIBUTIONS)))
    g = full_grid(h, w, 0)
    candidates = _candidates_for_bias(row_bias, h, w)
    candidates = _filter_columns(candidates, w, col_dist, rng)
    cells = _layout_cells(layout, candidates, density, rng)
    col_colors = {c: palette[c % len(palette)] for c in range(w)}
    for r, c in cells:
        if 0 <= r < h - 1 and 0 <= c < w:
            if val_dist == "same_color":
                g[r][c] = palette[0]
            elif val_dist == "per_column":
                g[r][c] = col_colors[c]
            else:
                g[r][c] = rng.choice(palette)
    if not any(g[r][c] != 0 for r in range(h - 1) for c in range(w)):
        g[0][0] = palette[0]
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """bg=0; ≥1 non-bg cell in rows 0..h-2 so gravity has visible effect."""
    errs = []
    h, w = len(grid), len(grid[0]) if grid else 0
    if not any(grid[r][c] != 0 for r in range(h - 1) for c in range(w)):
        errs.append("no non-bg cell in upper h-1 rows — gravity would be a no-op")
    return errs


def _candidates_for_bias(bias, h, w):
    if bias == "top":
        return [(r, c) for r in range(0, max(1, h // 2)) for c in range(w)]
    if bias == "bottom":
        return [(r, c) for r in range(max(0, h // 2), h - 1) for c in range(w)]
    if bias == "mid":
        m = h // 2
        return [(r, c) for r in range(max(0, m - 1), min(h - 1, m + 2))
                for c in range(w)]
    return [(r, c) for r in range(h - 1) for c in range(w)]


def _filter_columns(candidates, w, col_dist, rng):
    if col_dist == "uniform":
        return candidates
    if col_dist == "sparse_cols":
        chosen_cols = set(rng.sample(range(w), max(1, w // 3)))
        return [(r, c) for (r, c) in candidates if c in chosen_cols]
    if col_dist == "dense_cols":
        chosen_cols = set(rng.sample(range(w), max(1, w * 2 // 3)))
        return [(r, c) for (r, c) in candidates if c in chosen_cols]
    if col_dist == "one_col":
        c = rng.randint(0, w - 1)
        return [(r, c) for (r, _c) in candidates if _c == c]
    return candidates


def _layout_cells(layout, candidates, density, rng):
    if not candidates:
        return []
    n = max(1, int(len(candidates) * density))
    if layout == "clustered":
        cr, cc = rng.choice(candidates)
        candidates = sorted(candidates, key=lambda rc: abs(rc[0] - cr) + abs(rc[1] - cc))
        return candidates[:n]
    if layout == "row_band":
        rs = sorted({r for r, _ in candidates})
        if not rs: return []
        r = rng.choice(rs)
        cells = [(r, c) for (rr, c) in candidates if rr == r]
        rng.shuffle(cells)
        return cells[:n]
    if layout == "column_band":
        cs = sorted({c for _, c in candidates})
        if not cs: return []
        c = rng.choice(cs)
        cells = [(r, c) for (r, cc) in candidates if cc == c]
        rng.shuffle(cells)
        return cells[:n]
    if layout == "diagonal":
        cand_set = set(candidates)
        return [(k, k) for k in range(25) if (k, k) in cand_set][:n]
    if layout == "scattered":
        scat = [(r, c) for (r, c) in candidates if (r + c) % 2 == 0]
        rng.shuffle(scat)
        return scat[:n]
    if layout == "blob":
        cr, cc = rng.choice(candidates)
        candidates = sorted(candidates, key=lambda rc: max(abs(rc[0] - cr), abs(rc[1] - cc)))
        return candidates[:n]
    rng.shuffle(candidates)
    return candidates[:n]


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    fg = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    if name == "all_bg":
        g[0][0] = fg
        return g
    if name == "all_filled":
        for r in range(h):
            for c in range(w):
                g[r][c] = fg
        return g
    if name == "already_at_bottom":
        # All non-bg cells are already at the bottom rows — rule no-op.
        for c in range(w):
            for r in range(h - 1, h - 3, -1):
                if rng.random() < 0.5:
                    g[r][c] = fg
        # Add at least one stack-able cell to keep invariant true:
        g[0][0] = fg
        return g
    return g
