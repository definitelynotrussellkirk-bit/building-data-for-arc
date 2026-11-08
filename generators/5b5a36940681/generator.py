"""Generator for ARC task 989ce0ec.

Rule: input has a vertical divider col of 9 at the middle. Output is
half-width: cells encode {both non-0 → 4, only_left → 2, only_right → 8,
else → 0}.

Combinatorial axes: grid_h, half_w, left/right density, panel pattern,
encoded_4_target (forces ≥N "both" cells).
Degenerates: only_left (output all 2/0), only_right (output all 8/0),
identical_halves (output all 4 where either is non-0).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5b5a36940681"
VERSION = "1.2.0"
TASK_ID = "5b5a36940681"
SUMMARY = "Two halves separated by col-9 divider; rule encodes XOR/AND of nonzero-occupancy."

INVARIANTS = [
    "vertical divider of color 9 at col = (cols // 2)",
    "≥1 cell is non-zero in exactly one side (so output has 2 or 8)",
    "scattered cells use any non-zero non-9 color",
]

PANEL_PATTERNS = ("scatter", "blob", "stripes", "checker", "border", "diagonal")
DEGENERATE_TEXTURES = ("only_left", "only_right", "identical_halves")
HELPFUL_TEXTURES = PANEL_PATTERNS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 4..12", "valid": "3..15"},
    "half_w":         {"type": "int", "default": "rng 3..7", "valid": "2..14"},
    "left_density":   {"type": "float", "default": "rng 0.2..0.5", "valid": "0..1"},
    "right_density":  {"type": "float", "default": "rng 0.2..0.5", "valid": "0..1"},
    "panel_pattern":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PANEL_PATTERNS)},
    "encoded_4_target": {"type": "int", "default": "rng 1..h*half_w/3",
                         "valid": "0..h*half_w"},
    "texture":        {"type": "str", "default": "alias for panel_pattern",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _ensure_side_only(g, h, half_w, div, palette, rng):
    """Guarantee the normal path exercises overlap / left-only / right-only branches.

    Deterministic patterns can paint the same mask on both halves (collapsing the
    encoded output to only 4s); sparse masks can miss overlap entirely. This post-pass
    preserves the random texture but forces all three cases to appear. (repo-audit fix:
    one-sided 2/8 branches were frequently never exercised -> poisoned demos.)
    """
    def has_both():
        return any(g[r][c] != 0 and g[r][div + 1 + c] != 0
                   for r in range(h) for c in range(half_w))

    def has_left_only():
        return any(g[r][c] != 0 and g[r][div + 1 + c] == 0
                   for r in range(h) for c in range(half_w))

    def has_right_only():
        return any(g[r][c] == 0 and g[r][div + 1 + c] != 0
                   for r in range(h) for c in range(half_w))

    def shuffled_cells():
        cells = [(r, c) for r in range(h) for c in range(half_w)]
        rng.shuffle(cells)
        return cells

    def make_both():
        for r, c in shuffled_cells():
            if g[r][c] == 0 and g[r][div + 1 + c] == 0:
                g[r][c] = rng.choice(palette)
                g[r][div + 1 + c] = rng.choice(palette)
                return
        for r, c in shuffled_cells():
            if g[r][c] != 0 or g[r][div + 1 + c] != 0:
                if g[r][c] == 0:
                    g[r][c] = rng.choice(palette)
                if g[r][div + 1 + c] == 0:
                    g[r][div + 1 + c] = rng.choice(palette)
                return

    def make_left_only():
        for r, c in shuffled_cells():
            if g[r][c] == 0 and g[r][div + 1 + c] == 0:
                g[r][c] = rng.choice(palette)
                return
        for r, c in shuffled_cells():
            if g[r][c] != 0 and g[r][div + 1 + c] != 0:
                g[r][div + 1 + c] = 0
                return

    def make_right_only():
        for r, c in shuffled_cells():
            if g[r][c] == 0 and g[r][div + 1 + c] == 0:
                g[r][div + 1 + c] = rng.choice(palette)
                return
        for r, c in shuffled_cells():
            if g[r][c] != 0 and g[r][div + 1 + c] != 0:
                g[r][c] = 0
                return

    if not has_both():
        make_both()
    if not has_left_only():
        make_left_only()
    if not has_right_only():
        make_right_only()


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, hw_lo, hw_hi = 4, 6, 3, 4
    elif difficulty == "hard":
        h_lo, h_hi, hw_lo, hw_hi = 9, 12, 6, 7
    else:
        h_lo, h_hi, hw_lo, hw_hi = 4, 12, 3, 7
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    half_w = ctx.draw_int("half_w", hw_lo, hw_hi)
    rng = ctx.draw_rng("scatter")
    color_rng = ctx.draw_rng("colors")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, half_w, rng)
    ld = float(overrides.get("left_density",
                             ctx.draw_rng("left_density").uniform(0.2, 0.5)))
    rd = float(overrides.get("right_density",
                             ctx.draw_rng("right_density").uniform(0.2, 0.5)))
    pattern = (overrides.get("texture") or overrides.get("panel_pattern")
               or ctx.draw_choice("panel_pattern", list(PANEL_PATTERNS)))
    w = half_w * 2 + 1
    div = half_w
    g = full_grid(h, w, 0)
    for r in range(h):
        g[r][div] = 9
    palette = [c for c in [1, 2, 3, 4, 5, 6, 7, 8] if c != 9]
    _fill_panel(g, 0, div, h, pattern, ld, palette, color_rng)
    _fill_panel(g, div + 1, w, h, pattern, rd, palette, color_rng)
    target_4 = int(overrides.get("encoded_4_target",
                                 ctx.draw_int("encoded_4_target", 1,
                                              max(1, h * half_w // 3))))
    _ensure_overlaps(g, h, half_w, div, target_4, palette, rng)
    _ensure_side_only(g, h, half_w, div, palette, rng)  # repo-audit: force overlap/left-only/right-only branches
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: color-9 vertical divider at mid-column, >=1 non-zero on each side."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    div = w // 2
    # Check divider column is all 9
    bad_div = [r for r in range(h) if grid[r][div] != 9]
    if bad_div:
        errs.append(f"col {div} (divider) has non-9 cells at rows {bad_div[:3]}")
    # Check at least one non-zero cell somewhere (besides divider)
    left = any(grid[r][c] != 0 for r in range(h) for c in range(div))
    right = any(grid[r][c] != 0 for r in range(h) for c in range(div + 1, w))
    if not left and not right:
        errs.append("no non-zero cells on either side of divider")
    return errs


def _fill_panel(g, c0, c1, h, pattern, density, palette, rng):
    if pattern == "scatter":
        for r in range(h):
            for c in range(c0, c1):
                if rng.random() < density:
                    g[r][c] = rng.choice(palette)
    elif pattern == "blob":
        bh = max(1, int(h * density)); bw = max(1, int((c1 - c0) * density))
        r0 = rng.randint(0, h - bh); cc = rng.randint(c0, c1 - bw)
        color = rng.choice(palette)
        for r in range(r0, r0 + bh):
            for c in range(cc, cc + bw):
                g[r][c] = color
    elif pattern == "stripes":
        for r in range(h):
            if r % 2 == 0:
                color = rng.choice(palette)
                for c in range(c0, c1):
                    g[r][c] = color
    elif pattern == "checker":
        for r in range(h):
            for c in range(c0, c1):
                if (r + c) % 2 == 0:
                    g[r][c] = rng.choice(palette)
    elif pattern == "border":
        c0_color = rng.choice(palette)
        for c in range(c0, c1):
            g[0][c] = c0_color; g[h - 1][c] = c0_color
        for r in range(h):
            g[r][c0] = c0_color; g[r][c1 - 1] = c0_color
    elif pattern == "diagonal":
        for k in range(min(h, c1 - c0)):
            g[k][c0 + k] = rng.choice(palette)


def _ensure_overlaps(g, h, half_w, div, target, palette, rng):
    have = sum(1 for r in range(h) for c in range(half_w)
               if g[r][c] != 0 and g[r][div + 1 + c] != 0)
    if have >= target:
        return
    cells = [(r, c) for r in range(h) for c in range(half_w)]
    rng.shuffle(cells)
    for (r, c) in cells:
        if have >= target: break
        if g[r][c] == 0 and g[r][div + 1 + c] == 0:
            g[r][c] = rng.choice(palette)
            g[r][div + 1 + c] = rng.choice(palette)
            have += 1


def _draw_from_degenerate(name, h, half_w, rng):
    w = half_w * 2 + 1
    div = half_w
    g = full_grid(h, w, 0)
    for r in range(h):
        g[r][div] = 9
    color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])
    if name == "only_left":
        for r in range(h):
            for c in range(0, div):
                if rng.random() < 0.4:
                    g[r][c] = color
        return g
    if name == "only_right":
        for r in range(h):
            for c in range(div + 1, w):
                if rng.random() < 0.4:
                    g[r][c] = color
        return g
    if name == "identical_halves":
        for r in range(h):
            for c in range(half_w):
                if rng.random() < 0.5:
                    g[r][c] = color
                    g[r][div + 1 + c] = color
        return g
    return g
