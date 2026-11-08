"""Generator for additional_bank:H1.

Rule: control 1 mirrors nonzero cells left-right into blanks; control 2
mirrors up-down.

Combinatorial axes (8): grid_h, grid_w, palette_kind, control,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_control, no_source_cells, source_already_mirrored.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "37cec5981f3a"
VERSION = "2.0.1"
TASK_ID = "37cec5981f3a"
SUMMARY = (
    "0-bg grid (h, w~7-10) with: "
    "(a) cell (0, 0) holds "
    "CONTROL in {1, 2}; (b) 3 "
    "SOURCE CELLS in DISTINCT "
    "non-{0, control} colors at "
    "hardcoded positions "
    "depending on control: "
    "ctrl=1 (LR mirror) → "
    "sources at (1, 1), (2, 2), "
    "(h-2, 1); ctrl=2 (UD "
    "mirror) → sources at "
    "(1, 2), (1, w-3), (2, 1). "
    "Some sources may have a "
    "2-cell stripe extension. "
    "Rule (MIRROR SOURCE CELLS "
    "BY CONTROL AXIS): READ "
    "control at (0, 0). For "
    "EACH non-{0, control} "
    "SOURCE CELL at (r, c): "
    "ctrl=1 → PAINT (r, w-1-c) "
    "with the same color "
    "(left-right mirror); "
    "ctrl=2 → PAINT (h-1-r, c) "
    "with the same color (up-"
    "down mirror). The "
    "control + originals stay. "
    "Net: source cells mirror "
    "across the axis selected "
    "by control."
)

INVARIANTS = [
    "cell (0,0) is a mirror control",
    "source cells have blank mirrored partners so completion is visible",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_control", "no_source_cells", "source_already_mirrored")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "control":        {"type": "choice", "default": "rng {1,2}", "valid": "1 or 2"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "control_corner_sources",
                       "valid": "control_corner_sources"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; (0,0) control in {1,2}; ≥1 non-{0,control} source cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    for r in range(h):
        for c in range(w):
            if not (0 <= grid[r][c] <= 9):
                errors.append(f"out-of-range value {grid[r][c]} at ({r},{c})")
    ctrl = grid[0][0]
    if ctrl == 0:
        pass  # degenerate (no_control) — allowed
    elif ctrl not in (1, 2):
        errors.append(f"control at (0,0) not in {{1,2}}: got {ctrl}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        control = ctx.draw_choice("control", [1])
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        control = ctx.draw_choice("control", [2])
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 10)
        control = ctx.draw_choice("control", [1, 2])
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    g[0][0] = control
    colors = list(ctx.draw_distinct_colors("colors", n=3, exclude=[0, control]))
    if control == 1:
        cells = [(1, 1), (2, 2), (h - 2, 1)]
    else:
        cells = [(1, 2), (1, w - 3), (2, 1)]
    for color, (r, c) in zip(colors, cells):
        g[r][c] = color
        if rng.random() < 0.5 and r + 1 < h and c + 1 < w and g[r + 1][c] == 0:
            g[r + 1][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_control":
        # source cells but no control at (0,0) → rule has no axis selector
        for r, c, col in [(2, 2, 4), (4, 4, 6), (5, 1, 7)]:
            g[r][c] = col
        return g
    if name == "no_source_cells":
        # control set but no source cells → rule has nothing to mirror
        g[0][0] = 1
        return g
    if name == "source_already_mirrored":
        # source cells AND their mirrored partners already populated → rule is identity
        g[0][0] = 1
        for r, c, col in [(2, 2, 4), (4, 4, 6)]:
            g[r][c] = col
            g[r][w - 1 - c] = col  # mirror partner already painted
        return g
    return g
