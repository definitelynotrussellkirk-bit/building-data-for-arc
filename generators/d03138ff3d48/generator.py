"""Generator for 6f473927.

Rule: if col 0 has any non-zero, output places 8s at mirror of zeros
on LEFT and original on right. Else mirror on right.

Combinatorial axes (8): grid_h/w, col0_has_nonzero, palette_size,
fg_density, fg_layout, palette_kind, decoy_density, anchor_corner.
Degenerates: empty_grid, full_grid, single_cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d03138ff3d48"
VERSION = "2.0.0"
TASK_ID = "d03138ff3d48"
SUMMARY = (
    "h×w grid (h, w~3-6) with foreground "
    "non-bg cells in some PALETTE (warm/cool/"
    "broad/small) arranged in a LAYOUT "
    "(scattered/blob/diag/row/col/checker/"
    "frame). Column 0 is conditionally "
    "all-zero (col0_has_nonzero=false) or has "
    "at least one non-zero. ≥2 fg cells and "
    "≥1 bg cell guaranteed; color 8 is never "
    "used in input (rule writes 8 for output). "
    "Rule (TASK-SPECIFIC OUTPUT NORMALIZATION): "
    "if column 0 of input has ANY NON-ZERO, "
    "produce a 2w-wide output with the LEFT "
    "HALF showing color-8 wherever the input "
    "has a 0 (a mask of zeros), and the RIGHT "
    "HALF being the original grid. ELSE "
    "(col 0 is all-zero), produce a 2w-wide "
    "output with the LEFT HALF being the "
    "original grid and the RIGHT HALF being "
    "the horizontal mirror. Net: input grid "
    "is doubled horizontally with color-8 "
    "mask of bg cells or its mirror, depending "
    "on col 0 contents."
)

INVARIANTS = [
    "h, w in [3, 6]",
    ">=2 non-bg cells (so output is non-trivial)",
    ">=1 bg cell (so 8-mask is visible)",
    "no color 8 in input (rule writes 8 for output)",
]

FG_LAYOUTS = ("scattered", "blob", "diag", "row", "col",
              "checker", "frame")
PALETTE_KINDS = ("warm", "cool", "broad", "small")
DEGENERATE_TEXTURES = ("empty_grid", "full_grid", "single_cell")
HELPFUL_TEXTURES = FG_LAYOUTS

AXES = {
    "grid_h":          {"type": "int", "default": "rng 3..6", "valid": "3..8"},
    "grid_w":          {"type": "int", "default": "rng 3..6", "valid": "3..8"},
    "col0_has_nonzero": {"type": "bool", "default": "rng true|false",
                         "valid": "true|false"},
    "palette_size":    {"type": "int", "default": "rng 1..3", "valid": "1..7"},
    "fg_density":      {"type": "float", "default": "rng 0.3..0.6",
                        "valid": "0.1..1"},
    "fg_layout":       {"type": "str", "default": "rng helpful",
                        "valid": "|".join(FG_LAYOUTS)},
    "palette_kind":    {"type": "str", "default": "rng helpful",
                        "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":   {"type": "bool", "default": "false",
                        "valid": "true|false"},
    "texture":         {"type": "str", "default": "alias for fg_layout",
                        "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 3, 4
    elif difficulty == "hard":
        h_lo, h_hi = 5, 7
    else:
        h_lo, h_hi = 3, 6
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    if palette_kind == "warm":
        pool = [3, 4, 6, 9]
    elif palette_kind == "cool":
        pool = [1, 5, 7]
    elif palette_kind == "small":
        pool = [1, 2, 3]
    else:
        pool = [1, 2, 3, 4, 6, 7, 9]
    rng.shuffle(pool)
    n_palette = int(overrides.get("palette_size",
                                  ctx.draw_int("palette_size", 1, 3)))
    palette = pool[:max(1, n_palette)]
    layout = (overrides.get("texture") or overrides.get("fg_layout")
              or ctx.draw_choice("fg_layout", list(FG_LAYOUTS)))
    density = float(overrides.get("fg_density",
                                  ctx.draw_rng("fg_density")
                                  .uniform(0.3, 0.6)))
    col0_nonzero = bool(overrides.get("col0_has_nonzero",
                                      rng.random() < 0.5))
    g = full_grid(h, w, 0)
    _fill(g, layout, h, w, palette, density, rng)
    if col0_nonzero:
        if all(g[r][0] == 0 for r in range(h)):
            g[h // 2][0] = palette[0]
    else:
        for r in range(h):
            g[r][0] = 0
    if bool(overrides.get("anchor_corner", False)) and col0_nonzero:
        g[0][0] = palette[0]

    # Normal examples must have enough foreground to teach more than a scalar
    # presence/absence cue AND at least one 0 so the task-specific color-8 mask
    # is visible.  The previous one-shot fallback only guaranteed one foreground
    # cell; sparse scattered/blob draws leaked singletons in default generation.
    _enforce_normal_invariants(g, palette, col0_nonzero)
    return g


def _fill(g, layout, h, w, palette, density, rng):
    if layout == "blob":
        cr, cc = rng.randint(0, h - 1), rng.randint(0, w - 1)
        for r in range(h):
            for c in range(w):
                if abs(r - cr) + abs(c - cc) <= 2 and rng.random() < density + 0.2:
                    g[r][c] = rng.choice(palette)
        return
    if layout == "diag":
        for k in range(min(h, w)):
            g[k][k] = rng.choice(palette)
        return
    if layout == "row":
        r = rng.randint(0, h - 1)
        for c in range(w):
            g[r][c] = rng.choice(palette)
        return
    if layout == "col":
        c = rng.randint(0, w - 1)
        for r in range(h):
            g[r][c] = rng.choice(palette)
        return
    if layout == "checker":
        for r in range(h):
            for c in range(w):
                if (r + c) % 2 == 0:
                    g[r][c] = rng.choice(palette)
        return
    if layout == "frame":
        for r in range(h):
            for c in range(w):
                if r in (0, h - 1) or c in (0, w - 1):
                    g[r][c] = rng.choice(palette)
        return
    for r in range(h):
        for c in range(w):
            if rng.random() < density:
                g[r][c] = rng.choice(palette)


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    color = rng.choice([1, 2, 3, 4, 6, 7, 9])
    if name == "empty_grid":
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = color
        return g
    if name == "single_cell":
        g[h // 2][w // 2] = color
        return g
    return g


def _enforce_normal_invariants(g, palette, col0_nonzero):
    h, w = len(g), len(g[0])

    def fg_cells():
        return [(r, c) for r in range(h) for c in range(w) if g[r][c] != 0]

    # Add foreground cells away from column 0 when the branch requires col0 all
    # zero.  Prefer stable interior locations, then fall back to any legal slot.
    candidates = [(r, c) for r in range(h) for c in range(w)
                  if col0_nonzero or c != 0]
    candidates.sort(key=lambda rc: (abs(rc[0] - h // 2) + abs(rc[1] - w // 2),
                                    rc[0], rc[1]))
    for r, c in candidates:
        if len(fg_cells()) >= 2:
            break
        if g[r][c] == 0:
            g[r][c] = palette[len(fg_cells()) % len(palette)]

    # Keep the branch bit honest after repairs.
    if col0_nonzero and all(g[r][0] == 0 for r in range(h)):
        g[h // 2][0] = palette[0]
    if not col0_nonzero:
        for r in range(h):
            g[r][0] = 0
        if len(fg_cells()) < 2:
            for r, c in candidates:
                if c != 0 and g[r][c] == 0:
                    g[r][c] = palette[len(fg_cells()) % len(palette)]
                    if len(fg_cells()) >= 2:
                        break

    # At least one zero is required for the output's 8-mask to be visible.  If a
    # dense/frame/checker draw filled the whole board, clear a cell that does not
    # destroy the col0 branch or the two-foreground minimum.
    if all(g[r][c] != 0 for r in range(h) for c in range(w)):
        rr, cc = (0, 1) if not col0_nonzero and w > 1 else (0, 0)
        g[rr][cc] = 0


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    h = len(grid)
    w = len(grid[0]) if h else 0
    flat = [v for row in grid for v in row]
    msgs = []
    if not (3 <= h <= 7 and 3 <= w <= 7):
        msgs.append("grid dimensions outside generated 3..7 range")
    if 8 in flat:
        msgs.append("input uses color 8 reserved for the output mask")
    if sum(1 for v in flat if v != 0) < 2:
        msgs.append("fewer than two foreground cells")
    if not any(v == 0 for v in flat):
        msgs.append("no background zero cells for the output mask")
    return msgs
