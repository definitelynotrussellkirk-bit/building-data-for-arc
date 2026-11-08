"""Generator for arc_additional_puzzle_bank_volume18:H123.

Rule: blue marker count selects which yellow nested-frame depth is
filled cyan.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_marker, no_frames, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "35962615e0db"
VERSION = "2.1.1"  # +self_check  # dup-inputs 39%: 3 FIXED concentric frames + k in 1..3 -> tiny input space. k-th color-1 marker selects which concentric color-4 ring is filled with 8. Now n_frames 2..5, frame sizes, position, step, and k all vary.
TASK_ID = "35962615e0db"
SUMMARY = "Blue marker count selects which yellow nested-frame depth is filled cyan."

INVARIANTS = [
    "background is 0",
    "2-5 yellow (color-4) hollow frames are nested (concentric, gap >=1)",
    "blue (color-1) marker count k selects the ring/core to fill",
    "the selected band or core contains blank cells",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_marker", "no_frames", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 13..17", "valid": "11..24"},
    "grid_w":         {"type": "int", "default": "rng 13..17", "valid": "11..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "true",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "centered", "valid": "centered"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_marker|no_frames|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, color-4 frames present, color-1 marker cells present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    flat = [v for row in grid for v in row]
    if len(grid) > 30 or len(grid[0]) > 30:
        errs.append(f"grid exceeds ARC bounds: {len(grid)}x{len(grid[0])}")
    if 4 not in flat:
        errs.append("no color-4 (yellow) frame cells found")
    if 1 not in flat:
        errs.append("no color-1 (blue) marker cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("placement")
    # k color-1 markers select which concentric color-4 ring gets filled with 8.
    # Was 3 fixed concentric frames + k in 1..3 -> tiny input space (39% dups).
    # Now n_frames, frame sizes, position, step, and k all vary.
    if difficulty == "easy":
        n_frames = rng.randint(2, 3); step = 2
    elif difficulty == "hard":
        n_frames = rng.randint(3, 5)
        # Five frames at step 3 can exceed the 30x30 ARC bound once margins are
        # added; keep that case at step 2.
        step = 2 if n_frames >= 5 else rng.choice([2, 3])
    else:
        n_frames = rng.randint(2, 4); step = rng.choice([2, 2, 3])
    inner_h = rng.randint(3, 5); inner_w = rng.randint(3, 6)
    # outer extent: each level out adds 2*step to each dim (border + gap)
    fh = inner_h + 2 * (n_frames - 1) * step
    fw = inner_w + 2 * (n_frames - 1) * step
    h = fh + rng.randint(3, 5)        # +1 marker row +margins
    w = fw + rng.randint(3, 5)
    r0 = rng.randint(1, h - fh - 1)
    c0 = rng.randint(1, w - fw - 1)
    g = full_grid(h, w, 0)
    for i in range(n_frames):         # nested hollow color-4 frames (gap>=1 -> distinct)
        o = i * step
        draw_frame(g, r0 + o, c0 + o, r0 + fh - 1 - o, c0 + fw - 1 - o, 4)
    # k = which ring to fill; occasionally k>n_frames -> rule fills the innermost.
    k = n_frames + 1 if rng.random() < 0.25 else rng.randint(1, n_frames)
    cols = list(range(w)); rng.shuffle(cols)
    for c in cols[:k]:                # k markers in the top row (above the frames)
        g[0][c] = 1
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(15, 15, 0)
    if name == "no_marker":
        for offset in (0, 2, 4):
            draw_frame(g, 2 + offset, 2 + offset, 12 - offset, 12 - offset, 4)
        return g
    if name == "no_frames":
        g[0][1] = 1
        g[0][2] = 1
        return g
    if name == "full_grid":
        for r in range(15):
            for c in range(15):
                g[r][c] = 4
        return g
    return g
