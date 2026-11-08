"""Generator for arc_puzzle_bank_21_set22_s:S22_H7 — match candidate motif rotated 90deg.

Rule: a SOURCE frame (colors 2/3/4) carries a color-8 motif in its local
frame. Among the candidate frames (5/6/7), exactly ONE has the local
90-degree rotation of the source's motif. Output a 1xN strip marking
that matching candidate.

Combinatorial axes: grid size, the source motif, which candidate
matches, the per-frame basis orientations, and positions.
Degenerates: no_source, no_candidates, no_match.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e3bf7e173449"
VERSION = "2.2.0"  # adds executable input invariants for source/candidate frame counts and motif visibility.
TASK_ID = "e3bf7e173449"
SUMMARY = (
    "0-bg grid (size varies). A SOURCE L-frame (colors 2/3/4) with a "
    "color-8 MOTIF in its local frame, and 3-5 candidate L-frames "
    "(colors 5/6/7). Exactly ONE candidate's local motif equals the "
    "source motif ROTATED 90 degrees ((u,v)->(-v,u)); the rest are "
    "distractors with different signatures. Frame orientations vary "
    "freely (signatures are in local coords). Rule: output a 1xN strip "
    "with COLOR 8 at the matching candidate's index. The grid size, the "
    "source motif, the matching candidate, orientations and positions all "
    "vary freely (was a fixed 13x25 layout, ~9 distinct)."
)

INVARIANTS = [
    "one source 2/3/4 frame with a local color-8 motif",
    "3-5 candidate 5/6/7 frames; exactly one has the 90deg-rotated source motif",
    "the other candidates have signatures distinct from the rotated source motif",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_source", "no_candidates", "no_match")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "motif":          {"type": "int", "default": "varies", "valid": "varies"},
    "match":          {"type": "int", "default": "varies", "valid": "varies"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "7", "valid": "7"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors": {"type": "int", "default": "7", "valid": "7"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_source|no_candidates|no_match"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]
_BASES = [(vx, vy) for vx in _CARD for vy in _CARD
          if vx[0] * vy[0] + vx[1] * vy[1] == 0]
_FORBIDDEN = {(0, 0), (1, 0), (0, 1)}
_MOTIF_CANDS = [(u, v) for u in range(-3, 4) for v in range(-3, 4)
                if (u, v) not in _FORBIDDEN]


def _rot90(pts):
    return [(-v, u) for (u, v) in pts]


def _canon(pts):
    return tuple(sorted(pts))


def _place_cluster(occ, cells, h, w):
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


def _cells(origin, vx, vy, motif):
    o = origin
    frame = [o, (o[0] + vx[0], o[1] + vx[1]), (o[0] + vy[0], o[1] + vy[1])]
    mot = [(o[0] + u * vx[0] + v * vy[0], o[1] + u * vx[1] + v * vy[1])
           for (u, v) in motif]
    return frame, mot


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, ncr, kr = (12, 14), (18, 22), (3, 4), (2, 3)
    elif difficulty == "hard":
        hr, wr, ncr, kr = (14, 18), (24, 29), (5, 6), (3, 4)
    else:
        hr, wr, ncr, kr = (13, 16), (22, 28), (4, 5), (2, 4)

    for _attempt in range(40):
        source = rng.sample(_MOTIF_CANDS, rng.randint(*kr))
        match_motif = _rot90(source)
        # rotated motif must avoid the candidate frame cells
        if any(p in _FORBIDDEN for p in match_motif):
            continue
        match_sig = _canon(match_motif)

        h = rng.randint(*hr); w = rng.randint(*wr)
        n_cand = rng.randint(*ncr)
        match_pos = rng.randrange(n_cand)
        occ = [[False] * w for _ in range(h)]
        g = full_grid(h, w, 0)

        def _try(colors, motif):
            for _t in range(50):
                vx, vy = rng.choice(_BASES)
                o = (rng.randint(3, h - 4), rng.randint(3, w - 4))
                frame, mot = _cells(o, vx, vy, motif)
                allc = frame + mot
                if all(0 <= r < h and 0 <= c < w for r, c in allc) and _place_cluster(occ, allc, h, w):
                    g[frame[0][0]][frame[0][1]] = colors[0]
                    g[frame[1][0]][frame[1][1]] = colors[1]
                    g[frame[2][0]][frame[2][1]] = colors[2]
                    for (r, c) in mot:
                        g[r][c] = 8
                    return True
            return False

        if not _try((2, 3, 4), source):
            continue
        ok = True
        for i in range(n_cand):
            if i == match_pos:
                motif = match_motif
            else:
                motif = None
                for _s in range(30):
                    cand = rng.sample(_MOTIF_CANDS, rng.randint(*kr))
                    if _canon(cand) != match_sig and not any(p in _FORBIDDEN for p in cand):
                        motif = cand; break
                if motif is None:
                    ok = False; break
            if not _try((5, 6, 7), motif):
                ok = False; break
        if ok:
            return g

    return g   # fallback (rare)


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    vals = [v for row in grid for v in row]
    allowed = {0, 2, 3, 4, 5, 6, 7, 8}
    extra = sorted(set(vals) - allowed)
    if extra:
        errors.append(f"unexpected colors {extra}")
    counts = {v: vals.count(v) for v in allowed}
    if [counts[2], counts[3], counts[4]] != [1, 1, 1]:
        errors.append("expected exactly one source L-frame with colors 2,3,4")
    n_cand = counts[5]
    if not (3 <= n_cand <= 6) or counts[6] != n_cand or counts[7] != n_cand:
        errors.append(f"candidate frame colors 5/6/7 must occur equally 3..6 times, got "
                      f"{counts[5]}/{counts[6]}/{counts[7]}")
    # Source + every candidate carries a motif of at least two color-8 cells;
    # this catches rare fallback/partial layouts where the matching predicate is hidden.
    if n_cand and counts[8] < 2 * (n_cand + 1):
        errors.append("not enough color-8 motif cells for source plus all candidates")
    h, w = len(grid), len(grid[0])

    def pos(color):
        return [(r, c) for r in range(h) for c in range(w) if grid[r][c] == color]

    if counts[2] == counts[3] == counts[4] == 1:
        (r2, c2), (r3, c3), (r4, c4) = pos(2)[0], pos(3)[0], pos(4)[0]
        v3, v4 = (r3 - r2, c3 - c2), (r4 - r2, c4 - c2)
        if sorted((abs(v3[0]) + abs(v3[1]), abs(v4[0]) + abs(v4[1]))) != [1, 1] or \
                v3[0] * v4[0] + v3[1] * v4[1] != 0:
            errors.append("source colors 2/3/4 must form a one-step orthogonal L-frame")
    return errors


def _draw_from_degenerate(name, rng):
    g = full_grid(13, 25, 0)
    src = [(1, -1), (2, -1), (2, 0)]
    dist = [(1, 1), (2, 1), (2, 2)]
    cands = [(6, 4), (6, 12), (6, 20)]

    def frame(o, cols):
        g[o[0]][o[1]] = cols[0]; g[o[0]][o[1] + 1] = cols[1]; g[o[0] + 1][o[1]] = cols[2]

    def motif(o, pts):
        for u, v in pts:
            g[o[0] + v][o[1] + u] = 8

    if name == "no_source":
        for o in cands:
            frame(o, (5, 6, 7)); motif(o, dist)
        return g
    if name == "no_candidates":
        frame((2, 12), (2, 3, 4)); motif((2, 12), src)
        return g
    if name == "no_match":
        frame((2, 12), (2, 3, 4)); motif((2, 12), src)
        for o in cands:
            frame(o, (5, 6, 7)); motif(o, dist)
        return g
    return g
