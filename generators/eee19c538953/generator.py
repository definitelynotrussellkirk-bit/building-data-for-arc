"""Generator for arc_puzzle_bank_twentieth21:M135 — extract interior of 8-frame.

Rule: there is exactly one 8-color rectangle frame; output is the
strict interior crop (preserving any non-8 markers inside).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_markers,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_frame, frame_no_interior, multiple_frames.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_frame
from puzzle_generators.helpers.palette import random_palette
from puzzle_generators.helpers.selfcheck import color_rect_frames

GENERATOR_ID = "eee19c538953"
VERSION = "2.2.0"  # force at least two visible interior colors when the crop has room  # density-scaled interior fill with repeated colors (canonical interiors are denser patterns)
TASK_ID = "eee19c538953"
SUMMARY = "1 8-color rect frame somewhere in the grid; output = strict interior crop (interior pattern preserved). Frame + outside region vanish. Interior is filled to a density with a small repeated palette (matching canonical patterns), so the crop content scales with frame size."

# Rivals: 'output the full grid' refuted by any demo (output is
# smaller). 'crop to bbox including frame' refuted by any demo
# (output excludes the 8-row/col). 'preserve frame in output'
# refuted by any demo. 'output is the markers only on blank'
# refuted by ≥1 demo where interior has bg between markers.
# 3 demos with varied frame positions + sizes cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly one 8-color rectangle frame (>=5x5 so interior is non-trivial)",
    "strict interior has a non-empty repeated non-0/non-8 pattern",
    "no non-bg cells outside the frame",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frame", "frame_no_interior", "multiple_frames")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..18"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "6..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_markers":      {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "position_bias":  {"type": "str", "default": "interior", "valid": "interior"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 7, 9)
        n_min, n_max = 1, 3
        min_frame = 5
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 18)
        w = ctx.draw_int("grid_w", 12, 18)
        n_min, n_max = 4, 7
        min_frame = 7
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 9, 13)
        n_min, n_max = 2, 5
        min_frame = 6
    g = full_grid(h, w, 0)
    max_frame_h = h - 1
    max_frame_w = w - 1
    rh = rng.randint(min_frame, max(min_frame, max_frame_h))
    rw = rng.randint(min_frame, max(min_frame, max_frame_w))
    rh = min(rh, h - 1); rw = min(rw, w - 1)
    r1 = rng.randint(0, h - rh)
    c1 = rng.randint(0, w - rw)
    r2 = r1 + rh - 1
    c2 = c1 + rw - 1
    draw_frame(g, r1, c1, r2, c2, 8)
    interior = [(r, c) for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)]
    rng.shuffle(interior)
    # fill the interior to a density with a small REPEATED palette (a pattern),
    # so the crop content scales with frame size (matches canonical interiors)
    n_colors = min(max(2, rng.randint(max(1, n_min), n_max)), 6)
    palette = list(random_palette(rng, n_colors, exclude={8}))
    density = rng.uniform(0.3, 0.6)
    n_fill = max(1, min(len(interior), int(round(len(interior) * density))))
    for i, (r, c) in enumerate(interior[:n_fill]):
        # Seed the first two filled cells with different colors so the crop is
        # not a constant-color field; the rest stays random/repeated.
        g[r][c] = palette[i] if i < min(2, len(palette), n_fill) else rng.choice(palette)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_frame":
        # no 8-frame → rule has no anchor for cropping
        for r, c, v in [(2, 3, 4), (3, 5, 6), (5, 6, 7)]:
            g[r][c] = v
        return g
    if name == "frame_no_interior":
        # frame is 3x3 → strict interior is 1x1, rule still works but trivial
        draw_frame(g, 2, 2, 4, 4, 8)
        return g
    if name == "multiple_frames":
        # two separate 8-frames → ambiguous which one to crop to
        draw_frame(g, 0, 0, 3, 3, 8)
        g[1][1] = 4
        draw_frame(g, 4, 4, 8, 8, 8)
        g[5][5] = 6
        g[6][6] = 7
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    frames = color_rect_frames(grid, 8, min_outer_h=5, min_outer_w=5)
    if len(frames) != 1:
        return [f"expected exactly one nontrivial 8-frame, found {len(frames)}"]
    r1, c1, r2, c2 = frames[0]
    outside = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
               if v != 0 and not (r1 <= r <= r2 and c1 <= c <= c2)]
    if outside:
        msgs.append("non-background cells outside the selected frame")
    interior = [grid[r][c] for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)]
    filled = [v for v in interior if v not in (0, 8)]
    if not filled:
        msgs.append("strict interior has no crop content")
    if 8 in interior:
        msgs.append("frame color leaked into strict interior")
    if len(set(filled)) < 2 and len(filled) >= 3:
        msgs.append("interior pattern is effectively single-color")
    return msgs
