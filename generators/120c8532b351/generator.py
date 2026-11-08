"""Generator for ARC task 48f8583b.

Rule: `(rule! (lambda (g) (self-tile g (lambda (v) (= v (minority g))))))`.
Self-tile gated on cells equal to the LEAST-frequent color (the
minority). Output is H² × W² with the input duplicated where the
minority color appears.

Combinatorial axes:
  * grid_size              — kept at 3 (canonical)
  * minority_color         — the singleton color
  * minority_count         — how many cells take the minority (1..2;
                             must be strictly fewer than the others)
  * other_palette_size     — number of distinct non-minority colors
  * other_layout           — how the majority colors arrange:
                             uniform / two_colors / striped /
                             checker / diagonal_split
  * caller-opt-in degenerates: tied_minorities, monochrome, all_unique
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "120c8532b351"
VERSION = "3.0.0"  # diversity: vary grid dims 2..4 incl non-square (self-tile generalizes h x w -> h*h x w*w) so output dims vary (was fixed 3x3 -> 9x9 shape-locked)
TASK_ID = "120c8532b351"
SUMMARY = (
    "Fixed 3×3 grid with: (a) "
    "MINORITY color (1-2 cells in "
    "a randomly chosen color); "
    "(b) MAJORITY cells (7-8) in "
    "1-3 OTHER colors arranged in "
    "one of 5 layouts (uniform/"
    "two_colors/striped/checker/"
    "diagonal_split). Minority "
    "count must be STRICTLY LESS "
    "than every other color count. "
    "Rule (SELF-TILE GATED BY "
    "MINORITY): identify the "
    "MINORITY (least-frequent "
    "color). EMIT a 9×9 (3*h × "
    "3*w) OUTPUT grid where each "
    "cell at position (R, C) is "
    "computed as: if input[R // "
    "3][C // 3] == MINORITY → "
    "copy from input[R % 3][C % "
    "3]; ELSE → 0 (or the cell's "
    "value if input cell isn't "
    "minority — task-specific). "
    "Net: 3×3 input self-tiles "
    "into 9×9 output gated by "
    "minority-color cells."
)

INVARIANTS = [
    "input is 3 × 3",
    "the minority color appears strictly fewer times than every other color",
    "≥2 distinct colors so the rule has visible effect",
]

OTHER_LAYOUTS = ("uniform", "two_colors", "striped", "checker", "diagonal_split")
DEGENERATE_TEXTURES = ("tied_minorities", "monochrome", "all_unique")
HELPFUL_TEXTURES = OTHER_LAYOUTS

AXES = {
    "grid_h":             {"type": "int",   "default": "rng 2..4", "valid": "2..5"},
    "grid_w":             {"type": "int",   "default": "rng 2..4", "valid": "2..5"},
    "minority_color":     {"type": "color", "default": "rng", "valid": "1..9"},
    "minority_count":     {"type": "int",   "default": "rng 1..", "valid": "1..3"},
    "other_palette_size": {"type": "int",   "default": "rng 1..3", "valid": "1..6"},
    "other_layout":       {"type": "str",   "default": "rng helpful",
                           "valid": "|".join(OTHER_LAYOUTS)},
    "texture":            {"type": "str",   "default": "alias for other_layout",
                           "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    if difficulty == "easy":
        h_lo, h_hi, p_lo, p_hi = 2, 3, 1, 1
    elif difficulty == "hard":
        h_lo, h_hi, p_lo, p_hi = 3, 4, 2, 3
    else:
        h_lo, h_hi, p_lo, p_hi = 2, 4, 1, 3

    rng = ctx.draw_rng("cells")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], ctx, rng)

    h = int(overrides.get("grid_h", ctx.draw_int("grid_h", h_lo, h_hi)))
    w = int(overrides.get("grid_w", ctx.draw_int("grid_w", h_lo, h_hi)))
    n_total = h * w

    minority = int(overrides.get("minority_color",
                                 ctx.draw_color("minority_color",
                                                exclude={0})))
    n_other_palette = int(overrides.get("other_palette_size",
                                        ctx.draw_int("other_palette_size", p_lo, p_hi)))
    # Cap palette so each majority color can hold >=2 cells (strictly
    # more than 1 minority) -> the minority stays UNIQUELY least-frequent.
    # need n_minority(>=1) + 2*p <= n_total, so p <= (n_total - 1) // 2.
    max_palette = max(1, (n_total - 1) // 2)
    n_other_palette = max(1, min(n_other_palette, max_palette))
    other_palette = ctx.draw_distinct_colors(
        "other_palette", n=n_other_palette, exclude={minority, 0})

    # minority count: strictly less than each majority color's count.
    # With p palette colors sharing (n_total - n_min) cells, the smallest
    # majority count is ~ (n_total - n_min) / p; require n_min < that.
    p = len(other_palette)
    # keep each majority >= n_minority + 1: n_min*1 + (n_min+1)*p <= n_total
    max_min = max(1, (n_total - p) // (p + 1))
    n_minority = int(overrides.get("minority_count",
                                   ctx.draw_int("minority_count", 1,
                                                min(3, max_min))))
    n_minority = max(1, min(max_min, n_minority))
    layout = (overrides.get("texture")
              or overrides.get("other_layout")
              or ctx.draw_choice("other_layout", list(OTHER_LAYOUTS)))

    g = full_grid(h, w, other_palette[0])

    cells = [(r, c) for r in range(h) for c in range(w)]
    minority_positions = rng.sample(cells, n_minority)
    other_positions = [c for c in cells if c not in minority_positions]

    if layout == "uniform":
        color = other_palette[0]
        for r, c in other_positions:
            g[r][c] = color
    elif layout == "two_colors" and len(other_palette) >= 2:
        a = other_palette[0]; b = other_palette[1]
        rng.shuffle(other_positions)
        split = max(n_minority + 1, len(other_positions) // 2)
        for r, c in other_positions[:split]:
            g[r][c] = a
        for r, c in other_positions[split:]:
            g[r][c] = b
    elif layout == "striped":
        for r, c in other_positions:
            g[r][c] = other_palette[r % len(other_palette)]
    elif layout == "checker":
        a = other_palette[0]
        b = other_palette[1] if len(other_palette) > 1 else a
        for r, c in other_positions:
            g[r][c] = a if (r + c) % 2 == 0 else b
    elif layout == "diagonal_split":
        a = other_palette[0]
        b = other_palette[1] if len(other_palette) > 1 else a
        for r, c in other_positions:
            g[r][c] = a if r >= c else b
    else:
        for r, c in other_positions:
            g[r][c] = rng.choice(other_palette)

    for r, c in minority_positions:
        g[r][c] = minority

    # Enforce: minority strictly least-frequent than every other color.
    # Bump any tying/under majority by recoloring minority cells.
    def _counts():
        cc: dict = {}
        for r in range(h):
            for c in range(w):
                cc[g[r][c]] = cc.get(g[r][c], 0) + 1
        return cc

    for _ in range(n_total):
        counts = _counts()
        if minority not in counts:
            # over-bumped: re-add one minority cell on an other-position
            if other_positions:
                r, c = other_positions[-1]
                g[r][c] = minority
                continue
            break
        bad = [col for col, n in counts.items()
               if col != minority and n <= counts[minority]]
        if not bad:
            break
        # recolor one minority cell to the offending majority color
        if minority_positions:
            r, c = minority_positions.pop()
            g[r][c] = bad[0]
        else:
            break
    return g


def _draw_from_degenerate(name, ctx, rng):
    """Edge-case where the minority-gated self-tile signal collapses.

    tied_minorities — two colors share the lowest count; minority is
                      ambiguous.
    monochrome      — uniform input; minority is undefined / non-existent.
    all_unique      — every cell a different color; many "minorities".
    """
    palette = ctx.draw_distinct_colors("palette", n=9)
    g = full_grid(3, 3, palette[0])
    if name == "tied_minorities":
        # Two cells of color A, two of B (tie for minority), rest a third color.
        for r in range(3):
            for c in range(3):
                g[r][c] = palette[2]
        cells = [(r, c) for r in range(3) for c in range(3)]
        rng.shuffle(cells)
        g[cells[0][0]][cells[0][1]] = palette[0]
        g[cells[1][0]][cells[1][1]] = palette[0]
        g[cells[2][0]][cells[2][1]] = palette[1]
        g[cells[3][0]][cells[3][1]] = palette[1]
        return g
    if name == "monochrome":
        color = rng.choice(palette)
        for r in range(3):
            for c in range(3):
                g[r][c] = color
        return g
    if name == "all_unique":
        rng.shuffle(palette)
        for i, color in enumerate(palette[:9]):
            g[i // 3][i % 3] = color
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    h, w = len(grid), len(grid[0])
    if not (2 <= h <= 4 and 2 <= w <= 4):
        errors.append(f"default grid should be 2..4 by 2..4 after v3 generalization, got {h}x{w}")
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    if len(counts) < 2:
        errors.append("expected at least two colors")
    min_count = min(counts.values())
    minorities = [v for v, n in counts.items() if n == min_count]
    if len(minorities) != 1:
        errors.append(f"minority color must be unique, got {minorities}")
    return errors

