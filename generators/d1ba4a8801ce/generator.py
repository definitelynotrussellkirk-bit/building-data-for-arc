"""Generator for db615bd4.

Rule: a disrupted checkerboard is restored around a framed layout with
centered content blocks.

Combinatorial axes (8): grid_h/w, orientation, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_frame, no_blocks, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, draw_rect

GENERATOR_ID = "d1ba4a8801ce"
RULE_HASH = "86c7183bd54d"  # canonical rule this generator was written against
VERSION = "2.1.1"  # shape-locked in+out: FIXED 13x15 + fixed frame/block positions. Rule (checkerboard + most-frequent-disruption frame + content blocks relocated inside) is size-agnostic. Now vary dims 11-25 + random frame pos/size + 2-3 random content blocks."
TASK_ID = "d1ba4a8801ce"
SUMMARY = (
    "Fixed 13×15 grid. Background is a 2-COLOR "
    "CHECKERBOARD with even color (e) at (r%2==0 or "
    "c%2==0) and odd color (o) at (r%2==1 and "
    "c%2==1). The pattern is DISRUPTED by: (a) a "
    "RECTANGULAR FRAME (drawn in some FRAME color) "
    "at fixed coords for one of two ORIENTATIONS "
    "(horizontal: (3..8, 3..12) or vertical: (2..11, "
    "4..10)); (b) TWO CONTENT BLOCKS in distinct "
    "colors A and B placed at fixed offsets relative "
    "to the frame. Rule: RESTORE the checkerboard "
    "everywhere EXCEPT INSIDE the frame, where the "
    "two content blocks are kept CENTERED. The frame "
    "border stays. Net: input has a noisy backdrop "
    "with a framed layout; output restores the "
    "checkerboard outside the frame, centering "
    "content blocks inside it."
)

INVARIANTS = [
    "the base background follows the task's two-color checkerboard convention",
    "the most frequent disruption color is the rectangular frame",
    "remaining disruption colors provide content block sizes that are centered inside the frame",
]

ORIENTATIONS = ("horizontal", "vertical")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_frame", "no_blocks", "full_grid")
HELPFUL_TEXTURES = ORIENTATIONS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 14..20", "valid": "11..25"},
    "grid_w":         {"type": "int", "default": "rng 15..22", "valid": "13..25"},
    "orientation":    {"type": "str", "default": "rng helpful",
                       "valid": "|".join(ORIENTATIONS)},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "5", "valid": "5"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "5", "valid": "5"},
    "texture":        {"type": "str", "default": "alias for orientation",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _checker(h, w, even, odd):
    return [[odd if r % 2 == 1 and c % 2 == 1 else even for c in range(w)] for r in range(h)]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥2 distinct colors present (bg checkerboard + frame/blocks); grid non-empty."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    h, w = len(grid), len(grid[0])
    distinct = set(grid[r][c] for r in range(h) for c in range(w))
    if len(distinct) < 2:
        errs.append(f"expected ≥2 distinct colors; found {len(distinct)}")
    # background checkerboard uses 2 colors; expect ≥3 colors total (checker + frame + blocks)
    if len(distinct) < 3:
        errs.append(f"expected ≥3 distinct colors (checkerboard pair + frame/block); found {len(distinct)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    # was FIXED 13x15 + fixed frame/block positions -> shape-locked. The rule is
    # size-agnostic (checkerboard + most-frequent-disruption frame + content blocks
    # relocated inside it). Vary dims + random frame position/size + random blocks.
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 13, 16); n_blocks = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 18, 25); w = ctx.draw_int("grid_w", 18, 25); n_blocks = ctx.draw_int("n_blocks", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 14, 20); w = ctx.draw_int("grid_w", 15, 22); n_blocks = ctx.draw_int("n_blocks", 2, 3)
    cols = ctx.draw_distinct_colors("colors", n=3 + n_blocks, exclude={0})
    even, odd, frame = cols[0], cols[1], cols[2]
    block_colors = list(cols[3:])
    g = _checker(h, w, even, odd)
    # frame outline (most frequent disruption); interior must hold the content blocks
    fh = rng.randint(5, min(9, h - 1)); fw = rng.randint(5, min(9, w - 1))
    fr0 = rng.randint(0, h - fh); fc0 = rng.randint(0, w - fw)
    draw_frame(g, fr0, fc0, fr0 + fh - 1, fc0 + fw - 1, frame)
    frame_box = {(r, c) for r in range(fr0 - 1, fr0 + fh + 1)
                 for c in range(fc0 - 1, fc0 + fw + 1)}
    used = set(frame_box)
    # content blocks: small rects placed in the background, away from the frame
    for col in block_colors:
        bh = rng.randint(1, 2); bw = rng.randint(1, 2)
        for _ in range(80):
            r0 = rng.randint(0, h - bh); c0 = rng.randint(0, w - bw)
            cells = {(r0 + dr, c0 + dc) for dr in range(bh) for dc in range(bw)}
            if cells & used:
                continue
            for r, c in cells:
                g[r][c] = col
                used.add((r, c))
            break
    return g


def _draw_from_degenerate(name, rng):
    g = _checker(13, 15, 1, 2)
    if name == "no_frame":
        return g
    if name == "no_blocks":
        draw_frame(g, 3, 3, 8, 12, 4)
        return g
    if name == "full_grid":
        return [[4 for _ in range(15)] for _ in range(13)]
    return g
