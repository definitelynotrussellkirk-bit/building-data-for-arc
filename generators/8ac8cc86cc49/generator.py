"""Generator for 6350f1f4.

Rule: clean k-by-k template cell controls a separated macrogrid;
minority template positions preserve the template.

Combinatorial axes (8): grid_size, template_variant, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
n_distinct_colors.
Degenerates: no_template, full_template, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8ac8cc86cc49"
VERSION = "3.0.0"  # in_sh=out_sh=1/distinct=97: fixed 11x11 (k=3) + 3 fixed template variants. Rule derives k from grid size (n=k*(k+1)-1) and stamps the clean template across a kxk macrogrid. Vary k (2-4) -> grid 5x5/11x11/19x19, and use a RANDOM kxk 2-color template -> output dims and content vary.
TASK_ID = "8ac8cc86cc49"
SUMMARY = (
    "Fixed 11×11 0-bg grid structured as a 3×3 "
    "MACROGRID of 3×3 MACRO CELLS separated by "
    "1-cell SEPARATORS (rows 3, 7 and cols 3, "
    "7 are separator gaps). Each macro cell at "
    "(tr, tc) for tr, tc ∈ {0, 1, 2}: occupies "
    "rows tr*4..tr*4+2 × cols tc*4..tc*4+2 "
    "(3×3). One CLEAN TEMPLATE macro cell (the "
    "top-left at (0, 0)) contains a 3×3 "
    "PATTERN using TWO COLORS (majority_color "
    "and minority_color, both non-{0, 5}). The "
    "TEMPLATE variant ∈ {diag, corner, bar}. "
    "ALL OTHER 8 macro cells are filled with "
    "COLOR 5 (gray) — i.e., the template is "
    "the only non-5 macro cell. Rule: identify "
    "the TEMPLATE (the macro cell that "
    "contains NO COLOR 5 — the 'clean' "
    "template). For EACH OTHER macro cell "
    "(currently all-5), STAMP the template's "
    "pattern at the corresponding macro-cell "
    "position — where template has MINORITY "
    "color (the 2 in the encoding), KEEP that "
    "macro cell as 5; where template has "
    "MAJORITY color (the 1), CLEAR the macro "
    "cell to 0. Net: template controls which "
    "macro cells stay 5 and which become 0 "
    "across the 3×3 macrogrid."
)

INVARIANTS = [
    "grid size is k*(k+1)-1 for k=3 so 11x11",
    "macro cells are 3x3 with one-cell separators",
    "one clean template macro cell has two colors and no color 5",
    "other macro cells contain color 5 so they are skipped as templates",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_template", "full_template", "full_grid")
HELPFUL_TEXTURES = ("diag", "corner", "bar")

TEMPLATES = {
    "diag": [[1, 1, 2], [1, 2, 1], [2, 1, 1]],
    "corner": [[2, 1, 1], [1, 1, 1], [1, 1, 1]],
    "bar": [[1, 1, 1], [2, 2, 1], [1, 1, 1]],
}

AXES = {
    "grid_size":      {"type": "int", "default": "11", "valid": "11"},
    "template_variant":{"type": "str", "default": "rng helpful",
                       "valid": "|".join(HELPFUL_TEXTURES)},
    "palette_kind":   {"type": "str", "default": "rng", "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for template_variant",
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
        k = 2
    elif difficulty == "hard":
        k = ctx.draw_int("k", 3, 4)
    else:
        k = ctx.draw_int("k", 2, 4)
    majority_color, minority_color = ctx.draw_distinct_colors(
        "template_colors", n=2, exclude={0, 5}
    )
    s = k + 1
    n = k * s - 1
    g = full_grid(n, n, 0)
    # every macro cell starts as color 5
    for tr in range(k):
        for tc in range(k):
            r0 = tr * s; c0 = tc * s
            for dr in range(k):
                for dc in range(k):
                    g[r0 + dr][c0 + dc] = 5
    # clean template macro cell at (0,0): random kxk 2-color pattern with >=1
    # minority and >=1 majority cell (no color 5)
    n_min = rng.randint(1, k * k - 1)
    minpos = set(rng.sample([(r, c) for r in range(k) for c in range(k)], n_min))
    for r in range(k):
        for c in range(k):
            g[r][c] = minority_color if (r, c) in minpos else majority_color
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 11, 0)
    if name == "no_template":
        for tr in range(3):
            for tc in range(3):
                r0 = tr * 4; c0 = tc * 4
                for dr in range(3):
                    for dc in range(3):
                        g[r0 + dr][c0 + dc] = 5
        return g
    if name == "full_template":
        for r in range(11):
            for c in range(11):
                g[r][c] = 1 if r < 3 and c < 3 else 5
        return g
    if name == "full_grid":
        for r in range(11):
            for c in range(11):
                g[r][c] = 5
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Square grid with dims k*(k+1)-1 for k∈{2,3,4}; ≥1 color-5 macro cell."""
    errs = []
    h, w = len(grid), len(grid[0]) if grid else 0
    if h != w:
        errs.append(f"grid must be square, got {h}×{w}")
        return errs
    valid_sizes = {k * (k + 1) - 1 for k in range(2, 5)}  # {5, 11, 19}
    if h not in valid_sizes:
        errs.append(f"size {h} doesn't match k*(k+1)-1 for k∈{{2,3,4}} (valid: {sorted(valid_sizes)})")
    if not any(grid[r][c] == 5 for r in range(h) for c in range(w)):
        errs.append("no color-5 macro cell found")
    return errs
