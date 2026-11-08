"""Generator for b775ac94.

Rule: nonzero cells form 8-connected groups.  In each group the plurality
color is the main shape; every other cell is a seed.  Canonical groups keep
their 1..3 seed cells in the three ring cells around ONE corner of the main
shape's bbox, and the main shape occupies that corner cell.  Each seed
paints the main shape mirrored across the bbox side(s) it indicates (above/
below across the top/bottom edge, left/right across the left/right edge; a
corner-ring seed can trigger both), in its own color; out-of-bounds mirror
cells clip.  The output is the input plus these mirrored copies.

Every official input is SQUARE with (side, n_groups) in {(14,2), (20,1),
(24,3), (30,3)}, and one official main shape spans bbox 3x5 -- the
archetype prior reproduces those exact configurations at >=25% per band
(default draws only), while generalized dims (12..30), group counts 1..3,
and span-5 main shapes remain reachable outside it.

Combinatorial axes (4): grid_h/w, n_groups, seeds_per_group, texture.
Branches exercised: 1..3 groups, 4..9-cell non-solid polyomino main shapes
with bbox spans 2..5, all four bbox corners for the seed cluster, 1..3
seeds per group (subset of the corner ring), zone/position jitter, and seed
colors that may collide with another group's main color (canonical form).
Textures: one_group, single_seed, solid_main (all rule-valid).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dc2c4869445c"
VERSION = "3.1.0"
TASK_ID = "dc2c4869445c"
RULE_HASH = "f9fbf72b057d"
SUMMARY = "Each seed cell mirrors its group's main shape across the indicated bbox side."

INVARIANTS = [
    "background 0 is the modal color",
    "nonzero cells form 8-connected groups; each group has a strict "
    "plurality main color of at least 4 cells",
    "non-main cells are singleton seeds (1..3 per group), each a distinct "
    "color, all inside the three ring cells around one corner of the main "
    "shape's bbox; the main shape occupies that corner cell",
    "every seed's mirrored copy of the main shape stays in-bounds",
]

DEGENERATE_TEXTURES = ("one_group", "single_seed", "solid_main")

AXES = {
    "grid_h":         {"type": "int", "default": "band rng 14..30",
                       "valid": "12..30"},
    "grid_w":         {"type": "int", "default": "band rng 14..30",
                       "valid": "12..30"},
    "n_groups":       {"type": "int", "default": "band 1 easy, 2 medium, "
                       "2..3 hard", "valid": "1..3"},
    "seeds_per_group":{"type": "int", "default": "band 2 easy, 2..3 medium, "
                       "3 hard", "valid": "2..3"},
    "texture":        {"type": "str", "default": "none (plain draw)",
                       "valid": "|".join(("none",) + DEGENERATE_TEXTURES)},
}

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_VALID_H = (12, 30)
_VALID_W = (12, 30)
_VALID_G = (1, 3)
_VALID_SEEDS = (2, 3)
# Default-only canonical-archetype prior probability per difficulty band.
_ARCH_PRIOR = {"easy": 0.4, "medium": 0.4, "hard": 0.35}
# Official square configurations: (side, n_groups) shared by all four
# official inputs, with each group's complete extracted geometry below.
_ARCHETYPES = (
    (20, (([(0, 1), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 3), (2, 4)], 3, 5, 3, 3),)),
    (30, (([(0, 1), (0, 2), (1, 1), (2, 0), (2, 2)], 3, 3, 1, 3),
          ([(0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 3), (2, 3), (3, 2)], 4, 4, 1, 3),
          ([(0, 0), (1, 1), (1, 2), (2, 1)], 3, 3, 0, 2))),
    (14, (([(0, 0), (0, 1), (1, 0), (1, 1), (2, 2)], 3, 3, 3, 2),
          ([(0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 2)], 3, 4, 1, 2))),
    (24, (([(0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 3), (3, 2), (3, 3)], 4, 4, 3, 3),
          ([(0, 0), (0, 1), (0, 2), (1, 1)], 2, 3, 1, 3),
          ([(0, 2), (1, 0), (1, 1), (1, 2), (2, 0)], 3, 3, 1, 2))),
)
# Ring cells around each bbox corner, in canonical (diagonal, edge, edge) order.
_CORNERS = (
    lambda mr1, mr2, mc1, mc2: ((mr1, mc1), [(mr1 - 1, mc1 - 1), (mr1 - 1, mc1), (mr1, mc1 - 1)]),
    lambda mr1, mr2, mc1, mc2: ((mr1, mc2), [(mr1 - 1, mc2 + 1), (mr1 - 1, mc2), (mr1, mc2 + 1)]),
    lambda mr1, mr2, mc1, mc2: ((mr2, mc1), [(mr2 + 1, mc1 - 1), (mr2 + 1, mc1), (mr2, mc1 - 1)]),
    lambda mr1, mr2, mc1, mc2: ((mr2, mc2), [(mr2 + 1, mc2 + 1), (mr2 + 1, mc2), (mr2, mc2 + 1)]),
)


def _groups8(grid):
    """8-connected components of nonzero cells -> list of (r, c) cell lists."""
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or seen[r][c]:
                continue
            stack, cells = [(r, c)], []
            seen[r][c] = True
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = cr + dr, cc + dc
                        if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                                and grid[nr][nc] != 0):
                            seen[nr][nc] = True
                            stack.append((nr, nc))
            out.append(cells)
    return out


def _group_parts(grid, cells):
    """Split a group into (main_color, main_cells, seed_cells)."""
    freq = {}
    for r, c in cells:
        freq[grid[r][c]] = freq.get(grid[r][c], 0) + 1
    main = max(freq, key=lambda k: (freq[k], -k))
    mcells = [(r, c) for r, c in cells if grid[r][c] == main]
    seeds = [(r, c) for r, c in cells if grid[r][c] != main]
    return main, mcells, seeds


def _seed_corner(mcells, seeds):
    """The bbox corner whose 3 ring cells cover all seeds, or None."""
    mr1 = min(r for r, _ in mcells); mr2 = max(r for r, _ in mcells)
    mc1 = min(c for _, c in mcells); mc2 = max(c for _, c in mcells)
    for make in _CORNERS:
        corner, ring = make(mr1, mr2, mc1, mc2)
        if set(seeds) <= set(ring):
            return corner, ring, (mr1, mr2, mc1, mc2)
    return None


def _targets_for_seeds(mcells, seeds, bbox):
    """Exact rule paint-target cells for the given seeds: each seed mirrors
    the main cells across the bbox side(s) its position indicates."""
    (mr1, mr2, mc1, mc2) = bbox
    out = []
    for sr, sc in seeds:
        dr = "above" if sr < mr1 else "below" if sr > mr2 else "mid"
        dc = "left" if sc < mc1 else "right" if sc > mc2 else "mid"
        for r, c in mcells:
            nr = (2 * mr1 - 1 - r) if dr == "above" else \
                 (2 * mr2 + 1 - r) if dr == "below" else r
            nc = (2 * mc1 - 1 - c) if dc == "left" else \
                 (2 * mc2 + 1 - c) if dc == "right" else c
            out.append((nr, nc))
    return out


def rule_mirror(grid):
    """Independent Python port used only for parity and regression audits."""
    h, w = len(grid), len(grid[0])
    result = [row[:] for row in grid]
    for cells in _groups8(grid):
        _, mcells, seeds = _group_parts(grid, cells)
        mr1 = min(r for r, _ in mcells)
        mr2 = max(r for r, _ in mcells)
        mc1 = min(c for _, c in mcells)
        mc2 = max(c for _, c in mcells)
        for sr, sc in seeds:
            seed_color = grid[sr][sc]
            dr = "above" if sr < mr1 else "below" if sr > mr2 else "mid"
            dc = "left" if sc < mc1 else "right" if sc > mc2 else "mid"
            for r, c in mcells:
                nr = (
                    2 * mr1 - 1 - r if dr == "above"
                    else 2 * mr2 + 1 - r if dr == "below"
                    else r
                )
                nc = (
                    2 * mc1 - 1 - c if dc == "left"
                    else 2 * mc2 + 1 - c if dc == "right"
                    else c
                )
                if 0 <= nr < h and 0 <= nc < w:
                    result[nr][nc] = seed_color
    return result


def _mirror_cells(mcells, corner, bbox):
    """All mirror-target cells for the seed corner (reflection block)."""
    (mr1, mr2, mc1, mc2) = bbox
    cr, cc = corner
    out = []
    for r, c in mcells:
        nr = (2 * mr1 - 1 - r) if cr == mr1 else (2 * mr2 + 1 - r)
        nc = (2 * mc1 - 1 - c) if cc == mc1 else (2 * mc2 + 1 - c)
        out.append((nr, nc))
    return out


def observe_overrides(grid) -> dict:
    """Realized per-draw values of the exact semantic axes (KRF-0002):
    n_groups = number of 8-connected nonzero groups; seeds_per_group =
    minimum non-main-cell count over groups (uniform by construction)."""
    groups = _groups8(grid)
    seed_counts = []
    for cells in groups:
        _, _, seeds = _group_parts(grid, cells)
        seed_counts.append(len(seeds))
    return {
        "n_groups": len(groups),
        "seeds_per_group": min(seed_counts) if seed_counts else 0,
    }


def profile_features(grid):
    """ONE executable feature extractor, used for canonical pairs AND
    generated grids alike. Returns the linked configuration profile:
    (h, w, square, n_groups, per-group (main color, main bbox, main span,
    main cells, seed count, seed corner name, seed colors), max main span)."""
    h, w = len(grid), len(grid[0])
    names = ("top-left", "top-right", "bottom-left", "bottom-right")
    parts = []
    max_span = 0
    for cells in _groups8(grid):
        main, mcells, seeds = _group_parts(grid, cells)
        bh = max(r for r, c in mcells) - min(r for r, c in mcells) + 1
        bw = max(c for r, c in mcells) - min(c for r, c in mcells) + 1
        span = max(bh, bw)
        max_span = max(max_span, span)
        corner = _seed_corner(mcells, seeds)
        cname = None
        if corner is not None:
            (cr, cc), _ring, bbox = corner
            mr1, mr2, mc1, mc2 = bbox
            cname = names[(1 if cc == mc2 else 0) + (2 if cr == mr2 else 0)]
        parts.append({
            "main_color": main, "main_bbox": (bh, bw), "main_span": span,
            "main_cells": len(mcells), "n_seeds": len(seeds),
            "seed_corner": cname,
            "seed_colors": sorted({grid[r][c] for (r, c) in seeds}),
        })
    return {"h": h, "w": w, "square": h == w, "n_groups": len(parts),
            "groups": parts, "max_main_span": max_span}


_ROT_CORNER = (
    (0, 1, 2, 3),   # j=0 identity: TL TR BL BR stay
    (1, 3, 0, 2),   # j=1 rot90cw: TL->TR, TR->BR, BL->TL, BR->BL
    (3, 2, 1, 0),   # j=2 rot180: TL->BR, TR->BL, BL->TR, BR->TL
    (2, 0, 3, 1),   # j=3 rot270cw: TL->BL, TR->TL, BL->BR, BR->TR
)
_FLIP_CORNER = (1, 0, 3, 2)   # left<->right: TL<->TR, BL<->BR


def _d4_transform(rel, bh, bw, ci, k):
    """Apply dihedral variant k (0..7) to a group's normalized shape:
    rotation k%4 then a left-right flip when k>=4. Returns
    (rel', bh', bw', ci') with the seed corner index remapped. The rule's
    bbox-edge mirror commutes with D4, so transformed groups stay in the
    canonical family (true task symmetry)."""
    j = k % 4
    out = []
    for r, c in rel:
        if j == 0:
            rr, cc = r, c
        elif j == 1:
            rr, cc = c, bh - 1 - r
        elif j == 2:
            rr, cc = bh - 1 - r, bw - 1 - c
        else:
            rr, cc = bw - 1 - c, r
        out.append((rr, cc))
    nbh, nbw = (bh, bw) if j in (0, 2) else (bw, bh)
    if k >= 4:
        out = [(r, nbw - 1 - c) for r, c in out]
    nci = _ROT_CORNER[j][ci]
    if k >= 4:
        nci = _FLIP_CORNER[nci]
    return out, nbh, nbw, nci


def linked_profile_signature(grid):
    """Complete color-free official-profile signature, normalized under D4."""
    group_signatures = []
    for cells in _groups8(grid):
        _, mcells, seeds = _group_parts(grid, cells)
        mr1 = min(r for r, _ in mcells)
        mr2 = max(r for r, _ in mcells)
        mc1 = min(c for _, c in mcells)
        mc2 = max(c for _, c in mcells)
        found = _seed_corner(mcells, seeds)
        if found is None:
            return None
        corner, _, _ = found
        ci = (
            (2 if corner[0] == mr2 else 0)
            + (1 if corner[1] == mc2 else 0)
        )
        rel = [(r - mr1, c - mc1) for r, c in mcells]
        bh = mr2 - mr1 + 1
        bw = mc2 - mc1 + 1
        variants = []
        for k in range(8):
            transformed, _, _, transformed_ci = _d4_transform(
                rel, bh, bw, ci, k
            )
            variants.append(
                (tuple(sorted(transformed)), transformed_ci, len(seeds))
            )
        group_signatures.append(min(variants))
    return (
        len(grid),
        len(grid[0]),
        tuple(sorted(group_signatures)),
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance: rectangular grid inside
    the declared envelope (_VALID_H x _VALID_W, matching AXES grid_h/grid_w)
    of colors 0..9; 0 modal; at least one 8-connected nonzero group; every
    group has a strict plurality main color of >= 4 cells; non-main cells
    are 1..3 singleton seeds sitting in one bbox corner's ring with the
    corner cell occupied by the main shape; the corner's reflection block
    is in-bounds."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 9
           for row in grid for v in row):
        errs.append("color outside 0..9")
    if not (_VALID_H[0] <= h <= _VALID_H[1] and _VALID_W[0] <= w <= _VALID_W[1]):
        errs.append(f"dims {h}x{w} outside the declared envelope "
                    f"{_VALID_H[0]}..{_VALID_H[1]} x {_VALID_W[0]}..{_VALID_W[1]}")
    flat = [v for row in grid for v in row]
    if flat.count(0) * 2 <= len(flat):
        errs.append("background 0 is not modal")
    groups = _groups8(grid)
    if not groups:
        errs.append("no nonzero group: the oracle has nothing to reflect")
        return errs
    for cells in groups:
        freq = {}
        for r, c in cells:
            freq[grid[r][c]] = freq.get(grid[r][c], 0) + 1
        counts = sorted(freq.values(), reverse=True)
        if len(counts) > 1 and counts[0] == counts[1]:
            errs.append("plurality tie for a group's main color: ambiguous")
            continue
        main, mcells, seeds = _group_parts(grid, cells)
        if len(mcells) < 4:
            errs.append(f"main shape has {len(mcells)} cells (< 4)")
        seed_freq = {}
        for r, c in seeds:
            seed_freq[grid[r][c]] = seed_freq.get(grid[r][c], 0) + 1
        if any(n != 1 for n in seed_freq.values()):
            errs.append("a seed color has more than one cell in a group")
        if not 1 <= len(seeds) <= 3:
            errs.append(f"group has {len(seeds)} seeds (outside 1..3)")
        found = _seed_corner(mcells, seeds)
        if found is None:
            errs.append("seeds are not inside one bbox corner's ring")
            continue
        corner, ring, bbox = found
        if corner not in mcells:
            errs.append("main shape does not occupy the seed corner cell")
        for nr, nc in _mirror_cells(mcells, corner, bbox):
            if not (0 <= nr < h and 0 <= nc < w):
                errs.append("reflection block clips the grid edge")
                break
    # Order-sensitive collision ban (semantic veto): each group's exact
    # per-seed paint targets must miss every other group's input cells and
    # every other group's target set.
    target_sets = []
    for cells in groups:
        main, mcells, seeds = _group_parts(grid, cells)
        found = _seed_corner(mcells, seeds)
        if found is None:
            target_sets.append(set())
            continue
        _, _, bbox = found
        target_sets.append(set(_targets_for_seeds(mcells, seeds, bbox)))
    for i, cells in enumerate(groups):
        own = set(cells)
        for j, tset in enumerate(target_sets):
            if i == j:
                continue
            if own & tset:
                errs.append(f"group {j}'s reflection targets hit group {i}'s "
                            "input cells")
                break
    for i in range(len(target_sets)):
        for j in range(i + 1, len(target_sets)):
            if target_sets[i] & target_sets[j]:
                errs.append(f"groups {i} and {j} have overlapping reflection "
                            "target sets")
                break
    return errs


def _polyomino(rng, n_cells, max_bh, max_bw, solid=False, want_span5=False):
    """Random 4-connected polyomino as (relative-cells, bh, bw); bbox not
    fully filled unless solid. With want_span5, only accept bboxes whose
    larger side is exactly 5 (the official 3x5/5x4 extreme). None when
    retries exhaust."""
    for _ in range(60):
        cells = [(0, 0)]
        while len(cells) < n_cells:
            r, c = cells[rng.randrange(len(cells))]
            dr, dc = _DIRS4[rng.randrange(4)]
            nxt = (r + dr, c + dc)
            if nxt not in cells:
                cells.append(nxt)
        mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
        rel = [(r - mr, c - mc) for r, c in cells]
        bh = max(r for r, _ in rel) + 1
        bw = max(c for _, c in rel) + 1
        if bh > max_bh or bw > max_bw:
            continue
        if not solid and len(rel) == bh * bw:
            continue
        if want_span5 and max(bh, bw) != 5:
            continue
        return rel, bh, bw
    return None


def _solid_shape(rng, n_cells, max_bh, max_bw):
    """Solid rectangle of n_cells (4..9) within the bbox caps."""
    rects = [(bh, bw) for bh in range(2, max_bh + 1)
             for bw in range(2, max_bw + 1) if bh * bw == n_cells]
    if not rects:
        return None
    bh, bw = rects[rng.randrange(len(rects))]
    return [(r, c) for r in range(bh) for c in range(bw)], bh, bw


def _place_archetype_group(g, rng, zr0, zr1, w, main, cells_rel, bh, bw, ci,
                           n_seeds, reserved, occupied):
    """Place one extracted-archetype group (complete canonical morphology:
    exact main cell-set, exact seed corner, exact seed count) at a fresh
    position inside zone rows [zr0, zr1), with the reflection block
    in-bounds, everything disjoint from `reserved`, and its nonzero cells
    not 8-adjacent to `occupied`. Deterministic first-fit scan over legal
    positions with a random offset for jitter."""
    h = len(g)
    corner = _corner_cell(ci, bh, bw)
    mirrors = _mirror_cells(cells_rel, corner, (0, bh - 1, 0, bw - 1))
    span = list(cells_rel) + mirrors
    span_r0 = min(r for r, _ in span); span_r1 = max(r for r, _ in span)
    span_c0 = min(c for _, c in span); span_c1 = max(c for _, c in span)
    r_lo = max(zr0, -span_r0)
    r_hi = min(zr1 - bh, h - 1 - span_r1)
    c_lo = -span_c0
    c_hi = w - 1 - span_c1
    if r_hi < r_lo or c_hi < c_lo:
        return False
    positions = [(r0, c0) for r0 in range(r_lo, r_hi + 1)
                 for c0 in range(c_lo, c_hi + 1)]
    if not positions:
        return False
    start = rng.randrange(len(positions))
    positions = positions[start:] + positions[:start]
    cells = None
    for r0, c0 in positions:
        cells = [(r0 + r, c0 + c) for r, c in cells_rel]
        ring = [(r0 + a, c0 + b) for a, b in _corner_ring(ci, bh, bw)]
        seed_cells = ring[:n_seeds]
        bbox = (r0, r0 + bh - 1, c0, c0 + bw - 1)
        block = _targets_for_seeds(cells, seed_cells, bbox)
        if any(not (0 <= r < h and 0 <= c < w)
               for r, c in cells + ring + block):
            continue
        if any(cell in reserved for cell in cells + ring + block):
            continue
        if any((r + dr, c + dc) in occupied
               for r, c in cells + ring
               for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
            continue
        seed_colors = [c for c in rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 9)
                       if c != main][:n_seeds]
        for r, c in cells:
            g[r][c] = main
        for (r, c), sc in zip(seed_cells, seed_colors):
            g[r][c] = sc
        reserved.update(cells)
        reserved.update(seed_cells)
        reserved.update(block)
        occupied.update(cells)
        occupied.update(seed_cells)
        return True
    return False


def _generate_archetype(ctx, rng, difficulty):
    """Default-only canonical-archetype draw: one of the four exact
    official square configurations with its complete extracted group
    morphologies (each independently D4-varied -- a true task symmetry --
    and placed at fresh positions with fresh colors)."""
    side, groups = _ARCHETYPES[rng.randrange(len(_ARCHETYPES))]
    h = ctx.draw_int("grid_h", side, side)
    w = ctx.draw_int("grid_w", side, side)
    n_groups = ctx.draw_int("n_groups", len(groups), len(groups))
    # keyed provenance for the exact observer axis (min seeds over groups)
    ctx.draw_int("seeds_per_group", min(ns for _r, _b1, _b2, _c, ns in groups),
                 min(ns for _r, _b1, _b2, _c, ns in groups))
    mains = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_groups)
    zone_h = h // n_groups
    # Whole-layout retries: D4 variants and position offsets are re-rolled
    # per attempt (nuisance factors); the archetype count is never shed.
    for _layout in range(60):
        g = full_grid(h, w, 0)
        reserved = set()
        occupied = set()
        ok = True
        for gi, (rel, bh, bw, ci, n_seeds) in enumerate(groups):
            rel = [tuple(p) for p in rel]
            rel2, bh2, bw2, ci2 = _d4_transform(rel, bh, bw, ci,
                                                rng.randrange(8))
            zr0 = gi * zone_h
            zr1 = h if gi == n_groups - 1 else (gi + 1) * zone_h
            if not _place_archetype_group(g, rng, zr0, zr1, w, mains[gi],
                                          rel2, bh2, bw2, ci2, n_seeds,
                                          reserved, occupied):
                ok = False
                break
        if ok:
            break
    else:
        raise ValueError(
            f"cannot place archetype groups with reflection room on a "
            f"{h}x{w} grid")
    errs = self_check(g, difficulty=difficulty)
    if errs:
        raise ValueError(f"archetype layout violated self_check: {errs}")
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    # An explicit "none" is the exact public spelling of the ordinary path.
    # Normalize before GenCtx construction so omitted and explicit-none calls
    # have identical keyed draws and remain byte-for-byte reproducible.
    overrides = dict(overrides)
    if overrides.get("texture") == "none":
        overrides.pop("texture")
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    band = difficulty or "medium"
    texture = overrides.get("texture")
    if texture is not None and texture not in DEGENERATE_TEXTURES:
        raise ValueError(f"unknown texture {texture!r}")
    # Default-only canonical-archetype prior: exact official square
    # configurations with complete extracted morphologies.
    if not overrides and texture is None and \
            ctx.draw_rng("arche_prior").random() < _ARCH_PRIOR[band]:
        return _generate_archetype(ctx, rng, difficulty)
    if band == "easy":
        h_lo, h_hi, g_lo, g_hi, s_lo, s_hi = 14, 18, 1, 1, 2, 2
    elif band == "hard":
        h_lo, h_hi, g_lo, g_hi, s_lo, s_hi = 24, 30, 2, 3, 3, 3
    else:
        h_lo, h_hi, g_lo, g_hi, s_lo, s_hi = 18, 24, 2, 2, 2, 3

    # Exact overrides execute over the full declared valid range (or reject
    # loudly); band ranges apply to plain draws only.
    h = (ctx.draw_int("grid_h", *_VALID_H) if overrides.get("grid_h") is not None
         else ctx.draw_int("grid_h", h_lo, h_hi))
    w = (ctx.draw_int("grid_w", *_VALID_W) if overrides.get("grid_w") is not None
         else ctx.draw_int("grid_w", h_lo, h_hi))
    if texture == "one_group":
        if overrides.get("n_groups") is not None:
            raise ValueError("texture=one_group conflicts with n_groups override")
        n_groups = 1
    elif overrides.get("n_groups") is not None:
        n_groups = ctx.draw_int("n_groups", *_VALID_G)
    else:
        n_groups = ctx.draw_int("n_groups", g_lo, g_hi)
    if texture == "single_seed":
        if overrides.get("seeds_per_group") is not None:
            raise ValueError("texture=single_seed conflicts with seeds_per_group override")
        n_seeds = 1
    elif overrides.get("seeds_per_group") is not None:
        n_seeds = ctx.draw_int("seeds_per_group", *_VALID_SEEDS)
    else:
        n_seeds = ctx.draw_int("seeds_per_group", s_lo, s_hi)

    g = full_grid(h, w, 0)
    reserved = set()          # group cells + reflection blocks of placed groups
    occupied = set()          # nonzero cells only (8-adjacency must stay clear)
    mains = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_groups)
    zone_h = h // n_groups
    for gi in range(n_groups):
        zr0 = gi * zone_h
        zr1 = h if gi == n_groups - 1 else (gi + 1) * zone_h
        if not _place_group(g, rng, zr0, zr1, w, mains[gi], n_seeds,
                            solid=(texture == "solid_main"),
                            reserved=reserved, occupied=occupied):
            raise ValueError(
                f"cannot place group {gi + 1}/{n_groups} with reflection "
                f"room on a {h}x{w} grid")
    return g


def _corner_cell(ci, bh, bw):
    return [(0, 0), (0, bw - 1), (bh - 1, 0), (bh - 1, bw - 1)][ci]


def _corner_ring(ci, bh, bw):
    """The 3 ring cells (relative) around bbox corner ci."""
    return [
        [(-1, -1), (-1, 0), (0, -1)],
        [(-1, bw), (-1, bw - 1), (0, bw)],
        [(bh, -1), (bh, 0), (bh - 1, -1)],
        [(bh, bw), (bh, bw - 1), (bh - 1, bw)],
    ][ci]


def _place_group(g, rng, zr0, zr1, w, main, n_seeds, *, solid, reserved,
                 occupied):
    """Place one group (shape + corner ring seeds) with its shape inside
    zone rows [zr0, zr1), its reflection block in-bounds, everything
    disjoint from `reserved`, and its nonzero cells not 8-adjacent to
    `occupied` (groups must stay separate 8-components).  Random tries
    first, then a deterministic first-fit scan."""
    h = len(g)

    def try_caps(bh_cap, bw_cap, n_cells_choices, deterministic,
                 want_span5=False):
        tries = 1 if deterministic else 150
        for _ in range(tries):
            n_cells = (min(n_cells_choices) if deterministic
                       else rng.choice(n_cells_choices))
            made = (_solid_shape(rng, n_cells, bh_cap, bw_cap) if solid
                    else _polyomino(rng, n_cells, bh_cap, bw_cap,
                                    want_span5=want_span5))
            if made is None:
                continue
            rel, bh, bw = made
            # The seed corner must be one the shape actually occupies (so
            # the ring seeds stay 8-connected to the group).
            occ_corners = [ci for ci in range(4)
                           if _corner_cell(ci, bh, bw) in rel]
            if not occ_corners:
                continue
            ci = occ_corners[0] if deterministic else rng.choice(occ_corners)
            corner = _corner_cell(ci, bh, bw)
            mirrors = _mirror_cells(rel, corner, (0, bh - 1, 0, bw - 1))
            span = rel + mirrors
            span_r0 = min(r for r, _ in span); span_r1 = max(r for r, _ in span)
            span_c0 = min(c for _, c in span); span_c1 = max(c for _, c in span)
            # Shape bbox rows stay inside the zone; everything (shape, ring
            # seeds, reflection block) stays in-bounds and reservation-free.
            r_lo = max(zr0, -span_r0)
            r_hi = min(zr1 - bh, h - 1 - span_r1)
            c_lo = -span_c0
            c_hi = w - 1 - span_c1
            if r_hi < r_lo or c_hi < c_lo:
                continue
            if deterministic:
                positions = [(r0, c0) for r0 in range(r_lo, r_hi + 1)
                             for c0 in range(c_lo, c_hi + 1)]
            else:
                positions = [(rng.randint(r_lo, r_hi), rng.randint(c_lo, c_hi))
                             for _try in range(60)]
            for r0, c0 in positions:
                cells = [(r0 + r, c0 + c) for r, c in rel]
                ring = [(r0 + a, c0 + b) for a, b in _corner_ring(ci, bh, bw)]
                seed_cells = (ring[:n_seeds] if deterministic
                              else rng.sample(ring, n_seeds))
                # Reserve the ACTUAL per-seed paint targets (vertical-only,
                # horizontal-only, or diagonal mirror sets), not just the
                # diagonal corner block (semantic-veto fix).
                bbox = (r0, r0 + bh - 1, c0, c0 + bw - 1)
                block = _targets_for_seeds(cells, seed_cells, bbox)
                if any(not (0 <= r < h and 0 <= c < w)
                       for r, c in cells + ring + block):
                    continue
                if any(cell in reserved for cell in cells + ring + block):
                    continue
                # Groups must remain separate 8-connected components: no
                # new nonzero cell may touch an existing nonzero cell.
                if any((r + dr, c + dc) in occupied
                       for r, c in cells + ring
                       for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
                    continue
                seed_colors = [c for c in rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 9)
                               if c != main][:n_seeds]
                for r, c in cells:
                    g[r][c] = main
                for (r, c), sc in zip(seed_cells, seed_colors):
                    g[r][c] = sc
                reserved.update(cells)
                reserved.update(seed_cells)
                reserved.update(block)
                occupied.update(cells)
                occupied.update(seed_cells)
                return True
        return False

    # bbox span 5 (the official 3x5/5x4 extreme) is deliberately reachable:
    # ~30% of groups try a span-5 shape first, then the ordinary caps.
    if rng.random() < 0.3 and try_caps(5, 5, [5, 6, 7, 8, 9],
                                       deterministic=False, want_span5=True):
        return True
    for bh_cap, bw_cap, choices in ((4, 4, [5, 6, 7, 8, 9]),
                                    (3, 3, [4, 5, 6, 7]),
                                    (2, 2, [4])):
        if try_caps(bh_cap, bw_cap, choices, deterministic=False):
            return True
    return try_caps(2, 2, [4], deterministic=True)
