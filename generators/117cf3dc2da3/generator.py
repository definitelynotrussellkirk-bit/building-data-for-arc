"""Generator for ARC task d511f180.

Rule: `(rule! (lambda (g) (recolor-map* g {5 8 8 5})))`
  Swap gray(5) and cyan(8) everywhere. Other colors unchanged.

Combinatorial axes:
  * grid_h / grid_w        — outer canvas size
  * texture                — pattern of the 5/8 cells (and distractors)
  * mix_ratio              — fraction of fg cells that are 5 vs 8
                             (controls visual balance)
  * distractor_count       — how many other colors live alongside
  * bg_color               — background color (≠5, ≠8)
  * placement              — where 5s and 8s cluster: random/blob_pair/
                             striped/border/quadrants
  * noise_overlay          — light perturbation
  * caller-opt-in degenerates: only_5, only_8, no_target_colors
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "117cf3dc2da3"
VERSION = "2.0.1"
TASK_ID = "117cf3dc2da3"
SUMMARY = (
    "Compact colored grid (h, w in {3..5}) "
    "drawn with one of 8 "
    "TEXTURES (random/"
    "blob_pair/striped/"
    "border/quadrants/"
    "checker/diagonal/"
    "frame_5_inner_8) "
    "containing CELLS in "
    "COLOR-5 (gray) and "
    "COLOR-8 (cyan) at "
    "mix_ratio 0.3-0.7. "
    "Plus 3-6 DISTRACTOR "
    "color cells in non-"
    "{0, 5, 8} colors. BG "
    "is a non-target color (or task-"
    "specific). Guaranteed "
    "≥1 5-cell AND ≥1 "
    "8-cell. Rule (SWAP "
    "COLORS 5 ↔ 8 "
    "EVERYWHERE): For "
    "EACH cell with "
    "VALUE 5: REPAINT to "
    "8. For EACH cell "
    "with VALUE 8: "
    "REPAINT to 5. All "
    "other colors "
    "(distractors, bg) "
    "stay. Net: gray and "
    "cyan exchange "
    "places across the "
    "entire grid."
)

INVARIANTS = [
    "input contains at least one 5 and one 8 (otherwise rule is partial no-op)",
    "all other colors are distractors and remain unchanged",
    "grid dimensions stay compact",
]

HELPFUL_TEXTURES = (
    "random", "blob_pair", "striped", "border",
    "quadrants", "checker", "diagonal", "frame_5_inner_8",
)
DEGENERATE_TEXTURES = ("only_5", "only_8", "no_target_colors")

AXES = {
    "grid_h":           {"type": "choice", "default": "rng 3|5", "valid": "3|5"},
    "grid_w":           {"type": "choice", "default": "rng 3|5", "valid": "3|5"},
    "texture":          {"type": "str",   "default": "rng helpful",
                         "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
    "mix_ratio":        {"type": "float", "default": "rng 0.3..0.7",
                         "valid": "0.1..0.9 (fraction of fg that is 5)"},
    "distractor_count": {"type": "int",   "default": "rng 3..6", "valid": "0..6"},
    "bg_color":         {"type": "color", "default": "rng non-{5,8}", "valid": "0..9 (≠5,≠8)"},
    "noise_overlay":    {"type": "float", "default": "rng 0..0.05", "valid": "0..0.3"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    if difficulty == "easy":
        h_choices, w_choices, d_lo, d_hi = [3], [3], 3, 4
    elif difficulty == "hard":
        h_choices, w_choices, d_lo, d_hi = [5], [5], 5, 6
    else:
        # Canonical train pairs are compact 3x3/5x5 full-color grids.  The old
        # 9..12 hard band was semantically valid but taught a different size
        # regime and hid the exemplar's tiny recolor-map signature.
        h_choices, w_choices, d_lo, d_hi = [3, 5], [3, 5], 3, 5

    h = ctx.draw_choice("grid_h", h_choices)
    w = ctx.draw_choice("grid_w", w_choices)
    rng = ctx.draw_rng("layout")

    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)

    bg = int(overrides.get("bg_color", ctx.draw_choice("bg_color", [1, 2, 3, 4, 6, 7, 9])))
    if bg in {5, 8}:
        bg = 0
    n_dist = int(overrides.get("distractor_count",
                               ctx.draw_int("distractor_count", d_lo, d_hi)))
    # Reserve cells for both target colors; compact grids cannot host an
    # unbounded palette without overwriting the swap evidence.
    n_dist = max(0, min(n_dist, h * w - 2))
    distractors = [c for c in range(10) if c not in {bg, 5, 8}]
    rng.shuffle(distractors)
    distractors = distractors[:n_dist]

    texture = overrides.get(
        "texture",
        ctx.draw_choice("texture", list(HELPFUL_TEXTURES)))
    mix = float(overrides.get(
        "mix_ratio",
        ctx.draw_rng("mix_ratio").uniform(0.3, 0.7)))

    g = _paint_with_texture(texture, h, w, bg, distractors, mix, rng)

    no = float(overrides.get(
        "noise_overlay",
        ctx.draw_rng("noise_overlay").uniform(0.0, 0.05)))
    if no > 0.0 and distractors:
        for _ in range(max(1, int(h * w * no))):
            r = rng.randint(0, h - 1)
            c = rng.randint(0, w - 1)
            if g[r][c] not in {5, 8}:
                g[r][c] = rng.choice(distractors)

    # Invariants: at least one 5 and one 8, and the canonical examples are
    # distractor-rich.  Stamp each chosen distractor once on a non-critical cell
    # so the palette stays close to the exemplar without changing the rule.
    positions = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(positions)
    for color, (r, c) in zip(distractors, positions):
        g[r][c] = color
    # Force two distinct anchor cells after all palette stamping; this avoids rare
    # compact-grid cases where the only 5/8 was overwritten by a distractor stamp.
    g[0][0] = 5
    g[h - 1][w - 1] = 8
    return g


def _paint_with_texture(texture, h, w, bg, distractors, mix, rng):
    g = full_grid(h, w, bg)
    pick_5_8 = lambda: 5 if rng.random() < mix else 8

    if texture == "random":
        for r in range(h):
            for c in range(w):
                roll = rng.random()
                if roll < 0.4:
                    g[r][c] = pick_5_8()
                elif distractors and roll < 0.6:
                    g[r][c] = rng.choice(distractors)
    elif texture == "blob_pair":
        # One blob of 5s, one of 8s, possibly with distractors elsewhere.
        b_h, b_w = max(1, h // 3), max(1, w // 3)
        r0 = rng.randint(0, h - b_h)
        c0 = rng.randint(0, w // 2 - 1) if w >= 4 else 0
        for r in range(r0, r0 + b_h):
            for c in range(c0, c0 + b_w):
                g[r][c] = 5
        r1 = rng.randint(0, h - b_h)
        c1 = rng.randint(w // 2, max(0, w - b_w)) if w >= 4 else 0
        for r in range(r1, r1 + b_h):
            for c in range(c1, c1 + b_w):
                g[r][c] = 8
        if distractors:
            for r in range(h):
                for c in range(w):
                    if g[r][c] == bg and rng.random() < 0.15:
                        g[r][c] = rng.choice(distractors)
    elif texture == "striped":
        # Alternating rows of 5/8.
        for r in range(h):
            color = 5 if r % 2 == 0 else 8
            for c in range(w):
                if rng.random() < 0.7:
                    g[r][c] = color
                elif distractors:
                    g[r][c] = rng.choice(distractors)
    elif texture == "border":
        for c in range(w):
            g[0][c] = 5
            g[h - 1][c] = 8
        for r in range(h):
            g[r][0] = 5
            g[r][w - 1] = 8
        if distractors:
            for r in range(1, h - 1):
                for c in range(1, w - 1):
                    if rng.random() < 0.4:
                        g[r][c] = rng.choice(distractors)
    elif texture == "quadrants":
        for r in range(h):
            for c in range(w):
                if (r < h // 2) ^ (c < w // 2):
                    if rng.random() < 0.7:
                        g[r][c] = 5
                else:
                    if rng.random() < 0.7:
                        g[r][c] = 8
    elif texture == "checker":
        for r in range(h):
            for c in range(w):
                g[r][c] = 5 if (r + c) % 2 == 0 else 8
    elif texture == "diagonal":
        for k in range(min(h, w)):
            g[k][k] = 5
            anti = w - 1 - k
            if 0 <= anti < w:
                g[k][anti] = 8
        if distractors:
            for r in range(h):
                for c in range(w):
                    if g[r][c] == bg and rng.random() < 0.2:
                        g[r][c] = rng.choice(distractors)
    elif texture == "frame_5_inner_8":
        for c in range(w):
            g[0][c] = 5
            g[h - 1][c] = 5
        for r in range(h):
            g[r][0] = 5
            g[r][w - 1] = 5
        for r in range(1, h - 1):
            for c in range(1, w - 1):
                g[r][c] = 8 if rng.random() < 0.6 else (
                    rng.choice(distractors) if distractors else bg)
    else:
        # fallback
        for r in range(h):
            for c in range(w):
                if rng.random() < 0.5:
                    g[r][c] = pick_5_8()
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not isinstance(grid, list) or not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be a non-empty rectangular 2D list"]
    h, w = len(grid), len(grid[0])
    if h not in {3, 5} or w not in {3, 5}:
        errs.append(f"normal grid should match compact canonical 3x3/5x5 scale, got {h}x{w}")
    vals = {v for row in grid for v in row}
    bad = sorted(v for v in vals if not isinstance(v, int) or v < 0 or v > 9)
    if bad:
        errs.append(f"cell values outside 0..9: {bad}")
    if 5 not in vals or 8 not in vals:
        errs.append("normal sample must contain both gray(5) and cyan(8)")
    return errs


def _draw_from_degenerate(name, h, w, rng):
    """Edge-case where the swap signature is hidden.

    only_5            — input has 5 but no 8; rule recolors all 5→8 only.
    only_8            — symmetric: 8s become 5s, no other change.
    no_target_colors  — neither 5 nor 8 in input; rule is no-op.
    """
    bg = 0
    g = full_grid(h, w, bg)
    distractors = [c for c in range(10) if c not in {bg, 5, 8}]
    rng.shuffle(distractors)
    if name == "only_5":
        for r in range(h):
            for c in range(w):
                if rng.random() < 0.45:
                    g[r][c] = 5
                elif distractors and rng.random() < 0.4:
                    g[r][c] = rng.choice(distractors[:3])
        # ensure ≥1 5
        g[0][0] = 5
        return g
    if name == "only_8":
        for r in range(h):
            for c in range(w):
                if rng.random() < 0.45:
                    g[r][c] = 8
                elif distractors and rng.random() < 0.4:
                    g[r][c] = rng.choice(distractors[:3])
        g[0][0] = 8
        return g
    if name == "no_target_colors":
        palette = [c for c in range(10) if c not in {5, 8}]
        for r in range(h):
            for c in range(w):
                g[r][c] = rng.choice(palette)
        return g
    return g
