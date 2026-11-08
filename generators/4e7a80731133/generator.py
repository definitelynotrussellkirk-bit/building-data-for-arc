"""Generator for arc_puzzle_bank_fourth_21_bundle:easy_27_recolor_exact_2x3_rectangles.

Rule: each exact solid 2×3 or 3×2 color-2 rectangle is recolored to 8.

v1.1.0 only used color 2 in inputs → model couldn't tell whether the
rule was "recolor 2×3 of ANY color" or specifically "of color 2". It
also placed only one fixed distractor cell at (h-1, 0) so wrong-size /
hollow / wrong-color cases never appeared.

v1.2.0:
  * adds multi-color distractor blobs (other than 2) — these are ignored
    by the rule, teaching the model that color-2 is the trigger
  * adds wrong-size color-2 distractor rects (1×3, 2×2, 2×4, 3×3) that
    the rule must NOT recolor — teaching the exact-2×3 predicate
  * adds hollow color-2 rects (border-only) that the rule must NOT
    recolor — teaching the solid predicate
  * varies n_rects 1..4 by difficulty
  * varies grid sizes
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "4e7a80731133"
VERSION = "2.0.1"
TASK_ID = "4e7a80731133"
SUMMARY = "Exact solid 2×3 or 3×2 color-2 rectangles → color 8; other shapes/colors ignored."

# Rivals: 'recolor any 2×3 regardless of color' refuted by ≥1 demo
# with a non-color-2 2×3 rect that stays unchanged. 'recolor every
# color-2 cell' refuted by ≥1 demo with a wrong-size color-2 rect
# (e.g. 2×2 or 2×4) that stays color 2. 'recolor 2x3 outlines too'
# refuted by ≥1 demo with a hollow color-2 2×3 that stays unchanged.
# 'recolor with a different color' refuted by any demo (always 8).
# 4 demos covering at least one of each rival cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "≥1 solid color-2 2×3 or 3×2 rectangle (target)",
    "color-2 distractors of wrong size/shape may exist (rule ignores)",
    "non-color-2 distractor blobs may exist (rule ignores)",
    "all objects 4-adj separated by ≥1 bg cell",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_exact_rects", "wrong_size_rects", "hollow_rects",
                       "only_color2")  # no non-2 distractors → can't refute 'recolor any 2x3'
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "by difficulty", "valid": "8..16"},
    "grid_w":            {"type": "int", "default": "by difficulty", "valid": "9..16"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "default|warm|cool|varied"},
    "n_target_rects":    {"type": "int", "default": "rng 1..4", "valid": "1..6"},
    "n_wrong_size_rects": {"type": "int", "default": "rng 0..2", "valid": "0..3"},
    "n_color_distractors": {"type": "int", "default": "rng 1..3", "valid": "0..4"},
    "palette_size":      {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "position_bias":     {"type": "str", "default": "spaced", "valid": "spaced"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "default|warm|cool|varied|no_exact_rects|wrong_size_rects|hollow_rects|only_color2"},
}


def _overlaps(bb, occupied, margin=1):
    """bb = (r0, c0, r1, c1) inclusive. Returns True if bb is within
    `margin` of any existing bbox in `occupied`."""
    for ob in occupied:
        if not (bb[2] + margin < ob[0] or ob[2] + margin < bb[0]
                or bb[3] + margin < ob[1] or ob[3] + margin < bb[1]):
            return True
    return False


def _try_place_rect(g, h, w, rh, rw, color, occupied, rng, *, max_tries=80, solid=True):
    """Place a (rh, rw) rectangle (solid or hollow) at a random non-overlapping
    position. Returns True if placed."""
    for _ in range(max_tries):
        rr = rng.randint(0, h - rh)
        rc = rng.randint(0, w - rw)
        bb = (rr, rc, rr + rh - 1, rc + rw - 1)
        if _overlaps(bb, occupied):
            continue
        if solid:
            draw_rect(g, rr, rc, rh, rw, color)
        else:
            # hollow: border only
            for c in range(rw):
                g[rr][rc + c] = color
                g[rr + rh - 1][rc + c] = color
            for r in range(rh):
                g[rr + r][rc] = color
                g[rr + r][rc + rw - 1] = color
        occupied.append(bb)
        return True
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 solid 2x3 or 3x2 color-2 rectangle exists."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    # Scan for any 2x3 or 3x2 solid color-2 rectangle
    found = False
    for rh, rw in [(2, 3), (3, 2)]:
        for r in range(h - rh + 1):
            for c in range(w - rw + 1):
                if all(grid[r + dr][c + dc] == 2 for dr in range(rh) for dc in range(rw)):
                    found = True
    if not found:
        errs.append("no solid color-2 2x3 or 3x2 rectangle found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 8, 9, 9, 10
        n_target_lo, n_target_hi = 1, 2
        n_wrong_lo, n_wrong_hi = 0, 1
        n_other_lo, n_other_hi = 1, 2
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 12, 15, 13, 16
        n_target_lo, n_target_hi = 2, 4
        n_wrong_lo, n_wrong_hi = 1, 3
        n_other_lo, n_other_hi = 2, 4
    else:
        h_lo, h_hi, w_lo, w_hi = 10, 12, 11, 13
        n_target_lo, n_target_hi = 1, 3
        n_wrong_lo, n_wrong_hi = 0, 2
        n_other_lo, n_other_hi = 1, 3
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    occupied: list[tuple[int, int, int, int]] = []

    # Target rects: solid color-2 of size 2x3 or 3x2.
    n_targets = rng.randint(n_target_lo, n_target_hi)
    placed_targets = 0
    for _ in range(n_targets):
        rh, rw = rng.choice([(2, 3), (3, 2)])
        if _try_place_rect(g, h, w, rh, rw, 2, occupied, rng):
            placed_targets += 1
    # Ensure at least one target — rule is uninteresting without one.
    if placed_targets == 0:
        _try_place_rect(g, h, w, 2, 3, 2, occupied, rng)

    # Wrong-size color-2 rects (rule must not recolor).
    n_wrong = rng.randint(n_wrong_lo, n_wrong_hi)
    wrong_sizes = [(2, 2), (2, 4), (4, 2), (3, 3), (1, 3), (3, 1)]
    rng.shuffle(wrong_sizes)
    for sz in wrong_sizes[:n_wrong]:
        if sz[0] > h or sz[1] > w:
            continue
        if rng.random() < 0.3:
            _try_place_rect(g, h, w, sz[0], sz[1], 2, occupied, rng, solid=False)
        else:
            _try_place_rect(g, h, w, sz[0], sz[1], 2, occupied, rng, solid=True)

    # Non-color-2 distractor blobs (rule ignores).
    n_other = rng.randint(n_other_lo, n_other_hi)
    other_colors_pool = [1, 3, 4, 5, 6, 7, 9]  # skip 0 (bg) and 2 (target) and 8 (output)
    rng.shuffle(other_colors_pool)
    for i in range(n_other):
        color = other_colors_pool[i % len(other_colors_pool)]
        rh, rw = rng.choice([(2, 3), (3, 2), (2, 2), (1, 3), (3, 1), (1, 2)])
        if rh > h or rw > w:
            continue
        _try_place_rect(g, h, w, rh, rw, color, occupied, rng)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    if name == "no_exact_rects":
        g[1][1] = 2; g[2][3] = 2; g[5][6] = 2
        return g
    if name == "wrong_size_rects":
        for r in range(2):
            for c in range(2): g[1 + r][1 + c] = 2
        for r in range(2):
            for c in range(4): g[5 + r][4 + c] = 2
        return g
    if name == "hollow_rects":
        for c in range(3): g[1][1 + c] = 2; g[3][1 + c] = 2
        for r in range(3): g[1 + r][1] = 2; g[1 + r][3] = 2
        return g
    if name == "only_color2":
        # one target rect + only color-2 distractors, no other colors
        for r in range(2):
            for c in range(3): g[1 + r][1 + c] = 2
        g[5][5] = 2; g[5][6] = 2
        return g
    return g
