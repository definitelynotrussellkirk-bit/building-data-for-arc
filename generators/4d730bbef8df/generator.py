"""Generator for 55059096.

Rule: find 3-plus-shapes; pairs whose centers are exactly diagonal get
2-cells drawn between them.

Combinatorial axes (8): grid_h/w, min_distance, position_bias,
palette_kind, anchor_corner, asymmetry_force, palette_size, n_pluses.
Degenerates: single_plus, no_pluses, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4d730bbef8df"
# 2.1.0: defect-lint identity_demo + coverage — 40 failed placement tries fell
# through to an EMPTY grid (silent no-op demo). Deterministic aligned-pair
# fallback added + 1-2 decoy crosses to match the canonical multi-cross scenes.
VERSION = "2.1.0"
TASK_ID = "4d730bbef8df"
SUMMARY = "Several color-3 plus-shapes (each 5 cells: center + 4 cardinals) on a 0-bg grid. Some pairs of plus-centers are EXACTLY diagonal to each other (|dr| = |dc|). Rule draws color-2 cells in the bg cells between each such diagonal pair (interior diagonal cells fill with 2). Pairs that are not exactly diagonal don't connect."

# Rivals: 'output is input' refuted by demos with ≥1 diagonal pair.
# 'connect all pairs straight' refuted by demos with non-diagonal pairs.
# 'use color 3 for connector' refuted by demos (always 2). 'fill entire
# bbox between' refuted by demos (only diagonal cells fill).
# 3 demos with mix of diagonal and non-diagonal pairs cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "exactly 2 plus-shapes of color 3 (5 cells each: center + 4 cardinals)",
    "centers at exact diagonal distance >=3",
    "shapes don't overlap",
]

POSITION_BIASES = ("scattered", "diagonal", "corners", "rng")
DEGENERATE_TEXTURES = ("single_plus", "no_pluses", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..14", "valid": "8..18"},
    "grid_w":         {"type": "int", "default": "rng 10..16", "valid": "8..20"},
    "min_distance":   {"type": "int", "default": "rng 3..5", "valid": "3..8"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 8, 10, 8, 12
        d_lo, d_hi = 3, 4
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 14, 18, 16, 20
        d_lo, d_hi = 5, 8
    else:
        h_lo, h_hi, w_lo, w_hi = 10, 14, 10, 16
        d_lo, d_hi = 3, 5
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    g = full_grid(h, w, 0)
    min_d = int(overrides.get("min_distance",
                              ctx.draw_int("min_distance", d_lo, d_hi)))
    min_d = max(3, min(8, min_d))
    for _try in range(40):
        r1 = rng.randint(2, max(2, h // 2 - 1))
        c1 = rng.randint(2, max(2, w // 2 - 1))
        max_d = min(h - r1 - 3, w - c1 - 3)
        if max_d < min_d:
            continue
        d = rng.randint(min_d, max_d)
        sr = rng.choice([1, -1]) if r1 + d < h - 1 and r1 - d > 0 else 1
        sc = rng.choice([1, -1]) if c1 + d < w - 1 and c1 - d > 0 else 1
        r2 = r1 + d * sr
        c2 = c1 + d * sc
        if not (1 <= r2 <= h - 2 and 1 <= c2 <= w - 2):
            continue
        centers = [(r1, c1), (r2, c2)]
        break
    else:
        # Deterministic aligned pair — an empty grid is a no-op demo.
        centers = [(2, 2), (5, 5)]
    # 1-2 decoy crosses like the canonical scenes (extra centers the rule may
    # or may not connect), kept clear of existing crosses.
    for _ in range(rng.randint(1, 2)):
        for _t in range(40):
            cr = rng.randint(1, h - 2)
            cc = rng.randint(1, w - 2)
            if all(abs(cr - pr) + abs(cc - pc) >= 4 for pr, pc in centers):
                centers.append((cr, cc))
                break
    for cr, cc in centers:
        for dr, dc in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:
            g[cr + dr][cc + dc] = 3
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify 2 color-3 plus-shapes at exact diagonal distance invariants."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    flat = [v for row in grid for v in row]
    problems = []
    if all(v == 0 for v in flat):
        return ["empty grid — the rule has nothing to connect (no-op demo)"]
    count3 = flat.count(3)
    # Two plus-shapes = 10 cells total (5 each)
    if count3 < 10:
        problems.append(f"expected >=2 color-3 plus-shapes (>=10 cells), found {count3}")
    bad = [v for v in flat if v not in (0, 3)]
    if bad:
        problems.append(f"unexpected colors outside {{0,3}}: {sorted(set(bad))}")
    # >=1 diagonally aligned center pair, else the rule draws nothing
    centers = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)
               if all(grid[r + dr][c + dc] == 3
                      for dr, dc in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)))]
    aligned = any(abs(a[0] - b[0]) == abs(a[1] - b[1])
                  for i, a in enumerate(centers) for b in centers[i + 1:])
    if len(centers) >= 2 and not aligned:
        problems.append("no diagonally aligned cross pair — the demo would be an identity")
    return problems


def _draw_from_degenerate(name, rng):
    h, w = 12, 14
    g = full_grid(h, w, 0)
    if name == "single_plus":
        for dr, dc in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:
            g[5 + dr][6 + dc] = 3
        return g
    if name == "no_pluses":
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 3
        return g
    return g
