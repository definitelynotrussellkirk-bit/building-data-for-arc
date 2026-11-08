"""Generator for ARC task 195ba7dc.

Rule: input is h × 13 with separator at col 6. Output is h × 6:
left[r][c] != 0 OR right[r][c] != 0 → 1, else 0. (OR mask.)

Combinatorial axes: grid_h, fg_color_l/r, sep_color, density l/r,
panel_pattern, or_target. Degenerates: all_zero / all_filled /
disjoint_panels.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3970e6f97ab0"
VERSION = "1.1.2"  # ensure OR-mask output is neither empty nor solid; add stricter self_check
TASK_ID = "3970e6f97ab0"
SUMMARY = "Two 6-column panels separated by a marker; OR of nonzero-occupancy → 1, else 0."

INVARIANTS = [
    "input width is 13 (6 left + 1 separator + 6 right)",
    "panels use 0 + non-zero colors",
    "≥1 non-zero cell across the panels",
]

PANEL_PATTERNS = ("random", "blob", "stripes", "checker", "border", "diagonal", "scatter")
DEGENERATE_TEXTURES = ("all_zero", "all_filled", "disjoint_panels")
HELPFUL_TEXTURES = PANEL_PATTERNS

AXES = {
    "grid_h":        {"type": "int", "default": "rng 3..14", "valid": "1..18"},
    "fg_color_l":    {"type": "color", "default": "rng (≠0)", "valid": "1..9"},
    "fg_color_r":    {"type": "color", "default": "rng (≠0)", "valid": "1..9"},
    "sep_color":     {"type": "color", "default": "rng (≠0)", "valid": "1..9"},
    "left_density":  {"type": "float", "default": "rng 0.2..0.6", "valid": "0..1"},
    "right_density": {"type": "float", "default": "rng 0.2..0.6", "valid": "0..1"},
    "panel_pattern": {"type": "str", "default": "rng helpful",
                      "valid": "random|blob|stripes|checker|border|diagonal|scatter"},
    "or_target":     {"type": "int", "default": "rng 1..h*6", "valid": "1..h*6"},
    "texture":       {"type": "str", "default": "alias for panel_pattern",
                      "valid": "random|blob|stripes|checker|border|diagonal|scatter|all_zero|all_filled|disjoint_panels"},
}


def _or_mask_counts(grid):
    """Return (#ones, #zeros) in the oracle's 6-column OR mask."""
    h = len(grid)
    ones = zeros = 0
    for r in range(h):
        for c in range(6):
            if grid[r][c] != 0 or grid[r][c + 7] != 0:
                ones += 1
            else:
                zeros += 1
    return ones, zeros


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify width=13 and a non-trivial OR mask with both 0 and 1 cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    for r in range(h):
        for c in range(w):
            if not (0 <= grid[r][c] <= 9):
                errors.append(f"out-of-range value {grid[r][c]} at ({r},{c})")
    if w != 13:
        errors.append(f"expected width 13, got {w}")
    if not errors:
        ones, zeros = _or_mask_counts(grid)
        if ones == 0:
            errors.append("OR mask is empty; transformation is not demonstrated")
        if zeros == 0:
            errors.append("OR mask is solid; output collapses to an all-1 grid")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 3, 6
    elif difficulty == "hard":
        h_lo, h_hi = 11, 14
    else:
        h_lo, h_hi = 3, 14
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    rng = ctx.draw_rng("panels")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, rng)
    fg_l = int(overrides.get("fg_color_l", ctx.draw_color("fg_color_l", exclude={0})))
    fg_r = int(overrides.get("fg_color_r", ctx.draw_color("fg_color_r", exclude={0, fg_l})))
    sep = int(overrides.get("sep_color", ctx.draw_color("sep_color", exclude={0, fg_l, fg_r})))
    ld = float(overrides.get("left_density",
                             ctx.draw_rng("left_density").uniform(0.2, 0.6)))
    rd = float(overrides.get("right_density",
                             ctx.draw_rng("right_density").uniform(0.2, 0.6)))
    pattern = (overrides.get("texture")
               or overrides.get("panel_pattern")
               or ctx.draw_choice("panel_pattern", list(PANEL_PATTERNS)))
    g = full_grid(h, 13, 0)
    for r in range(h):
        g[r][6] = sep
    _fill_panel(g, 0, 6, h, pattern, ld, fg_l, rng)
    _fill_panel(g, 7, 13, h, pattern, rd, fg_r, rng)
    target = int(overrides.get("or_target",
                               ctx.draw_int("or_target", 1, max(1, h))))
    _ensure_or(g, h, target, fg_l, rng)
    _ensure_nontrivial_or_mask(g, h, fg_l, rng)
    return g


def _fill_panel(g, c0, c1, h, pattern, density, fg, rng):
    if pattern == "random":
        for r in range(h):
            for c in range(c0, c1):
                g[r][c] = fg if rng.random() < density else 0
    elif pattern == "blob":
        bh = max(1, int(h * density)); bw = max(1, int((c1 - c0) * density))
        r0 = rng.randint(0, h - bh); cc0 = rng.randint(c0, c1 - bw)
        for r in range(r0, r0 + bh):
            for c in range(cc0, cc0 + bw):
                g[r][c] = fg
    elif pattern == "stripes":
        for r in range(h):
            if r % 2 == 0:
                for c in range(c0, c1):
                    g[r][c] = fg
    elif pattern == "checker":
        for r in range(h):
            for c in range(c0, c1):
                if (r + c) % 2 == 0:
                    g[r][c] = fg
    elif pattern == "border":
        for c in range(c0, c1):
            g[0][c] = fg; g[h - 1][c] = fg
        for r in range(h):
            g[r][c0] = fg; g[r][c1 - 1] = fg
    elif pattern == "diagonal":
        for k in range(min(h, c1 - c0)):
            g[k][c0 + k] = fg
    elif pattern == "scatter":
        for r in range(h):
            for c in range(c0, c1):
                if rng.random() < density * 0.5:
                    g[r][c] = fg


def _ensure_or(g, h, target, fg, rng):
    have = sum(1 for r in range(h) for c in range(6)
               if g[r][c] != 0 or g[r][c + 7] != 0)
    if have >= target:
        return
    cells = [(r, c) for r in range(h) for c in range(6)]
    rng.shuffle(cells)
    for (r, c) in cells:
        if have >= target: break
        if g[r][c] == 0 and g[r][c + 7] == 0:
            g[r][c] = fg
            have += 1


def _ensure_nontrivial_or_mask(g, h, fg, rng):
    """Keep default examples informative: at least one 1 and one 0 in the OR mask."""
    ones, zeros = _or_mask_counts(g)
    if ones == 0:
        r = rng.randrange(h); c = rng.randrange(6)
        g[r][c] = fg
        ones, zeros = _or_mask_counts(g)
    if zeros == 0:
        cells = [(r, c) for r in range(h) for c in range(6)]
        rng.shuffle(cells)
        r, c = cells[0]
        g[r][c] = 0
        g[r][c + 7] = 0


def _draw_from_degenerate(name, h, rng):
    g = full_grid(h, 13, 0)
    fg_l = rng.choice([1, 2, 3, 4, 5])
    fg_r = rng.choice([6, 7, 8, 9])
    sep = rng.choice([c for c in range(1, 10) if c not in {fg_l, fg_r}])
    for r in range(h):
        g[r][6] = sep
    if name == "all_zero":
        return g
    if name == "all_filled":
        for r in range(h):
            for c in range(6):
                g[r][c] = fg_l
                g[r][c + 7] = fg_r
        return g
    if name == "disjoint_panels":
        for r in range(h):
            for c in range(6):
                if rng.random() < 0.5:
                    g[r][c] = fg_l
                else:
                    g[r][c + 7] = fg_r
        return g
    return g
