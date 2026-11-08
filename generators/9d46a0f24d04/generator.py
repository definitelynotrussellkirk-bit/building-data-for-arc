"""Generator for 73c3b0d8 -- context-sensitive recolor (memorized radius-3 table).

Rule: apply a memorized 7x7 (49-cell) context table (apply-local-rewrite
radius 3, OOB filled with -1); each cell whose 7x7 neighborhood matches an
entry is recolored to that entry value (0 or 4), others keep their value.

Most table entries are border-specific (they contain -1 OOB markers); only
3 interior entries fire away from the edge. This generator stamps those 3
interior windows on a 0-background lattice. The local TRANSFORM variety is
bounded by the 3 interior contexts, but distinct INPUTS/OUTPUTS are large
because the stamp positions, counts and grid sizes vary.

Combinatorial axes: grid size, which/how-many windows are stamped, and
their positions.
Degenerates: empty, single_stamp, dense.

NOTE: this is a MEMORIZED lookup table dominated by edge contexts; the
interior firing variety is only 3, so the per-cell transform is bounded,
but whole-grid INPUTS/OUTPUTS remain diverse via placement.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9d46a0f24d04"
VERSION = "2.1.0"  # self_check + closer-to-canonical scale: smaller grids and 1-2 normal stamps keep object/area drift bounded while still firing the radius-3 table.
TASK_ID = "9d46a0f24d04"
SUMMARY = (
    "0-bg grid (size varies) with 0/2/4 cells. A memorized radius-3 (7x7) "
    "context table recolors each cell whose 49-cell neighborhood matches an "
    "entry to 0 or 4. This generator stamps the 3 interior table windows on a "
    "0-background lattice so recolors fire. Grid size, stamp choice and "
    "positions vary, but normal examples stay near canonical scale instead of "
    "expanding to large 20x20+ canvases. The table is "
    "memorized and edge-dominated, so the per-cell transform variety is 3; "
    "whole-grid inputs/outputs stay diverse via placement."
)

INVARIANTS = [
    "cells hold 0/2/4; recolors map matching 7x7 contexts to 0 or 4",
    "stamped 7x7 windows are disjoint so each center reads its own context",
    "normal examples contain at least one interior table-window match",
    "the output is the input with matching centers recolored per the table",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("empty", "single_stamp", "dense")
HELPFUL_TEXTURES = PALETTE_KINDS

# Interior (no-OOB) entries of the rule's radius-3 table: (new_value, 49-cell
# row-major signature, dr=-3..3 x dc=-3..3).
_STAMPS = [
    (4, (0,0,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,0,0,0,0,0,0,0,0,0,2,2,2,2,2,2,2,0,0,0,4,0,0,0)),
    (0, (0,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,0,0,0,0,0,0,0,0,0,0,2,2,2,2,2,2,2,0,0,4,0,0,0,0)),
    (4, (0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,0,0,0,0,0,0,0,0,0,0,2,2,2,2,2,2,2,0,0,4,0,0,0,0,0,0,0,0,0,0,0)),

]

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..20"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "8..20"},
    "n_stamps":       {"type": "int", "default": "varies", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "lattice", "valid": "lattice"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|empty|single_stamp|dense"},
}


def _slots(h, w):
    """centers of disjoint 7x7 windows on a stride-8 lattice (>=3 from border)."""
    out = []
    r = 3
    while r <= h - 4:
        c = 3
        while c <= w - 4:
            out.append((r, c)); c += 8
        r += 8
    return out


def _stamp(g, cr, cc, sig):
    for dr in range(-3, 4):
        for dc in range(-3, 4):
            g[cr + dr][cc + dc] = sig[(dr + 3) * 7 + (dc + 3)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"])

    if difficulty == "easy":
        hr, wr, nr = (8, 12), (8, 12), (1, 1)
    elif difficulty == "hard":
        hr, wr, nr = (14, 20), (14, 20), (2, 3)
    else:
        hr, wr, nr = (10, 15), (10, 15), (1, 2)

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

    raise ValueError("could not place interior radius-3 table stamps")


def _signature_at(grid, cr, cc):
    h, w = len(grid), len(grid[0])
    vals = []
    for dr in range(-3, 4):
        for dc in range(-3, 4):
            r, c = cr + dr, cc + dc
            vals.append(grid[r][c] if 0 <= r < h and 0 <= c < w else -1)
    return tuple(vals)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the interior lookup-table generator.

    The generator intentionally stamps only the three interior 7x7 contexts from
    the canonical radius-3 table.  This check catches regressions where a stamp
    is clipped/overlapped, a stray nonzero appears outside stamped windows, or
    normal generation stops demonstrating a firing context at all.
    """
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    errs = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    bad = sorted({v for row in grid for v in row if v not in (0, 2, 4)})
    if bad:
        errs.append(f"unexpected colors {bad}; expected only 0/2/4")
    h = len(grid)
    stamp_sigs = {sig for _, sig in _STAMPS}
    centers = []
    covered = set()
    for r in range(3, max(3, h - 3)):
        for c in range(3, max(3, w - 3)):
            sig = _signature_at(grid, r, c)
            if sig in stamp_sigs:
                centers.append((r, c))
                for dr in range(-3, 4):
                    for dc in range(-3, 4):
                        if sig[(dr + 3) * 7 + (dc + 3)] != 0:
                            covered.add((r + dr, c + dc))
    if not centers:
        errs.append("no intact interior 7x7 table window found")
    nonzero = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0}
    stray = nonzero - covered
    if stray:
        errs.append(f"{len(stray)} nonzero cell(s) are not explained by a stamped 7x7 context")
    return errs


def _draw_from_degenerate(name):
    h, w = 16, 16
    if name == "empty":
        return full_grid(h, w, 0)
    g = full_grid(h, w, 0)
    _stamp(g, 7, 7, _STAMPS[0][1])
    if name == "dense":
        _stamp(g, 7, 7, _STAMPS[2][1])
    return g
