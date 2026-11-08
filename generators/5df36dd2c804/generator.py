"""Generator for 4e469f39.

Rule: gray containers with one top-row gap; rule fills interior red and
shoots a red ray above each toward the longer arm.

Combinatorial axes (8): grid_h/w, n_containers, container_h, container_w,
gap_position, position_bias, anchor_corner, asymmetry_force.
Degenerates: no_gap, no_container, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5df36dd2c804"
VERSION = "2.1.0"
TASK_ID = "5df36dd2c804"
SUMMARY = (
    "0-bg grid (h, w ~14-22) with 1-2 GRAY (color-5) "
    "rectangular CONTAINERS, each ≥3 rows × ≥4 cols, with "
    "ONE GAP in the top row (gap column varies — left, "
    "center, or right lean). Containers have ≥2 rows of "
    "bg margin above. Rule: detect each gray container. "
    "FILL its INTERIOR (cells inside the container border, "
    "excluding the border itself) with color 2 (red). "
    "Then SHOOT a vertical color-2 ray UPWARD from the "
    "GAP cell to the top of the grid (or until obstacle). "
    "Net: each container gets red-filled and emits a "
    "rising red ray through its gap."
)

INVARIANTS = [
    "background is 0",
    ">=1 gray rectangular outlines, each with one gap in top row",
    "containers separated by bg margin >= 2",
    "each container has at least 1 row of bg above it",
]

POSITION_BIASES = ("scattered", "row_aligned", "stacked", "centered")
GAP_POSITIONS = ("center", "left_lean", "right_lean", "rng")
DEGENERATE_TEXTURES = ("no_gap", "no_container", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 14..18", "valid": "12..22"},
    "grid_w":         {"type": "int", "default": "rng 14..18", "valid": "12..22"},
    "n_containers":   {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "container_h":    {"type": "int", "default": "rng 3..5", "valid": "3..6"},
    "container_w":    {"type": "int", "default": "rng 4..7", "valid": "4..8"},
    "gap_position":   {"type": "str", "default": "rng",
                       "valid": "|".join(GAP_POSITIONS)},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _draw_container_with_gap(g, rr, rc, ch, cw, gap_dc):
    for c in range(cw):
        if c != gap_dc:
            g[rr][rc + c] = 5
        g[rr + ch - 1][rc + c] = 5
    for r in range(ch):
        g[rr + r][rc] = 5
        g[rr + r][rc + cw - 1] = 5


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 12, 14
        nc_lo, nc_hi = 1, 1
        ch_lo, ch_hi, cw_lo, cw_hi = 3, 4, 4, 5
    elif difficulty == "hard":
        h_lo, h_hi = 18, 22
        nc_lo, nc_hi = 2, 3
        ch_lo, ch_hi, cw_lo, cw_hi = 4, 6, 5, 8
    else:
        h_lo, h_hi = 14, 18
        nc_lo, nc_hi = 1, 2
        ch_lo, ch_hi, cw_lo, cw_hi = 3, 5, 4, 7
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    g = full_grid(h, w, 0)
    n_containers = int(overrides.get("n_containers",
                                     ctx.draw_int("n_containers",
                                                  nc_lo, nc_hi)))
    n_containers = max(1, min(3, n_containers))
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias", list(POSITION_BIASES)))
    gap_pos = overrides.get("gap_position",
                            ctx.draw_choice("gap_position",
                                            list(GAP_POSITIONS)))
    placed = []
    for _try in range(60):
        if len(placed) >= n_containers:
            break
        ch = rng.randint(ch_lo, ch_hi)
        cw = rng.randint(cw_lo, cw_hi)
        rr, rc = _pick_pos(bias, h, w, ch, cw, len(placed), placed, rng)
        if gap_pos == "center":
            gap_dc = cw // 2
        elif gap_pos == "left_lean":
            gap_dc = rng.randint(1, max(1, cw // 2))
        elif gap_pos == "right_lean":
            gap_dc = rng.randint(max(1, cw // 2), cw - 2)
        else:
            gap_dc = rng.randint(1, cw - 2)
        ok = True
        for r in range(max(0, rr - 2), min(h, rr + ch + 1)):
            for c in range(max(0, rc - 1), min(w, rc + cw + 1)):
                if g[r][c] != 0:
                    ok = False
                    break
            if not ok:
                break
        if not ok:
            continue
        _draw_container_with_gap(g, rr, rc, ch, cw, gap_dc)
        placed.append((rr, rc, ch, cw, gap_dc))
    if not placed:
        return _draw_from_degenerate("no_container", rng)
    return g


def _pick_pos(bias, h, w, ch, cw, idx, placed, rng):
    if bias == "stacked":
        rr = 2 + idx * (ch + 2)
        rc = rng.randint(1, max(1, w - cw - 1))
    elif bias == "row_aligned":
        rr = max(2, h // 3)
        rc = 1 + idx * (cw + 2)
    elif bias == "centered":
        rr = max(2, (h - ch) // 2 + rng.randint(-1, 1))
        rc = max(1, (w - cw) // 2 + rng.randint(-1, 1))
    else:
        rr = rng.randint(2, max(2, h - ch - 1))
        rc = rng.randint(1, max(1, w - cw - 1))
    rr = max(2, min(rr, h - ch - 1))
    rc = max(1, min(rc, w - cw - 1))
    return rr, rc


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, color-5 gray container cells present, >=1 row of bg above them."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    fives = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    if not fives:
        errs.append("no color-5 container cells found")
    # Row 0 should be all bg (containers have >=1 row above)
    if fives:
        min_r = min(r for r, c in fives)
        if min_r == 0:
            errs.append("gray container starts at row 0 (no bg row above)")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 14, 14
    g = full_grid(h, w, 0)
    if name == "no_gap":
        for c in range(4):
            g[3][3 + c] = 5
            g[6][3 + c] = 5
        for r in range(4):
            g[3 + r][3] = 5
            g[3 + r][6] = 5
        return g
    if name == "no_container":
        g[5][5] = 5
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 5
        return g
    return g
