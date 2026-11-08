"""Generator for arc_additional_puzzles_21_set9:H58.

Copy a framed source motif into target frames using local transform command cells.

v3.0.0: exploits the canonical rule's full generality. The rule finds ANY
color-9 rectangular frame (any size), copies its ENTIRE interior subgrid (so the
source may be MULTICOLOR), and pastes the transformed copy into EVERY color-8
frame it finds (any count, any position). So this generator now varies: grid
size, number of target frames (1-5), frame interior size (square k in 3-4),
frame positions (grid-of-slots layout), a random MULTICOLOR source pattern, and
a per-target transform code. Square interiors keep every transform (rot-cw,
rot-180, flip-ud, identity) the same dims so the centered paste always fits.

Locked by the rule (and only these): the source frame border is 9, target frame
borders are 8 (the rule does `keep-only g 9` / `keep-only g 8`), and the code
set is {1=id, 2=rot-cw, 3=rot-180, 4=flip-ud} (the rule's `transform` cond).
Everything else is pushed for diversity.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "ffc1598119d4"
VERSION = "3.0.0"
TASK_ID = "ffc1598119d4"
SUMMARY = (
    "0-bg grid (size varies) laid out as ONE "
    "color-9 SOURCE FRAME plus 1-5 color-8 "
    "TARGET FRAMES (all square, interior k in "
    "3-4), arranged in a grid of slots. The "
    "source frame's interior holds a random "
    "MULTICOLOR pattern (2-4 colors from {1..7}). "
    "Each target frame has a COMMAND CELL "
    "directly above its top-left corner with a "
    "value in {1..4} (1=identity, 2=rotate-CW, "
    "3=rotate-180, 4=flip-UD). Rule: extract the "
    "9-frame interior as the SOURCE. For EACH "
    "8-frame, read the command above its top-left "
    "corner, TRANSFORM the source by that code, "
    "and PAINT the result centered in the "
    "target's interior (clearing it first). The "
    "frames, command cells, and source stay. Net: "
    "every target frame fills with a transformed "
    "copy of the multicolor source."
)

INVARIANTS = [
    "there is exactly one color-9 source frame containing a nonempty interior",
    "there are 1-5 color-8 target frames with initially empty interiors",
    "every frame is square with the same interior size k",
    "each target frame has a command cell (1-4) above its top-left corner",
    "commands map to identity, rotate-CW, rotate-180, or flip-UD",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motif", "no_targets", "no_codes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "derived from layout", "valid": "8..30"},
    "grid_w":         {"type": "int", "default": "derived from layout", "valid": "8..30"},
    "n_targets":      {"type": "int", "default": "rng by-difficulty 1..5", "valid": "1..5"},
    "interior":       {"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "source_colors":  {"type": "int", "default": "rng 2..4 from {1..7}", "valid": "1..7"},
    "code_a":         {"type": "int", "default": "rng 1..4", "valid": "1..4"},
    "code_b":         {"type": "int", "default": "rng 1..4", "valid": "1..4"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_MOTIFS = [
    [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)],
    [(0, 0), (0, 1), (1, 1), (2, 0), (2, 1)],
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 2)],
    [(0, 0), (0, 2), (1, 0), (1, 1), (2, 1)],
]


def _paint(g, top, left, cells, color):
    for r, c in cells:
        g[top + r][left + c] = color


def _random_source(rng, k):
    """A non-empty k x k multicolor pattern in colors {1..7}."""
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7], rng.randint(2, 4))
    n = rng.randint(max(2, (k * k) // 3), max(3, (k * k * 3) // 4))
    positions = [(r, c) for r in range(k) for c in range(k)]
    rng.shuffle(positions)
    src = [[0] * k for _ in range(k)]
    for (r, c) in positions[:n]:
        src[r][c] = rng.choice(colors)
    if all(src[r][c] == 0 for r in range(k) for c in range(k)):
        src[0][0] = colors[0]
    return src


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        n_targets = ctx.draw_int("n_targets", 1, 2)
        k = ctx.draw_int("interior", 3, 3)
    elif difficulty == "hard":
        n_targets = ctx.draw_int("n_targets", 3, 5)
        k = ctx.draw_int("interior", 3, 4)
    else:
        n_targets = ctx.draw_int("n_targets", 2, 4)
        k = ctx.draw_int("interior", 3, 4)

    fs = k + 2                       # full (bordered) frame size
    n_total = 1 + n_targets
    hgap, vgap = 1, 2               # vgap leaves a free row above each frame for its command cell
    cell_w, cell_h = fs + hgap, fs + vgap
    ncols = max(1, min(n_total, (30 - 2) // cell_w))
    nrows = (n_total + ncols - 1) // ncols
    left_margin = rng.randint(1, 2)
    top_margin = rng.randint(1, 2)
    h = min(30, (top_margin + 1) + (nrows - 1) * cell_h + fs + 1)
    w = min(30, left_margin + (ncols - 1) * cell_w + fs + left_margin)
    g = full_grid(h, w, 0)

    src = _random_source(rng, k)
    source_slot = rng.randint(0, n_total - 1)
    codes = [rng.choice([1, 2, 3, 4]) for _ in range(n_total)]

    for i in range(n_total):
        gr, gc = divmod(i, ncols)
        top = (top_margin + 1) + gr * cell_h
        left = left_margin + gc * cell_w
        if top + fs - 1 >= h or left + fs - 1 >= w:
            continue                 # safety: skip a slot that would overrun the cap
        if i == source_slot:
            draw_frame(g, top, left, top + fs - 1, left + fs - 1, 9)
            for r in range(k):
                for c in range(k):
                    if src[r][c]:
                        g[top + 1 + r][left + 1 + c] = src[r][c]
        else:
            draw_frame(g, top, left, top + fs - 1, left + fs - 1, 8)
            g[top - 1][left] = codes[i]   # command cell above the frame's top-left corner
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 19, 0)
    if name == "no_motif":
        # source frame empty → no template to copy into targets
        draw_frame(g, 2, 1, 6, 5, 9)
        draw_frame(g, 2, 7, 6, 11, 8)
        draw_frame(g, 2, 13, 6, 17, 8)
        g[1][7] = 1; g[1][13] = 2
        return g
    if name == "no_targets":
        # only source frame with motif → nowhere to copy to
        draw_frame(g, 2, 1, 6, 5, 9)
        _paint(g, 3, 2, _MOTIFS[0], 4)
        return g
    if name == "no_codes":
        # framed motif + targets but no command cells → identity transform
        draw_frame(g, 2, 1, 6, 5, 9)
        draw_frame(g, 2, 7, 6, 11, 8)
        draw_frame(g, 2, 13, 6, 17, 8)
        _paint(g, 3, 2, _MOTIFS[0], 4)
        return g
    return g
