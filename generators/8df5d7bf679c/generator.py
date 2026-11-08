"""Generator for arc_puzzle_bank_21_set22_s:S22_M6.

Rule: find the SOURCE L-frame (color 2 origin, color 3 at one cardinal
basis vector vx, color 4 at a perpendicular cardinal vector vy). Extract
the color-8 MOTIF in the source frame's LOCAL coordinates (cells within
Chebyshev radius 3 of the origin). Then for EACH candidate frame (color
5 origin, 6 at vx, 7 at vy) whose oriented basis (vx,vy) EQUALS the
source's, paint the motif into that frame's local coordinates. Frames
with a different basis are left untouched.

Combinatorial axes: grid size, the source basis orientation (8 ordered
perpendicular cardinal pairs), the motif, and the frame positions /
the distractor frames' bases.
Degenerates: no_source, no_candidates, no_match.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8df5d7bf679c"
VERSION = "3.0.1"
TASK_ID = "8df5d7bf679c"
SUMMARY = (
    "0-bg grid (size varies). A SOURCE L-frame: color 2 at the origin, "
    "color 3 one cardinal step along basis vector vx, color 4 one "
    "perpendicular cardinal step along vy. A small color-8 (cyan) MOTIF "
    "sits within Chebyshev radius 3 of the origin. ONE MATCHING candidate "
    "frame (color 5/6/7) uses the SAME oriented basis (vx,vy); 1-2 "
    "DISTRACTOR candidate frames use a DIFFERENT ordered basis. Rule: "
    "read the source basis + motif (in local coords), and copy the motif "
    "into every candidate whose basis matches — here exactly the matching "
    "frame. Distractors stay untouched. The grid size, the basis "
    "orientation (8 options), the motif, and all frame positions vary "
    "freely (was a fixed 13x25 layout with only 3 origins x 3 motifs)."
)

INVARIANTS = [
    "exactly one color-2/3/4 source L-frame (perpendicular cardinal basis)",
    "color-8 motif cells all within Chebyshev radius 3 of the source origin",
    "exactly one color-5/6/7 candidate shares the source's ordered basis; "
    "1-2 distractors use a different basis; all frames non-touching",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_source", "no_candidates", "no_match")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "matching_slot":  {"type": "int", "default": "varies", "valid": "0..3"},
    "motif":          {"type": "str", "default": "varies", "valid": "varies"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "7", "valid": "6..8"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors": {"type": "int", "default": "7", "valid": "6..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|"
                                "no_source|no_candidates|no_match"},
}

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: source L-frame (colors 2,3,4) and candidate frame (5,6,7) both present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in ("no_source", "no_candidates", "no_match"):
        return errs
    flat = {grid[r][c] for r in range(h) for c in range(w)}
    for c in (2, 3, 4):
        if c not in flat:
            errs.append(f"source frame color {c} missing")
    for c in (5, 6, 7):
        if c not in flat:
            errs.append(f"candidate frame color {c} missing")
    return errs


_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]
# all ordered (vx, vy) pairs of perpendicular cardinal unit vectors
_BASES = [(vx, vy) for vx in _CARD for vy in _CARD
          if vx[0] * vy[0] + vx[1] * vy[1] == 0]


def _place_cluster(occ, cells, h, w):
    """Place `cells` if all in-bounds, free, and >=1 cell from other clusters."""
    cset = set(cells)
    for (r, c) in cells:
        if not (0 <= r < h and 0 <= c < w) or occ[r][c]:
            return False
    for (r, c) in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if (rr, cc) in cset:
                    continue
                if 0 <= rr < h and 0 <= cc < w and occ[rr][cc]:
                    return False
    for (r, c) in cells:
        occ[r][c] = True
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, rad, ndr, kr = (13, 15), (16, 20), 2, (1, 1), (2, 3)
    elif difficulty == "hard":
        hr, wr, rad, ndr, kr = (16, 20), (21, 28), 3, (2, 2), (3, 5)
    else:
        hr, wr, rad, ndr, kr = (14, 18), (18, 24), 3, (1, 2), (2, 4)

    forbidden = {(0, 0), (1, 0), (0, 1)}  # origin + the two basis cells (local)
    motif_cands = [(u, v) for u in range(-rad, rad + 1)
                   for v in range(-rad, rad + 1) if (u, v) not in forbidden]

    for _attempt in range(80):
        h = rng.randint(*hr); w = rng.randint(*wr)
        vx, vy = rng.choice(_BASES)
        others = [b for b in _BASES if b != (vx, vy)]
        n_d = rng.randint(*ndr)
        distract = rng.sample(others, min(n_d, len(others)))

        motif = rng.sample(motif_cands, rng.randint(*kr))
        # motif global deltas (same for source and any matching frame)
        D = [(u * vx[0] + v * vy[0], u * vx[1] + v * vy[1]) for (u, v) in motif]

        occ = [[False] * w for _ in range(h)]
        g = full_grid(h, w, 0)
        ok = True

        def _frame_cells(o, bx, by):
            return [o, (o[0] + bx[0], o[1] + bx[1]), (o[0] + by[0], o[1] + by[1])]

        # --- source cluster: frame (2,3,4) + motif (8) ---
        placed = False
        for _t in range(60):
            o = (rng.randint(3, h - 4), rng.randint(3, w - 4))
            fcells = _frame_cells(o, vx, vy)
            mcells = [(o[0] + d[0], o[1] + d[1]) for d in D]
            if _place_cluster(occ, fcells + mcells, h, w):
                g[o[0]][o[1]] = 2
                g[fcells[1][0]][fcells[1][1]] = 3
                g[fcells[2][0]][fcells[2][1]] = 4
                for (r, c) in mcells:
                    g[r][c] = 8
                placed = True
                break
        if not placed:
            continue

        # --- matching candidate: frame (5,6,7) only; reserve the motif footprint ---
        placed = False
        for _t in range(60):
            o = (rng.randint(3, h - 4), rng.randint(3, w - 4))
            fcells = _frame_cells(o, vx, vy)
            footprint = [(o[0] + d[0], o[1] + d[1]) for d in D]
            if _place_cluster(occ, fcells + footprint, h, w):
                g[o[0]][o[1]] = 5
                g[fcells[1][0]][fcells[1][1]] = 6
                g[fcells[2][0]][fcells[2][1]] = 7
                placed = True
                break
        if not placed:
            continue

        # --- distractor candidates: frame (5,6,7) with a different basis ---
        for (dbx, dby) in distract:
            for _t in range(60):
                o = (rng.randint(1, h - 2), rng.randint(1, w - 2))
                fcells = _frame_cells(o, dbx, dby)
                if _place_cluster(occ, fcells, h, w):
                    g[o[0]][o[1]] = 5
                    g[fcells[1][0]][fcells[1][1]] = 6
                    g[fcells[2][0]][fcells[2][1]] = 7
                    break
            else:
                ok = False
                break
        if ok:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(13, 25, 0)
    sbx, sby = (0, 1), (1, 0)

    def frame(o, bx, by, cols):
        g[o[0]][o[1]] = cols[0]
        g[o[0] + bx[0]][o[1] + bx[1]] = cols[1]
        g[o[0] + by[0]][o[1] + by[1]] = cols[2]

    if name == "no_source":
        # no 2/3/4 source frame — rule has no orientation reference
        frame((3, 12), sbx, sby, [5, 6, 7])
        frame((7, 18), (1, 0), (0, -1), [5, 6, 7])
        return g
    if name == "no_candidates":
        # source + motif present but no candidate frames
        frame((7, 4), sbx, sby, [2, 3, 4])
        for d in [(-1, 0), (1, 1), (2, -1)]:
            g[7 + d[0]][4 + d[1]] = 8
        return g
    if name == "no_match":
        # all candidates use a rotated basis — no orientation match
        frame((7, 4), sbx, sby, [2, 3, 4])
        for d in [(-1, 0), (1, 1), (2, -1)]:
            g[7 + d[0]][4 + d[1]] = 8
        frame((3, 12), (1, 0), (0, -1), [5, 6, 7])
        frame((9, 12), (0, -1), (-1, 0), [5, 6, 7])
        return g
    return g
