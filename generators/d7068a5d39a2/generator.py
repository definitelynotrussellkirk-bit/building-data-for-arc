"""Generator for puzzle dae9d2b5.

Rule: input is h × 2w (no separator). Output is h × w: OR of
left|right halves nonzero → 6, else 0.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d7068a5d39a2"
VERSION = "1.6.0"  # canonical-scale defaults plus OR/zero witnesses
TASK_ID = "d7068a5d39a2"
SUMMARY = "Input is h × 2*half_w (two equal-width halves stacked horizontally, no separator). Output is h × half_w: cell (r, c) = 6 if either left[r][c] or right[r][c] is non-zero, else 0."

# Rivals: 'output = left half' refuted by ≥2 demos where right has
# nonzero cells the left lacks. 'use input colors in output' refuted
# by any demo (output is just 0/6). 'AND instead of OR' refuted by
# any demo where some cells are nonzero only on one side. 'output
# preserves width' refuted by any demo (output halves the width).
# 3 demos with mixed patterns + densities cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "input width is even (2*half_w)",
    "halves use 0 + non-zero colors",
    "≥1 non-zero cell across the halves",
]

PANEL_PATTERNS = ("random", "blob", "stripes", "checker", "border", "diagonal")
DEGENERATE_TEXTURES = ("all_zero", "all_filled", "disjoint_halves")
HELPFUL_TEXTURES = PANEL_PATTERNS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 3..5", "valid": "1..30"},
    "half_w":         {"type": "int", "default": "rng 3..4", "valid": "1..15"},
    "left_color":     {"type": "color", "default": "rng (≠0,6)", "valid": "1..9 (≠6)"},
    "right_color":    {"type": "color", "default": "rng (≠0,6,left)", "valid": "1..9 (≠6)"},
    "left_density":   {"type": "float", "default": "rng 0.3..0.6", "valid": "0..1"},
    "right_density":  {"type": "float", "default": "rng 0.3..0.6", "valid": "0..1"},
    "panel_pattern":  {"type": "str", "default": "rng helpful",
                       "valid": "random|blob|stripes|checker|border|diagonal"},
    "or_target":      {"type": "int", "default": "rng 1..max", "valid": "1..h*half_w"},
    "texture":        {"type": "str", "default": "alias for panel_pattern",
                       "valid": "random|blob|stripes|checker|border|diagonal|all_zero|all_filled|disjoint_halves"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    # Canonical examples are all 3x6 input grids (h=3, half_w=3).  Keep the
    # default/easy distribution near that scale; reserve moderate extrapolation
    # for hard instead of teaching mostly large 10x20-ish panels.
    if difficulty == "easy":
        h_lo, h_hi, hw_lo, hw_hi = 3, 3, 3, 3
    elif difficulty == "hard":
        h_lo, h_hi, hw_lo, hw_hi = 4, 6, 4, 5
    else:
        h_lo, h_hi, hw_lo, hw_hi = 3, 5, 3, 4
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    half_w = ctx.draw_int("half_w", hw_lo, hw_hi)
    w = 2 * half_w
    rng = ctx.draw_rng("panels")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, half_w, rng)
    left_c = int(overrides.get("left_color", ctx.draw_color("left_color", exclude={0, 6})))
    right_c = int(overrides.get("right_color", ctx.draw_color("right_color", exclude={0, 6, left_c})))
    ld = float(overrides.get("left_density",
                             ctx.draw_rng("left_density").uniform(0.3, 0.6)))
    rd = float(overrides.get("right_density",
                             ctx.draw_rng("right_density").uniform(0.3, 0.6)))
    pattern = (overrides.get("texture") or overrides.get("panel_pattern")
               or ctx.draw_choice("panel_pattern", list(PANEL_PATTERNS)))
    g = full_grid(h, w, 0)
    _fill_panel(g, 0, half_w, h, pattern, ld, left_c, rng)
    _fill_panel(g, half_w, w, h, pattern, rd, right_c, rng)
    target = int(overrides.get("or_target",
                               ctx.draw_int("or_target", 1, max(1, h))))
    _ensure_or(g, h, half_w, target, left_c, rng)
    _ensure_teaching_witnesses(g, h, half_w, left_c, right_c, rng)
    _ensure_zero_witness(g, h, half_w, rng)
    return g


def _fill_panel(g, c0, c1, h, pattern, density, fg, rng):
    if pattern == "random":
        for r in range(h):
            for c in range(c0, c1):
                g[r][c] = fg if rng.random() < density else 0
    elif pattern == "blob":
        bh = max(1, int(h * density)); bw = max(1, int((c1 - c0) * density))
        r0 = rng.randint(0, h - bh); cc = rng.randint(c0, c1 - bw)
        for r in range(r0, r0 + bh):
            for c in range(cc, cc + bw):
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


def _ensure_or(g, h, half_w, target, fg, rng):
    have = sum(1 for r in range(h) for c in range(half_w)
               if g[r][c] != 0 or g[r][c + half_w] != 0)
    if have >= target:
        return
    cells = [(r, c) for r in range(h) for c in range(half_w)]
    rng.shuffle(cells)
    for (r, c) in cells:
        if have >= target:
            break
        if g[r][c] == 0 and g[r][c + half_w] == 0:
            g[r][c] = fg
            have += 1


def _ensure_teaching_witnesses(g, h, half_w, left_c, right_c, rng):
    """Force OR-specific evidence into every default instance.

    Deterministic panel patterns (stripes/checker/border/diagonal) used to put
    identical support in both halves, so OR, AND, left-only, and right-only
    hypotheses collapsed.  Reserve three paired coordinates: left-only,
    right-only, and overlap.
    """
    cells = [(r, c) for r in range(h) for c in range(half_w)]
    rng.shuffle(cells)
    if len(cells) < 3:
        return
    lr, lc = cells[0]
    rr, rc = cells[1]
    br, bc = cells[2]
    g[lr][lc] = left_c
    g[lr][lc + half_w] = 0
    g[rr][rc] = 0
    g[rr][rc + half_w] = right_c
    g[br][bc] = left_c
    g[br][bc + half_w] = right_c


def _ensure_zero_witness(g, h, half_w, rng):
    """Keep at least one paired coordinate mapping to output 0.

    Small canonical-scale panels plus border/checker textures can cover every
    paired coordinate, making the OR output a solid 6 rectangle.  That teaches a
    bad constant-output shortcut.  Clear one redundant support pair while
    preserving the left-only, right-only, and overlap witnesses.
    """
    if any(g[r][c] == 0 and g[r][c + half_w] == 0
           for r in range(h) for c in range(half_w)):
        return
    counts = {"left": 0, "right": 0, "both": 0}
    kinds = []
    for r in range(h):
        for c in range(half_w):
            left = g[r][c] != 0
            right = g[r][c + half_w] != 0
            if left and right:
                kind = "both"
            elif left:
                kind = "left"
            elif right:
                kind = "right"
            else:
                kind = "zero"
            if kind in counts:
                counts[kind] += 1
            kinds.append((r, c, kind))
    rng.shuffle(kinds)
    for r, c, kind in kinds:
        if kind in counts and counts[kind] > 1:
            g[r][c] = 0
            g[r][c + half_w] = 0
            return
    # Extremely small adversarial override fallback.  Preserve non-emptiness and
    # let self_check catch impossible 1- or 2-cell teaching cases.
    r, c, _ = kinds[-1]
    g[r][c] = 0
    g[r][c + half_w] = 0


def self_check(grid, *, difficulty=None, meta=None):
    """Verify even-width two-halves plus OR-teaching witnesses."""
    errs = []
    h, w = len(grid), len(grid[0])
    if w % 2 != 0:
        errs.append(f"width {w} is odd (need even for two equal halves)")
        return errs
    half_w = w // 2
    left_only = right_only = both = or_cells = zero_pairs = 0
    for r in range(h):
        for c in range(half_w):
            left = grid[r][c] != 0
            right = grid[r][c + half_w] != 0
            if left or right:
                or_cells += 1
            else:
                zero_pairs += 1
            if left and right:
                both += 1
            elif left:
                left_only += 1
            elif right:
                right_only += 1
    if or_cells == 0:
        errs.append("no non-zero cells across either half")
    if left_only == 0:
        errs.append("no left-only support cell; OR collapses toward right/AND")
    if right_only == 0:
        errs.append("no right-only support cell; OR collapses toward left/AND")
    if both == 0:
        errs.append("no overlapping support cell; AND branch is never visible")
    if zero_pairs == 0:
        errs.append("no zero-output witness; output can collapse to a solid 6 rectangle")
    return errs


def _draw_from_degenerate(name, h, half_w, rng):
    w = 2 * half_w
    g = full_grid(h, w, 0)
    left_c = rng.choice([1, 2, 3, 4, 5])
    right_c = rng.choice([7, 8, 9])
    if name == "all_zero":
        return g
    if name == "all_filled":
        for r in range(h):
            for c in range(half_w):
                g[r][c] = left_c
                g[r][c + half_w] = right_c
        return g
    if name == "disjoint_halves":
        for r in range(h):
            for c in range(half_w):
                if rng.random() < 0.5:
                    g[r][c] = left_c
                else:
                    g[r][c + half_w] = right_c
        return g
    return g
