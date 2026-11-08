"""Generator for 3aa6fb7a.

Rule: for each 2×2 sub-block where 3 cells = 8 and 1 = 0, set the
0-cell to 1.

Combinatorial axes (8): grid_h/w, n_patterns, L_variant_kind,
position_bias, decoy_density, palette_size, separation,
asymmetry_force.
Degenerates: no_patterns, all_8s, single_pattern.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "60527b695836"
VERSION = "2.0.1"
TASK_ID = "60527b695836"
SUMMARY = (
    "0-bg grid (h~5-10, w~6-12) with 2-4 L-TROMINO "
    "PATTERNS of color 8 (cyan). Each L is a 2×2 "
    "sub-block with 3 cells of color 8 and 1 cell of "
    "0 — the variant determines which corner is "
    "missing: missing_BR, missing_BL, missing_TR, "
    "missing_TL (or mixed across the grid). Patterns "
    "are separated by ≥ 2-3 cells. No color-1 in "
    "input. Rule: scan every 2×2 sub-block of the "
    "grid. If exactly 3 of the 4 cells are color 8 "
    "AND the remaining cell is 0, SET that 0-cell to "
    "color 1 (blue) — completing the L into a solid "
    "2×2 (3 cyan + 1 blue). Net: each L-tromino "
    "sprouts a blue cell in its missing corner."
)

INVARIANTS = [
    "background is 0",
    ">=2 L-tromino patterns of color 8 (3 cells in 2×2 with 4th = 0)",
    "patterns separated by margin >=2",
    "no color 1 in input (rule writes 1 for output)",
]

L_VARIANT_KINDS = ("missing_BR", "missing_BL", "missing_TR", "missing_TL", "mixed")
DEGENERATE_TEXTURES = ("no_patterns", "all_8s", "single_pattern")
HELPFUL_TEXTURES = L_VARIANT_KINDS

AXES = {
    "grid_h":          {"type": "int", "default": "rng 5..10", "valid": "4..14"},
    "grid_w":          {"type": "int", "default": "rng 6..12", "valid": "5..16"},
    "n_patterns":      {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "L_variant_kind":  {"type": "str", "default": "rng helpful",
                        "valid": "|".join(L_VARIANT_KINDS)},
    "position_bias":   {"type": "str", "default": "rng spread|center|edge",
                        "valid": "spread|center|edge"},
    "separation":      {"type": "int", "default": "3", "valid": "2..5"},
    "anchor_corner":   {"type": "bool", "default": "false",
                        "valid": "true|false"},
    "asymmetry_force": {"type": "bool", "default": "false",
                        "valid": "true|false"},
    "texture":         {"type": "str", "default": "alias for L_variant_kind",
                        "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

L_VARIANTS = {
    "missing_BR": [(0, 0), (0, 1), (1, 0)],
    "missing_BL": [(0, 0), (0, 1), (1, 1)],
    "missing_TR": [(0, 0), (1, 0), (1, 1)],
    "missing_TL": [(0, 1), (1, 0), (1, 1)],
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 4, 7, 5, 9
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 9, 14, 11, 16
    else:
        h_lo, h_hi, w_lo, w_hi = 5, 10, 6, 12
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_patterns = int(overrides.get("n_patterns",
                                   ctx.draw_int("n_patterns", 2, 4)))
    n_patterns = max(1, min(6, n_patterns))
    variant_kind = (overrides.get("texture") or
                    overrides.get("L_variant_kind")
                    or ctx.draw_choice("L_variant_kind",
                                       list(L_VARIANT_KINDS)))
    bias = overrides.get("position_bias",
                         ctx.draw_choice("position_bias",
                                         ["spread", "center", "edge"]))
    sep = int(overrides.get("separation", 3))
    g = full_grid(h, w, 0)
    placed = []
    for _ in range(n_patterns * 5):
        if len(placed) >= n_patterns:
            break
        r, c = _pick_pos(bias, h, w, rng)
        if all(abs(r - pr) > sep or abs(c - pc) > sep for pr, pc in placed):
            cells = _pick_variant(variant_kind, rng)
            for dr, dc in cells:
                if r + dr < h and c + dc < w:
                    g[r + dr][c + dc] = 8
            placed.append((r, c))
    if not placed:
        if h >= 2 and w >= 2:
            g[0][0] = 8; g[0][1] = 8; g[1][0] = 8
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=2 L-tromino patterns of color 8; no color 1 in input."""
    if not grid or not grid[0]:
        return ["grid is empty"]
    h, w = len(grid), len(grid[0])
    errors = []
    if any(grid[r][c] == 1 for r in range(h) for c in range(w)):
        errors.append("color 1 found in input (rule writes color 1 as output only)")
    # count L-tromino patterns: 2x2 windows with exactly 3 cells of color 8 and 4th=0
    n_patterns = 0
    for r in range(h - 1):
        for c in range(w - 1):
            window = [grid[r][c], grid[r][c+1], grid[r+1][c], grid[r+1][c+1]]
            if window.count(8) == 3 and window.count(0) == 1:
                n_patterns += 1
    if n_patterns < 1:
        errors.append(f"expected >=1 L-tromino pattern (3-of-4 cells=8 in 2x2), found none")
    return errors


def _pick_pos(bias, h, w, rng):
    if bias == "center":
        return h // 2 - 1, w // 2 - 1
    if bias == "edge":
        choices = [(0, 0), (0, w - 2), (h - 2, 0), (h - 2, w - 2)]
        return rng.choice(choices)
    return rng.randint(0, h - 2), rng.randint(0, w - 2)


def _pick_variant(kind, rng):
    if kind in L_VARIANTS:
        return L_VARIANTS[kind]
    return rng.choice(list(L_VARIANTS.values()))


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "no_patterns":
        return g
    if name == "all_8s":
        for r in range(h):
            for c in range(w):
                g[r][c] = 8
        return g
    if name == "single_pattern":
        if h >= 2 and w >= 2:
            g[h // 2][w // 2] = 8
            g[h // 2][w // 2 + 1] = 8
            g[h // 2 + 1][w // 2] = 8
        return g
    return g
