"""Generator for ARC task 6430c8c4.

Rule: input is 9 × w (4 top + 1 sep + 4 bot). Output is 4 × w:
top[r][c]==0 AND bot[r][c]==0 → 3, else 0. (Both-zero mask.)
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e110503c4f88"
VERSION = "1.3.0"  # wider widths + executable self_check for both-zero-mask evidence
TASK_ID = "e110503c4f88"
SUMMARY = "Two 4-row panels separated by row 4; aligned both-zero cells become 3."

INVARIANTS = [
    "input height is 9 (4 top + 1 separator + 4 bot)",
    "row 4 is a separator",
    "≥1 aligned cell pair is both zero",
]

PANEL_PATTERNS = ("random", "blob", "stripes", "checker", "border", "diagonal")
DEGENERATE_TEXTURES = ("no_both_zero", "all_both_zero", "same_panels")
HELPFUL_TEXTURES = PANEL_PATTERNS

AXES = {
    "grid_w":         {"type": "int", "default": "rng 6..18", "valid": "3..24"},
    "top_color":      {"type": "color", "default": "rng (≠0)", "valid": "1..9"},
    "bot_color":      {"type": "color", "default": "rng (≠0,top)", "valid": "1..9"},
    "sep_color":      {"type": "color", "default": "rng (≠0)", "valid": "1..9"},
    "top_density":    {"type": "float", "default": "rng 0.3..0.6", "valid": "0..1"},
    "bot_density":    {"type": "float", "default": "rng 0.3..0.6", "valid": "0..1"},
    "panel_pattern":  {"type": "str", "default": "rng helpful",
                       "valid": "random|blob|stripes|checker|border|diagonal"},
    "both_zero_target": {"type": "int", "default": "rng 1..max", "valid": "1..4*w"},
    "texture":        {"type": "str", "default": "alias for panel_pattern",
                       "valid": "random|blob|stripes|checker|border|diagonal|no_both_zero|all_both_zero|same_panels"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the aligned both-zero mask task."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular and nonempty"]
    h, w = len(grid), len(grid[0])
    errs = []
    if h != 9:
        errs.append(f"expected height 9 (4 + sep + 4), found {h}")
        return errs
    if w < 3:
        errs.append(f"expected width >=3 for teachable row masks, found {w}")
    sep_colors = set(grid[4])
    if len(sep_colors) != 1 or 0 in sep_colors:
        errs.append(f"row 4 should be a solid nonzero separator, found {sorted(sep_colors)}")
    panel_values = [grid[r][c] for r in list(range(4)) + list(range(5, 9)) for c in range(w)]
    nonzero_panel_colors = {v for v in panel_values if v != 0}
    if len(nonzero_panel_colors) < 2:
        errs.append(f"expected two distinct nonzero panel colors, found {sorted(nonzero_panel_colors)}")
    both_zero = [(r, c) for r in range(4) for c in range(w)
                 if grid[r][c] == 0 and grid[5 + r][c] == 0]
    if not both_zero:
        errs.append("expected at least one aligned both-zero cell pair")
    if len(both_zero) == 4 * w:
        errs.append("all aligned pairs are zero; output mask would hide the panel evidence")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        w_lo, w_hi = 4, 8
    elif difficulty == "hard":
        w_lo, w_hi = 14, 24
    else:
        w_lo, w_hi = 6, 18
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("panels")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], w, rng)
    top_color = int(overrides.get("top_color", ctx.draw_color("top_color", exclude={0})))
    bot_color = int(overrides.get("bot_color", ctx.draw_color("bot_color", exclude={0, top_color})))
    sep = int(overrides.get("sep_color", ctx.draw_color("sep_color", exclude={0, top_color, bot_color})))
    td = float(overrides.get("top_density",
                             ctx.draw_rng("top_density").uniform(0.3, 0.6)))
    bd = float(overrides.get("bot_density",
                             ctx.draw_rng("bot_density").uniform(0.3, 0.6)))
    pattern = (overrides.get("texture")
               or overrides.get("panel_pattern")
               or ctx.draw_choice("panel_pattern", list(PANEL_PATTERNS)))
    g = full_grid(9, w, 0)
    for c in range(w):
        g[4][c] = sep
    _fill_panel(g, 0, 4, w, pattern, td, top_color, rng)
    _fill_panel(g, 5, 9, w, pattern, bd, bot_color, rng)
    target_hi = max(2, min(4 * w - 1, (4 * w) // 2))
    target = int(overrides.get("both_zero_target",
                               ctx.draw_int("both_zero_target", 1, target_hi)))
    _ensure_both_zero(g, w, target, rng)
    return g


def _fill_panel(g, r0, r1, w, pattern, density, fg, rng):
    h_p = r1 - r0
    if pattern == "random":
        for r in range(r0, r1):
            for c in range(w):
                g[r][c] = fg if rng.random() < density else 0
    elif pattern == "blob":
        bh = max(1, int(h_p * density)); bw = max(1, int(w * density))
        rr = rng.randint(r0, r1 - bh); cc = rng.randint(0, w - bw)
        for r in range(rr, rr + bh):
            for c in range(cc, cc + bw):
                g[r][c] = fg
    elif pattern == "stripes":
        for r in range(r0, r1):
            if (r - r0) % 2 == 0:
                for c in range(w):
                    g[r][c] = fg
    elif pattern == "checker":
        for r in range(r0, r1):
            for c in range(w):
                if (r + c) % 2 == 0:
                    g[r][c] = fg
    elif pattern == "border":
        for c in range(w):
            g[r0][c] = fg; g[r1 - 1][c] = fg
        for r in range(r0, r1):
            g[r][0] = fg; g[r][w - 1] = fg
    elif pattern == "diagonal":
        for k in range(min(h_p, w)):
            g[r0 + k][k] = fg


def _ensure_both_zero(g, w, target, rng):
    have = sum(1 for r in range(4) for c in range(w)
               if g[r][c] == 0 and g[5 + r][c] == 0)
    if have >= target:
        return
    cells = [(r, c) for r in range(4) for c in range(w)]
    rng.shuffle(cells)
    for (r, c) in cells:
        if have >= target: break
        g[r][c] = 0; g[5 + r][c] = 0
        have += 1


def _draw_from_degenerate(name, w, rng):
    g = full_grid(9, w, 0)
    top_c = rng.choice([1, 2, 3, 4, 5])
    bot_c = rng.choice([6, 7, 8, 9])
    sep = rng.choice([c for c in range(1, 10) if c not in {top_c, bot_c}])
    for c in range(w):
        g[4][c] = sep
    if name == "no_both_zero":
        for r in range(4):
            for c in range(w):
                g[r][c] = top_c
                g[5 + r][c] = 0 if rng.random() < 0.4 else bot_c
        return g
    if name == "all_both_zero":
        return g
    if name == "same_panels":
        for r in range(4):
            for c in range(w):
                v = top_c if rng.random() < 0.5 else 0
                g[r][c] = v
                g[5 + r][c] = (bot_c if v != 0 else 0)
        return g
    return g
