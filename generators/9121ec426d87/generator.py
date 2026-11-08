"""Generator for arc_additional_puzzles_21_set13_bundle:H88 — rotate, crop, pack boxes.

Rule: each color-1 rectangular frame has a transform token directly above its
top-left corner (9=identity, 2=cw, 3=180, 4=transpose, else identity). Crop
the inside motif to its bbox, apply the transform, then pack the transformed
crops left-to-right with one-column gaps.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_frames, no_tokens, empty_motifs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "9121ec426d87"
VERSION = "1.2.1"
TASK_ID = "9121ec426d87"

SUMMARY = "3 horizontal color-1 frames; each has a transform token (2/3/4/9) above its TL corner."

INVARIANTS = [
    "background is 0",
    "exactly 3 hollow color-1 rectangular frames in a horizontal row",
    "above each frame's top-left a single transform token (2, 3, 4, or 9)",
    "each frame interior contains 2-4 colored motif cells",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "no_tokens", "empty_motifs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "frame_n":        {"type": "int", "default": "rng 5..6", "valid": "5..7"},
    "n_frames":       {"type": "int", "default": "rng 3..3", "valid": "2..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "rng 4..5", "valid": "4..5"},
    "position_bias":  {"type": "str", "default": "frames_with_tokens",
                       "valid": "frames_with_tokens"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..5", "valid": "4..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_frames|no_tokens|empty_motifs"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 color-1 frame cell and >=1 transform token in {2,3,4,9}."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in ("no_frames", "no_tokens", "empty_motifs"):
        return errs
    if not any(grid[r][c] == 1 for r in range(h) for c in range(w)):
        errs.append("no color-1 frame cells found")
    if not any(grid[0][c] in (2, 3, 4, 9) for c in range(w)):
        errs.append("no transform token (2,3,4,9) in row 0")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        fn = ctx.draw_int("frame_n", 5, 5)
        n_frames = ctx.draw_int("n_frames", 2, 2)
    elif difficulty == "hard":
        fn = ctx.draw_int("frame_n", 6, 7)
        n_frames = ctx.draw_int("n_frames", 4, 4)
    else:
        fn = ctx.draw_int("frame_n", 5, 6)
        n_frames = ctx.draw_int("n_frames", 3, 3)
    rng = ctx.draw_rng("layout")
    gap = 3
    # Fit n_frames frames (each fn wide) + gaps within the 30-col ARC canvas
    # (hard reached 4 frames x fn 7 + 9 = 37). Keep fn >= 5 (inner pattern needs it).
    fn = min(fn, (30 - (n_frames - 1) * gap) // n_frames)
    inner_n = fn - 2
    h = fn + 2
    w = n_frames * fn + (n_frames - 1) * gap

    for outer in range(40):
        g = full_grid(h, w, 0)
        anchors = []
        for i in range(n_frames):
            ar = 1
            ac = i * (fn + gap)
            anchors.append((ar, ac))
            draw_frame(g, ar, ac, ar + fn - 1, ac + fn - 1, 1)

        for ar, ac in anchors:
            token = rng.choice([2, 3, 4, 9])
            g[ar - 1][ac] = token

        for ar, ac in anchors:
            n_cells = rng.randint(2, max(2, inner_n))
            inner_cells = [(r, c) for r in range(inner_n) for c in range(inner_n)]
            chosen = rng.sample(inner_cells, n_cells)
            color = rng.choice([5, 6, 7, 8])
            for ir, ic in chosen:
                g[ar + 1 + ir][ac + 1 + ic] = color
        return g
    raise ValueError("could not realize boxed-tokens layout in 40 attempts")


def _draw_from_degenerate(name, rng):
    fn = 5; n_frames = 3; gap = 3
    h = fn + 2
    w = n_frames * fn + (n_frames - 1) * gap
    g = full_grid(h, w, 0)
    if name == "no_frames":
        # Tokens but no frames — rule's "transform per frame"
        # has no scope; pack undefined.
        for i in range(n_frames):
            ac = i * (fn + gap)
            g[0][ac] = 2
        return g
    anchors = []
    for i in range(n_frames):
        ar = 1; ac = i * (fn + gap)
        anchors.append((ar, ac))
        draw_frame(g, ar, ac, ar + fn - 1, ac + fn - 1, 1)
    if name == "no_tokens":
        # Frames with motifs but no transform tokens above —
        # rule's transform lookup fails per frame.
        for ar, ac in anchors:
            g[ar + 1][ac + 1] = 6; g[ar + 2][ac + 2] = 6
        return g
    if name == "empty_motifs":
        # Frames + tokens but no interior cells — rule has no
        # motif to crop and pack.
        for ar, ac in anchors:
            g[ar - 1][ac] = 2
        return g
    return g
