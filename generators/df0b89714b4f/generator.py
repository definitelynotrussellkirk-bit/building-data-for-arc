"""Generator for arc_puzzle_bank_fourteenth21:H94.

A color-9 anchor defines the rotation center. The surrounding colored shape is
stamped at all four quarter-turn rotations around that anchor.

Combinatorial axes (8): grid_size, palette_kind, motif, n_motif_cells,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_anchor, no_payload, anchor_at_corner.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "df0b89714b4f"
VERSION = "1.3.0"  # was FIXED 5-motif bank + 3 odd sizes (out_shapes 3). Now RANDOM connected motifs (3-6 cells within radius 3, anchor-excluded) + wider odd sizes 11-19 -> far more distinct payloads/outputs.
TASK_ID = "df0b89714b4f"
SUMMARY = "A 9-anchored colored shape is completed across four rotations."

INVARIANTS = [
    "there is exactly one color-9 anchor",
    "payload cells are nonzero and not 9",
    "all four rotations of every payload cell remain in bounds",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_anchor", "no_payload", "anchor_at_corner")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_size":      {"type": "int", "default": "rng 13..17 odd", "valid": "11..19"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "motif":          {"type": "int", "default": "rng 0..4", "valid": "0..4"},
    "n_motif_cells":  {"type": "int", "default": "rng 3..5", "valid": "3..6"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "position_bias":  {"type": "str", "default": "anchor_with_motif",
                       "valid": "anchor_with_motif"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_OFFSETS = [
    [(-2, 0), (-1, 0), (-1, 1)],
    [(-2, -1), (-1, -1), (-1, 0), (0, 0)],
    [(-3, 0), (-2, 0), (-1, 0), (-1, 1)],
    [(-2, 1), (-1, 0), (-1, 1), (0, 1)],
    [(-3, -1), (-2, -1), (-2, 0), (-1, 0), (-1, 1)],
]

_R = 3   # payload radius; margin = _R + 1 keeps all 4 rotations in bounds
_FALLBACK_MOTIF = [(-1, 0), (-2, 0), (-3, 0), (-3, 1), (-3, 2), (-2, 2)]


def _rotations(dr, dc):
    return [(dr, dc), (dc, -dr), (-dr, -dc), (-dc, dr)]


def _orbit(dr, dc):
    return tuple(sorted(set(_rotations(dr, dc))))


def _rand_motif(rng, n):
    """Random connected payload of n cells within [-_R,_R]^2.

    No two payload cells may be in the same quarter-turn orbit.  Otherwise
    two differently-colored input cells teach contradictory colors for the
    same rotated target cell.
    """
    starts = [(-1, 0), (1, 0), (0, -1), (0, 1),
              (-1, -1), (-1, 1), (1, -1), (1, 1)]
    for _ in range(120):
        start = rng.choice(starts)
        cells = [start]
        seen = {start}
        used_orbits = {_orbit(*start)}
        for _ in range(240):
            if len(cells) >= n:
                break
            r, c = rng.choice(cells)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            nr, nc = r + dr, c + dc
            orb = _orbit(nr, nc)
            if ((nr, nc) != (0, 0) and abs(nr) <= _R and abs(nc) <= _R
                    and (nr, nc) not in seen and orb not in used_orbits):
                cells.append((nr, nc))
                seen.add((nr, nc))
                used_orbits.add(orb)
        if len(cells) == n:
            return cells
    return _FALLBACK_MOTIF[:n]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    # RANDOM motifs (not a fixed 5-bank) + wider odd-size range for diversity.
    if difficulty == "easy":
        n_cells = ctx.draw_int("n_motif_cells", 3, 4)
        size = ctx.draw_int("grid_size", 11, 13)
    elif difficulty == "hard":
        n_cells = ctx.draw_int("n_motif_cells", 5, 6)
        size = ctx.draw_int("grid_size", 17, 19)
    else:
        n_cells = ctx.draw_int("n_motif_cells", 3, 6)
        size = ctx.draw_int("grid_size", 11, 19)
    if size % 2 == 0:
        size += 1
    motif = _rand_motif(rng, n_cells)
    g = full_grid(size, size, 0)
    margin = _R + 1
    ar = rng.randint(margin, size - margin - 1)
    ac = rng.randint(margin, size - margin - 1)
    g[ar][ac] = 9
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8], len(motif))
    for (dr, dc), color in zip(motif, colors):
        g[ar + dr][ac + dc] = color
    return g


def _draw_from_degenerate(name, rng):
    size = 13
    g = full_grid(size, size, 0)
    if name == "no_anchor":
        # payload cells without 9-anchor → no rotation pivot defined
        for (dr, dc), color in zip(_OFFSETS[0], [4, 6, 7]):
            g[6 + dr][6 + dc] = color
        return g
    if name == "no_payload":
        # anchor alone → nothing to rotate
        g[6][6] = 9
        return g
    if name == "anchor_at_corner":
        # anchor at corner (0,0) → rotations of payload land out of bounds
        g[0][0] = 9
        # tiny payload near corner
        g[1][1] = 4
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    anchors = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9]
    if len(anchors) != 1:
        return [f"anchor count {len(anchors)} != 1"]
    ar, ac = anchors[0]
    payload = [(r - ar, c - ac, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 9)]
    if difficulty == "easy":
        lo, hi = 3, 4
    elif difficulty == "hard":
        lo, hi = 5, 6
    else:
        lo, hi = 3, 6
    if not (lo <= len(payload) <= hi):
        msgs.append(f"payload count {len(payload)} outside {lo}..{hi}")
    orbit_colors = {}
    for dr, dc, color in payload:
        if color == 9:
            msgs.append("payload used anchor color 9")
        for rr, cc in _rotations(dr, dc):
            tr, tc = ar + rr, ac + cc
            if not (0 <= tr < h and 0 <= tc < w):
                msgs.append("rotated payload target out of bounds")
                break
        orb = _orbit(dr, dc)
        old = orbit_colors.setdefault(orb, color)
        if old != color:
            msgs.append("multiple colors in one rotational orbit")
            break
    return msgs
