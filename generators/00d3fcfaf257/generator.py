"""Generator for ARC task b1948b0a.

Rule: `(rule! (lambda (g) (recolor-map* g {6 2})))`
  Replace every magenta(6) cell with red(2). Other colors unchanged.

Combinatorial axes:
  * grid_h / grid_w     — outer canvas size
  * texture             — pattern type that holds the 6-cells (and others)
  * fg_density_6        — fraction of fg cells that are 6 (the rule's target)
  * distractor_palette  — which other colors live alongside the 6s
  * bg_color            — usually 0; can be any non-6 color
  * placement_pattern   — how 6-cells are clustered: scattered/blob/line/border
  * noise_overlay       — perturb a few cells (must not introduce new 6s)
  * caller-opt-in degenerates: solid_6, no_6 (rule no-op), single_6
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "00d3fcfaf257"
VERSION = "1.3.0"  # bumped: canonical dense 6/7 field; remove object-fragment drift
TASK_ID = "00d3fcfaf257"
SUMMARY = "Dense canonical 7/6 field; the rule recolors every magenta(6) cell to red(2)."

# Rivals: 'swap 6 and 2' refuted by demos where pre-existing red(2)
# cells STAY red while 6s turn red (include_2s axis guarantees such
# demos exist). 'recolor everything to 2' refuted by surviving
# distractors. 'bg is always black' refuted by non-zero-bg demos.
# 3 demos: >=1 with input 2s, >=1 with non-zero bg.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "normal samples are dense two-color fields over canonical colors {6,7}",
    "input contains at least one magenta(6) cell (rule has visible effect)",
    "input contains at least one 7 cell that survives unchanged",
    "normal path avoids extra distractor colors/objects so the task stays a simple recolor",
]

HELPFUL_TEXTURES = (
    "scattered", "blob", "line_h", "line_v", "border",
    "rect", "L_shape", "checker_subgrid", "diagonal",
)
DEGENERATE_TEXTURES = ("solid_6", "no_6", "single_6")

AXES = {
    "grid_h":             {"type": "int",   "default": "rng 3..6", "valid": "3..8"},
    "grid_w":             {"type": "int",   "default": "rng 4..6", "valid": "3..8"},
    "texture":            {"type": "str",   "default": "rng helpful",
                           "valid": "scattered|blob|line_h|line_v|border|rect|"
                                    "L_shape|checker_subgrid|diagonal|"
                                    "solid_6|no_6|single_6"},
    "fg_density_6":       {"type": "float", "default": "rng 0.35..0.60", "valid": "0.10..0.90"},
    "distractor_count":   {"type": "int",   "default": "0",  "valid": "0"},
    "bg_color":           {"type": "color", "default": "7", "valid": "7"},
    "include_2s":         {"type": "bool",  "default": "0",  "valid": "0"},
    "placement_pattern":  {"type": "str",   "default": "alias for texture",
                           "valid": "scattered|blob|line_h|line_v|border|rect|"
                                    "L_shape|checker_subgrid|diagonal"},
    "noise_overlay":      {"type": "float", "default": "rng 0..0.05", "valid": "0..0.3"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 3, 4, 4, 5
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 5, 6, 5, 6
    else:
        h_lo, h_hi, w_lo, w_hi = 3, 6, 4, 6

    h = int(overrides.get("grid_h", ctx.draw_int("grid_h", h_lo, h_hi)))
    w = int(overrides.get("grid_w", ctx.draw_int("grid_w", w_lo, w_hi)))
    rng = ctx.draw_rng("layout")

    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)

    # Canonical b1948b0a is a dense two-color field over {7,6}: the only
    # transformation is 6 -> 2.  Earlier versions added many distractor colors
    # and sparse object textures, which made the random-audit drift linter see an
    # object-count puzzle instead of a pure recolor task.
    bg = int(overrides.get("bg_color", 7))
    if bg == 6:
        bg = 7
    density_6 = float(overrides.get(
        "fg_density_6",
        ctx.draw_rng("fg_density_6").uniform(0.35, 0.60)))
    density_6 = max(0.10, min(0.90, density_6))

    g = full_grid(h, w, bg)
    for r in range(h):
        for c in range(w):
            if rng.random() < density_6:
                g[r][c] = 6

    # Keep both classes visible; all-6 or all-bg boards hide the recolor rule.
    cells = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(cells)
    if not any(g[r][c] == 6 for r, c in cells):
        r, c = cells[0]
        g[r][c] = 6
    if not any(g[r][c] != 6 for r, c in cells):
        r, c = cells[-1]
        g[r][c] = bg
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not isinstance(grid, list) or not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be a non-empty rectangular 2D list"]
    vals = {v for row in grid for v in row}
    bad = sorted(v for v in vals if not isinstance(v, int) or v < 0 or v > 9)
    if bad:
        errs.append(f"cell values outside 0..9: {bad}")
    if 6 not in vals:
        errs.append("normal sample must contain at least one magenta(6) target cell")
    if vals - {6, 7}:
        errs.append(f"normal sample should use only canonical colors {{6,7}}, saw {sorted(vals)}")
    if 7 not in vals:
        errs.append("normal sample must contain at least one 7 survivor/background cell")
    return errs


def _paint_with_texture(texture, h, w, bg, distractors, density_6, rng):
    g = full_grid(h, w, bg)

    def stamp_distractors():
        # Lay a low-density distractor base before the 6s land on top.
        if not distractors:
            return
        for r in range(h):
            for c in range(w):
                if rng.random() < 0.20:
                    g[r][c] = rng.choice(distractors)

    if texture == "scattered":
        stamp_distractors()
        for r in range(h):
            for c in range(w):
                if rng.random() < density_6:
                    g[r][c] = 6
    elif texture == "blob":
        stamp_distractors()
        bh = max(1, int(h * (0.3 + density_6 * 0.5)))
        bw = max(1, int(w * (0.3 + density_6 * 0.5)))
        r0 = rng.randint(0, h - bh)
        c0 = rng.randint(0, w - bw)
        for r in range(r0, r0 + bh):
            for c in range(c0, c0 + bw):
                g[r][c] = 6
    elif texture == "line_h":
        stamp_distractors()
        r = rng.randint(0, h - 1)
        for c in range(w):
            g[r][c] = 6
    elif texture == "line_v":
        stamp_distractors()
        c = rng.randint(0, w - 1)
        for r in range(h):
            g[r][c] = 6
    elif texture == "border":
        for c in range(w):
            g[0][c] = 6
            g[h - 1][c] = 6
        for r in range(h):
            g[r][0] = 6
            g[r][w - 1] = 6
        # interior gets distractors
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
                g[r][c] = 6
    elif texture == "L_shape":
        stamp_distractors()
        rh = max(2, h - 1)
        rw = max(2, w - 1)
        rr = rng.randint(0, h - rh)
        rc = rng.randint(0, w - rw)
        for r in range(rr, rr + rh):
            g[r][rc] = 6
        for c in range(rc, rc + rw):
            g[rr + rh - 1][c] = 6
    elif texture == "checker_subgrid":
        stamp_distractors()
        for r in range(h):
            for c in range(w):
                if (r + c) % 2 == 0 and rng.random() < density_6 * 2:
                    g[r][c] = 6
    elif texture == "diagonal":
        stamp_distractors()
        for k in range(min(h, w)):
            g[k][k] = 6
    else:  # fall back to scattered
        stamp_distractors()
        for r in range(h):
            for c in range(w):
                if rng.random() < density_6:
                    g[r][c] = 6
    return g


def _draw_from_degenerate(name, h, w, rng):
    """Edge-case where the recolor signature is hidden.

    solid_6   — entire grid is 6, output is solid 2; could be confused
                with "fill with 2" rules.
    no_6      — zero 6s in input; rule is a no-op (output == input).
                Demonstration carries no rule signal.
    single_6  — one 6 cell only; very low signal-to-noise.
    """
    bg = 0
    g = full_grid(h, w, bg)
    if name == "solid_6":
        for r in range(h):
            for c in range(w):
                g[r][c] = 6
        return g
    if name == "no_6":
        # Random grid with everything except 6.
        palette = [c for c in range(10) if c != 6]
        for r in range(h):
            for c in range(w):
                g[r][c] = rng.choice(palette)
        return g
    if name == "single_6":
        palette = [c for c in range(10) if c not in {bg, 6}]
        for r in range(h):
            for c in range(w):
                if rng.random() < 0.4:
                    g[r][c] = rng.choice(palette)
        g[rng.randint(0, h - 1)][rng.randint(0, w - 1)] = 6
        return g
    return g
