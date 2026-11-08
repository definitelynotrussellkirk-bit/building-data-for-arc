"""Generator for arc_puzzle_bank_fifteenth21:H100 — 3-panel cellwise A==B ? Q : B.

Rule (verified): the grid is THREE square nxn panels A | B | Q (n = grid height),
sliced positionally at i*(n+1) with single divider columns between them (so the
grid is n x (3n+2)). Output is nxn: for each cell, if A[r][c] == B[r][c] take
Q[r][c], else take B[r][c].

The previous body was the generic "6 panels find pair" template with width-4
panels and color-9 dividers -> the rule sliced 3 mis-aligned panels of width n
and produced garbage (wrong task entirely). This rewrite builds three proper
nxn panels with partial A/B overlap so both branches (==->Q, !=->B) fire.

Degenerates: no_dividers, empty_panels, single_panel.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e732c7d4e15d"
VERSION = "3.1.0"  # WRONG-TASK rewrite: was 6-panel motif-pair; rule is 3 square panels A|B|Q -> cellwise (A==B ? Q : B)
TASK_ID = "e732c7d4e15d"

SUMMARY = (
    "Three square n x n panels A | B | Q (n = height) separated by single "
    "divider columns (grid n x (3n+2)). Rule: output n x n where each cell is "
    "Q if A==B at that cell else B. Panels are filled so A and B partially "
    "overlap (both branches fire); panel size, colors and density vary."
)

INVARIANTS = [
    "background is 0; grid is n x (3n+2) -> three square n x n panels A|B|Q",
    "A and B partially match (some equal cells, some differing) so both branches fire",
    "divider columns sit at index n and 2n+1",
]

DEGENERATE_TEXTURES = ("a_equals_b", "a_disjoint_b", "empty_q")
HELPFUL_TEXTURES = ()

AXES = {
    "panel_n":  {"type": "int", "default": "rng 3..9 by diff", "valid": "3..9"},
    "density":  {"type": "float", "default": "rng 0.35..0.6", "valid": "0..1"},
    "texture":  {"type": "str", "default": "n/a",
                 "valid": "a_equals_b|a_disjoint_b|empty_q"},
}

_DIVIDER = 5
_PANEL_COLORS = [1, 2, 3, 4, 6, 7, 8, 9]


def _panel_color(rng):
    return _PANEL_COLORS[rng.randrange(len(_PANEL_COLORS))]


def _fill_panel(g, off, n, density, rng):
    for r in range(n):
        for c in range(n):
            if rng.random() < density:
                g[r][off + c] = _panel_color(rng)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], ctx.draw_rng("degenerate"))
    if difficulty == "easy":
        n = ctx.draw_int("panel_n", 3, 5)
    elif difficulty == "hard":
        n = ctx.draw_int("panel_n", 7, 9)
    else:
        n = ctx.draw_int("panel_n", 5, 7)
    rng = ctx.draw_rng("layout")
    density = ctx.draw_int("dpct", 35, 60) / 100.0
    w = 3 * n + 2
    g = full_grid(n, w, 0)
    for r in range(n):
        g[r][n] = _DIVIDER; g[r][2 * n + 1] = _DIVIDER
    offA, offB, offQ = 0, n + 1, 2 * n + 2
    _fill_panel(g, offA, n, density, rng)               # A
    # B = a partial copy of A (so many cells match -> Q) plus independent changes
    for r in range(n):
        for c in range(n):
            if rng.random() < 0.5:
                g[r][offB + c] = g[r][offA + c]          # match A here
            elif rng.random() < density:
                g[r][offB + c] = _panel_color(rng)       # differ from A
    _fill_panel(g, offQ, n, density, rng)               # Q

    # Force one visibly-taken Q branch and one visibly-taken B branch.  The
    # random fill almost always did this, but the invariant is pedagogical enough
    # to make it constructive rather than probabilistic.
    g[0][offA + 0] = 1; g[0][offB + 0] = 1; g[0][offQ + 0] = 2  # A==B, Q!=B
    g[0][offA + 1] = 1; g[0][offB + 1] = 3; g[0][offQ + 1] = 4  # A!=B, output B
    return g


def _draw_from_degenerate(name, rng):
    n = 5
    w = 3 * n + 2
    g = full_grid(n, w, 0)
    for r in range(n):
        g[r][n] = _DIVIDER; g[r][2 * n + 1] = _DIVIDER
    offA, offB, offQ = 0, n + 1, 2 * n + 2
    for r in range(n):
        for c in range(n):
            g[r][offQ + c] = rng.randint(0, 9) if name != "empty_q" else 0
    if name == "a_equals_b":            # A == B everywhere -> output is all Q
        for r in range(n):
            for c in range(n):
                v = rng.randint(0, 6)
                g[r][offA + c] = v; g[r][offB + c] = v
        return g
    if name == "a_disjoint_b":          # A and B differ everywhere -> output is B
        for r in range(n):
            for c in range(n):
                g[r][offA + c] = 1; g[r][offB + c] = 2
        return g
    # empty_q: A/B partial overlap, Q blank
    for r in range(n):
        for c in range(n):
            g[r][offA + c] = rng.randint(0, 3)
            g[r][offB + c] = g[r][offA + c] if rng.random() < 0.5 else rng.randint(0, 3)
    return g



def _panel(grid, off, n):
    return [[grid[r][off + c] for c in range(n)] for r in range(n)]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the three-panel A==B ? Q : B task."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    n = len(grid)
    errors = []
    if w != 3 * n + 2:
        errors.append("grid must be n x (3n+2) for A|B|Q panels")
        return errors
    for r in range(n):
        if grid[r][n] != _DIVIDER or grid[r][2 * n + 1] != _DIVIDER:
            errors.append("divider columns are not solid color 5")
            break
    offA, offB, offQ = 0, n + 1, 2 * n + 2
    matches = diffs = visible_q = 0
    divider_inside = False
    for r in range(n):
        for c in range(n):
            a, b, q = grid[r][offA + c], grid[r][offB + c], grid[r][offQ + c]
            if _DIVIDER in (a, b, q):
                divider_inside = True
            if a == b:
                matches += 1
                if q != b:
                    visible_q += 1
            else:
                diffs += 1
    if divider_inside:
        errors.append("panel cells should not use divider color 5")
    if matches < 1:
        errors.append("A and B need at least one equal cell")
    if diffs < 1:
        errors.append("A and B need at least one differing cell")
    if visible_q < 1:
        errors.append("need at least one matched cell where Q visibly changes output")
    return sorted(set(errors))
