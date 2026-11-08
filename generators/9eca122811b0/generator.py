"""Generator for ARC task c8f0f002.

Rule: `(rule! (lambda (g) (recolor-map* g {7 5})))`
  Replace every orange(7) cell with gray(5). Other colors unchanged.

Same shape as b1948b0a but the target color is 7 (and a different output
target). Kept independent so each task contributes its own slice.

Combinatorial axes:
  * grid_h / grid_w     — outer canvas size
  * texture             — pattern type for the 7-cells
  * fg_density_7        — fraction of fg cells that are 7
  * distractor_count    — how many other colors live alongside the 7s
  * bg_color            — usually 0; can be any non-7 color
  * placement_pattern   — alias for texture
  * noise_overlay       — light perturbation
  * caller-opt-in degenerates: solid_7, no_7 (no-op), single_7
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9eca122811b0"
VERSION = "2.1.0"
TASK_ID = "9eca122811b0"
SUMMARY = (
    "Grid (h×w, ~3-10 by ~3-10) with at least one color-7 (orange) "
    "cell + 1-4 DISTRACTOR colors (not 7) in various textures "
    "(scattered, blob, line, border, rect, L-shape, diagonal, "
    "checker). Background usually 0. Rule: recolor every cell of "
    "color 7 to color 5 (gray). All other cells preserved "
    "unchanged. Output: same shape and structure as input with "
    "7s replaced by 5s; distractor colors remain as-is."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "input contains at least one color-7 cell (rule must fire)",
    "input contains ≥1 distractor color ≠ 7 (proves rule is selective)",
    "background can be any non-7 color (default 0)",
]

HELPFUL_TEXTURES = (
    "scattered", "blob", "line_h", "line_v", "border",
    "rect", "L_shape", "checker_subgrid", "diagonal",
)
DEGENERATE_TEXTURES = ("solid_7", "no_7", "single_7")

AXES = {
    "grid_h":             {"type": "int",   "default": "rng 3..10", "valid": "1..18"},
    "grid_w":             {"type": "int",   "default": "rng 3..10", "valid": "1..18"},
    "texture":            {"type": "str",   "default": "rng helpful",
                           "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
    "fg_density_7":       {"type": "float", "default": "rng 0.10..0.45", "valid": "0.05..0.9"},
    "distractor_count":   {"type": "int",   "default": "rng 1..4", "valid": "0..6"},
    "bg_color":           {"type": "color", "default": "0",        "valid": "0..9 (≠7)"},
    "placement_pattern":  {"type": "str",   "default": "alias for texture",
                           "valid": "|".join(HELPFUL_TEXTURES)},
    "noise_overlay":      {"type": "float", "default": "rng 0..0.05", "valid": "0..0.3"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    if difficulty == "easy":
        h_lo, h_hi, d_lo, d_hi = 3, 5, 1, 2
    elif difficulty == "hard":
        h_lo, h_hi, d_lo, d_hi = 8, 10, 3, 4
    else:
        h_lo, h_hi, d_lo, d_hi = 3, 10, 1, 4

    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("layout")

    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)

    bg = int(overrides.get("bg_color", 0))
    if bg == 7:
        bg = 0
    n_dist = int(overrides.get("distractor_count",
                               ctx.draw_int("distractor_count", d_lo, d_hi)))
    distractor_palette = [c for c in range(10) if c not in {bg, 7}]
    rng.shuffle(distractor_palette)
    distractors = distractor_palette[:max(0, n_dist)]

    texture = overrides.get(
        "texture",
        ctx.draw_choice("texture", list(HELPFUL_TEXTURES)))
    density_7 = float(overrides.get(
        "fg_density_7",
        ctx.draw_rng("fg_density_7").uniform(0.10, 0.45)))

    g = _paint_with_texture(texture, h, w, bg, distractors, density_7, rng)

    no = float(overrides.get(
        "noise_overlay",
        ctx.draw_rng("noise_overlay").uniform(0.0, 0.05)))
    if no > 0.0 and distractors:
        for _ in range(max(1, int(h * w * no))):
            r = rng.randint(0, h - 1)
            c = rng.randint(0, w - 1)
            if g[r][c] != 7:
                g[r][c] = rng.choice(distractors)

    if not any(g[r][c] == 7 for r in range(h) for c in range(w)):
        g[rng.randint(0, h - 1)][rng.randint(0, w - 1)] = 7
    if not any(g[r][c] not in {bg, 7} for r in range(h) for c in range(w)):
        choices = [(r, c) for r in range(h) for c in range(w) if g[r][c] != 7]
        if not choices:
            choices = [(rng.randrange(h), rng.randrange(w))]
        rr, cc = rng.choice(choices)
        g[rr][cc] = rng.choice(distractors or [c for c in range(10) if c not in {bg, 7}])
    return g


def _paint_with_texture(texture, h, w, bg, distractors, density_7, rng):
    """Lay distractors first, then the target-color (7) cells on top."""
    g = full_grid(h, w, bg)

    def stamp_distractors():
        if not distractors:
            return
        for r in range(h):
            for c in range(w):
                if rng.random() < 0.25:
                    g[r][c] = rng.choice(distractors)

    if texture == "scattered":
        stamp_distractors()
        for r in range(h):
            for c in range(w):
                if rng.random() < density_7:
                    g[r][c] = 7
    elif texture == "blob":
        stamp_distractors()
        bh = max(1, int(h * (0.3 + density_7 * 0.5)))
        bw = max(1, int(w * (0.3 + density_7 * 0.5)))
        r0 = rng.randint(0, h - bh)
        c0 = rng.randint(0, w - bw)
        for r in range(r0, r0 + bh):
            for c in range(c0, c0 + bw):
                g[r][c] = 7
    elif texture == "line_h":
        stamp_distractors()
        r = rng.randint(0, h - 1)
        for c in range(w):
            g[r][c] = 7
    elif texture == "line_v":
        stamp_distractors()
        c = rng.randint(0, w - 1)
        for r in range(h):
            g[r][c] = 7
    elif texture == "border":
        for c in range(w):
            g[0][c] = 7
            g[h - 1][c] = 7
        for r in range(h):
            g[r][0] = 7
            g[r][w - 1] = 7
        if distractors:
            for r in range(1, h - 1):
                for c in range(1, w - 1):
                    if rng.random() < 0.4:
                        g[r][c] = rng.choice(distractors)
    elif texture == "rect":
        stamp_distractors()
        rh = max(2, int(h * 0.5))
        rw = max(2, int(w * 0.5))
        rr = rng.randint(0, h - rh)
        rc = rng.randint(0, w - rw)
        for r in range(rr, rr + rh):
            for c in range(rc, rc + rw):
                g[r][c] = 7
    elif texture == "L_shape":
        stamp_distractors()
        rh = max(2, h - 1)
        rw = max(2, w - 1)
        rr = rng.randint(0, h - rh)
        rc = rng.randint(0, w - rw)
        for r in range(rr, rr + rh):
            g[r][rc] = 7
        for c in range(rc, rc + rw):
            g[rr + rh - 1][c] = 7
    elif texture == "checker_subgrid":
        stamp_distractors()
        for r in range(h):
            for c in range(w):
                if (r + c) % 2 == 0 and rng.random() < density_7 * 2:
                    g[r][c] = 7
    elif texture == "diagonal":
        stamp_distractors()
        for k in range(min(h, w)):
            g[k][k] = 7
    else:
        stamp_distractors()
        for r in range(h):
            for c in range(w):
                if rng.random() < density_7:
                    g[r][c] = 7
    return g


def _draw_from_degenerate(name, h, w, rng):
    """Edge-case where the recolor signature is hidden.

    solid_7  — entire grid is 7, output is solid 5; ambiguous with "fill 5".
    no_7     — no 7s in input; rule is no-op (output == input).
    single_7 — single 7 cell, very low signal.
    """
    bg = 0
    g = full_grid(h, w, bg)
    if name == "solid_7":
        for r in range(h):
            for c in range(w):
                g[r][c] = 7
        return g
    if name == "no_7":
        palette = [c for c in range(10) if c != 7]
        for r in range(h):
            for c in range(w):
                g[r][c] = rng.choice(palette)
        return g
    if name == "single_7":
        palette = [c for c in range(10) if c not in {bg, 7}]
        for r in range(h):
            for c in range(w):
                if rng.random() < 0.4:
                    g[r][c] = rng.choice(palette)
        g[rng.randint(0, h - 1)][rng.randint(0, w - 1)] = 7
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    vals = {v for row in grid for v in row}
    errs = []
    if 7 not in vals:
        errs.append("main-path board must contain at least one 7")
    bg = grid[0][0] if grid and grid[0] else 0
    if not any(v not in {bg, 7} for v in vals):
        errs.append("main-path board must contain at least one non-7 distractor color")
    return errs
