"""Generator for ARC task 3428a4f5.

Rule: input is 13 × w (6 top + 1 sep + 6 bot). Output is 6 × w:
XOR of zero-occupancy across panels — exactly one zero → 3, else 0.

Combinatorial axes: grid_w, top_color/density, bot_color/density,
sep_color, panel_pattern, xor_target. Degenerates: same_panels (all 0),
disjoint_panels (all 3), all_filled.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ac3c9342fc5c"
VERSION = "2.1.0"  # guarantee a MIXED output: >=1 XOR-false cell so 'checker' (parity-flipped by +7 offset) no longer yields a solid-3 output
TASK_ID = "ac3c9342fc5c"
SUMMARY = (
    "Input is 13 × w (w ~3-14). Rows 0-5 = TOP panel, row "
    "6 = solid-color separator, rows 7-12 = BOTTOM panel. "
    "Each panel filled with some pattern (random/blob/"
    "stripes/checker/border/diagonal) at a chosen density "
    "in some color. Rule: output is 6 × w. For each (r, c) "
    "with r ∈ [0,5]: output[r][c] = 3 (green) IFF "
    "(input[r][c] == 0) XOR (input[r+7][c] == 0) — i.e. "
    "exactly ONE of the two panels has a zero at that cell "
    "(equivalently: the cells differ in zero/non-zero). "
    "Otherwise 0."
)

INVARIANTS = [
    "input height is 13 (6 top + 1 separator + 6 bot)",
    "row 6 is a separator",
    "≥1 cell differs in zero-occupancy across panels",
]

PANEL_PATTERNS = ("random", "blob", "stripes", "checker", "border", "diagonal")
DEGENERATE_TEXTURES = ("same_panels", "disjoint_panels", "all_filled")
HELPFUL_TEXTURES = PANEL_PATTERNS

AXES = {
    "grid_w":         {"type": "int", "default": "rng 3..14", "valid": "1..30"},
    "top_color":      {"type": "color", "default": "rng (≠0)", "valid": "1..9"},
    "bot_color":      {"type": "color", "default": "rng (≠0,top)", "valid": "1..9"},
    "sep_color":      {"type": "color", "default": "rng (≠0)", "valid": "1..9"},
    "top_density":    {"type": "float", "default": "rng 0.3..0.7", "valid": "0..1"},
    "bot_density":    {"type": "float", "default": "rng 0.3..0.7", "valid": "0..1"},
    "panel_pattern":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PANEL_PATTERNS)},
    "xor_target":     {"type": "int", "default": "rng 1..max", "valid": "1..6*w"},
    "texture":        {"type": "str", "default": "alias for panel_pattern",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        w_lo, w_hi = 3, 5
    elif difficulty == "hard":
        w_lo, w_hi = 10, 14
    else:
        w_lo, w_hi = 3, 14
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("panels")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], w, rng)
    top_color = int(overrides.get("top_color", ctx.draw_color("top_color", exclude={0})))
    bot_color = int(overrides.get("bot_color", ctx.draw_color("bot_color", exclude={0, top_color})))
    sep = int(overrides.get("sep_color", ctx.draw_color("sep_color", exclude={0, top_color, bot_color})))
    td = float(overrides.get("top_density",
                             ctx.draw_rng("top_density").uniform(0.3, 0.7)))
    bd = float(overrides.get("bot_density",
                             ctx.draw_rng("bot_density").uniform(0.3, 0.7)))
    pattern = (overrides.get("texture")
               or overrides.get("panel_pattern")
               or ctx.draw_choice("panel_pattern", list(PANEL_PATTERNS)))
    g = full_grid(13, w, 0)
    for c in range(w):
        g[6][c] = sep
    _fill_panel(g, 0, 6, w, pattern, td, top_color, rng)
    _fill_panel(g, 7, 13, w, pattern, bd, bot_color, rng)
    target = int(overrides.get("xor_target",
                               ctx.draw_int("xor_target", 1, max(1, 6 * w // 4))))
    _ensure_xor(g, w, target, top_color, rng)
    _ensure_mix(g, w, rng)
    return g


def _ensure_mix(g, w, rng):
    """Guarantee the XOR output is NOT solid: it must have >=1 green (XOR-true) AND
    >=1 zero (XOR-false) cell. `checker` panels are XOR-true everywhere (the +7 row
    offset flips parity), which renders a solid-3 output. Force one XOR-false cell."""
    def xor(r, c):
        return (g[r][c] == 0) != (g[7 + r][c] == 0)
    cells = [(r, c) for r in range(6) for c in range(w)]
    if all(xor(r, c) for r, c in cells):
        r, c = rng.choice(cells)
        g[r][c] = 0
        g[7 + r][c] = 0  # both zero -> XOR-false -> output 0 here


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


def _ensure_xor(g, w, target, top_color, rng):
    have = sum(1 for r in range(6) for c in range(w)
               if (g[r][c] == 0) != (g[7 + r][c] == 0))
    if have >= target:
        return
    cells = [(r, c) for r in range(6) for c in range(w)]
    rng.shuffle(cells)
    for (r, c) in cells:
        if have >= target: break
        # Force a XOR: paint top fg, leave bot bg.
        if g[r][c] == 0 and g[7 + r][c] == 0:
            g[r][c] = top_color
            have += 1


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Input is 13 rows (6 top + separator + 6 bottom). The XOR-of-zero-occupancy
    output (6 x w) must be MIXED — >=1 green and >=1 zero cell — never solid."""
    errs = []
    h = len(grid); w = len(grid[0]) if h else 0
    if h != 13:
        errs.append(f"input height {h} != 13")
        return errs
    trues = sum(1 for r in range(6) for c in range(w)
                if (grid[r][c] == 0) != (grid[7 + r][c] == 0))
    total = 6 * w
    if trues == 0:
        errs.append("XOR output is all zero (no differing cells)")
    if trues == total:
        errs.append("XOR output is solid green (every cell differs) — degenerate")
    return errs


def _draw_from_degenerate(name, w, rng):
    g = full_grid(13, w, 0)
    top_c = rng.choice([1, 2, 3, 4, 5])
    bot_c = rng.choice([6, 7, 8, 9])
    sep = rng.choice([c for c in range(1, 10) if c not in {top_c, bot_c}])
    for c in range(w):
        g[6][c] = sep
    if name == "same_panels":
        for r in range(6):
            for c in range(w):
                v = top_c if rng.random() < 0.5 else 0
                g[r][c] = v
                g[7 + r][c] = v if v == 0 else bot_c
        return g
    if name == "disjoint_panels":
        for r in range(6):
            for c in range(w):
                if rng.random() < 0.5:
                    g[r][c] = top_c
                else:
                    g[7 + r][c] = bot_c
        return g
    if name == "all_filled":
        for r in range(6):
            for c in range(w):
                g[r][c] = top_c
                g[7 + r][c] = bot_c
        return g
    return g
