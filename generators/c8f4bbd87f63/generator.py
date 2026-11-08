"""Generator for arc_additional_puzzles_21_set5:M34.

Rule: the upper-left 3x3 is a template (color-3 arms + color-2 center);
it is stamped, centered, at every color-2 anchor outside that 3x3,
painting empty cells with the template's arm values.

Combinatorial axes: grid size, the template arms (a random subset of the
8 surrounding cells), and the anchor count / positions.
Degenerates: no_template, no_anchors, anchor_in_template.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c8f4bbd87f63"
VERSION = "2.0.1"  # diversity: random template arms + N anchors + positions + grid (was fixed plus + 2 anchors)
TASK_ID = "c8f4bbd87f63"
SUMMARY = (
    "0-bg grid (size varies). The upper-left 3x3 is a TEMPLATE: a "
    "color-2 center with a random set of color-3 ARM cells among the 8 "
    "surrounding cells. Elsewhere sit 1-4 single color-2 ANCHOR cells "
    "(clear of the template and of each other so their stamps don't "
    "overlap). Rule: stamp the template centered on each anchor, painting "
    "every empty cell under a template ARM with that arm's color; the "
    "anchor stays color 2. The grid size, the template arm pattern, and "
    "the anchor count / positions all vary freely (was a fixed plus "
    "template + 2 fixed anchors)."
)

INVARIANTS = [
    "the upper-left 3x3 holds a color-2 center with color-3 arms",
    "1-4 anchor color-2 cells sit outside the template",
    "each anchor's 3x3 stamp fits in-bounds clear of the template and other anchors",
]

PALETTE_KINDS = ("default", "two_anchors", "spread_anchors", "tight_anchors")
DEGENERATE_TEXTURES = ("no_template", "no_anchors", "anchor_in_template")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|two_anchors|spread_anchors|tight_anchors"},
    "num_anchors":    {"type": "int", "default": "rng 1..4", "valid": "1..4"},
    "template_color": {"type": "int", "default": "3", "valid": "3"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|two_anchors|spread_anchors|tight_anchors|no_template|no_anchors|anchor_in_template"},
}

_ARM_OFFSETS = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, na = (8, 10), (9, 11), (1, 2)
    elif difficulty == "hard":
        hr, wr, na = (12, 16), (12, 16), (3, 4)
    else:
        hr, wr, na = (9, 12), (10, 13), (2, 3)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        # Template arms: a random non-empty subset of the 8 surrounding cells.
        arms = rng.sample(_ARM_OFFSETS, rng.randint(2, 6))
        for tr, tc in arms:
            g[tr][tc] = 3
        g[1][1] = 2

        anchor_boxes = []   # (r,c) anchor centers, separated by >=3

        def _ok(r, c):
            if not (1 <= r <= h - 2 and 1 <= c <= w - 2):
                return False                          # stamp fits in-bounds
            # the 3x3 stamp must avoid the template region (rows 0-2, cols 0-2)
            if r - 1 <= 2 and c - 1 <= 2:
                return False
            for ar, ac in anchor_boxes:
                if abs(ar - r) < 3 and abs(ac - c) < 3:
                    return False                      # stamps don't overlap
            return True

        n = rng.randint(*na)
        for _ in range(n):
            for _t in range(40):
                r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
                if _ok(r, c):
                    anchor_boxes.append((r, c)); g[r][c] = 2
                    break
        if anchor_boxes:
            return g

    return g   # fallback (rare)


def _plus_template(g):
    g[0][1] = 3
    g[1][0] = 3; g[1][1] = 2; g[1][2] = 3
    g[2][1] = 3


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 10, 0)
    if name == "no_template":
        g[5][5] = 2; g[7][8] = 2
        return g
    if name == "no_anchors":
        _plus_template(g)
        return g
    if name == "anchor_in_template":
        _plus_template(g)
        g[0][0] = 2
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Upper-left 3x3 must be the template (color-2 center at (1,1), >=1 color-3 arm); >=1 color-2 anchor elsewhere."""
    msgs = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    if h < 3 or w < 3:
        msgs.append("grid too small for 3x3 template")
        return msgs
    if grid[1][1] != 2:
        msgs.append(f"template center (1,1) is {grid[1][1]}, expected color-2")
    # At least one color-3 arm in the 8 surrounding cells of (1,1)
    surround = [(r, c) for r in range(0, 3) for c in range(0, 3) if (r, c) != (1, 1)]
    tmpl_arms = [grid[r][c] for r, c in surround if 0 <= r < h and 0 <= c < w]
    if not any(v == 3 for v in tmpl_arms):
        msgs.append("template 3x3 has no color-3 arm cells in surrounding positions")
    # At least one color-2 anchor outside the 3x3 template
    anchors = [(r, c) for r in range(h) for c in range(w)
               if grid[r][c] == 2 and not (r <= 2 and c <= 2)]
    if not anchors:
        msgs.append("no color-2 anchor found outside the upper-left 3x3 template")
    return msgs
