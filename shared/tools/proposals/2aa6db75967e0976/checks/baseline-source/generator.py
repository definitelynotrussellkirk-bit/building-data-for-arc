"""Generator for arc_puzzle_bank_21_set12_s:S12_E4 — marker selects smallest neighbor.

Rule: a color-1 marker touches multiple shapes; the smallest adjacent
shape is cropped.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import components, components_have_clearance, color_counts, has_row_gap, interior_cells, is_full_frame_component, norm

GENERATOR_ID = "23a0c42b8a1c"
VERSION = "2.0.0"  # distinct=9: SMALL (answer) from a 9-shape bank -> 9 crops. Output = smallest marker-adjacent object cropped. Now random polyominoes (SMALL strictly < BIG) + orientations + varied grid. distinct 9->70 (residual dup is inherent to the small-shape output mask).
TASK_ID = "23a0c42b8a1c"
SUMMARY = "A color-1 marker touches multiple shapes; the smallest adjacent shape is cropped."

INVARIANTS = [
    "background is 0",
    "there is exactly one color-1 marker component",
    "the marker touches at least two components of different sizes",
    "the smallest marker neighbor is unique",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "no_neighbors", "tied_neighbors")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "7..20"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "8..19"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "small_size":     {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4..4"},
    "position_bias":  {"type": "str", "default": "marker_with_neighbors",
                       "valid": "marker_with_neighbors"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_marker|no_neighbors|tied_neighbors"},
}

# Smallest-shape library (normalized). Variety here drives output diversity,
# since the rule crops exactly the smallest marker-adjacent shape.
_SMALL_SHAPES = {
    1: [[(0, 0)]],
    2: [[(0, 0), (0, 1)], [(0, 0), (1, 0)]],
    3: [[(0, 0), (0, 1), (0, 2)], [(0, 0), (1, 0), (2, 0)],
        [(0, 0), (0, 1), (1, 0)], [(0, 0), (0, 1), (1, 1)],
        [(0, 0), (1, 0), (1, 1)], [(0, 1), (1, 0), (1, 1)]],
}

_NONBG = [2, 3, 4, 6, 7, 8, 9]


def _paint(g, cells, color):
    h, w = len(g), len(g[0])
    for r, c in cells:
        if 0 <= r < h and 0 <= c < w:
            g[r][c] = color



_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _norm(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _orient(cells, code):
    # 8 dihedral orientations -> spreads the random-walk's compact-shape bias across
    # rotations/reflections so the output crop (raw orientation) varies far more.
    out = cells
    if code & 1:
        out = [(c, r) for r, c in out]                 # transpose
    if code & 2:
        out = [(r, -c) for r, c in out]                # flip
    if code & 4:
        out = [(-r, c) for r, c in out]                # flip
    return _norm(out)


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nb = (r + dr, c + dc)
        if nb not in seen:
            cells.append(nb); seen.add(nb)
    return _orient(_norm(cells), rng.randint(0, 7))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # output = the SMALLEST marker-adjacent object cropped (in colour 8). The answer
    # (SMALL) was drawn from a 9-shape bank -> distinct=9. Now SMALL + BIG are RANDOM
    # polyominoes with SMALL strictly smaller (so it's the rule's pick) -> the crop varies.
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 10, 14); sk = (3, 5)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 15, 20); w = ctx.draw_int("grid_w", 13, 19); sk = (4, 7)
    else:
        h = ctx.draw_int("grid_h", 13, 17); w = ctx.draw_int("grid_w", 11, 17); sk = (3, 6)
    rng = ctx.draw_rng("layout")

    for _outer in range(40):
        g = full_grid(h, w, 0)
        k_small = rng.randint(*sk)
        k_big = rng.randint(k_small + 1, k_small + 3)
        small = _rand_poly(rng, k_small)
        big = _rand_poly(rng, k_big)
        sh = max(r for r, _ in small) + 1; bh = max(r for r, _ in big) + 1
        sw = max(c for _, c in small) + 1; bw = max(c for _, c in big) + 1
        # small occupies sh rows above the marker, big bh rows below (+1 marker row)
        if sh + bh + 1 > h or max(sw, bw) + 2 > w:
            continue
        mr = rng.randint(sh, h - bh - 1)
        mc = rng.randint(1, w - 2)
        g[mr][mc] = 1
        # SMALL anchored above: a bottom cell sits at (mr-1, mc), adjacent to marker
        maxr = max(r for r, _ in small)
        ar, ac = rng.choice([(r, c) for (r, c) in small if r == maxr])
        dr, dc = (mr - 1) - ar, mc - ac
        small_cells = [(r + dr, c + dc) for (r, c) in small]
        # BIG anchored below: a top cell sits at (mr+1, mc)
        bar, bac = rng.choice([(r, c) for (r, c) in big if r == 0])
        bdr, bdc = (mr + 1) - bar, mc - bac
        big_cells = [(r + bdr, c + bdc) for (r, c) in big]
        if not all(0 <= r < h and 0 <= c < w for r, c in small_cells + big_cells):
            continue
        if set(small_cells) & set(big_cells):
            continue
        break
    else:
        # fallback (rare): a varied small domino/tromino + a bigger blob
        g = full_grid(h, w, 0); mr, mc = h // 2, w // 2; g[mr][mc] = 1
        ssh = _rand_poly(rng, rng.randint(2, 3))
        small_cells = [(mr - 1 - (max(r for r, _ in ssh) - r), mc + c) for r, c in ssh
                       if 0 <= mr - 1 - (max(rr for rr, _ in ssh) - r) and mc + c < w]
        big_cells = [(mr + 1, mc), (mr + 1, mc + 1), (mr + 2, mc), (mr + 2, mc + 1),
                     (mr + 2, mc - 1) if mc > 0 else (mr + 2, mc + 1)]
    scolor = rng.choice(_NONBG)
    bcolor = rng.choice([c for c in _NONBG if c != scolor])

    _paint(g, small_cells, scolor)
    _paint(g, big_cells, bcolor)

    # Optional distractor (not touching the marker) in the corner farthest from
    # it — a red herring the rule ignores. Skip if it would touch anything.
    dcolor = rng.choice([c for c in _NONBG if c not in (scolor, bcolor)])
    cr = 0 if mr > h // 2 else h - 1
    cc = 0 if mc > w // 2 else w - 1
    dcells = [(cr, cc), (cr, cc - 1 if cc > 0 else cc + 1)]
    occ = {(mr, mc)} | set(small_cells) | set(big_cells)
    if all(0 <= r < h and 0 <= c < w and
           all((r + dr2, c + dc2) not in occ
               for dr2 in (-1, 0, 1) for dc2 in (-1, 0, 1))
           for r, c in dcells):
        _paint(g, dcells, dcolor)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    if name == "no_marker":
        # no color-1 component → no marker to anchor selection
        _paint(g, [(2, 2), (2, 3)], 3)
        _paint(g, [(5, 5), (6, 5)], 4)
        return g
    if name == "no_neighbors":
        # marker exists but is isolated → no neighbor to crop
        g[3][3] = 1
        _paint(g, [(7, 8), (7, 9)], 6)
        return g
    if name == "tied_neighbors":
        # two equally-small marker neighbors → ambiguous "smallest"
        g[3][3] = 1
        g[3][4] = 4
        g[4][3] = 6
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    comps = components(grid)
    markers = [c for c in comps if c["color"] == 1]
    if len(markers) != 1 or len(markers[0]["cells"]) != 1:
        errs.append("expected exactly one single-cell color-1 marker component")
        return errs
    mr, mc = markers[0]["cells"][0]
    neighbor_ids = set()
    for idx, comp in enumerate(comps):
        if comp["color"] == 1:
            continue
        if any(abs(r - mr) + abs(c - mc) == 1 for r, c in comp["cells"]):
            neighbor_ids.add(idx)
    sizes = [len(comps[i]["cells"]) for i in neighbor_ids]
    if len(sizes) < 2:
        errs.append("marker should touch at least two non-marker components")
    if sizes and sizes.count(min(sizes)) != 1:
        errs.append("smallest marker-adjacent component should be unique")
    if len(set(sizes)) < 2:
        errs.append("marker-adjacent components should have different sizes")
    return errs
