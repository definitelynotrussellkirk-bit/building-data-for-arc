"""Generator for arc_puzzle_bank_21_set21_s:S21_H4 — odd room motif under dihedral equivalence.

Rule (verified from canonical Racket): walls are colours {1,7,9}; each connected
non-wall region is a ROOM. Within each room the non-zero cells form a MOTIF, reduced
to its 8-element dihedral variant set. Output is a 1xN strip (N = room count, reading
order) marking colour 8 at the rooms whose motif's dihedral set is shared by NO other
room (the odd ones out).

The previous body was the generic scatter template; it made no walled rooms with
per-room motifs, so the strip never varied (distinct_out=1). This rewrite CONSTRUCTS
a row of rooms separated by colour-1 walls, where N-1 rooms carry dihedral variants
of one common motif and exactly one room carries a different motif.

Axes: room count, common/odd motifs, odd position, per-room dihedral variant.
Degenerates: all_same_motif, single_room, two_odd.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e08e27759d9d"
RULE_HASH = "51de94bbe22e"  # canonical rule this generator was written against
VERSION = "2.2.0"  # output is a 1xN index strip (odd room marked) -> distinct ~ sum(N), capped by room count. Shrink room width (pw 5->4) and allow more rooms (3-6) to lift the index-output ceiling and add input variety (canvas-clamped to 30)."
TASK_ID = "e08e27759d9d"

SUMMARY = ("Rooms separated by colour-1 walls each hold a motif; the rule marks (1xN strip, "
           "colour 8) the rooms whose motif is dihedral-unique. N-1 rooms share a motif (up to "
           "dihedral); one is the odd one out. Room count, motifs and odd position vary.")

INVARIANTS = [
    "rooms are colour-1-walled non-wall regions, one motif each",
    "N-1 rooms carry dihedral variants of one common motif",
    "exactly one room carries a motif with a different cell count (the odd one)",
]

DEGENERATE_TEXTURES = ("all_same_motif", "single_room", "two_odd")
HELPFUL_TEXTURES = ("default", "warm", "cool", "varied")

AXES = {
    "grid_h":     {"type": "int", "default": "rng 6..8", "valid": "5..12"},
    "n_rooms":    {"type": "int", "default": "3 easy / 4-6 hard", "valid": "3..6"},
    "common_k":   {"type": "int", "default": "rng 3..5 common-motif cells", "valid": "2..6"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                     "valid": "default|warm|cool|varied"},
    "density":    {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":    {"type": "str", "default": "alias for palette_kind",
                   "valid": "default|warm|cool|varied|all_same_motif|single_room|two_odd"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]
_MOTIF_COLORS = (2, 3, 4, 5, 6, 8)   # never 1/7/9 (walls)


def _build_motif(rng, k, s=3):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nr, nc = r + dr, c + dc
        if 0 <= nr < s and 0 <= nc < s and (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return _norm(cells)


def _norm(cells):
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return sorted((r - rmin, c - cmin) for r, c in cells)


def _dihedral(cells, t):
    out = []
    for (r, c) in cells:
        if t == 0:   out.append((r, c))
        elif t == 1: out.append((c, -r))
        elif t == 2: out.append((-r, -c))
        elif t == 3: out.append((-c, r))
        elif t == 4: out.append((r, -c))
        elif t == 5: out.append((-c, -r))
        elif t == 6: out.append((-r, c))
        else:        out.append((c, r))
    return _norm(out)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7); n = ctx.draw_int("n_rooms", 3, 3)
        ck = ctx.draw_int("common_k", 3, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 10); n = ctx.draw_int("n_rooms", 4, 6)
        ck = ctx.draw_int("common_k", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 6, 9); n = ctx.draw_int("n_rooms", 3, 5)
        ck = ctx.draw_int("common_k", 3, 5)
    rng = ctx.draw_rng("layout")

    common = _build_motif(rng, ck)
    ok = ck
    while ok == ck:
        ok = rng.randint(2, 6)
    odd = _build_motif(rng, ok)
    odd_idx = rng.randint(0, n - 1)

    pw = 4                                          # room interior width (motifs <=3 wide)
    w = n * pw + (n - 1)                            # rooms + 1-wide colour-1 walls (<=29 for n<=6)
    g = full_grid(h, w, 0)
    cx = 0
    for i in range(n):
        motif = odd if i == odd_idx else _dihedral(common, rng.randint(0, 7))
        mh = max(r for r, _ in motif) + 1; mw = max(c for _, c in motif) + 1
        r0 = max(0, (h - mh) // 2); c0 = cx + max(0, (pw - mw) // 2)
        color = rng.choice(_MOTIF_COLORS)
        for (r, c) in motif:
            if r0 + r < h and c0 + c < cx + pw:
                g[r0 + r][c0 + c] = color
        cx += pw
        if i < n - 1:                               # full-height colour-1 wall
            for r in range(h):
                g[r][cx] = 1
            cx += 1
    return g


def _draw_from_degenerate(name, rng):
    h = 6
    common = [(0, 0), (0, 1), (1, 0)]
    odd = [(0, 0), (0, 1), (0, 2), (1, 1)]

    def build(motifs):
        pw = 5
        n = len(motifs)
        w = n * pw + (n - 1)
        g = full_grid(h, w, 0)
        cx = 0
        for i, m in enumerate(motifs):
            for (r, c) in m:
                g[1 + r][cx + 1 + c] = 4
            cx += pw
            if i < n - 1:
                for r in range(h):
                    g[r][cx] = 1
                cx += 1
        return g

    if name == "single_room":
        return build([common])
    if name == "all_same_motif":
        return build([common, common, common])      # none unique -> all-0 strip
    return build([common, odd, [(0, 0), (1, 0)]])    # two_odd -> two distinct singletons


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid is empty or ragged"]
    h, w = len(grid), len(grid[0])
    wall_cols = [c for c in range(w) if all(grid[r][c] == 1 for r in range(h))]
    rooms = []
    start = 0
    for c in wall_cols + [w]:
        if c > start:
            rooms.append((start, c))
        start = c + 1
    if not (3 <= len(rooms) <= 6):
        errs.append(f"expected 3-6 rooms, found {len(rooms)}")
    counts = []
    for a, b in rooms:
        cells = [(r, c) for r in range(h) for c in range(a, b) if grid[r][c] not in (0, 1, 7, 9)]
        if not cells:
            errs.append("a room has no motif cells")
        counts.append(len(cells))
    freqs = {k: counts.count(k) for k in set(counts)}
    if counts and not (len(freqs) == 2 and sorted(freqs.values()) == [1, len(rooms) - 1]):
        errs.append(f"motif cell counts do not encode exactly one odd room: {counts}")
    return errs
