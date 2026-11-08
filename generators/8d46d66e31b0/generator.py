"""Generator for arc_additional_puzzles_21_set7:M49 — center-stamp 2-template inside each rect-frame.

Rule: a non-rect-border 2-blob is the template (cell shape). Each
rect-frame (color != 2) gets the template centered in its interior,
painted in the frame's color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_frames (no rect-frames → rule's per-frame loop is
empty, output equals input), no_template (no 2-blob → rule's
template extractor finds nothing), single_cell_template (template
is one cell → rule's stamp is trivial, no shape contrast).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_frame, paint_at
from puzzle_generators.helpers.palette import random_palette
from puzzle_generators.helpers.blobs import bbox_overlaps

GENERATOR_ID = "8d46d66e31b0"
# 1.2.1: every non-degenerate color-2 template is now a single 4-connected
# component, matching the rule's single-object extractor and the stated invariant.
# 1.2.0: defect-lint all_background_output — frame placement could fail silently,
# leaving only the 2-template; the rule then emits an EMPTY grid. Every frame is
# now guaranteed (whole-layout retry, loud raise).
VERSION = "1.2.1"
TASK_ID = "8d46d66e31b0"
SUMMARY = "Small 2-color template + 1-2 rect-frames in other colors (large enough to fit centered template)."

INVARIANTS = [
    "background is 0",
    "exactly one connected 2-color blob (non-rect-border)",
    "1-2 rect-frames in distinct non-2 colors, each ≥5×5 to fit a centered 2-template",
    "objects don't touch each other",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "no_template", "single_cell_template")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 12..15", "valid": "10..18"},
    "n_frames":       {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "template_plus_frames",
                       "valid": "template_plus_frames"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_TEMPLATES = [
    [(0, 0), (0, 1), (1, 1)],
    [(0, 0), (1, 0), (1, 1), (2, 0)],
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (0, 1), (0, 2), (1, 0)],
]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify that any color-2 template is one 4-connected component."""
    if not grid or not grid[0]:
        return ["empty grid"]
    template = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    }
    if not template:
        return []  # no_template degenerate — allowed

    unseen = set(template)
    start = unseen.pop()
    frontier = [start]
    while frontier:
        r, c = frontier.pop()
        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if neighbor in unseen:
                unseen.remove(neighbor)
                frontier.append(neighbor)
    if unseen:
        return ["color-2 template must be exactly one 4-connected component"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 12, 13)
        n_frames = ctx.draw_int("n_frames", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 14, 17)
        n_frames = ctx.draw_int("n_frames", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 12, 15)
        n_frames = ctx.draw_int("n_frames", 1, 2)
    rng = ctx.draw_rng("layout")
    for _layout in range(60):
        g = full_grid(h, w, 0)
        template = rng.choice(_TEMPLATES)
        th = max(c[0] for c in template) + 1
        tw = max(c[1] for c in template) + 1
        tr = rng.randint(1, 3)
        tc = rng.randint(1, 3)
        paint_at(g, tr, tc, template, 2)
        placed: list[tuple[int, int, int, int]] = [(tr - 1, tc - 1, tr + th, tc + tw)]
        frame_colors = list(random_palette(rng, n_frames, exclude={2}))
        n_placed = 0
        for fc in frame_colors:
            for _ in range(80):
                rh = rng.randint(5, 6)
                rw = rng.randint(5, 6)
                r1 = rng.randint(0, h - rh)
                c1 = rng.randint(0, w - rw)
                r2 = r1 + rh - 1
                c2 = c1 + rw - 1
                bb_pad = (r1 - 1, c1 - 1, r2 + 1, c2 + 1)
                if any(bbox_overlaps(bb_pad, p) for p in placed): continue
                draw_frame(g, r1, c1, r2, c2, fc)
                placed.append((r1, c1, r2, c2))
                n_placed += 1
                break
        # A frame-less grid makes the rule emit an EMPTY output (no-op demo).
        # Prefer full layouts; late in the retry budget accept >=1 frame
        # (fewer frames is still a valid instance), never zero.
        if n_placed == len(frame_colors) or (_layout > 30 and n_placed >= 1):
            return g
    raise ValueError("could not place the template plus at least one frame")


def _draw_from_degenerate(name, rng):
    h, w = 11, 14
    g = full_grid(h, w, 0)
    if name == "no_frames":
        # No rect-frames — rule's per-frame loop is empty; output
        # equals input (just the 2-template).
        for dr, dc in [(2, 2), (2, 3), (3, 3)]:
            g[dr][dc] = 2
        return g
    if name == "no_template":
        # No 2-blob — rule's template extractor finds nothing;
        # the per-frame stamp has nothing to paint.
        draw_frame(g, 1, 1, 5, 5, 3)
        draw_frame(g, 1, 8, 5, 12, 4)
        return g
    if name == "single_cell_template":
        # Template is one cell — rule's centered stamp is trivial;
        # no shape contrast across frames.
        g[2][2] = 2
        draw_frame(g, 4, 5, 8, 9, 3)
        return g
    return g
