"""Generator for arc_additional_puzzle_bank_volume23:H157.

Rule: a control color selects one of three blue nested-frame regions
for blank-output fill.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_control, no_frames, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "277c2478bab6"
VERSION = "2.0.1"
TASK_ID = "277c2478bab6"
SUMMARY = (
    "0-bg grid (h, w~13-17) "
    "with: (a) CONTROL "
    "CELL at (0, 0) in "
    "COLOR ∈ {2, 3, 4} "
    "encoding a band "
    "index; (b) THREE "
    "CONCENTRIC COLOR-1 "
    "(blue) FRAMES drawn "
    "at offsets (0, 2, 4) "
    "from a centered "
    "anchor — frame 0 "
    "outermost, frame 1 "
    "middle, frame 2 "
    "innermost. Rule (A "
    "CONTROL COLOR "
    "SELECTS ONE OF "
    "THREE BLUE NESTED-"
    "FRAME REGIONS FOR "
    "BLANK-OUTPUT FILL): "
    "READ the CONTROL "
    "cell's color k ∈ "
    "{2, 3, 4}. The 3 "
    "concentric blue "
    "frames define 3 "
    "BANDS/REGIONS: "
    "region-1 = ring "
    "between frame 0 and "
    "1; region-2 = ring "
    "between 1 and 2; "
    "region-3 = interior "
    "inside frame 2. "
    "SELECT the k-th "
    "REGION. PRODUCE a "
    "FRESH BLANK 0-grid "
    "and PAINT only "
    "that region with "
    "the control color k. "
    "Net: control color "
    "picks one nested "
    "ring; output is "
    "that ring on a "
    "blank canvas in the "
    "control color."
)

INVARIANTS = [
    "background is 0",
    "three color-1 frames are concentric",
    "control marker is exactly one of colors 2, 3, or 4",
    "the selected region is nonempty",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_control", "no_frames", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 13..17", "valid": "11..24"},
    "grid_w":         {"type": "int", "default": "rng 13..17", "valid": "11..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "true",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "centered", "valid": "centered"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: (0,0) has control color 2/3/4; grid has color-1 frame cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_control", "no_frames", "full_grid"):
        return []
    errs = []
    ctrl = grid[0][0]
    if ctrl not in (2, 3, 4):
        errs.append(f"(0,0) control color {ctrl} not in {{2,3,4}}")
    c1_count = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 1)
    if c1_count == 0:
        errs.append("no color-1 frame cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # control at (0,0) selects one of 3 concentric color-1 frames. Frames were ALWAYS
    # flush to the border at fixed offsets (0,2,4) -> only grid size + control varied
    # (dup-inputs 44%). Now the nested structure's position AND size vary.
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 13, 16); w = ctx.draw_int("grid_w", 13, 16)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 18, 24); w = ctx.draw_int("grid_w", 18, 24)
    else:
        h = ctx.draw_int("grid_h", 14, 20); w = ctx.draw_int("grid_w", 14, 20)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    g[0][0] = rng.choice([2, 3, 4])
    # outer frame >= 11 in each dim so 3 nested frames (gap 2) all have >=3 extent;
    # top-left starts at row >= 1 so the (0,0) control cell stays clear of the frame.
    oh = rng.randint(11, h - 1); ow = rng.randint(11, w - 1)
    r0 = rng.randint(1, h - oh); c0 = rng.randint(0, w - ow)
    r1 = r0 + oh - 1; c1 = c0 + ow - 1
    for off in (0, 2, 4):
        draw_frame(g, r0 + off, c0 + off, r1 - off, c1 - off, 1)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(15, 15, 0)
    if name == "no_control":
        for offset in (0, 2, 4):
            draw_frame(g, 2 + offset, 2 + offset, 12 - offset, 12 - offset, 1)
        return g
    if name == "no_frames":
        g[0][0] = 2
        return g
    if name == "full_grid":
        for r in range(15):
            for c in range(15):
                g[r][c] = 1
        return g
    return g
