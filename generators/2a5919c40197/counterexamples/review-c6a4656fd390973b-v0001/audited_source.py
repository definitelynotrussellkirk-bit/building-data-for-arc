"""Generator for puzzle 25d8a9c8.

Rule: `(rule! (lambda (g) (cellmap g (r c v) (if (= 1 (length (unique (row-at g r)))) 5 0))))`.
Each row is either uniform (every cell the same color) or non-uniform.
The rule paints every cell of a uniform row to gray(5) and every cell
of a non-uniform row to black(0).

Combinatorial axes:
  * grid_h / grid_w        — outer canvas size
  * uniform_ratio          — fraction of rows that are uniform (must be
                             > 0 and < 1 so output has both 5s and 0s)
  * uniform_color_diversity — how the uniform rows pick colors:
                             same / mixed / palette
  * non_uniform_pattern    — how non-uniform rows look: random / pair /
                             stripes / one_minority
  * palette_size           — number of distinct colors
  * caller-opt-in degenerates: all_uniform (output all 5),
                               all_non_uniform (output all 0),
                               single_color_palette (uniform rows
                               indistinguishable from non-uniform)
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "2a5919c40197"
VERSION = "1.1.1"  # keep default draws near the canonical 3x3 task scale
TASK_ID = "2a5919c40197"
SUMMARY = "Mix of uniform/non-uniform rows; rule paints uniform → 5, else → 0."

INVARIANTS = [
    "≥1 uniform row AND ≥1 non-uniform row (output has both 5 and 0)",
    "grid dims in [3, 15] × [2, 15]",
]

UNIFORM_DIVERSITIES = ("same", "mixed", "palette")
NON_UNIFORM_PATTERNS = ("random", "pair", "stripes", "one_minority")
DEGENERATE_TEXTURES = ("all_uniform", "all_non_uniform", "single_color_palette")
HELPFUL_TEXTURES = NON_UNIFORM_PATTERNS

AXES = {
    "grid_h":                  {"type": "int",   "default": "rng 3..6", "valid": "3..18"},
    "grid_w":                  {"type": "int",   "default": "rng 2..6", "valid": "2..18"},
    "uniform_ratio":           {"type": "float", "default": "rng 0.3..0.7", "valid": "0.1..0.9"},
    "uniform_color_diversity": {"type": "str",   "default": "rng same|mixed|palette",
                                "valid": "|".join(UNIFORM_DIVERSITIES)},
    "non_uniform_pattern":     {"type": "str",   "default": "rng helpful",
                                "valid": "|".join(NON_UNIFORM_PATTERNS)},
    "palette_size":            {"type": "int",   "default": "rng 3..7", "valid": "2..10"},
    "texture":                 {"type": "str",   "default": "alias for non_uniform_pattern",
                                "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi, p_lo, p_hi = 3, 4, 2, 4, 2, 4
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi, p_lo, p_hi = 4, 6, 4, 6, 4, 7
    else:
        h_lo, h_hi, w_lo, w_hi, p_lo, p_hi = 3, 6, 2, 6, 3, 7

    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("rows")

    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)

    n_colors = int(overrides.get("palette_size",
                                 ctx.draw_int("palette_size", p_lo, p_hi)))
    palette = list(ctx.draw_distinct_colors("palette", n=max(2, n_colors)))
    uniform_ratio = float(overrides.get(
        "uniform_ratio",
        ctx.draw_rng("uniform_ratio").uniform(0.3, 0.7)))
    diversity = overrides.get(
        "uniform_color_diversity",
        ctx.draw_choice("uniform_color_diversity", list(UNIFORM_DIVERSITIES)))
    pattern = (overrides.get("texture")
               or overrides.get("non_uniform_pattern")
               or ctx.draw_choice("non_uniform_pattern", list(NON_UNIFORM_PATTERNS)))

    n_uniform = max(1, min(h - 1, int(h * uniform_ratio)))

    rows: list[list[int]] = []
    is_uniform_flags = [True] * n_uniform + [False] * (h - n_uniform)
    rng.shuffle(is_uniform_flags)

    same_color = palette[0]
    palette_idx = 0
    for is_u in is_uniform_flags:
        if is_u:
            if diversity == "same":
                c = same_color
            elif diversity == "palette":
                c = palette[palette_idx % len(palette)]
                palette_idx += 1
            else:  # mixed
                c = rng.choice(palette)
            rows.append([c] * w)
        else:
            rows.append(_non_uniform_row(pattern, w, palette, rng))
    return rows


def self_check(grid, *, difficulty=None, meta=None):
    """≥1 uniform row AND ≥1 non-uniform row so output has both 5s and 0s."""
    errs = []
    has_uniform = any(len(set(row)) == 1 for row in grid)
    has_nonuniform = any(len(set(row)) > 1 for row in grid)
    if not has_uniform:
        errs.append("no uniform row (output would be all 0s)")
    if not has_nonuniform:
        errs.append("no non-uniform row (output would be all 5s)")
    return errs


def _non_uniform_row(pattern, w, palette, rng):
    if pattern == "pair":
        a = palette[0]
        b = palette[1] if len(palette) > 1 else (a + 1) % 10
        row = [a if i < w // 2 else b for i in range(w)]
    elif pattern == "stripes":
        row = [palette[i % len(palette)] for i in range(w)]
    elif pattern == "one_minority":
        c = rng.choice(palette)
        row = [c] * w
        idx = rng.randint(0, w - 1)
        other = next((x for x in palette if x != c), (c + 1) % 10)
        row[idx] = other
    else:  # random
        row = [rng.choice(palette) for _ in range(w)]
    if len(set(row)) == 1:
        row[0] = next((c for c in palette if c != row[0]), (row[0] + 1) % 10)
    return row


def _draw_from_degenerate(name, h, w, rng):
    """Edge-case where the uniform-row signal collapses.

    all_uniform           — every row uniform; output is all 5s.
    all_non_uniform       — every row non-uniform; output is all 0s.
    single_color_palette  — only one color in palette; "non-uniform"
                            rows can't exist (only width 1 etc.); rule
                            collapses.
    """
    palette = list(range(1, 10))
    rng.shuffle(palette)
    if name == "all_uniform":
        return [[rng.choice(palette)] * w for _ in range(h)]
    if name == "all_non_uniform":
        rows = []
        for _ in range(h):
            row = [rng.choice(palette) for _ in range(w)]
            if len(set(row)) == 1:
                row[0] = next((c for c in palette if c != row[0]), (row[0] + 1) % 10)
            rows.append(row)
        return rows
    if name == "single_color_palette":
        c = palette[0]
        return [[c] * w for _ in range(h)]
    return [[palette[0]] * w for _ in range(h)]
