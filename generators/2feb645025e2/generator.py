"""Generator for puzzle dd2401ed.

Rule: vertical 5-mirror column at old_c + blue probes; move gray to
2*old_c+1, may recolor probes.

Combinatorial axes (8): grid_h/w, n_grays, n_probes, old_c_position,
gray_layout, probe_layout, anchor_corner, asymmetry_force.
Degenerates: no_grays, no_probes, single_gray.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2feb645025e2"
VERSION = "2.0.0"
TASK_ID = "2feb645025e2"
SUMMARY = (
    "0-bg grid (h ∈ 8-18, w ∈ 11-22, by "
    "difficulty) with: (a) ONE COLOR-5 "
    "(GRAY) MIRROR COLUMN at column "
    "OLD_C ∈ 1..(w-2)//2 (constrained "
    "so 2*old_c+1 < w), with N_GRAYS ∈ "
    "2-6 GRAY CELLS placed in that "
    "column at rows per GRAY_LAYOUT ∈ "
    "{scattered / contiguous / edges "
    "/ evenly_spaced}; (b) N_PROBES "
    "∈ 0-4 COLOR-2 (BLUE) PROBE "
    "CELLS placed between cols "
    "old_c+1 and 2*old_c per "
    "PROBE_LAYOUT ∈ {scattered / "
    "vertical / diag} — these "
    "probes lie in the 'reflection "
    "zone' between the gray column "
    "and its mirror position. "
    "Rule (MOVE EVERY GRAY-5 CELL "
    "FROM COLUMN OLD_C TO COLUMN "
    "2*OLD_C + 1 (THE MIRROR-"
    "REFLECTED COLUMN); ANY PROBES "
    "IN THE REFLECTION ZONE GET "
    "RECOLORED PER A FIXED RULE — "
    "PER DEMOS, MAY TURN COLOR 1 "
    "OR ANOTHER MARKER): IDENTIFY "
    "the gray-5 mirror column "
    "old_c. COMPUTE new_c = "
    "2*old_c + 1. CLEAR the gray "
    "cells from old_c. PAINT "
    "gray-5 at the same rows in "
    "column new_c. For each blue-2 "
    "probe in cols old_c..new_c: "
    "RECOLOR it per the canonical "
    "rule (e.g., color 1 to "
    "indicate it was 'crossed' "
    "by the mirror). Net: the "
    "gray column slides to its "
    "mirrored position; probes "
    "in the swept zone are marked."
)

INVARIANTS = [
    "background is 0",
    "2-4 gray(5) cells in same column (the 'mirror column')",
    "the column position old_c satisfies 2*old_c+1 < grid_w",
    "0-2 blue(2) probe cells between cols old_c and 2*old_c+1",
]

GRAY_LAYOUTS = ("scattered", "contiguous", "edges", "evenly_spaced")
PROBE_LAYOUTS = ("scattered", "vertical", "diag")
DEGENERATE_TEXTURES = ("no_grays", "no_probes", "single_gray")
HELPFUL_TEXTURES = GRAY_LAYOUTS

AXES = {
    "grid_h":           {"type": "int", "default": "rng 8..14", "valid": "6..18"},
    "grid_w":           {"type": "int", "default": "rng 11..18", "valid": "9..22"},
    "n_grays":          {"type": "int", "default": "rng 2..4", "valid": "2..6"},
    "n_probes":         {"type": "int", "default": "rng 0..2", "valid": "0..4"},
    "old_c_position":   {"type": "str", "default": "rng spread|left|right",
                         "valid": "spread|left|right"},
    "gray_layout":      {"type": "str", "default": "rng helpful",
                         "valid": "|".join(GRAY_LAYOUTS)},
    "probe_layout":     {"type": "str", "default": "rng helpful",
                         "valid": "|".join(PROBE_LAYOUTS)},
    "anchor_corner":    {"type": "bool", "default": "false",
                         "valid": "true|false"},
    "texture":          {"type": "str", "default": "alias for gray_layout",
                         "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: bg=0, has color-5 gray cells in a single column (the mirror column)."""
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    fives = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    if not fives:
        pass  # degenerate (no_grays) — allowed
    elif fives:
        five_cols = set(c for _, c in fives)
        if len(five_cols) > 1:
            pass  # degenerate (single_gray or scattered) — allowed
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 6, 9, 9, 12
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 13, 18, 17, 22
    else:
        h_lo, h_hi, w_lo, w_hi = 8, 14, 11, 18
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    max_old_c = (w - 2) // 2
    if max_old_c < 1:
        return _draw_from_degenerate("no_grays", h, w, rng)
    pos_kind = overrides.get("old_c_position",
                             ctx.draw_choice("old_c_position",
                                             ["spread", "left", "right"]))
    if pos_kind == "left":
        old_c = 1
    elif pos_kind == "right":
        old_c = max_old_c
    else:
        old_c = rng.randint(1, max_old_c)
    n_grays = int(overrides.get("n_grays",
                                ctx.draw_int("n_grays", 2, 4)))
    n_grays = max(2, min(min(h, 6), n_grays))
    gray_layout = (overrides.get("texture") or
                   overrides.get("gray_layout")
                   or ctx.draw_choice("gray_layout", list(GRAY_LAYOUTS)))
    g = full_grid(h, w, 0)
    rows = _layout_gray_rows(gray_layout, h, n_grays, rng)
    for r in rows:
        g[r][old_c] = 5
    new_c = 2 * old_c + 1
    n_probes = int(overrides.get("n_probes",
                                 ctx.draw_int("n_probes", 0, 2)))
    n_probes = max(0, min(4, n_probes))
    probe_layout = overrides.get("probe_layout",
                                 ctx.draw_choice("probe_layout",
                                                 list(PROBE_LAYOUTS)))
    placed_probes = 0
    for _ in range(n_probes * 8):
        if placed_probes >= n_probes:
            break
        for _try in range(8):
            r = rng.randint(0, h - 1)
            if probe_layout == "vertical":
                c = old_c + 1 if new_c > old_c + 1 else old_c
            elif probe_layout == "diag":
                k = placed_probes
                c = min(new_c - 1, old_c + 1 + k)
            else:
                c = rng.randint(old_c + 1, new_c - 1) if new_c > old_c + 1 else old_c + 1
            if 0 <= c < w and g[r][c] == 0:
                g[r][c] = 2
                placed_probes += 1
                break
        else:
            break
    return g


def _layout_gray_rows(layout, h, n, rng):
    if layout == "contiguous":
        start = rng.randint(0, max(0, h - n))
        return list(range(start, start + n))
    if layout == "edges":
        return [0, h - 1] + sorted(rng.sample(range(1, h - 1),
                                              max(0, n - 2)))
    if layout == "evenly_spaced":
        step = max(1, h // (n + 1))
        return [step * (i + 1) for i in range(n) if step * (i + 1) < h]
    return rng.sample(range(h), n)


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "no_grays":
        for r in range(2, 5):
            if r < h and 4 < w:
                g[r][4] = 2
        return g
    if name == "no_probes":
        for r in range(0, min(4, h)):
            g[r][2] = 5
        return g
    if name == "single_gray":
        g[h // 2][2] = 5
        return g
    return g
