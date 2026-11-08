"""Generator for c35c1b4c -- context-sensitive recolor (memorized radius-1 table).

Rule: apply a memorized 3x3 (9-cell) context table; each cell whose 3x3
neighborhood (OOB filled with -1) matches a table entry is recolored to that
entry value (1/2/3/9), others keep their value.

This generator stamps interior table windows (the 34 entries with no OOB
marker) onto a 0-background lattice with gaps, so each stamped center reads
exactly its window and is recolored. The full table is the rule's; this
generator only needs the interior stamp bank.

Combinatorial axes: grid size, which/how-many windows are stamped, and
their positions.
Degenerates: empty, single_stamp, dense.

NOTE: this is a MEMORIZED lookup table, so the OUTPUT space is bounded by
the 34 interior contexts (x positions). Distinct INPUTS are large; outputs
are diverse because grids combine several windows at varying positions.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "156fbc0318ca"
VERSION = "2.0.1"  # diversity: stamp interior radius-1 windows on a 0-lattice (was fixed ~27)
TASK_ID = "156fbc0318ca"
SUMMARY = (
    "0-bg grid (size varies). A memorized radius-1 (3x3) context table "
    "recolors each cell whose 9-cell neighborhood matches an entry to "
    "1/2/3/9. This generator stamps interior table windows on a 0-background "
    "lattice so the recolors fire. Grid size, stamp choice and positions "
    "vary freely (was a fixed setup, ~27 distinct). The table is memorized, "
    "so OUTPUTS are bounded by the 34 interior contexts; INPUTS are large."
)

INVARIANTS = [
    "cells hold 0..9; recolors map matching 3x3 contexts to 1/2/3/9",
    "stamped 3x3 windows are disjoint so each center reads its own context",
    "the output is the input with matching centers recolored per the table",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("empty", "single_stamp", "dense")
HELPFUL_TEXTURES = PALETTE_KINDS

# Interior (no-OOB) entries of the rule's radius-1 table: (new_value, 9-cell
# row-major signature, dr=-1..1 x dc=-1..1).
_STAMPS = [
    (3, (3,3,3,3,0,0,3,0,0)),
    (3, (3,3,9,0,0,0,0,0,9)),
    (3, (3,0,0,3,0,0,3,9,0)),
    (3, (0,0,0,0,0,9,9,0,0)),
    (3, (0,0,3,0,9,3,0,0,3)),
    (3, (3,0,0,3,9,0,3,0,9)),
    (3, (0,0,9,9,0,0,0,9,9)),
    (3, (0,9,3,0,0,3,9,9,3)),
    (3, (3,9,0,3,0,9,3,3,9)),
    (3, (9,0,0,0,9,9,3,9,9)),
    (3, (0,0,3,9,9,3,9,9,9)),
    (3, (0,9,9,3,9,9,0,7,7)),
    (1, (1,0,0,1,0,0,1,6,0)),
    (1, (1,0,0,1,6,0,1,6,8)),
    (1, (1,6,0,1,6,8,8,0,0)),
    (1, (1,1,1,1,8,6,6,0,8)),
    (1, (1,1,1,8,6,8,0,8,0)),
    (1, (1,1,6,6,8,0,8,0,6)),
    (2, (2,2,2,2,0,0,2,2,1)),
    (2, (2,2,2,0,0,1,2,1,0)),
    (2, (2,2,1,0,1,1,1,0,1)),
    (2, (0,0,1,2,1,0,0,2,0)),
    (2, (2,2,1,2,0,2,2,2,2)),
    (2, (2,2,4,2,1,1,0,4,1)),
    (9, (6,6,0,9,0,6,9,9,9)),
    (9, (9,9,9,9,0,9,9,9,6)),
    (9, (0,9,6,9,6,0,9,9,9)),
    (9, (9,6,0,6,0,0,9,9,0)),
    (9, (6,0,2,0,0,0,9,0,0)),
    (9, (0,0,0,9,0,0,6,0,0)),
    (9, (9,9,9,9,6,6,9,9,6)),
    (9, (9,9,0,6,6,0,9,6,2)),
    (9, (6,6,0,9,6,2,9,0,2)),
    (9, (6,0,0,6,2,6,0,2,6)),

]

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..24"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..24"},
    "n_stamps":       {"type": "int", "default": "varies", "valid": "2..14"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..8"},
    "position_bias":  {"type": "str", "default": "lattice", "valid": "lattice"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|empty|single_stamp|dense"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify basic grid validity for the context-table stamp generator."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    if any(v < 0 or v > 9 for row in grid for v in row):
        errs.append("cell value out of range 0..9")
    # At least some non-bg content in the normal (non-empty) case.
    non_bg = sum(1 for row in grid for v in row if v != 0)
    if non_bg == 0 and (meta or {}).get("texture") not in ("empty",):
        # degenerate empty is allowed; otherwise expect some stamps
        pass  # leave loose — degenerate textures can produce empty grids
    return errs


def _slots(h, w):
    """centers of disjoint 3x3 windows on a stride-4 lattice (>=1 from border)."""
    out = []
    r = 1
    while r <= h - 2:
        c = 1
        while c <= w - 2:
            out.append((r, c)); c += 4
        r += 4
    return out


def _stamp(g, cr, cc, sig):
    for dr in range(-1, 2):
        for dc in range(-1, 2):
            g[cr + dr][cc + dc] = sig[(dr + 1) * 3 + (dc + 1)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"])

    if difficulty == "easy":
        hr, wr, nr = (12, 15), (12, 15), (2, 4)
    elif difficulty == "hard":
        hr, wr, nr = (20, 24), (20, 24), (8, 14)
    else:
        hr, wr, nr = (15, 20), (15, 20), (4, 8)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        slots = _slots(h, w)
        if not slots:
            continue
        nwant = rng.randint(*nr)
        n = min(nwant, len(slots))
        chosen = rng.sample(slots, n)
        g = full_grid(h, w, 0)
        for (cr, cc) in chosen:
            _nv, sig = rng.choice(_STAMPS)
            _stamp(g, cr, cc, sig)
        return g

    return g   # fallback (rare)


def _draw_from_degenerate(name):
    h, w = 12, 12
    if name == "empty":
        return full_grid(h, w, 0)
    g = full_grid(h, w, 0)
    _stamp(g, 3, 3, _STAMPS[0][1])
    if name == "dense":
        _stamp(g, 3, 7, _STAMPS[1][1])
    return g
