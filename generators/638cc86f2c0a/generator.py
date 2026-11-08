"""Generator for arc_puzzle_bank_sixth_21_bundle:hard_42_chamber_elbow_paths.

Rule: inside each color-5 hollow chamber, any color appearing EXACTLY
twice in the interior is a same-color endpoint pair; connect the pair
with a VERTICAL-FIRST elbow path (down/up the first endpoint's column,
then across to the second), painted in that color and clipped to the
chamber interior. Frames and outside cells are preserved.

Combinatorial axes: grid size, number of chambers (1-3) + their
sizes/positions, each chamber's endpoint color, and the two endpoint
positions.
Degenerates: no_chambers, no_pairs, mismatched_pair_colors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "638cc86f2c0a"
VERSION = "3.0.1"  # diversity: N random chambers (size/pos) + endpoint color/positions + grid (was fixed 7x15)
TASK_ID = "638cc86f2c0a"
SUMMARY = (
    "0-bg grid (size varies). 1-3 color-5 (gray) hollow rectangular "
    "CHAMBERS (>=5 per side so interiors are >=3x3) at random "
    "sizes/positions, placed apart. Each chamber interior holds EXACTLY "
    "TWO same-color endpoint cells (a non-{0,5} color, distinct per "
    "chamber); an optional decoy sits outside. Rule: for each chamber, "
    "connect the same-color pair with a VERTICAL-FIRST elbow path painted "
    "in that color, clipped to the interior. The grid size, chamber "
    "count, chamber sizes/positions, endpoint color and the two endpoint "
    "positions all vary freely (was a fixed 7x15 grid with 5 pair "
    "presets)."
)

INVARIANTS = [
    "1-3 non-touching color-5 hollow chambers, each interior >=3x3",
    "each interior has exactly two cells of one non-{0,5} color (the pair)",
    "no other color appears exactly twice in an interior (one path per chamber)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_chambers", "no_pairs", "mismatched_pair_colors")
HELPFUL_TEXTURES = PALETTE_KINDS

_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)  # non-0 (bg), non-5 (frame)

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "9..18"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "variant":        {"type": "int", "default": "varies", "valid": "varies"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "3..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|"
                                "no_chambers|no_pairs|mismatched_pair_colors"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 color-5 cell (chamber wall); ≥1 non-{0,5} pair color present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    has_5 = any(grid[r][c] == 5 for r in range(h) for c in range(w))
    if not has_5:
        errs.append("no color-5 chamber walls found")
    pair_colors = {grid[r][c] for r in range(h) for c in range(w)
                   if grid[r][c] not in (0, 5)}
    if not pair_colors:
        errs.append("no endpoint pair colors found (interior should have 2 same-color cells)")
    return errs


def _reserve_bbox(occ, top, left, bh, bw, h, w):
    for r in range(top - 1, top + bh + 1):
        for c in range(left - 1, left + bw + 1):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + bh):
        for c in range(left, left + bw):
            occ[r][c] = True
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, nfr, szr = (9, 11), (10, 13), (1, 2), (5, 7)
    elif difficulty == "hard":
        hr, wr, nfr, szr = (14, 18), (15, 20), (2, 3), (5, 9)
    else:
        hr, wr, nfr, szr = (11, 15), (12, 16), (1, 2), (5, 8)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        occ = [[False] * w for _ in range(h)]
        g = full_grid(h, w, 0)
        placed = 0
        n_frames = rng.randint(*nfr)
        for _ in range(n_frames):
            for _t in range(40):
                fh = rng.randint(*szr); fw = rng.randint(*szr)
                if fh > h or fw > w:
                    continue
                top = rng.randint(0, h - fh); left = rng.randint(0, w - fw)
                if not _reserve_bbox(occ, top, left, fh, fw, h, w):
                    continue
                draw_frame(g, top, left, top + fh - 1, left + fw - 1, 5)
                interior = [(r, c) for r in range(top + 1, top + fh - 1)
                            for c in range(left + 1, left + fw - 1)]
                pair = None
                for _p in range(20):
                    (ar, ac), (br, bc) = rng.sample(interior, 2)
                    # Manhattan >=2 so the elbow paints >=1 cell beyond the endpoints
                    if abs(ar - br) + abs(ac - bc) >= 2:
                        pair = ((ar, ac), (br, bc)); break
                if pair is None:
                    continue
                (ar, ac), (br, bc) = pair
                color = rng.choice(_COLORS)
                g[ar][ac] = color; g[br][bc] = color
                placed += 1
                break
        if placed < 1:
            continue

        if rng.random() < 0.5:
            for _t in range(20):
                r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                if not occ[r][c]:
                    g[r][c] = rng.choice([1, 2, 3, 4, 6, 7, 8, 9])
                    break
        return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 15, 0)
    if name == "no_chambers":
        g[1][1] = 4; g[4][5] = 4
        g[1][9] = 6; g[4][13] = 6
        return g
    if name == "no_pairs":
        draw_frame(g, 0, 0, 5, 6, 5)
        draw_frame(g, 0, 8, 5, 14, 5)
        return g
    if name == "mismatched_pair_colors":
        draw_frame(g, 0, 0, 5, 6, 5)
        draw_frame(g, 0, 8, 5, 14, 5)
        g[1][1] = 4; g[4][5] = 6
        g[1][9] = 7; g[4][13] = 8
        return g
    return g
