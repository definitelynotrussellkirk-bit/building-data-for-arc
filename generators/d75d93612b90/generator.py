"""Generator for d93c6891.

Rule: gray contact pushes orange blocks, while isolated orange blocks
remain orange.

Combinatorial axes (8): grid_h/w, direction, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_orange, no_gray, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "d75d93612b90"
RULE_HASH = "eca2fe4b3b91"  # canonical rule this generator was written against
VERSION = "3.2.0"  # fix OOB left/right strip placement on narrow easy boards; add self_check
TASK_ID = "d75d93612b90"
SUMMARY = (
    "Variable-size 0-bg grid with: (a) one ORANGE(7) rectangular "
    "block (rh∈3-4 × rw∈3-5) at a random interior position; "
    "(b) one GRAY(5) strip of THICKNESS t spanning exactly "
    "one side of the block (top/bottom/left/right) so the "
    "rule's push = t ∈ {1,2,3}; (c) one isolated 2×2 orange "
    "block in the top-left corner (no gray contact). Rule: "
    "first recolor every gray(5) cell → yellow(4) and every "
    "orange(7) cell → gray(5) into a base result. Then for "
    "each orange block in the input, find total gray contact "
    "size and contact direction. Push = floor(gray_size / "
    "perpendicular_dim) cells from the contacted side. Re-"
    "paint that side's slice of the orange block back to "
    "orange(7); the remaining slice stays gray(5). Isolated "
    "orange blocks (no gray contact) revert entirely to "
    "orange(7) — staying unchanged from input."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "orange blocks may touch a gray block on exactly one side",
    "gray cells recolor to yellow and orange cells first recolor to gray",
    "the far side of each contacted orange block remains orange according to contact size",
    "orange blocks without gray contact stay orange",
]

DIRECTIONS = ("top", "left", "bottom", "right")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_orange", "no_gray", "full_grid")
HELPFUL_TEXTURES = DIRECTIONS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 12..16", "valid": "10..22"},
    "grid_w":         {"type": "int", "default": "rng 14..18", "valid": "12..22"},
    "direction":      {"type": "str", "default": "rng (random of 4)",
                       "valid": "top|left|bottom|right"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for direction",
                       "valid": "top|left|bottom|right|no_orange|no_gray|full_grid"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    # rule (gray strip pushes the orange block) is size-agnostic; was FIXED 12x14
    # (shape-locked in+out). Vary dims.
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 12); w = ctx.draw_int("grid_w", 12, 14)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 15, 20); w = ctx.draw_int("grid_w", 17, 22)
    else:
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 14, 18)
    direction = (overrides.get("texture") if overrides.get("texture") in DIRECTIONS else None) or \
                overrides.get("direction") or \
                rng.choice(list(DIRECTIONS))
    # Gray strip THICKNESS = the rule's push amount: push = floor(gray_size /
    # perp_dim), and the strip spans the full contact side so gray_size = t*side →
    # push = t.  Choose t together with the sampled block dimensions so the gray
    # strip and orange block both fit; the old left/right branch used max(lower,
    # upper), which forced an out-of-bounds c when narrow boards drew t too large.
    for _attempt in range(40):
        rh = rng.randint(3, 4)
        rw = rng.randint(3, 5)
        if direction in ("top", "bottom"):
            max_t = min(rh - 1, h - rh - 1)
        else:
            max_t = min(rw - 1, w - rw - 4)
        if max_t < 1:
            continue
        t = rng.randint(1, max_t)
        g = full_grid(h, w, 0)
        # isolated 2×2 orange in the top-left corner — placing the main block + gray at
        # cols ≥ 4 keeps it clear of this corner (no gray contact → it reverts to orange).
        draw_rect(g, 1, 1, 2, 2, 7)
        if direction == "top":
            r_lo, r_hi = t + 1, h - rh
            c_lo, c_hi = 4, w - rw
            if r_lo > r_hi or c_lo > c_hi:
                continue
            r = rng.randint(r_lo, r_hi); c = rng.randint(c_lo, c_hi)
            draw_rect(g, r, c, rh, rw, 7); draw_rect(g, r - t, c, t, rw, 5)
        elif direction == "bottom":
            r_lo, r_hi = 1, h - rh - t
            c_lo, c_hi = 4, w - rw
            if r_lo > r_hi or c_lo > c_hi:
                continue
            r = rng.randint(r_lo, r_hi); c = rng.randint(c_lo, c_hi)
            draw_rect(g, r, c, rh, rw, 7); draw_rect(g, r + rh, c, t, rw, 5)
        elif direction == "left":
            r_lo, r_hi = 1, h - rh
            c_lo, c_hi = 4 + t, w - rw
            if r_lo > r_hi or c_lo > c_hi:
                continue
            r = rng.randint(r_lo, r_hi); c = rng.randint(c_lo, c_hi)
            draw_rect(g, r, c, rh, rw, 7); draw_rect(g, r, c - t, rh, t, 5)
        else:  # right
            r_lo, r_hi = 1, h - rh
            c_lo, c_hi = 4, w - rw - t
            if r_lo > r_hi or c_lo > c_hi:
                continue
            r = rng.randint(r_lo, r_hi); c = rng.randint(c_lo, c_hi)
            draw_rect(g, r, c, rh, rw, 7); draw_rect(g, r, c + rw, rh, t, 5)
        return g
    raise ValueError("could not realize gray/orange push layout")


def _components_of(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    problems = []
    orange = _components_of(grid, 7)
    gray = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5}
    if not gray:
        problems.append("no gray push strip")
    contacted = []
    isolated = []
    for cells in orange:
        sides = set()
        for r, c in cells:
            for name, dr, dc in (("top", -1, 0), ("bottom", 1, 0), ("left", 0, -1), ("right", 0, 1)):
                if (r + dr, c + dc) in gray:
                    sides.add(name)
        if sides:
            contacted.append(sides)
        else:
            isolated.append(cells)
    if not contacted:
        problems.append("no orange block contacts a gray strip")
    if not isolated:
        problems.append("no isolated orange block")
    for sides in contacted:
        if len(sides) != 1:
            problems.append(f"orange block touches gray on {len(sides)} sides")
    return sorted(set(problems))


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 14, 0)
    if name == "no_orange":
        draw_rect(g, 3, 5, 1, 4, 5)
        return g
    if name == "no_gray":
        draw_rect(g, 3, 5, 3, 4, 7)
        return g
    if name == "full_grid":
        for r in range(12):
            for c in range(14):
                g[r][c] = 7
        return g
    return g
