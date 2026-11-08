"""Generator for arc_puzzle_bank_21_set13_bundle:hard_m06 — template stamped
into framed boxes, transformed by a corner marker.

Rule: a free-standing COLOR-7 TEMPLATE shape + several rectangular FRAMES,
each a distinct border color. Each frame carries a MARKER (color 1/2/3/4)
just outside one corner; the marker selects a transform of the template
(1=rot-cw, 2=rot-180, 3=flip-lr, 4=identity), which is recolored to the
marker color and centered inside the frame. The free template and markers
are erased in the output.

Combinatorial axes: grid size, template shape, number / size / border-color
of the frames, each frame's marker (transform), and frame positions.
Degenerates: no_template, no_frames, no_markers.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_frame, paint_at

GENERATOR_ID = "16eb1b9873e1"
RULE_HASH = "a21c38ce7415"  # canonical rule this generator was written against
# 2.0.0: WRONG-TASK FIX. Old generator drew random scattered motifs (a
#        "vertical pack" docstring) that did not match the rule at all
#        (rule needs a color-7 template + bordered frames + corner markers).
#        Rewrote to produce the genuine structure: 1-3 frames each with a
#        corner marker (1/2/3/4) selecting a transform of the shared color-7
#        template, centered inside.
VERSION = "2.0.1"
TASK_ID = "16eb1b9873e1"

SUMMARY = (
    "0-bg grid. ONE free-standing COLOR-7 TEMPLATE polyomino (3-5 cells), "
    "plus 1-3 hollow rectangular FRAMES in distinct border colors. Each "
    "frame has a MARKER cell (color 1/2/3/4) just outside one corner, "
    "selecting a transform (1=rot-cw, 2=rot-180, 3=flip-lr, 4=identity). "
    "Rule: transform the template by each frame's marker, recolor it to the "
    "marker color, and centre it inside that frame; erase the free template "
    "and the markers."
)

INVARIANTS = [
    "background is 0",
    "exactly one free color-7 template outside all frames",
    "each frame is a hollow rectangle in a distinct non-{1,2,3,4,7} border color",
    "each frame has one marker in {1,2,3,4} just outside a corner",
    "frame interiors are large enough to hold the centered transformed template",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_template", "no_frames", "no_markers")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..16", "valid": "9..20"},
    "grid_w":         {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "n_frames":       {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "varies", "valid": "varies"},
    "position_bias":  {"type": "str", "default": "template_plus_framed_boxes",
                       "valid": "template_plus_framed_boxes"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "varies"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

# Frame border colors (exclude 0, the markers 1/2/3/4, and template color 7).
_FRAME_COLORS = [5, 6, 8, 9]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, at least one color-7 template cell and marker cells (1-4)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in ("no_template", "no_frames", "no_markers"):
        return errs
    sevens = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 7]
    markers = [(r, c) for r in range(h) for c in range(w) if grid[r][c] in (1, 2, 3, 4)]
    if not sevens:
        errs.append("no color-7 template cells found")
    if not markers:
        errs.append("no marker cells (colors 1-4) found")
    return errs


def _norm(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _grow(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        cells.add((r + dr, c + dc))
    return _norm(list(cells))


def _free(g, r0, c0, r1, c1):
    h, w = len(g), len(g[0])
    if r0 < 0 or c0 < 0 or r1 >= h or c1 >= w:
        return False
    for r in range(max(0, r0 - 1), min(h, r1 + 2)):
        for c in range(max(0, c0 - 1), min(w, c1 + 2)):
            if g[r][c] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 12, 14)
        n_frames = ctx.draw_int("n_frames", 1, 1)
        tmpl_sz = (3, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 15, 20)
        w = ctx.draw_int("grid_w", 16, 22)
        n_frames = ctx.draw_int("n_frames", 2, 3)
        tmpl_sz = (4, 5)
    else:
        h = ctx.draw_int("grid_h", 12, 17)
        w = ctx.draw_int("grid_w", 13, 18)
        n_frames = ctx.draw_int("n_frames", 1, 3)
        tmpl_sz = (3, 5)

    for _attempt in range(40):
        g = full_grid(h, w, 0)
        template = _grow(rng, rng.randint(*tmpl_sz))
        th = max(r for r, _ in template) + 1
        tw = max(c for _, c in template) + 1
        # Interior must hold the template under rotation -> need side >= max(th,tw).
        inner = max(th, tw)

        # Place the free-standing color-7 template first (top region).
        placed_template = False
        for _t in range(60):
            r0 = rng.randint(0, h - th)
            c0 = rng.randint(0, w - tw)
            if _free(g, r0, c0, r0 + th - 1, c0 + tw - 1):
                paint_at(g, r0, c0, template, 7)
                placed_template = True
                break
        if not placed_template:
            continue

        frame_colors = rng.sample(_FRAME_COLORS, min(n_frames, len(_FRAME_COLORS)))
        ok = True
        for fcolor in frame_colors:
            # Frame outer dims: interior >= inner, plus border, plus a buffer
            # of >=1 outside the corner for the marker.
            fih = inner + rng.randint(0, 2)
            fiw = inner + rng.randint(0, 2)
            foh = fih + 2
            fow = fiw + 2
            placed_frame = False
            for _t in range(80):
                fr0 = rng.randint(1, h - foh - 1)   # leave room for marker above
                fc0 = rng.randint(1, w - fow - 1)   # and to the left
                fr1 = fr0 + foh - 1
                fc1 = fc0 + fow - 1
                # the frame + its 1-cell halo (incl. marker slots) must be free
                if not _free(g, fr0 - 1, fc0 - 1, fr1, fc1):
                    continue
                draw_frame(g, fr0, fc0, fr1, fc1, fcolor)
                # marker just outside a corner; rule checks
                # (fr0-1,fc0),(fr0,fc0-1),(fr0-1,fc1),(fr1,fc0-1) in order.
                marker = rng.choice([1, 2, 3, 4])
                slot = rng.choice([(fr0 - 1, fc0), (fr0, fc0 - 1),
                                   (fr0 - 1, fc1), (fr1, fc0 - 1)])
                mr, mc = slot
                if 0 <= mr < h and 0 <= mc < w and g[mr][mc] == 0:
                    g[mr][mc] = marker
                    placed_frame = True
                    break
                else:
                    # undo frame if marker can't be placed
                    for r in range(fr0, fr1 + 1):
                        for c in range(fc0, fc1 + 1):
                            if r in (fr0, fr1) or c in (fc0, fc1):
                                g[r][c] = 0
            if not placed_frame:
                ok = False
                break
        if ok:
            return g

    # Fallback: minimal valid layout.
    g = full_grid(12, 14, 0)
    paint_at(g, 1, 1, [(0, 0), (1, 0), (1, 1)], 7)
    draw_frame(g, 5, 5, 10, 10, 8)
    g[4][5] = 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 12, 14
    g = full_grid(h, w, 0)
    tmpl = [(0, 0), (1, 0), (1, 1)]
    if name == "no_template":
        # frame + marker but no color-7 template to stamp
        draw_frame(g, 4, 4, 9, 9, 8)
        g[3][4] = 1
        return g
    if name == "no_frames":
        # free template but no frames to stamp into
        paint_at(g, 2, 2, tmpl, 7)
        return g
    if name == "no_markers":
        # template + frame but no marker -> default transform, no marker color
        paint_at(g, 1, 1, tmpl, 7)
        draw_frame(g, 4, 5, 9, 10, 8)
        return g
    return g
