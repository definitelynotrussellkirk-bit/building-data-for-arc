"""Generator for arc_puzzle_bank_21_next:hard_c01 — stamp rotated template copies at markers.

Rule (verified from canonical Racket): isolated cells whose value is in {1,2,3,4}
are MARKERS (a value with no cardinal same-value neighbour). Remove them, crop the
remaining content to a TEMPLATE. For each marker, stamp a rotated copy of the
template (1=identity, 2=cw, 3=180, 4=ccw) with its top-left at the marker, onto a
blank grid.

The previous body was the generic scatter template; it built neither a clean
single template (colours 5-9) nor isolated {1,2,3,4} markers, so the rule produced
no real transform (output equalled input / blank — fired=0). This rewrite
CONSTRUCTS one colour-5-9 template plus several isolated rotation markers, placed
so every rotated stamp stays in bounds.

Axes: grid size, template shape, marker count, marker rotations + positions.
Degenerates: no_markers, single_marker, all_identity.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "76e1a5257af0"
VERSION = "2.2.0"  # add non-overlap stamp placement + self_check; v2.1 could hide a stamp by overlap
TASK_ID = "76e1a5257af0"

SUMMARY = ("A colour-5-9 template plus several isolated marker cells (values 1-4) that encode "
           "rotations; the rule stamps a rotated copy of the template at each marker. Template "
           "shape, marker count, rotations and positions vary.")

INVARIANTS = [
    "one connected template in colours 5-9 (the only non-marker content)",
    ">=1 isolated marker cell with value in {1,2,3,4} (rotation code)",
    "each marker leaves room for a rotated template stamp to stay in bounds",
]

DEGENERATE_TEXTURES = ("no_markers", "single_marker", "all_identity")
HELPFUL_TEXTURES = ("default", "warm", "cool", "varied")

AXES = {
    "grid_h":     {"type": "int", "default": "rng 11..16", "valid": "8..20"},
    "grid_w":     {"type": "int", "default": "rng 11..16", "valid": "8..20"},
    "tpl_k":      {"type": "int", "default": "rng 3..5 template cells", "valid": "2..7"},
    "n_markers":  {"type": "int", "default": "2-3 easy / 3-4 hard", "valid": "1..6"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                     "valid": "default|warm|cool|varied"},
    "density":    {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":    {"type": "str", "default": "alias for palette_kind",
                   "valid": "default|warm|cool|varied|no_markers|single_marker|all_identity"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _rotate_grid(g, code):
    if code == 1:
        return [row[:] for row in g]
    if code == 2:
        return [list(row) for row in zip(*g[::-1])]
    if code == 3:
        return [row[::-1] for row in g[::-1]]
    if code == 4:
        return [list(row) for row in zip(*g)][::-1]
    raise ValueError(code)


def _stamp_targets(tpl_grid, marker):
    mr, mc, code = marker
    rot = _rotate_grid(tpl_grid, code)
    return {(mr + r, mc + c)
            for r, row in enumerate(rot)
            for c, v in enumerate(row) if v != 0}


def _safe_default():
    g = full_grid(12, 12, 0)
    for r, c in [(0, 0), (0, 1), (1, 0)]:
        g[r][c] = 6
    g[0][6] = 1
    g[6][0] = 2
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 12); w = ctx.draw_int("grid_w", 11, 12)
        k = ctx.draw_int("tpl_k", 3, 4); n_markers = ctx.draw_int("n_markers", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 16); w = ctx.draw_int("grid_w", 14, 16)
        k = ctx.draw_int("tpl_k", 4, 5); n_markers = ctx.draw_int("n_markers", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 12, 14); w = ctx.draw_int("grid_w", 12, 14)
        k = ctx.draw_int("tpl_k", 3, 5); n_markers = ctx.draw_int("n_markers", 2, 4)
    rng = ctx.draw_rng("layout")

    tpl = _build_motif(rng, k)
    th = max(r for r, _ in tpl) + 1; tw = max(c for _, c in tpl) + 1
    maxd = max(th, tw)
    tcolor = rng.choice([5, 6, 7, 8, 9])

    g = full_grid(h, w, 0)
    # template in the top-left corner (its position is irrelevant — the rule crops it)
    occupied = set()
    for (r, c) in tpl:
        g[r][c] = tcolor; occupied.add((r, c))
    tpl_halo = {(r + dr, c + dc) for (r, c) in occupied for dr in (-1, 0, 1) for dc in (-1, 0, 1)}

    # isolated markers (values 1-4) placed so a rotated stamp fits within bounds
    # AND so its nonzero target cells do not overlap any earlier stamp.  Overlap
    # is legal for the Racket rule, but it hides one marker's effect and makes the
    # demos under-teach the rotation mapping.
    made = 0
    marker_occ = set(tpl_halo)
    target_occ: set[tuple[int, int]] = set()
    for _ in range(1000):
        if made >= n_markers:
            break
        mr = rng.randint(0, h - maxd); mc = rng.randint(0, w - maxd)
        # keep markers isolated: clear of template, other markers, and their halos
        if any((mr + dr, mc + dc) in marker_occ for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
            continue
        if g[mr][mc] != 0:
            continue
        code = rng.randint(1, 4)
        targets = _stamp_targets([[tcolor if (r, c) in tpl else 0 for c in range(tw)] for r in range(th)],
                                 (mr, mc, code))
        if any(not (0 <= r < h and 0 <= c < w) for r, c in targets):
            continue
        if targets & target_occ:
            continue
        g[mr][mc] = code
        marker_occ |= {(mr + dr, mc + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
        target_occ |= targets
        made += 1
    if made < 2:                         # guarantee the normal path is not the single-marker degenerate
        return _safe_default()
    return g


def _marker_cells(grid):
    h, w = len(grid), len(grid[0])
    out = []
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v in (1, 2, 3, 4):
                same = False
                for dr, dc in _CARD:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == v:
                        same = True
                        break
                if not same:
                    out.append((r, c, v))
    return out


def _crop_nonzero(grid):
    pts = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0]
    if not pts:
        return []
    r1, r2 = min(r for r, _ in pts), max(r for r, _ in pts)
    c1, c2 = min(c for _, c in pts), max(c for _, c in pts)
    return [row[c1:c2 + 1] for row in grid[r1:r2 + 1]]


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    h, w = len(grid), len(grid[0])
    markers = _marker_cells(grid)
    if len(markers) < 2:
        errs.append(f"expected at least two isolated rotation markers, found {len(markers)}")
    cleaned = [row[:] for row in grid]
    for r, c, _ in markers:
        cleaned[r][c] = 0
    tpl = _crop_nonzero(cleaned)
    if not tpl:
        errs.append("missing non-marker template")
        return errs
    colors = {v for row in tpl for v in row if v != 0}
    if not colors or not colors <= {5, 6, 7, 8, 9}:
        errs.append(f"template colors should be 5-9 only, saw {sorted(colors)}")
    target_occ: set[tuple[int, int]] = set()
    for m in markers:
        targets = _stamp_targets(tpl, m)
        if any(not (0 <= r < h and 0 <= c < w) for r, c in targets):
            errs.append(f"marker {m} stamps out of bounds")
            continue
        if targets & target_occ:
            errs.append(f"marker {m} stamp overlaps an earlier marker's stamp")
        target_occ |= targets
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 12, 12
    g = full_grid(h, w, 0)
    for r, c in [(0, 0), (0, 1), (1, 0)]:        # L template
        g[r][c] = 6
    if name == "no_markers":
        return g                                  # no markers -> blank stamp output
    if name == "single_marker":
        g[5][5] = 1                               # one identity stamp
        return g
    # all_identity -> several markers, all value 1 (identity stamps only)
    for (r, c) in [(4, 4), (4, 8), (8, 4)]:
        g[r][c] = 1
    return g
