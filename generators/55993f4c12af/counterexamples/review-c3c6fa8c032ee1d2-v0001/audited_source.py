"""Generator for ARC task d19f7514.

Rule: input is 2h × w (no separator). Output is h × w: OR of nonzero
across top/bot halves → 4, else 0.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "55993f4c12af"
VERSION = "2.2.0"  # ensure OR has both overlap and single-half witnesses; add self_check
TASK_ID = "55993f4c12af"
SUMMARY = (
    "0-bg grid of even height 2*hh × w (hh=3..7, w=3..14) with the "
    "TOP half (rows 0..hh-1) using one non-zero non-4 color and "
    "the BOTTOM half (rows hh..2hh-1) using a DIFFERENT non-zero "
    "non-4 color. Each half is filled per a random pattern "
    "(random/blob/stripes/checker/border/diagonal) at varying "
    "density. At least one (r, c) position has overlap (both halves "
    "non-zero) and some have only one half non-zero. Rule: output "
    "is hh × w. For each (r, c) in 0..hh-1, output[r][c] = 4 if "
    "input[r][c] != 0 OR input[r+hh][c] != 0, else 0. Output uses "
    "only colors {0, 4}; input colors don't survive."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "input height is even = 2*hh",
    "top half uses one non-zero non-4 color; bottom half uses a different one",
    "≥1 (r, c) position has both halves non-zero (so OR matters)",
    "≥1 (r, c) position has only one half non-zero (so OR vs AND distinguish)",
]

PANEL_PATTERNS = ("random", "blob", "stripes", "checker", "border", "diagonal")
DEGENERATE_TEXTURES = ("all_zero", "all_filled", "disjoint_halves")
HELPFUL_TEXTURES = PANEL_PATTERNS

AXES = {
    "half_h":         {"type": "int", "default": "rng 3..7", "valid": "1..15"},
    "grid_w":         {"type": "int", "default": "rng 3..14", "valid": "1..30"},
    "top_color":      {"type": "color", "default": "rng (≠0,4)", "valid": "1..9 (≠4)"},
    "bot_color":      {"type": "color", "default": "rng (≠0,4,top)", "valid": "1..9 (≠4)"},
    "top_density":    {"type": "float", "default": "rng 0.3..0.6", "valid": "0..1"},
    "bot_density":    {"type": "float", "default": "rng 0.3..0.6", "valid": "0..1"},
    "panel_pattern":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PANEL_PATTERNS)},
    "or_target":      {"type": "int", "default": "rng 1..max", "valid": "1..h*w"},
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
    top_c = int(overrides.get("top_color", ctx.draw_color("top_color", exclude={0, 4})))
    bot_c = int(overrides.get("bot_color", ctx.draw_color("bot_color", exclude={0, 4, top_c})))
    td = float(overrides.get("top_density",
                             ctx.draw_rng("top_density").uniform(0.3, 0.6)))
    bd = float(overrides.get("bot_density",
                             ctx.draw_rng("bot_density").uniform(0.3, 0.6)))
    pattern = (overrides.get("texture") or overrides.get("panel_pattern")
               or ctx.draw_choice("panel_pattern", list(PANEL_PATTERNS)))
    g = full_grid(2 * half_h, w, 0)
    _fill_panel(g, 0, half_h, w, pattern, td, top_c, rng)
    _fill_panel(g, half_h, 2 * half_h, w, pattern, bd, bot_c, rng)
    target = int(overrides.get("or_target",
                               ctx.draw_int("or_target", 1, max(1, half_h))))
    _ensure_or(g, half_h, w, target, top_c, rng)
    _ensure_or_witnesses(g, half_h, w, top_c, bot_c, rng)
    _ensure_empty_or_witness(g, half_h, w)
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


def _ensure_or(g, half_h, w, target, top_c, rng):
    have = sum(1 for r in range(half_h) for c in range(w)
               if g[r][c] != 0 or g[half_h + r][c] != 0)
    if have >= target:
        return
    cells = [(r, c) for r in range(half_h) for c in range(w)]
    rng.shuffle(cells)
    for (r, c) in cells:
        if have >= target:
            break
        if g[r][c] == 0 and g[half_h + r][c] == 0:
            g[r][c] = top_c
            have += 1


def _ensure_or_witnesses(g, half_h, w, top_c, bot_c, rng):
    """Ensure default episodes exercise OR, not only copy/fill cardinality.

    Several panel patterns (stripes/checker/border/diagonal) paint identical
    support in both halves, so every nonzero position is overlap-only. Other
    sparse patterns can by chance have no overlap. The task's own invariants
    require BOTH witness types: at least one cell where both halves are nonzero
    and at least one cell where exactly one half is nonzero.
    """
    cells = [(r, c) for r in range(half_h) for c in range(w)]
    rng.shuffle(cells)

    def has_overlap():
        return any(g[r][c] != 0 and g[half_h + r][c] != 0 for r, c in cells)

    def has_single():
        return any((g[r][c] != 0) != (g[half_h + r][c] != 0) for r, c in cells)

    if not has_overlap():
        r, c = cells[0]
        g[r][c] = top_c
        g[half_h + r][c] = bot_c

    if not has_single():
        for r, c in cells:
            # Prefer not to destroy the overlap witness we may just have created.
            if not (g[r][c] != 0 and g[half_h + r][c] != 0):
                g[r][c] = top_c
                g[half_h + r][c] = 0
                return
        # All cells overlap; with half_h>=3 and w>=3 there is always a second
        # cell. Make one top-only while leaving at least one overlap intact.
        r, c = cells[-1]
        g[r][c] = top_c
        g[half_h + r][c] = 0


def _ensure_empty_or_witness(g, half_h, w):
    """Keep at least one output-background witness in normal rows.

    Dense patterns can otherwise make the OR target all 4s, hiding the else
    branch of the rule.  The old implementation cleared the first pair from
    the lower-right corner; for opposite-parity checker panels this could erase
    the single overlap witness that `_ensure_or_witnesses` just created.  Clear
    a non-essential pair instead, preserving at least one overlap and one
    single-half witness whenever possible.
    """
    pairs = [(r, c) for r in range(half_h) for c in range(w)]
    if any(g[r][c] == 0 and g[half_h + r][c] == 0 for r, c in pairs):
        return

    overlap = [(r, c) for r, c in pairs if g[r][c] != 0 and g[half_h + r][c] != 0]
    single = [(r, c) for r, c in pairs if (g[r][c] != 0) != (g[half_h + r][c] != 0)]
    protected = set()
    if overlap:
        protected.add(overlap[0])
    if single:
        protected.add(single[0])

    for r in range(half_h - 1, -1, -1):
        for c in range(w - 1, -1, -1):
            if (r, c) in protected:
                continue
            g[r][c] = 0
            g[half_h + r][c] = 0
            return

    # Tiny override grids can leave every pair protected.  Fall back to any pair:
    # self_check will still reject impossible 1-cell cases, while normal draws
    # are at least 3x3 and take the preserving branch above.
    r, c = pairs[-1]
    g[r][c] = 0
    g[half_h + r][c] = 0


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["grid is not a nonempty rectangular list"]
    widths = {len(row) for row in grid}
    if len(widths) != 1 or 0 in widths:
        return ["grid is ragged or has empty rows"]
    h, w = len(grid), len(grid[0])
    if h % 2:
        errs.append(f"input height is odd ({h}); expected 2*half_h")
        return errs
    half_h = h // 2
    top_colors = {grid[r][c] for r in range(half_h) for c in range(w) if grid[r][c] != 0}
    bot_colors = {grid[half_h + r][c] for r in range(half_h) for c in range(w) if grid[half_h + r][c] != 0}
    if len(top_colors) != 1:
        errs.append(f"top half should use exactly one nonzero color, got {sorted(top_colors)}")
    if len(bot_colors) != 1:
        errs.append(f"bottom half should use exactly one nonzero color, got {sorted(bot_colors)}")
    if top_colors & ({0, 4}):
        errs.append(f"top color uses reserved 0/4: {sorted(top_colors)}")
    if bot_colors & ({0, 4}):
        errs.append(f"bottom color uses reserved 0/4: {sorted(bot_colors)}")
    if top_colors and bot_colors and top_colors == bot_colors:
        errs.append(f"top/bottom colors not distinct: {sorted(top_colors)}")
    overlap = single = 0
    for r in range(half_h):
        for c in range(w):
            top = grid[r][c] != 0
            bot = grid[half_h + r][c] != 0
            overlap += int(top and bot)
            single += int(top != bot)
    if overlap == 0:
        errs.append("no cell has both halves nonzero; OR overlap witness missing")
    if single == 0:
        errs.append("no cell has exactly one nonzero half; OR-vs-AND witness missing")
    empty = sum(1 for r in range(half_h) for c in range(w)
                if grid[r][c] == 0 and grid[half_h + r][c] == 0)
    if empty == 0:
        errs.append("no all-background pair; OR else-branch witness missing")
    return errs


def _draw_from_degenerate(name, half_h, w, rng):
    g = full_grid(2 * half_h, w, 0)
    top_c = rng.choice([1, 2, 3, 5])
    bot_c = rng.choice([6, 7, 8, 9])
    if name == "all_zero":
        return g
    if name == "all_filled":
        for r in range(half_h):
            for c in range(w):
                g[r][c] = top_c
                g[half_h + r][c] = bot_c
        return g
    if name == "disjoint_halves":
        for r in range(half_h):
            for c in range(w):
                if rng.random() < 0.5:
                    g[r][c] = top_c
                else:
                    g[half_h + r][c] = bot_c
        return g
    return g
