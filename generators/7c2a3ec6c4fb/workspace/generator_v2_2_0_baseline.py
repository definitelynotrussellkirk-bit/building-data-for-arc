"""Generator for puzzle cd3c21df.

Rule: among 8-connected multi-color blobs, output the one whose bbox-
cropped pattern is unique (count==1) among all blobs.

Combinatorial axes (8): grid_h/w, n_blobs, n_duplicates, blob_size,
blob_palette, position_bias, anchor_corner, asymmetry_force.
Degenerates: all_unique, all_identical, single_blob.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "7c2a3ec6c4fb"
VERSION = "2.2.0"  # FIX crash: n_blobs==4 left two unique blobs (n_dups was capped at 2) so the unique pattern appeared twice -> no count==1 blob -> rule returned #f and crashed (17/24). Now n_dups = n_blobs-1 (exactly one unique), unique placed first. + self_check.
TASK_ID = "7c2a3ec6c4fb"
SUMMARY = (
    "0-bg grid (h~9-12, w~12-16) with 3-4 "
    "MULTI-COLOR 8-CONNECTED BLOBS placed "
    "at non-touching positions (1-cell "
    "buffer for 8-conn separation). "
    "Blobs are split into TWO PATTERN "
    "CLASSES drawn from a 3-5 color "
    "palette: (a) the DUPLICATE PATTERN "
    "— a 3-cell horizontal line in one "
    "color — appears n_duplicates "
    "(2-3) times; (b) the UNIQUE "
    "PATTERN — a 3-cell L-shape with 2 "
    "distinct colors at specific cell "
    "positions — appears EXACTLY ONCE. "
    "The unique pattern's bbox is "
    "guaranteed to differ from the "
    "duplicate's bbox or color "
    "arrangement, so its normalized "
    "shape is unique. Rule (OUTPUT THE "
    "UNIQUE-PATTERN BLOB — THE ONE "
    "WHOSE BBOX-CROPPED PATTERN APPEARS "
    "EXACTLY ONCE AMONG ALL BLOBS): "
    "extract every 8-CONNECTED non-bg "
    "BLOB. CROP each to its bbox. "
    "COUNT how many times each "
    "normalized cropped pattern "
    "appears across all blobs. SELECT "
    "the blob whose pattern has "
    "count == 1 (unique). OUTPUT "
    "the unique blob's bbox crop with "
    "its colors preserved. Net: the "
    "odd-pattern-out blob's bbox "
    "crop is the output. Flagged "
    "borderline (uniq_out=36): bounded "
    "by patterns × positions."
)

INVARIANTS = [
    "background is 0",
    ">=3 8-connected multi-color blobs",
    "exactly one blob has a unique bbox pattern (rest have duplicates)",
    "blobs are 8-conn separated (no diagonal adjacency)",
]

POSITION_BIASES = ("spread", "corners", "row_aligned", "scattered")
DEGENERATE_TEXTURES = ("all_unique", "all_identical", "single_blob")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 12..16", "valid": "9..20"},
    "n_blobs":        {"type": "int", "default": "rng 3..4", "valid": "3..6"},
    "n_duplicates":   {"type": "int", "default": "2", "valid": "2..4"},
    "blob_size":      {"type": "int", "default": "rng 3..6", "valid": "2..8"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "spread|corners|row_aligned|scattered"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "2..7"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "spread|corners|row_aligned|scattered|all_unique|all_identical|single_blob"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 7, 9
    elif difficulty == "hard":
        h_lo, h_hi = 12, 16
    else:
        h_lo, h_hi = 9, 12
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo + 3, h_hi + 4)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_blobs = int(overrides.get("n_blobs",
                                ctx.draw_int("n_blobs", 3, 4)))
    # The rule selects the blob whose bbox crop is UNIQUE (count==1).
    # There must be EXACTLY ONE unique blob; every other blob shares one
    # duplicate pattern. (Previously n_blobs==4 left two "unique" blobs ->
    # the unique pattern appeared twice -> no count==1 blob -> the rule
    # returned #f and crashed. Force n_dups = n_blobs - 1.)
    n_dups = n_blobs - 1
    palette_size = int(overrides.get("palette_size",
                                     ctx.draw_int("palette_size", 3, 5)))
    palette_size = max(2, min(7, palette_size))
    pal = ctx.draw_distinct_colors("palette", n=palette_size,
                                   exclude={0})
    g = full_grid(h, w, 0)
    # Keep patterns small enough that >=2 duplicates + 1 unique fit even on
    # the tightest (easy) grids, so the duplicate genuinely appears twice.
    kmax = 4 if (h * w) < 110 else 6
    duplicate_pattern = _make_pattern("dup", pal, rng, kmax)
    unique_pattern = _make_pattern("unique", pal, rng, kmax)
    while _patterns_equal(unique_pattern, duplicate_pattern):
        unique_pattern = _make_pattern("unique", pal, rng, kmax)
    placed = []
    # Place the unique blob FIRST so it is guaranteed present even if some
    # later slots fail (the rule needs exactly one count==1 pattern).
    upos = _find_slot(g, h, w, unique_pattern, placed, rng)
    if upos is not None:
        paint_at(g, upos[0], upos[1], unique_pattern)
        placed.append((upos, unique_pattern))
    # Place duplicates
    dup_positions = []
    for _ in range(n_dups):
        pos = _find_slot(g, h, w, duplicate_pattern, placed, rng)
        if pos is None:
            break
        paint_at(g, pos[0], pos[1], duplicate_pattern)
        placed.append((pos, duplicate_pattern))
        dup_positions.append(pos)
    # Guard: the duplicate must appear 0 or >=2 times. If exactly one fit,
    # it is itself a unique pattern -> two count==1 blobs -> wrong/ambiguous
    # output. Erase that lone duplicate, leaving just the unique blob.
    if len(dup_positions) == 1:
        pr, pc = dup_positions[0]
        for (dr, dc, _col) in duplicate_pattern:
            g[pr + dr][pc + dc] = 0
    return g


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _make_pattern(kind, palette, rng, kmax=6):
    # random connected polyomino, each cell a random palette color
    k = rng.randint(3, max(3, kmax))
    poly = _rand_poly(rng, k)
    return [(r, c, rng.choice(palette)) for (r, c) in poly]


def _patterns_equal(a, b):
    return sorted(a) == sorted(b)


def _find_slot(g, h, w, pattern, placed, rng):
    pat_h = max(r for r, _, _ in pattern) + 1
    pat_w = max(c for _, c, _ in pattern) + 1
    for _ in range(40):
        rr = rng.randint(0, h - pat_h)
        rc = rng.randint(0, w - pat_w)
        # Check 1-cell buffer for 8-conn separation
        ok = True
        for dr in range(-1, pat_h + 1):
            for dc in range(-1, pat_w + 1):
                r2, c2 = rr + dr, rc + dc
                if 0 <= r2 < h and 0 <= c2 < w and g[r2][c2] != 0:
                    ok = False; break
            if not ok:
                break
        if ok:
            return (rr, rc)
    return None


def self_check(grid, *, difficulty=None, meta=None):
    """Exactly one 8-connected blob must have a bbox-crop count of 1.

    Mirrors the canonical rule: extract multicolor blobs, crop each to its
    bbox, and require exactly one pattern that appears exactly once.
    Returns a list of violation strings (empty == pass).
    """
    h = len(grid); w = len(grid[0])
    seen = [[False] * w for _ in range(h)]
    blobs = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or seen[r][c]:
                continue
            stack = [(r, c)]; seen[r][c] = True; cells = []
            while stack:
                cr, cc = stack.pop(); cells.append((cr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] \
                                and grid[nr][nc] != 0:
                            seen[nr][nc] = True; stack.append((nr, nc))
            blobs.append(cells)
    msgs = []
    if len(blobs) < 2:
        msgs.append(f"need >=2 blobs, got {len(blobs)}")
        return msgs
    crops = []
    for cells in blobs:
        rs = [p[0] for p in cells]; cs = [p[1] for p in cells]
        r1, c1, r2, c2 = min(rs), min(cs), max(rs), max(cs)
        crop = tuple(tuple(grid[rr][cc] for cc in range(c1, c2 + 1))
                     for rr in range(r1, r2 + 1))
        crops.append(crop)
    uniq = [p for p in crops if crops.count(p) == 1]
    if len(uniq) != 1:
        msgs.append(f"need exactly one unique blob, got {len(uniq)}")
    return msgs


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    pal = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], 4)
    if name == "all_unique":
        # 3 different patterns — rule has 3 candidate uniques (ambiguous)
        paint_at(g, 1, 1, [(0, 0, pal[0]), (0, 1, pal[1])])
        paint_at(g, 1, 6, [(0, 0, pal[2])])
        paint_at(g, h - 3, 3, [(0, 0, pal[3]), (1, 0, pal[3])])
        return g
    if name == "all_identical":
        # 3 same patterns — rule has no unique candidate
        for r0, c0 in [(1, 1), (1, 6), (h - 3, 3)]:
            paint_at(g, r0, c0, [(0, 0, pal[0]), (0, 1, pal[0])])
        return g
    if name == "single_blob":
        paint_at(g, 1, 1, [(0, 0, pal[0]), (0, 1, pal[1])])
        return g
    return g
