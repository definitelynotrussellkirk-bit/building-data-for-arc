"""Generator for puzzle 253bf280.

Rule: bg=0. Cells between two 8s in same column → 3. Same for rows.

Combinatorial axes (8): grid_h/w, n_col_pairs, n_row_pairs, gap_size,
position_bias, decoy_density, palette_size, anchor_endpoints.
Degenerates: no_pairs, all_columns_paired, single_pair.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c144d11bf38c"
VERSION = "1.1.1"
TASK_ID = "c144d11bf38c"
SUMMARY = "Cyan dots; rule fills between 2 cyans in same col/row with green."

INVARIANTS = [
    "background is 0",
    ">=1 column has exactly 2 cyan(8) cells with bg gap >=1 between",
    "no color 3 in input (rule writes 3 for output)",
    "for column pairs: each column has at most 2 cyan cells",
]

POSITION_BIAS = ("center", "spread", "edge")
DEGENERATE_TEXTURES = ("no_pairs", "all_columns_paired", "single_pair")
HELPFUL_TEXTURES = POSITION_BIAS

AXES = {
    "grid_h":           {"type": "int", "default": "rng 6..16", "valid": "5..22"},
    "grid_w":           {"type": "int", "default": "rng 6..16", "valid": "5..22"},
    "n_col_pairs":      {"type": "int", "default": "rng 1..3", "valid": "0..6"},
    "n_row_pairs":      {"type": "int", "default": "rng 0..2", "valid": "0..4"},
    "gap_size":         {"type": "int", "default": "rng 2..5", "valid": "1..10"},
    "position_bias":    {"type": "str", "default": "rng helpful",
                         "valid": "|".join(POSITION_BIAS)},
    "edge_avoidance":   {"type": "bool", "default": "false",
                         "valid": "true|false"},
    "anchor_endpoints": {"type": "bool", "default": "false",
                         "valid": "true|false"},
    "texture":          {"type": "str", "default": "alias for position_bias",
                         "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; has cyan (8) cells; no color-3 in input (rule writes 3)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    cyans = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    greens = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    if not cyans:
        errs.append("no cyan (color 8) cells found")
    if greens:
        errs.append(f"color 3 already present in input ({len(greens)} cells) — rule writes 3")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 5, 8
    elif difficulty == "hard":
        h_lo, h_hi = 14, 22
    else:
        h_lo, h_hi = 6, 16
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_col_pairs = int(overrides.get("n_col_pairs",
                                    ctx.draw_int("n_col_pairs", 1, 3)))
    n_row_pairs = int(overrides.get("n_row_pairs",
                                    ctx.draw_int("n_row_pairs", 0, 2)))
    n_col_pairs = max(1, min(w, n_col_pairs))
    n_row_pairs = max(0, min(h, n_row_pairs))
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias", list(POSITION_BIAS)))
    gap_size = int(overrides.get("gap_size",
                                 ctx.draw_int("gap_size", 2, 5)))
    g = full_grid(h, w, 0)
    cols = _pick_cols(bias, w, n_col_pairs, rng)
    for c in cols:
        r1, r2 = _pair_rows(bias, h, gap_size, rng)
        if r2 - r1 < 2:
            r1, r2 = 0, h - 1
        g[r1][c] = 8
        g[r2][c] = 8
    rows_for_row_pairs = _pick_rows(bias, h, n_row_pairs, rng,
                                    exclude=set())
    for r in rows_for_row_pairs:
        c1, c2 = _pair_cols(bias, w, gap_size, rng)
        if c2 - c1 < 2:
            c1, c2 = 0, w - 1
        # Avoid creating a 3rd 8 in a column that already has 2
        if g[r][c1] == 8 or g[r][c2] == 8:
            continue
        col_count_c1 = sum(1 for rr in range(h) if g[rr][c1] == 8)
        col_count_c2 = sum(1 for rr in range(h) if g[rr][c2] == 8)
        if col_count_c1 >= 2 or col_count_c2 >= 2:
            continue
        g[r][c1] = 8
        g[r][c2] = 8
    return g


def _pick_cols(bias, w, n, rng):
    if n <= 0:
        return []
    if bias == "center":
        center = w // 2
        cols = sorted(range(w), key=lambda c: abs(c - center))
        return cols[:n]
    if bias == "edge":
        cols = sorted(range(w), key=lambda c: -min(c, w - 1 - c))
        return cols[:n]
    cols = list(range(w))
    rng.shuffle(cols)
    return cols[:n]


def _pick_rows(bias, h, n, rng, exclude):
    if n <= 0:
        return []
    available = [r for r in range(h) if r not in exclude]
    if bias == "center":
        center = h // 2
        available.sort(key=lambda r: abs(r - center))
        return available[:n]
    rng.shuffle(available)
    return available[:n]


def _pair_rows(bias, h, gap, rng):
    if bias == "center":
        center = h // 2
        r1 = max(0, center - gap // 2 - 1)
        r2 = min(h - 1, center + gap // 2 + 1)
        return r1, r2
    if bias == "edge":
        return 0, h - 1
    r1 = rng.randint(0, max(0, h - gap - 2))
    r2 = rng.randint(min(h - 1, r1 + gap), h - 1)
    return r1, r2


def _pair_cols(bias, w, gap, rng):
    if bias == "center":
        center = w // 2
        c1 = max(0, center - gap // 2 - 1)
        c2 = min(w - 1, center + gap // 2 + 1)
        return c1, c2
    if bias == "edge":
        return 0, w - 1
    c1 = rng.randint(0, max(0, w - gap - 2))
    c2 = rng.randint(min(w - 1, c1 + gap), w - 1)
    return c1, c2


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        for c in range(0, w, 3):
            g[0][c] = 8
        return g
    if name == "all_columns_paired":
        for c in range(w):
            g[0][c] = 8
            g[h - 1][c] = 8
        return g
    if name == "single_pair":
        c = w // 2
        g[0][c] = 8
        g[h - 1][c] = 8
        return g
    return g
