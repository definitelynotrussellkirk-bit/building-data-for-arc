"""Generator for arc_puzzle_bank_sixth_21_bundle:hard_38 (task 03000b260ae0).

THE RULE (what a solver must learn to see):
  The multi-cell component containing a 9 is the TEMPLATE (its last
  9-cell in scan order is the anchor). Every singleton 9 is a marker.
  For each output cell, count how many marker-shifted template copies
  cover it: 1 -> red(2), 2 -> green(3), >=3 -> yellow(4), else 0.
  Output is a fresh canvas — the template itself vanishes.

WHAT MAKES AN INPUT TEACH THIS RULE (helpful textures):
  - OVERLAP CONTROL (overlap axis): disjoint copies give an all-red
    map; 'double' boards force a green region (two copies overlap);
    'triple' boards force a yellow region (three copies share cells).
    The old generator never controlled overlap, so greens/yellows —
    the actual point of a count-map — appeared only by luck
  - template position varies across the whole grid (was glued to the
    top-left corner), random grown shapes of 4-6 cells (was 4 fixed
    tetrominoes), body color varies and may be MULTICOLOR (the count
    map ignores colors entirely)

WHAT HIDES IT (degenerate textures, reachable via texture=...):
  - no_markers  template only: output is blank
  (a board with no multi-cell 9-component CRASHES the rule and is
  never generated)
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "03000b260ae0"
VERSION = "2.1.0"  # raise outer cap 80→400 (overlap=triple stacking is hard to satisfy on the smaller grid)
TASK_ID = "03000b260ae0"

SUMMARY = (
    "A 4-6 cell template (random body colors, one 9 anchor) plus 2-4 "
    "singleton 9 markers; rule paints the overlap count-map of "
    "marker-shifted template copies (1=red, 2=green, 3+=yellow) on a "
    "blank canvas. Overlap is generation-controlled so green and "
    "yellow regions actually occur."
)

# Rivals: 'stamp copies in the template color' refuted (map colors are
# 2/3/4 by COUNT). 'template survives' refuted (fresh canvas).
# 'overlaps merge to one color' refuted by green/yellow regions.
# 'body color matters' refuted by multicolor templates. 4 demos:
# >=1 disjoint, >=1 double, >=1 triple board.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "one connected multi-cell component contains exactly one 9 (anchor)",
    "all other 9 cells are isolated singletons (markers)",
    "overlap=double boards: some cell is covered by exactly 2 copies",
    "overlap=triple boards: some cell is covered by >=3 copies",
]

DEGENERATE_TEXTURES = ("no_markers",)
HELPFUL_TEXTURES = ("disjoint", "double", "triple", "multicolor")

AXES = {
    "grid_h":    {"type": "int", "default": "rng 10..12", "valid": "8..14"},
    "grid_w":    {"type": "int", "default": "rng 12..15", "valid": "10..17"},
    "n_markers": {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "overlap":   {"type": "enum", "default": "rng disjoint|double|triple",
                  "valid": "disjoint|double|triple",
                  "doc": "Max copy-overlap multiplicity (the map's palette)."},
    "texture":   {"type": "str", "default": "rng helpful",
                  "valid": "disjoint|double|triple|multicolor|no_markers",
                  "doc": "Overlap flavor, multicolor body, or a degenerate."},
}

_BODY_COLORS = (1, 2, 3, 4, 5, 6, 7, 8)


def _grow_template(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc))
            seen.add((r + dr, c + dc))
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("disjoint", "double", "double", "triple", "multicolor"))
    overlap = texture if texture in ("disjoint", "double", "triple") else \
        overrides.get("overlap", "double")

    h = ctx.draw_int("grid_h", 10, 12)
    w = ctx.draw_int("grid_w", 12, 15)
    n_markers = ctx.draw_int("n_markers", 2, 4)
    rng = ctx.draw_rng("layout")

    # The overlap=triple texture forces markers 1 and 2 to land so their template-
    # copy footprints stack (hits == k) on a shared cell — a strict constraint that
    # on the smaller grid (10×12) with a 6-cell template occasionally can't be met
    # in 80 template+marker redraws (~3/120 None). Raised the cap to 400: each
    # attempt redraws the template + marker positions, so more attempts simply give
    # the stacking constraint more chances; seeds that realized within 80 return at
    # the same attempt with the same draws (byte-identical). Retry-exhaustion class.
    for _attempt in range(400):
        g = full_grid(h, w, 0)
        occ = _grow_template(rng, rng.randint(4, 6))
        th = max(r for r, _ in occ) + 1
        tw = max(c for _, c in occ) + 1
        if th > h - 2 or tw > w - 2:
            continue
        # template anywhere on the board (was glued to the top-left)
        top = rng.randint(0, h - th)
        left = rng.randint(0, w - tw)
        anchor = occ[rng.randrange(len(occ))]
        if texture == "multicolor":
            colors = rng.sample(_BODY_COLORS, 2)
        else:
            colors = [rng.choice(_BODY_COLORS)]
        taken = set()
        for i, (dr, dc) in enumerate(occ):
            r, c = top + dr, left + dc
            g[r][c] = 9 if (dr, dc) == anchor else colors[i % len(colors)]
            taken.add((r, c))

        # markers: copy footprint = occ shifted so the anchor cell lands
        # at the marker
        ar, ac = anchor
        footprints = []
        markers = []

        def fp(mr, mc):
            return {(mr + r - ar, mc + c - ac) for r, c in occ}

        def overlap_count(cells):
            return max((sum(1 for f in footprints if p in f) for p in cells),
                       default=0)

        ok = True
        for k in range(n_markers):
            placed = False
            for _try in range(120):
                mr, mc = rng.randrange(h), rng.randrange(w)
                if g[mr][mc] != 0 or any(abs(mr - tr) <= 1 and abs(mc - tc) <= 1
                                          for tr, tc in taken):
                    continue
                cells = fp(mr, mc)
                # copies must stay clear of the template's own cells so
                # the input components stay clean
                if cells & taken:
                    continue
                hits = max((sum(1 for f in footprints if p in f) for p in cells),
                           default=0)
                if overlap == "disjoint" and hits > 0:
                    continue
                if overlap == "double" and k == 1 and hits != 1:
                    continue  # second copy must overlap the first once
                if overlap == "triple" and 1 <= k <= 2 and hits != k:
                    continue  # stack three copies on a shared cell
                footprints.append(cells)
                markers.append((mr, mc))
                taken.add((mr, mc))
                placed = True
                break
            if not placed:
                ok = False
                break
        if not ok or len(markers) < 2:
            continue
        for mr, mc in markers:
            g[mr][mc] = 9
        return g
    raise ValueError("could not realize count-map board")


def _draw_from_degenerate(name, ctx):
    """no_markers — template only: every count is 0, output blank."""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 10, 12)
    w = ctx.draw_int("grid_w", 12, 15)
    g = full_grid(h, w, 0)
    occ = _grow_template(rng, rng.randint(4, 6))
    th = max(r for r, _ in occ) + 1
    tw = max(c for _, c in occ) + 1
    top = rng.randint(0, max(0, h - th))
    left = rng.randint(0, max(0, w - tw))
    anchor = occ[rng.randrange(len(occ))]
    color = rng.choice(_BODY_COLORS)
    for dr, dc in occ:
        if top + dr < h and left + dc < w:
            g[top + dr][left + dc] = 9 if (dr, dc) == anchor else color
    return g

def _self_nonzero_components_4(g):
    h, w = len(g), len(g[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or g[r][c] == 0:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                x, y = stack.pop(); cells.append((x, y))
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < h and 0 <= ny < w and (nx, ny) not in seen and g[nx][ny] != 0:
                        seen.add((nx, ny)); stack.append((nx, ny))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    comps = _self_nonzero_components_4(grid)
    template = [cells for cells in comps if len(cells) > 1 and sum(grid[r][c] == 9 for r, c in cells) == 1]
    markers = [cells for cells in comps if len(cells) == 1 and grid[cells[0][0]][cells[0][1]] == 9]
    errs = []
    if len(template) != 1:
        errs.append(f"expected one connected template component with one 9 anchor, found {len(template)}")
    if not (2 <= len(markers) <= 4):
        errs.append(f"expected 2-4 singleton 9 markers, found {len(markers)}")
    for cells in comps:
        if cells not in template and cells not in markers:
            errs.append(f"unexpected non-template/non-marker component of size {len(cells)}")
            break
    return errs
