"""Generator for arc_puzzle_bank_21_set2:S2_H3 — rotate an object by a corner code.

Rule (verified from canonical Racket): a single colour-8 cell sits at one of the
four CORNERS, which selects a rotation code (top-left=0, top-right=1,
bottom-right=2, else bottom-left=3). Take the largest colour-2 OBJECT, rotate its
cells by that many quarter-turns, and emit a blank grid with the colour-8 marker
back at its corner and the rotated object pasted at the object's original
top-left. Out-of-bounds rotated cells are dropped.

The previous body was the generic scatter template; with no colour-2 object the
rule's `(first (sort (objs-of 2) ...))` was first-of-empty -> crash (~8/10). This
rewrite CONSTRUCTS valid inputs: one colour-8 corner marker + one colour-2 object
in the interior.

Axes: grid size, which corner (rotation code), object shape/position.
Degenerates: tiny_object, corner_tl_identity, object_at_edge.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "85de4165ebbd"
VERSION = "2.1.0"  # identity fix: corner=0 (top-left) selects 0 quarter-turns -> the object is re-pasted unrotated -> output == input (the canonical task never shows this). Now draw corner in 1..3 AND reject objects that are invariant under the selected rotation, so the rotation is always visible.
TASK_ID = "85de4165ebbd"

SUMMARY = ("A single colour-8 corner marker selects a rotation code (TL=0/TR=1/BR=2/BL=3); "
           "the largest colour-2 object is rotated by that many quarter-turns and re-pasted "
           "at its original top-left, with the marker kept at its corner. Grid size, corner "
           "and object vary.")

INVARIANTS = [
    "exactly one colour-8 cell, located at a grid corner",
    "exactly one colour-2 object (the shape to rotate)",
    "the object lies in the interior, clear of the marked corner",
]

DEGENERATE_TEXTURES = ("tiny_object", "corner_tl_identity", "object_at_edge")
HELPFUL_TEXTURES = ("default", "warm", "cool", "varied")

AXES = {
    "grid_n":       {"type": "int", "default": "rng 8..11 (square)", "valid": "6..16"},
    "obj_size":     {"type": "int", "default": "rng 3..5", "valid": "2..7"},
    "corner":       {"type": "int", "default": "rng 0..3 (TL/TR/BR/BL)", "valid": "0..3"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                     "valid": "default|warm|cool|varied"},
    "density":      {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":      {"type": "str", "default": "alias for palette_kind",
                     "valid": "default|warm|cool|varied|tiny_object|corner_tl_identity|object_at_edge"},
}

_CORNERS = {0: ("tl",), 1: ("tr",), 2: ("br",), 3: ("bl",)}


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def _corner_cell(corner, n):
    return {0: (0, 0), 1: (0, n - 1), 2: (n - 1, n - 1), 3: (n - 1, 0)}[corner]


def _normalize(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return frozenset((r - mr, c - mc) for r, c in cells)


def _rot90(cells):                       # 90 deg CW
    return [(c, -r) for r, c in cells]


def _rot_invariant(cells, t):
    """True if the shape is unchanged after t quarter-turns (rotation hidden)."""
    base = _normalize(cells)
    cur = list(cells)
    for _ in range(t % 4):
        cur = _rot90(cur)
    return _normalize(cur) == base


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        n = ctx.draw_int("grid_n", 8, 9); osize = ctx.draw_int("obj_size", 3, 4)
    elif difficulty == "hard":
        n = ctx.draw_int("grid_n", 11, 13); osize = ctx.draw_int("obj_size", 4, 6)
    else:
        n = ctx.draw_int("grid_n", 9, 11); osize = ctx.draw_int("obj_size", 3, 5)
    # corner 1..3 -> 1/2/3 quarter-turns (never 0, which is an identity).
    corner = ctx.draw_int("corner", 1, 3)
    rng = ctx.draw_rng("layout")

    g = full_grid(n, n, 0)
    cr, cc = _corner_cell(corner, n)
    g[cr][cc] = 8

    # colour-2 object: build a motif that is NOT invariant under the selected
    # rotation (else the rotated copy equals the original -> identity), place it
    # in the interior, clear of the marked corner cell (and its halo). Keep it
    # away from edges so a rotated copy mostly stays in bounds (the rule clips
    # OOB cells anyway).
    cells = _build_motif(rng, osize)
    for _ in range(40):
        if not _rot_invariant(cells, corner):
            break
        cells = _build_motif(rng, osize)
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
    placed = False
    for _ in range(200):
        r0 = rng.randint(1, max(1, n - 1 - sh))
        c0 = rng.randint(1, max(1, n - 1 - sw))
        norm = [(r0 + r - min(rs), c0 + c - min(cs)) for r, c in cells]
        if any(abs(r - cr) <= 1 and abs(c - cc) <= 1 for r, c in norm):
            continue
        if all(0 <= r < n and 0 <= c < n for r, c in norm):
            for r, c in norm:
                g[r][c] = 2
            placed = True
            break
    if not placed:                       # guaranteed fallback: a small object centre-ish
        br, bc = n // 2, n // 2
        for r, c in [(br, bc), (br, bc + 1), (br + 1, bc)]:
            if (abs(r - cr) > 1 or abs(c - cc) > 1) and 0 <= r < n and 0 <= c < n:
                g[r][c] = 2
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """One colour-8 marker at a NON-top-left corner (rotation code 1/2/3) and a
    colour-2 object that is NOT invariant under that rotation, so the rule's
    rotation is always visible (output != input)."""
    n = len(grid)
    eights = [(r, c) for r in range(len(grid)) for c in range(len(grid[0]))
              if grid[r][c] == 8]
    if len(eights) != 1:
        return [f"expected exactly one colour-8 marker, got {len(eights)}"]
    corners = {(0, 0): 0, (0, len(grid[0]) - 1): 1,
               (len(grid) - 1, len(grid[0]) - 1): 2, (len(grid) - 1, 0): 3}
    if eights[0] not in corners:
        return ["colour-8 marker is not at a grid corner"]
    code = corners[eights[0]]
    if code == 0:
        return ["marker at top-left -> 0 quarter-turns -> identity output"]
    twos = [(r, c) for r in range(len(grid)) for c in range(len(grid[0]))
            if grid[r][c] == 2]
    if not twos:
        return ["no colour-2 object to rotate (rule crashes on empty)"]
    if _rot_invariant(twos, code):
        return [f"colour-2 object is invariant under {code} quarter-turns "
                "-> rotation hidden (identity)"]
    return []


def _draw_from_degenerate(name, rng):
    n = 9
    g = full_grid(n, n, 0)
    g[0][0] = 8  # corner code 0 (top-left) for all degenerates
    if name == "tiny_object":
        # single colour-2 cell -> rotation is identity, trivial
        g[4][4] = 2
        return g
    if name == "corner_tl_identity":
        # code 0 -> 0 quarter-turns -> output equals cleaned input
        for r, c in [(3, 3), (3, 4), (4, 3)]:
            g[r][c] = 2
        return g
    # object_at_edge -> rotation clips part of the object (lossy/degenerate)
    for r, c in [(0, 4), (1, 4), (1, 5), (2, 5)]:
        g[r][c] = 2
    return g
