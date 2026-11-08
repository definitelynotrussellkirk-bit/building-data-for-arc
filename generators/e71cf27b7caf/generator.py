"""Generator for puzzle 5ad8a7c0.

Rule: rows with exactly 2 cells of color 2 have a "gap" = c2 - c1.
Rule fills cells between the two 2s with 2 in EVERY row whose gap
equals the overall minimum gap.

Combinatorial axes (8): grid_h/w, n_pair_rows, gap_distribution,
min_gap, position_bias, anchor_corner, asymmetry_force, palette_size.
Degenerates: no_pairs, all_same_gap, single_pair_row.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e71cf27b7caf"
VERSION = "2.0.1"  # helpful draws enforce a non-min comparison row and add self_check
TASK_ID = "e71cf27b7caf"
SUMMARY = (
    "0-bg grid (h~4-12, w~7-16) with 2-4 "
    "PAIR ROWS — each pair row holds EXACTLY "
    "2 cells of COLOR 2 (red) at distinct "
    "columns (c_left, c_right), with a GAP = "
    "c_right - c_left. Gaps are assigned by "
    "one of 6 DISTRIBUTIONS (uniform / "
    "increasing / decreasing / min_at_top / "
    "min_at_bottom / alternating), starting "
    "from min_gap (2-3) and extending by up to "
    "extra (2-4). At least ONE row has the "
    "UNIQUE MINIMUM GAP (strict). Other rows "
    "(non-pair rows) have 0 cells of color 2. "
    "Pair-row positions are random (sampled "
    "without replacement). Rule (FILL CELLS "
    "BETWEEN THE TWO 2s IN EVERY ROW WHOSE "
    "GAP EQUALS THE OVERALL MINIMUM GAP): for "
    "EACH PAIR ROW r: COMPUTE its GAP = "
    "c_right - c_left. find the GLOBAL "
    "MINIMUM GAP across all pair rows. For "
    "EACH row whose gap = min_gap: FILL every "
    "cell (r, c) with c_left < c < c_right "
    "with COLOR 2 (the interior between the "
    "two 2s). The endpoint 2s stay; the "
    "other (larger-gap) pair rows keep just "
    "their endpoints unchanged. Net: the "
    "tightest pair row(s) become solid "
    "horizontal red bars; wider-gap rows "
    "stay as their two endpoints."
)

INVARIANTS = [
    "background is 0",
    "2-4 rows have exactly 2 cells of color 2",
    "other rows have 0 cells of color 2",
    ">=1 row has the unique minimum gap",
]

GAP_DISTRIBUTIONS = ("uniform", "increasing", "decreasing",
                     "min_at_top", "min_at_bottom", "alternating")
DEGENERATE_TEXTURES = ("no_pairs", "all_same_gap", "single_pair_row")
HELPFUL_TEXTURES = GAP_DISTRIBUTIONS

AXES = {
    "grid_h":           {"type": "int", "default": "rng 4..8", "valid": "3..12"},
    "grid_w":           {"type": "int", "default": "rng 7..12", "valid": "5..16"},
    "n_pair_rows":      {"type": "int", "default": "rng 2..3", "valid": "2..5"},
    "gap_distribution": {"type": "str", "default": "rng helpful",
                         "valid": "|".join(GAP_DISTRIBUTIONS)},
    "min_gap":          {"type": "int", "default": "rng 2..3", "valid": "2..5"},
    "max_gap_extra":    {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "anchor_corner":    {"type": "bool", "default": "false",
                         "valid": "true|false"},
    "asymmetry_force":  {"type": "bool", "default": "false",
                         "valid": "true|false"},
    "texture":          {"type": "str", "default": "alias for gap_distribution",
                         "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    if any(v not in (0, 2) for row in grid for v in row):
        errors.append("grid should contain only background 0 and marker color 2")
    pair_rows = []
    for r, row in enumerate(grid):
        cols = [c for c, v in enumerate(row) if v == 2]
        if not cols:
            continue
        if len(cols) != 2:
            errors.append(f"row {r} has {len(cols)} color-2 cells; expected exactly 2")
            continue
        c0, c1 = cols
        pair_rows.append((r, c1 - c0))
    if not (2 <= len(pair_rows) <= 5):
        errors.append(f"expected 2..5 pair rows, found {len(pair_rows)}")
    gaps = [gap for _, gap in pair_rows]
    if gaps and min(gaps) < 2:
        errors.append(f"all marker gaps must be at least 2, got {gaps}")
    if len(set(gaps)) < 2:
        errors.append("helpful draw collapsed to all-same gap; no wider comparison row")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 3, 5
    elif difficulty == "hard":
        h_lo, h_hi = 8, 12
    else:
        h_lo, h_hi = 4, 8
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo + 3, h_hi + 4)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_pair = int(overrides.get("n_pair_rows",
                               ctx.draw_int("n_pair_rows", 2, 3)))
    n_pair = max(2, min(min(h, 5), n_pair))
    distribution = (overrides.get("texture") or
                    overrides.get("gap_distribution")
                    or ctx.draw_choice("gap_distribution",
                                       list(GAP_DISTRIBUTIONS)))
    min_gap = int(overrides.get("min_gap",
                                ctx.draw_int("min_gap", 2, 3)))
    extra = int(overrides.get("max_gap_extra",
                              ctx.draw_int("max_gap_extra", 2, 4)))
    min_gap = max(2, min(w - 1, min_gap))
    g = full_grid(h, w, 0)
    rows = rng.sample(range(h), n_pair)
    rows.sort()
    gaps = _build_gaps(distribution, n_pair, min_gap, extra, rng)
    for i, r in enumerate(rows):
        gap = gaps[i]
        gap = max(2, min(w - 1, gap))
        c0 = rng.randint(0, w - gap - 1)
        c1 = c0 + gap
        g[r][c0] = 2
        g[r][c1] = 2
    return g


def _build_gaps(distribution, n, min_gap, extra, rng):
    if distribution == "uniform":
        gaps = [min_gap + rng.randint(0, extra) for _ in range(n)]
        if n > 1 and len(set(gaps)) == 1:
            gaps[-1] = gaps[-1] + 1 if gaps[-1] <= min_gap else gaps[-1] - 1
        return gaps
    if distribution == "increasing":
        return [min_gap + i for i in range(n)]
    if distribution == "decreasing":
        return [min_gap + (n - 1 - i) for i in range(n)]
    if distribution == "min_at_top":
        return [min_gap if i == 0 else min_gap + 1 + rng.randint(0, extra)
                for i in range(n)]
    if distribution == "min_at_bottom":
        return [min_gap if i == n - 1 else min_gap + 1 + rng.randint(0, extra)
                for i in range(n)]
    if distribution == "alternating":
        return [min_gap if i % 2 == 0 else min_gap + 1 + rng.randint(0, extra)
                for i in range(n)]
    return [min_gap + rng.randint(0, extra) for _ in range(n)]


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # No 2-cells — rule has no work
        return g
    if name == "all_same_gap":
        # All pair rows have the same gap → all rows get filled
        gap = 3
        for r in range(min(h, 3)):
            c0 = rng.randint(0, w - gap - 1)
            g[r][c0] = 2
            g[r][c0 + gap] = 2
        return g
    if name == "single_pair_row":
        r = h // 2
        g[r][1] = 2
        g[r][w - 2] = 2
        return g
    return g
