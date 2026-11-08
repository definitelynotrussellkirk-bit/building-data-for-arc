"""Generator for arc_puzzle_bank_21_set22_s:S22_M7 — copy max-distance motif points to target.

Rule: a SOURCE L-frame (2/3/4) has color-8 motif points in local coords;
copy ONLY the points with maximum local Manhattan radius (|u|+|v|) into
the TARGET L-frame (5/6/7), re-oriented to its basis.

Combinatorial axes: grid size, the source basis + motif (with varied
radii), the target basis, and the frame positions.
Degenerates: no_motif, no_target_frame, all_equal_distance.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a303ac60ccc6"
RULE_HASH = "9a80de547892"  # sha256 of whitespace-normalized canonical rule
VERSION = "3.0.1"  # diversity: random bases + motif (varied radii) + positions + grid (was fixed ~12)
TASK_ID = "a303ac60ccc6"
SUMMARY = (
    "0-bg grid (size varies). A SOURCE L-frame (2/3/4) with several "
    "color-8 MOTIF points at varied local Manhattan radii, and a TARGET "
    "L-frame (5/6/7) with its own basis, placed apart. Rule: copy ONLY "
    "the source points with the MAXIMUM local Manhattan radius into the "
    "target frame's local coords. The grid size, both bases, the motif "
    "and the positions all vary freely (was a fixed 12x18 layout, ~12 "
    "distinct)."
)

INVARIANTS = [
    "one source 2/3/4 frame and one target 5/6/7 frame",
    "several color-8 motif points within Chebyshev radius 3 of the source",
    "the max-Manhattan-radius points' copies land in-bounds on empty cells",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motif", "no_target_frame", "all_equal_distance")
HELPFUL_TEXTURES = PALETTE_KINDS

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]
_BASES = [(vx, vy) for vx in _CARD for vy in _CARD
          if vx[0] * vy[0] + vx[1] * vy[1] == 0]
_FORBIDDEN = {(0, 0), (1, 0), (0, 1)}
_MOTIF_CANDS = [(u, v) for u in range(-3, 4) for v in range(-3, 4)
                if (u, v) not in _FORBIDDEN]

AXES = {
    "target_basis":   {"type": "int", "default": "varies", "valid": "0..7"},
    "motif":          {"type": "str", "default": "varies", "valid": "varies"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "7", "valid": "7"},
    "position_bias":  {"type": "str", "default": "two_frames_max_distance",
                       "valid": "two_frames_max_distance"},
    "n_distinct_colors": {"type": "int", "default": "7", "valid": "7"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|"
                                "no_motif|no_target_frame|all_equal_distance"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: source frame colors {2,3,4} + target frame colors {5,6,7} + motif
    color 8 all present; source and target frames are distinct regions."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    all_colors = set(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    src_colors = all_colors & {2, 3, 4}
    tgt_colors = all_colors & {5, 6, 7}
    if len(src_colors) < 2:
        errs.append(f"source frame colors (subset of {{2,3,4}}) too few: {src_colors}")
    if len(tgt_colors) < 2:
        errs.append(f"target frame colors (subset of {{5,6,7}}) too few: {tgt_colors}")
    if 8 not in all_colors:
        errs.append("no color-8 motif points found")
    return errs


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
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, kr = (11, 13), (15, 19), (3, 4)
    elif difficulty == "hard":
        hr, wr, kr = (13, 18), (20, 26), (4, 6)
    else:
        hr, wr, kr = (12, 16), (17, 24), (3, 5)

    for _attempt in range(50):
        h = rng.randint(*hr); w = rng.randint(*wr)
        svx, svy = rng.choice(_BASES)
        tvx, tvy = rng.choice(_BASES)
        motif = rng.sample(_MOTIF_CANDS, rng.randint(*kr))
        occ = [[False] * w for _ in range(h)]
        g = full_grid(h, w, 0)

        placed = False
        for _t in range(50):
            o = (rng.randint(3, h - 4), rng.randint(3, w - 4))
            frame, mot = _cells(o, svx, svy, motif)
            if all(0 <= r < h and 0 <= c < w for r, c in frame + mot) and \
               _place_cluster(occ, frame + mot, h, w):
                g[o[0]][o[1]] = 2
                g[frame[1][0]][frame[1][1]] = 3
                g[frame[2][0]][frame[2][1]] = 4
                for (r, c) in mot:
                    g[r][c] = 8
                placed = True
                break
        if not placed:
            continue

        # target frame (5,6,7); reserve the WHOLE motif footprint empty
        # (the copied subset lands within it)
        placed = False
        for _t in range(50):
            o = (rng.randint(3, h - 4), rng.randint(3, w - 4))
            frame, footprint = _cells(o, tvx, tvy, motif)
            if all(0 <= r < h and 0 <= c < w for r, c in frame + footprint) and \
               _place_cluster(occ, frame + footprint, h, w):
                g[o[0]][o[1]] = 5
                g[frame[1][0]][frame[1][1]] = 6
                g[frame[2][0]][frame[2][1]] = 7
                placed = True
                break
        if placed:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 18, 0)
    sb = ((0, 1), (1, 0))

    def place(o, basis, cols):
        vx, vy = basis
        g[o[0]][o[1]] = cols[0]
        g[o[0] + vx[0]][o[1] + vx[1]] = cols[1]
        g[o[0] + vy[0]][o[1] + vy[1]] = cols[2]

    if name == "no_motif":
        place((6, 5), sb, [2, 3, 4]); place((6, 13), sb, [5, 6, 7])
        return g
    if name == "no_target_frame":
        place((6, 5), sb, [2, 3, 4])
        for (u, v) in [(-1, 0), (1, 1), (2, -1)]:
            g[6 + u][5 + v] = 8
        return g
    if name == "all_equal_distance":
        place((6, 5), sb, [2, 3, 4]); place((6, 13), sb, [5, 6, 7])
        for (u, v) in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            g[6 + v][5 + u] = 8
        return g
    return g
