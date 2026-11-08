"""Generator for arc_additional_puzzles_21_set3:M15.

Rule: find the first color-3 blob that has a cell cardinally adjacent to a
color-2 marker; output that blob cropped to its bbox, painted color 3.

v2.0.0 placed exactly 2 small 3-blobs, one marked -> output (the chosen blob
mask) was tiny and repetitive (uniq_out ~0.19). v3.0.0 uses bigger/varied
chosen blobs, 2-4 color-3 blobs (exactly one marker-adjacent), decoy non-3
objects (ignored by the rule), more markers, bigger grids, gated so exactly one
3-blob touches a marker.

Combinatorial axes: grid size, blob count + shapes, chosen blob, marker count,
decoy objects, colors.
Degenerates: no_blobs, no_markers, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "f9fed0e0bad4"
VERSION = "3.1.0"  # bigger/varied chosen blob + 2-4 blobs (one marked) + decoy non-3 objects + bigger grids (was 2 tiny blobs, uniq_out 0.19)
TASK_ID = "f9fed0e0bad4"
SUMMARY = (
    "0-bg grid (size varies) with 2-4 color-3 (green) BLOBS, EXACTLY ONE of "
    "which has a color-2 (red) MARKER cell cardinally adjacent to it (1-2 "
    "markers). The grid may also hold DECOY objects in other colors (ignored "
    "by the rule). Rule: find the first color-3 blob with a cell cardinally "
    "adjacent to a color-2 marker; OUTPUT just that blob cropped to its "
    "bounding box, painted color 3 (markers and all other blobs/decoys are "
    "dropped). Net: the marker selects which green blob to extract. (Was 2 tiny "
    "blobs with one marked.)"
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "2-4 isolated color-3 blobs",
    "exactly ONE color-3 blob is cardinally adjacent to a color-2 marker",
    "other blobs and decoy objects are NOT marker-adjacent",
    "decoy objects use colors other than 0, 2, 3",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_blobs", "no_markers", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {'grid_h': {'type': 'int', 'default': '9-12 easy / 11-15 med / 14-20 hard', 'valid': '8..22'},
 'grid_w': {'type': 'int', 'default': '11-14 easy / 13-18 med / 16-24 hard', 'valid': '10..26'},
 'palette_kind': {'type': 'str', 'default': 'rng helpful', 'valid': 'warm|cool|broad|primary'},
 'n_blobs': {'type': 'int', 'default': '2 easy / 2-3 med / 3-4 hard', 'valid': '2..4'},
 'n_decoys': {'type': 'int', 'default': '0-1 easy / 1-2 med / 2-3 hard', 'valid': '0..3'},
 'palette_size': {'type': 'int', 'default': '2 + decoys', 'valid': '2..8'},
 'position_bias': {'type': 'str',
                   'default': 'scattered_blobs_one_marked',
                   'valid': 'scattered_blobs_one_marked'},
 'n_distinct_colors': {'type': 'int', 'default': 'up to 8', 'valid': '2..8'},
 'texture': {'type': 'str',
             'default': 'alias for palette_kind',
             'valid': 'warm|cool|broad|primary|no_blobs|no_markers|full_grid'}}

_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]




def _components_of(grid, color):
    h, w = len(grid), len(grid[0]) if grid else 0
    seen: set[tuple[int, int]] = set()
    comps: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            comp: list[tuple[int, int]] = []
            while stack:
                cr, cc = stack.pop()
                comp.append((cr, cc))
                for dr, dc in _CARD:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(comp)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Exactly one color-3 component must be cardinally adjacent to marker color 2."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs: list[str] = []
    colors = {v for row in grid for v in row if v != 0}
    bad_decoys = sorted(colors - {1, 2, 3, 4, 5, 6, 7, 8, 9})
    if bad_decoys:
        errs.append(f"unexpected colors: {bad_decoys}")
    blobs = _components_of(grid, 3)
    markers = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2}
    if not (2 <= len(blobs) <= 4):
        errs.append(f"expected 2-4 color-3 blobs, got {len(blobs)}")
    if not (1 <= len(markers) <= 2):
        errs.append(f"expected 1-2 color-2 markers, got {len(markers)}")
    touched = []
    for i, blob in enumerate(blobs):
        if any((r + dr, c + dc) in markers for r, c in blob for dr, dc in _CARD):
            touched.append(i)
    if len(touched) != 1:
        errs.append(f"expected exactly one marker-adjacent color-3 blob, got {touched}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        hr, wr, br, dr_, kr = (9, 12), (11, 14), (2, 2), (0, 1), (3, 5)
    elif difficulty == "hard":
        hr, wr, br, dr_, kr = (14, 20), (16, 24), (3, 4), (2, 3), (4, 9)
    else:
        hr, wr, br, dr_, kr = (11, 15), (13, 18), (2, 3), (1, 2), (3, 7)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)

        def _free(r1, c1, r2, c2):
            if r1 < 1 or c1 < 1 or r2 >= h - 1 or c2 >= w - 1:
                return False
            for rr in range(r1 - 1, r2 + 2):
                for cc in range(c1 - 1, c2 + 2):
                    if g[rr][cc] != 0:
                        return False
            return True

        # place color-3 blobs
        n_blobs = rng.randint(*br)
        blobs = []
        for _ in range(n_blobs * 4):
            if len(blobs) >= n_blobs:
                break
            norm = _build_motif(rng, rng.randint(*kr))
            sh = max(r for r, _ in norm) + 1; sw = max(c for _, c in norm) + 1
            for _ in range(60):
                r0 = rng.randint(1, h - sh - 1); c0 = rng.randint(1, w - sw - 1)
                if not _free(r0, c0, r0 + sh - 1, c0 + sw - 1):
                    continue
                for dr, dc in norm:
                    g[r0 + dr][c0 + dc] = 3
                blobs.append({(r0 + dr, c0 + dc) for dr, dc in norm})
                break
        if len(blobs) < 2:
            continue

        # decoy non-3 objects (ignored by the rule)
        decoy_cols = [1, 4, 5, 6, 7, 8, 9]
        rng.shuffle(decoy_cols)
        n_dec = rng.randint(*dr_)
        for i in range(n_dec):
            norm = _build_motif(rng, rng.randint(2, 5))
            sh = max(r for r, _ in norm) + 1; sw = max(c for _, c in norm) + 1
            for _ in range(40):
                r0 = rng.randint(1, h - sh - 1); c0 = rng.randint(1, w - sw - 1)
                if not _free(r0, c0, r0 + sh - 1, c0 + sw - 1):
                    continue
                col = decoy_cols[i % len(decoy_cols)]
                for dr, dc in norm:
                    g[r0 + dr][c0 + dc] = col
                break

        # choose ONE blob; place 1-2 markers adjacent to it only (not adjacent
        # to any other blob).
        chosen = rng.randrange(len(blobs))
        others = set().union(*[blobs[i] for i in range(len(blobs)) if i != chosen])
        cand = []
        for (br_, bc_) in blobs[chosen]:
            for ddr, ddc in _CARD:
                nr, nc = br_ + ddr, bc_ + ddc
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] == 0:
                    # not adjacent to any other blob
                    if not any((nr + a, nc + b) in others for a, b in _CARD):
                        cand.append((nr, nc))
        cand = list(dict.fromkeys(cand))
        rng.shuffle(cand)
        n_mark = rng.randint(1, 2)
        placed = 0
        for (mr, mc) in cand:
            if placed >= n_mark:
                break
            if g[mr][mc] == 0:
                g[mr][mc] = 2
                placed += 1
        if placed == 0:
            continue

        # GATE: exactly one color-3 blob is marker-adjacent.
        markers = {(r, c) for r in range(h) for c in range(w) if g[r][c] == 2}
        touched = sum(1 for blob in blobs
                      if any((cr + a, cc + b) in markers
                             for (cr, cc) in blob for a, b in _CARD))
        if touched == 1:
            return g

    # deterministic fallback
    g = full_grid(10, 12, 0)
    paint_at(g, 2, 2, [(0, 0), (0, 1), (1, 0)], 3)
    paint_at(g, 6, 7, [(0, 0), (1, 0), (1, 1)], 3)
    g[2][4] = 2
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 12, 0)
    if name == "no_blobs":
        g[5][5] = 2
        return g
    if name == "no_markers":
        paint_at(g, 1, 1, [(0, 0), (0, 1), (1, 0)], 3)
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(12):
                g[r][c] = 3
        return g
    return g



def _color_components(grid, color):
    h, w = len(grid), len(grid[0]) if grid else 0
    seen = set()
    comps = []
    for sr in range(h):
        for sc in range(w):
            if (sr, sc) in seen or grid[sr][sc] != color:
                continue
            q = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            for r, c in q:
                cells.append((r, c))
                for dr, dc in _CARD:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            comps.append(set(cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    """Exactly one color-3 blob is selected by cardinal adjacency to color-2."""
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    blobs = _color_components(grid, 3)
    markers = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2}
    if not (2 <= len(blobs) <= 4):
        errs.append(f"expected 2-4 color-3 blobs, got {len(blobs)}")
    if not markers:
        errs.append("no color-2 marker cells")
    touched = []
    for i, blob in enumerate(blobs):
        if any((r + dr, c + dc) in markers for r, c in blob for dr, dc in _CARD):
            touched.append(i)
    if len(touched) != 1:
        errs.append(f"expected exactly one marker-adjacent color-3 blob, got {len(touched)}")
    return errs
