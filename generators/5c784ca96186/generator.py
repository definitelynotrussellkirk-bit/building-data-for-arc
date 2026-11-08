"""Generator for next_b:hard_08 — rotate template by control and stamp.

Rule: template = color-2 component. control = single-cell color from
{1,3,4,6} where 1→0 rotations, 3→1, 4→2, 6→3 (CW). target = the
unique color-8 cell. Output stamps the rotated template at target,
painted color 7.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_template (no color-2 component → rule has nothing
to stamp); no_target (no color-8 cell → rule has no stamp
destination); rot_symmetric_template (template invariant under all
4 rotations → control choice has no visible effect, all rotations
identical).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5c784ca96186"
VERSION = "2.1.0"
TASK_ID = "5c784ca96186"

SUMMARY = (
    "0-bg grid (h×w, ~11-13 by ~12-14) with: (a) one connected "
    "color-2 (red) TEMPLATE shape, 3-4 cells, not rotationally "
    "symmetric; (b) one isolated CONTROL cell in {1, 3, 4, 6} "
    "(determines rotation amount: 1→0, 3→1, 4→2, 6→3 quarter-"
    "turns CW); (c) one isolated color-8 TARGET cell. All three "
    "components are 8-conn isolated. Rule: extract template "
    "cells; normalize. Read control color; rotate template by "
    "k=0..3 CW based on control. Stamp at target position: "
    "paint color 7 (orange) at each (target_r + offset_r, "
    "target_c + offset_c). Output: fresh canvas with only the "
    "stamped 7-pattern."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly one connected color-2 template (3-4 cells, non-symmetric)",
    "exactly one isolated single-cell control in {1, 3, 4, 6}",
    "exactly one isolated color-8 target cell",
    "rotated template stamped at target stays in bounds",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_template", "no_target", "rot_symmetric_template")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 11..13", "valid": "10..16"},
    "grid_w":            {"type": "int", "default": "rng 12..14", "valid": "11..16"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 4..4", "valid": "4..4"},
    "position_bias":     {"type": "str", "default": "template_control_target",
                          "valid": "template_control_target"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..4", "valid": "4..4"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_SHAPES = [
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 1)],
    [(0, 0), (1, 0), (2, 0), (2, 1)],
]


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _too_close(g, r, c) -> bool:
    h, w = len(g), len(g[0])
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0:
                return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 12, 13)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 13)
        w = ctx.draw_int("grid_w", 13, 14)
    else:
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 12, 14)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    shape = rng.choice(_SHAPES)
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    bound = max(sh, sw)
    placed = False
    for _ in range(40):
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = 2
        placed = True; break
    if not placed:
        raise ValueError("could not place template")
    control = rng.choice([1, 3, 4, 6])
    for _ in range(60):
        r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        if g[r][c] != 0 or _too_close(g, r, c): continue
        g[r][c] = control; break
    for _ in range(60):
        r = rng.randint(0, h - bound); c = rng.randint(0, w - bound)
        if g[r][c] != 0 or _too_close(g, r, c): continue
        bad = False
        for rr in range(r, r + bound):
            for cc in range(c, c + bound):
                if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0:
                    bad = True; break
            if bad: break
        if bad: continue
        g[r][c] = 8
        return g
    raise ValueError("could not place 8-target with stamp clearance")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, color-2 template cells present, one control in {1,3,4,6}, one color-8 target."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    eights = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    controls = [(r, c) for r in range(h) for c in range(w) if grid[r][c] in (1, 3, 4, 6)]
    if not twos:
        errs.append("no color-2 template cells found")
    if not eights:
        errs.append("no color-8 target cell found")
    if not controls:
        errs.append("no control cell in {1,3,4,6} found")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 12, 13
    g = full_grid(h, w, 0)
    if name == "no_template":
        # No color-2 template — rule has nothing to stamp.
        g[3][3] = 4
        g[7][9] = 8
        return g
    if name == "no_target":
        # Template + control but no color-8 target — no stamp destination.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][2 + dc] = 2
        g[7][9] = 4
        return g
    if name == "rot_symmetric_template":
        # 2x2 solid square invariant under all rotations.
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            g[2 + dr][2 + dc] = 2
        g[6][6] = 4
        g[8][10] = 8
        return g
    return g
