"""Generator for puzzle 94f9d214.

Rule: input is 2h × w (no separator). Output is h × w: top[r][c]==0
AND bot[r][c]==0 → 2, else 0. Same shape as fafffa47.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4043070e87c0"
VERSION = "2.0.0"
TASK_ID = "4043070e87c0"
SUMMARY = (
    "0-bg grid of EVEN HEIGHT (2 × half_h, "
    "where half_h ∈ {3..7}) × WIDTH w ∈ "
    "{3..14}: (a) TOP HALF (rows 0..half_h-"
    "1) filled with TOP_COLOR (non-{0, 2}) "
    "via one of 6 PANEL_PATTERNS (random / "
    "blob / stripes / checker / border / "
    "diagonal) at density 0.3..0.6; "
    "(b) BOTTOM HALF (rows half_h..2 * "
    "half_h - 1) filled with BOT_COLOR "
    "(distinct from {0, 2, top_color}) "
    "using the same pattern type at "
    "independent density 0.3..0.6. NO "
    "SEPARATOR ROW between the halves. At "
    "least 1 cell-pair (r, c) has g[r][c] "
    "= 0 AND g[half_h+r][c] = 0 (enforced "
    "via _ensure_both_zero). Rule (PRODUCE "
    "AN h × w OUTPUT: BOTH-ZERO CELL PAIRS "
    "BECOME 2, ELSE 0): COMPUTE a fresh "
    "half_h × w OUTPUT grid. For EACH "
    "(r, c) with r ∈ [0, half_h-1] and "
    "c ∈ [0, w-1]: IF g[r][c] = 0 AND "
    "g[half_h+r][c] = 0 → output[r][c] "
    "= 2; ELSE output[r][c] = 0. The "
    "output is HALF the input's height. "
    "Net: a cell-wise NOR of the two "
    "stacked panels, emitted as 2s on a "
    "bg-0 half-height grid."
)

INVARIANTS = [
    "input height is even (2*half_h)",
    "halves use 0 + non-zero colors",
    "≥1 cell-pair is both zero",
]

PANEL_PATTERNS = ("random", "blob", "stripes", "checker", "border", "diagonal")
DEGENERATE_TEXTURES = ("no_both_zero", "all_both_zero", "same_halves")
HELPFUL_TEXTURES = PANEL_PATTERNS

AXES = {
    "half_h":         {"type": "int", "default": "rng 3..7", "valid": "1..15"},
    "grid_w":         {"type": "int", "default": "rng 3..14", "valid": "1..30"},
    "top_color":      {"type": "color", "default": "rng (≠0,2)", "valid": "1..9 (≠2)"},
    "bot_color":      {"type": "color", "default": "rng (≠0,2,top)", "valid": "1..9 (≠2)"},
    "top_density":    {"type": "float", "default": "rng 0.3..0.6", "valid": "0..1"},
    "bot_density":    {"type": "float", "default": "rng 0.3..0.6", "valid": "0..1"},
    "panel_pattern":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PANEL_PATTERNS)},
    "both_zero_target": {"type": "int", "default": "rng 1..max", "valid": "1..h*w"},
    "texture":        {"type": "str", "default": "alias for panel_pattern",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 3, 4, 3, 5
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 6, 7, 10, 14
    else:
        h_lo, h_hi, w_lo, w_hi = 3, 7, 3, 14
    half_h = ctx.draw_int("half_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("panels")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], half_h, w, rng)
    top_c = int(overrides.get("top_color", ctx.draw_color("top_color", exclude={0, 2})))
    bot_c = int(overrides.get("bot_color", ctx.draw_color("bot_color", exclude={0, 2, top_c})))
    td = float(overrides.get("top_density",
                             ctx.draw_rng("top_density").uniform(0.3, 0.6)))
    bd = float(overrides.get("bot_density",
                             ctx.draw_rng("bot_density").uniform(0.3, 0.6)))
    pattern = (overrides.get("texture") or overrides.get("panel_pattern")
               or ctx.draw_choice("panel_pattern", list(PANEL_PATTERNS)))
    g = full_grid(2 * half_h, w, 0)
    _fill_panel(g, 0, half_h, w, pattern, td, top_c, rng)
    _fill_panel(g, half_h, 2 * half_h, w, pattern, bd, bot_c, rng)
    target = int(overrides.get("both_zero_target",
                               ctx.draw_int("both_zero_target", 1, max(1, half_h))))
    _ensure_both_zero(g, half_h, w, target, rng)
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


def _ensure_both_zero(g, half_h, w, target, rng):
    have = sum(1 for r in range(half_h) for c in range(w)
               if g[r][c] == 0 and g[half_h + r][c] == 0)
    if have >= target:
        return
    cells = [(r, c) for r in range(half_h) for c in range(w)]
    rng.shuffle(cells)
    for (r, c) in cells:
        if have >= target: break
        g[r][c] = 0; g[half_h + r][c] = 0
        have += 1


def _draw_from_degenerate(name, half_h, w, rng):
    g = full_grid(2 * half_h, w, 0)
    top_c = rng.choice([1, 3, 4, 5])
    bot_c = rng.choice([6, 7, 8, 9])
    if name == "no_both_zero":
        for r in range(half_h):
            for c in range(w):
                g[r][c] = top_c
                g[half_h + r][c] = 0 if rng.random() < 0.4 else bot_c
        return g
    if name == "all_both_zero":
        return g
    if name == "same_halves":
        for r in range(half_h):
            for c in range(w):
                v = top_c if rng.random() < 0.5 else 0
                g[r][c] = v
                g[half_h + r][c] = (bot_c if v != 0 else 0)
        return g
    return g
def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if h % 2:
        errors.append("input height must be even")
        return errors
    half_h = h // 2
    if any(v == 2 for row in grid for v in row):
        errors.append("input colors must exclude output marker color 2")
    both_zero = sum(1 for r in range(half_h) for c in range(w)
                    if grid[r][c] == 0 and grid[half_h + r][c] == 0)
    if both_zero == 0:
        errors.append("no top/bottom cell-pair is both zero")
    if both_zero == half_h * w:
        errors.append("all cell-pairs are both zero; no negative contrast")
    top_nz = {grid[r][c] for r in range(half_h) for c in range(w) if grid[r][c] != 0}
    bot_nz = {grid[half_h + r][c] for r in range(half_h) for c in range(w)
              if grid[half_h + r][c] != 0}
    if not top_nz or not bot_nz:
        errors.append("both halves need nonzero panel evidence")
    return errors
