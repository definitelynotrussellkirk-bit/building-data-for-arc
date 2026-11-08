"""Generator for 494ef9d7.

Rule: rows with exactly 2 non-zero cells; if pair is (4,7) or (1,8),
move right cell to be adjacent to left cell (c0+1 = v1).

Combinatorial axes (8): grid_h/w, n_pairs, n_distractors,
distractor_palette_size, pair_kind, position_bias,
pair_separation, asymmetry_force.
Degenerates: no_pairs, all_pairs, single_pair_only.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3b5d28c24297"
VERSION = "1.1.2"
TASK_ID = "3b5d28c24297"
SUMMARY = "Sparse cells; rows with (4,7) or (1,8) pair → pull right cell adjacent."

INVARIANTS = [
    "background is 0",
    ">=1 row contains exactly the pair (4,7) or (1,8) — non-adjacent",
    "scattering of distractor cells in other rows",
    "no distractor row accidentally creates the trigger pattern",
]

PAIR_KINDS = ("four_seven_only", "one_eight_only", "mixed")
POSITION_BIAS = ("center", "spread", "edge")
DEGENERATE_TEXTURES = ("no_pairs", "all_pairs", "single_pair_only")
HELPFUL_TEXTURES = PAIR_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 8..14", "valid": "6..18"},
    "grid_w":            {"type": "int", "default": "rng 8..14", "valid": "6..18"},
    "n_pairs":           {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "n_distractors":     {"type": "int", "default": "rng 4..8", "valid": "0..15"},
    "distractor_palette_size": {"type": "int", "default": "rng 2..5",
                                "valid": "1..7"},
    "pair_kind":         {"type": "str", "default": "rng helpful",
                          "valid": "four_seven_only|one_eight_only|mixed"},
    "position_bias":     {"type": "str", "default": "rng spread|center|edge",
                          "valid": "spread|center|edge"},
    "pair_separation":   {"type": "str", "default": "rng near|medium|far",
                          "valid": "near|medium|far"},
    "texture":           {"type": "str", "default": "alias for pair_kind",
                          "valid": "four_seven_only|one_eight_only|mixed|no_pairs|all_pairs|single_pair_only"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 6, 9, 6, 9
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 13, 18, 13, 18
    else:
        h_lo, h_hi, w_lo, w_hi = 8, 14, 8, 14
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_pairs = int(overrides.get("n_pairs",
                                ctx.draw_int("n_pairs", 2, 4)))
    n_pairs = max(1, min(6, n_pairs))
    n_dist = int(overrides.get("n_distractors",
                               ctx.draw_int("n_distractors", 4, 8)))
    n_dist = max(0, min(15, n_dist))
    n_dist_pal = int(overrides.get("distractor_palette_size",
                                   ctx.draw_int("distractor_palette_size",
                                                2, 5)))
    pair_kind = (overrides.get("texture") or
                 overrides.get("pair_kind")
                 or ctx.draw_choice("pair_kind", list(PAIR_KINDS)))
    bias = overrides.get("position_bias",
                         ctx.draw_choice("position_bias",
                                         list(POSITION_BIAS)))
    sep = overrides.get("pair_separation",
                        ctx.draw_choice("pair_separation",
                                        ["near", "medium", "far"]))
    g = full_grid(h, w, 0)

    # Reserve and draw trigger rows FIRST.  The old order scattered distractors
    # first, so small/easy grids could have zero empty rows left and silently
    # produce identity demos with no (4,7)/(1,8) row for the rule to transform.
    n_pair_rows = min(n_pairs, h)
    rows = list(range(h))
    rng.shuffle(rows)
    pair_rows = set(rows[:n_pair_rows])
    for r in sorted(pair_rows):
        pair = _pick_pair(pair_kind, rng)
        v0, v1 = pair if rng.random() < 0.5 else (pair[1], pair[0])
        c0, c1 = _bracket_cols(sep, bias, w, rng)
        if c1 - c0 < 2 or c0 < 0 or c1 >= w:
            c0, c1 = 0, w - 1
        g[r][c0] = v0
        g[r][c1] = v1

    distractor_pool = [c for c in [2, 3, 5, 6, 9] if c not in (4, 7, 1, 8)]
    rng.shuffle(distractor_pool)
    distractor_palette = distractor_pool[:max(1, n_dist_pal)]
    distractor_rows = [r for r in range(h) if r not in pair_rows]
    placed = 0
    for _ in range(n_dist * 6):
        if placed >= n_dist or not distractor_rows:
            break
        r = rng.choice(distractor_rows); c = rng.randint(0, w - 1)
        if g[r][c] != 0:
            continue
        # Distractors live only outside trigger rows, so every reserved pair row
        # stays exactly two non-zero cells and always demonstrates the rule.
        g[r][c] = rng.choice(distractor_palette)
        placed += 1
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, pair cells {4,7,1,8} appear in proper row-pairs (distractors exclude these)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    # Check values are in valid range
    for r in range(h):
        for c in range(w):
            if not (0 <= grid[r][c] <= 9):
                errs.append(f"invalid cell value {grid[r][c]} at ({r},{c})")
                return errs
    # Distractor pool excludes {4,7,1,8}; any row containing these colors must
    # be an exact, non-adjacent trigger pair.  Also require at least one trigger
    # row so default samples cannot collapse to identity/no-op demonstrations.
    trigger_rows = 0
    for r in range(h):
        nonzero = [(c, v) for c, v in enumerate(grid[r]) if v != 0]
        vals = [v for _, v in nonzero]
        if not any(v in (1, 4, 7, 8) for v in vals):
            continue
        if len(nonzero) != 2:
            errs.append(f"row {r} has trigger colors but {len(nonzero)} nonzero cells")
            continue
        (c0, v0), (c1, v1) = nonzero
        if sorted((v0, v1)) not in ([1, 8], [4, 7]):
            errs.append(f"row {r} has invalid trigger pair values {v0},{v1}")
            continue
        if c1 - c0 < 2:
            errs.append(f"row {r} trigger pair is adjacent; expected a gap to close")
            continue
        trigger_rows += 1
    if trigger_rows == 0:
        errs.append("no trigger row with a non-adjacent (4,7) or (1,8) pair")
    return errs


def _pick_pair(kind, rng):
    if kind == "four_seven_only":
        return (4, 7)
    if kind == "one_eight_only":
        return (1, 8)
    return rng.choice([(4, 7), (1, 8)])


def _bracket_cols(sep, bias, w, rng):
    target = {"near": 3, "medium": w // 2, "far": w - 2}.get(sep, w // 2)
    target = max(2, min(w - 1, target))
    if bias == "center":
        c0 = max(0, (w - target) // 2)
    elif bias == "edge":
        c0 = 0
    else:
        c0 = rng.randint(0, max(0, w - target - 1))
    c1 = min(w - 1, c0 + target)
    return c0, c1


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        for r in range(h):
            for c in range(w):
                if rng.random() < 0.3:
                    g[r][c] = rng.choice([2, 3, 5, 6, 9])
        return g
    if name == "all_pairs":
        for r in range(h):
            pair = (4, 7) if r % 2 == 0 else (1, 8)
            g[r][0] = pair[0]
            g[r][w - 1] = pair[1]
        return g
    if name == "single_pair_only":
        g[h // 2][0] = 4
        g[h // 2][w - 1] = 7
        return g
    return g
