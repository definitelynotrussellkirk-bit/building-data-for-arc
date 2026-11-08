"""Generator for ff805c23 -- reconstruct the occluded 5x5 from grid symmetry.

Rule: a solid 5x5 blue(1) marker occludes part of a fully lr+ud(+180)
symmetric pattern.  The rule takes the marker bbox and recovers each
occluded cell as the first non-1 value among [self, lr-mirror, ud-mirror,
180-mirror]; output is the reconstructed 5x5 region.

Canonical demos are ALWAYS 24x24 with full lr+ud symmetry and exactly one
solid 5x5 marker in one of three placement families: corner-flush (touching
two edges), v-band (crossing the vertical center axis), or h-band (crossing
the horizontal center axis).  A marker never crosses BOTH center axes --
that is exactly the condition guaranteeing every occluded cell has a clean
mirror (when it does not cross the horizontal center, its ud-mirror row is
never a marker row, and symmetrically).  This rebuild places markers from
those three families (corner/v-band/h-band), keeps the grid even-sided so
the center axes are well defined, and guarantees every palette color
appears (n_distinct_colors stays observable).

Combinatorial axes (6): grid_h, grid_w, marker_position, sym_density,
n_distinct_colors, texture.
Branches witnessed: corner / v-band / h-band markers, markers touching
edges, 2-4 pattern colors, density spread, even grid sizes around the
canonical 24x24.
Edge textures (crash-free, self_check-clean): dense_field.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect

GENERATOR_ID = "f283b8535697"
VERSION = "3.4.0"  # answer-bearing archetype profile, patch protection, explicit defaults, and texture provenance
TASK_ID = "f283b8535697"
RULE_HASH = "4829c9bc9298"
SUMMARY = ("Even grid (~24x24) with a full lr+ud symmetric multicolor "
           "pattern and one solid 5x5 blue(1) marker placed corner-flush or "
           "crossing exactly one center axis; oracle reconstructs the "
           "occluded 5x5 from clean mirrors.")

# Rivals refuted by construction: 'output is input cropped' fails on every
# draw (output is the 5x5 RECONSTRUCTED region, dims differ from input);
# 'copy the lr mirror only' fails on band markers whose lr mirror is partly
# occluded (the ud/180 fallback matters); 'marker always in a strict
# quadrant' fails against canonical band markers that cross one center axis;
# 'output palette echoes the input modal color' fails since reconstruction
# copies structured mirrors, not the mode.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0; pattern uses 2..4 non-{0,1} colors, all present",
    "the visible pattern is symmetric under lr AND ud (hence 180)",
    "exactly one solid 5x5 block of blue(1) cells; no other 1-cells",
    "the marker crosses at most one center axis (corner-flush, v-band, or h-band)",
    "every occluded cell has a non-marker lr/ud/180 mirror (reconstructable)",
]

MARKER_POSITIONS = ("corner", "band_v", "band_h", "rng")
DEGENERATE_TEXTURES = ("dense_field",)
_CANONICAL_POOL = (2, 3, 4, 5, 6, 8)   # every color seen in the official demos

AXES = {
    "grid_h":       {"type": "int", "default": "band even 20..30 (even values only)",
                     "valid": "10..30"},
    "grid_w":       {"type": "int", "default": "band even 20..30 (even values only)",
                     "valid": "10..30"},
    "marker_position": {"type": "str", "default": "rng v .4 / h .3 / corner .3",
                        "valid": "|".join(MARKER_POSITIONS)},
    "sym_density":  {"type": "float", "default": "band rng 0.3..0.55",
                     "valid": "0.2..0.85"},
    "n_distinct_colors": {"type": "int", "default": "band rng 2..4",
                          "valid": "2..4"},
    "texture":      {"type": "str", "default": "none",
                     "valid": "none|" + "|".join(DEGENERATE_TEXTURES)},
}


# --------------------------------------------------------------------------
# Structural validation
# --------------------------------------------------------------------------

def _marker_cells(g):
    return [(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v == 1]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance (all 8 canonical pairs
    satisfy them): rectangular even-sided grid 10..30; colors 0..9; blue(1)
    cells form exactly one solid 5x5 block with no other 1-cells; the marker
    crosses at most one center axis; every marker cell has at least one
    non-marker lr/ud/180 mirror (the oracle's fallback chain stays total);
    and the visible (non-marker) pattern is lr+ud symmetric. Rejects
    asymmetric patterns, split/multiple markers, markers crossing both
    center axes, odd dims, and stray 1-cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 9
           for row in grid for v in row):
        errs.append("color outside 0..9")
        return errs
    if h % 2 or w % 2:
        errs.append(f"odd grid side {h}x{w} (canonical grids are even-sided)")
    if not 10 <= h <= 30 or not 10 <= w <= 30:
        errs.append(f"grid {h}x{w} outside declared envelope 10..30")
    cells = _marker_cells(grid)
    if not cells:
        errs.append("no blue(1) marker (oracle crashes on empty min-list)")
        return errs
    n_pattern_colors = len({v for row in grid for v in row} - {0, 1})
    if not 2 <= n_pattern_colors <= 4:
        errs.append(
            f"{n_pattern_colors} pattern colors outside the documented 2..4 grammar")
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    if len(cells) != 25 or r1 - r0 != 4 or c1 - c0 != 4:
        errs.append("marker is not a single solid 5x5 block")
    elif any(grid[r][c] != 1 for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)):
        errs.append("marker block is not solid blue(1)")
    marker_set = set(cells)
    crosses_h = any((h - 1 - r) in {rr for rr, _ in marker_set}
                    for r in range(r0, r1 + 1))
    crosses_v = any((w - 1 - c) in {cc for _, cc in marker_set}
                    for c in range(c0, c1 + 1))
    if crosses_h and crosses_v:
        errs.append("marker crosses both center axes (center cells unreconstructable)")
    else:
        for (r, c) in cells:
            mirrors = [(r, w - 1 - c), (h - 1 - r, c), (h - 1 - r, w - 1 - c)]
            if all(m in marker_set for m in mirrors):
                errs.append(f"marker cell ({r},{c}) has no clean mirror")
                break
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v == 1:
                continue
            for (rr, cc) in ((r, w - 1 - c), (h - 1 - r, c)):
                mv = grid[rr][cc]
                if mv != 1 and mv != v:
                    errs.append(
                        f"visible pattern breaks symmetry at ({r},{c}) vs ({rr},{cc})")
                    return errs
    return errs


def observe_overrides(grid):
    """Realized exact-axis values (KRF-0002): the number of distinct
    non-{0,1} pattern colors (construction guarantees every palette color
    appears, so this equals the palette size)."""
    return {"n_distinct_colors": len({v for row in grid for v in row} - {0, 1})}


def rule_mirror(grid):
    """Independent Python mirror of the canonical Racket reconstruction rule."""
    h, w = len(grid), len(grid[0])
    marker = _marker_cells(grid)
    if not marker:
        raise ValueError("cannot reconstruct a grid with no color-1 marker")
    r0 = min(r for r, _ in marker)
    r1 = max(r for r, _ in marker)
    c0 = min(c for _, c in marker)
    c1 = max(c for _, c in marker)
    out = []
    for r in range(r0, r1 + 1):
        row = []
        for c in range(c0, c1 + 1):
            values = (
                grid[r][c],
                grid[r][w - 1 - c],
                grid[h - 1 - r][c],
                grid[h - 1 - r][w - 1 - c],
            )
            row.append(next((value for value in values if value != 1), 1))
        out.append(row)
    return out


def _marker_family(grid):
    """Return the demonstrated corner/v-band/h-band family, else ``None``."""
    h, w = len(grid), len(grid[0])
    marker = _marker_cells(grid)
    if not marker:
        return None
    rows = {r for r, _ in marker}
    cols = {c for _, c in marker}
    r0, c0 = min(rows), min(cols)
    crosses_h = any(h - 1 - r in rows for r in rows)
    crosses_v = any(w - 1 - c in cols for c in cols)
    if crosses_v and not crosses_h:
        return "band_v"
    if crosses_h and not crosses_v:
        return "band_h"
    near_h_edge = r0 <= 1 or r0 >= h - 6
    near_w_edge = c0 <= 1 or c0 >= w - 6
    if not crosses_h and not crosses_v and near_h_edge and near_w_edge:
        return "corner"
    return None


def canonical_profile_signature(grid):
    """Complete returned-grid profile, including the answer-bearing patch."""
    counts = Counter(value for row in grid for value in row)
    pattern_colors = [
        value for value in counts if value not in (0, 1)
    ]
    largest = max(
        (len(_largest_component(grid, color)) for color in pattern_colors),
        default=0,
    )
    output_counts = Counter(
        value for row in rule_mirror(grid) for value in row
    )
    return (
        len(grid),
        len(grid[0]),
        len(pattern_colors),
        counts.most_common(1)[0][0],
        counts.get(0, 0),
        largest,
        _marker_family(grid),
        tuple(sorted(value for value in output_counts if value != 0)),
        output_counts.get(0, 0),
    )


def is_canonical_profile(grid):
    """Whether a returned grid satisfies every universal official feature."""
    (
        h,
        w,
        n_colors,
        modal,
        zeros,
        largest,
        marker_family,
        output_colors,
        output_zeros,
    ) = canonical_profile_signature(grid)
    return (
        (h, w) == (24, 24)
        and 2 <= n_colors <= 3
        and modal in (0, 2, 3)
        and 176 <= zeros <= 246
        and 61 <= largest <= 252
        and marker_family in ("corner", "band_v", "band_h")
        and len(output_colors) == 1
        and output_colors != (1,)
        and 4 <= output_zeros <= 14
    )


# --------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------

def _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    """Band-shaped random draw; overrides validated against the full valid
    range (an override must execute exactly on any band, KRF-0001). Reads the
    effective ctx.overrides so injected values (archetype prior) are seen."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, lo, hi)


def _even_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    """Even-sided dims only (canonical 24x24 family). Every path records the
    final dimension under the declared keyed label (KRF-0004/v6): the even
    pick itself is unchanged (same label-keyed stream), then injected into
    ctx.overrides so the typed draw records it under grid_h/grid_w."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        v = ctx.draw_int(label, valid_lo, valid_hi)
        if v % 2:
            raise ValueError(
                f"{label}={v} must be even (canonical grids are even-sided)")
        return v
    evens = [v for v in range(lo, hi + 1) if v % 2 == 0]
    v = ctx.draw_rng(label).choice(evens)          # unchanged pick stream
    ctx.overrides[label] = v                        # inject, then typed record
    return ctx.draw_int(label, valid_lo, valid_hi)


def _marker_top_left(rng, h, w, family):
    """(mr, mc) for a solid 5x5 marker in a canonical placement family.
    A marker may cross at most one center axis (the reconstructability
    condition), so the free coordinate is resampled until it stays clear of
    the other center band."""
    def crosses(r0, c0):
        rows = set(range(r0, r0 + 5))
        cols = set(range(c0, c0 + 5))
        ch = any((h - 1 - r) in rows for r in rows)
        cv = any((w - 1 - c) in cols for c in cols)
        return ch, cv

    for _try in range(60):
        if family == "band_v":
            mc = w // 2 - 2 + rng.choice((-1, 0))
            mr = rng.randint(0, h - 5)
        elif family == "band_h":
            mr = h // 2 - 2 + rng.choice((-1, 0))
            mc = rng.randint(0, w - 5)
        else:  # corner: flush to one corner, occasionally one cell off
            mr = rng.choice((0, 0, 1, h - 6, h - 5, h - 5))
            mc = rng.choice((0, 0, 1, w - 6, w - 5, w - 5))
        ch, cv = crosses(mr, mc)
        if not (ch and cv):
            return mr, mc
    return 0, 0   # corner (0,0) never crosses on grids >= 10


def generate(seed, sample_index, *, difficulty=None, **overrides):
    overrides = dict(overrides)
    if overrides.get("texture") == "none":
        overrides.pop("texture")
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    texture = overrides.get("texture")
    extra = sorted(k for k, v in overrides.items()
                   if k != "texture" and v is not None)
    if texture in DEGENERATE_TEXTURES:
        if extra:
            raise ValueError(
                f"edge texture {texture!r} is a fixed layout; it takes no "
                f"other overrides, got {extra}")
        grid = _draw_from_degenerate(texture, rng)
        ctx.draw_int("grid_h", len(grid), len(grid))
        ctx.draw_int("grid_w", len(grid[0]), len(grid[0]))
        realized = observe_overrides(grid)["n_distinct_colors"]
        ctx.draw_int("n_distinct_colors", realized, realized)
        return grid
    if texture not in (None, "none"):
        raise ValueError(f"unknown texture {texture!r}; valid: "
                         f"none|{'|'.join(DEGENERATE_TEXTURES)}")
    # All-band archetype prior (KRF-0003/veto): ~34% of default draws pin the
    # exact official 24x24 profile -- 2..3 pattern colors, modal in {0,2,3},
    # zero count 176..246, largest non-{0,1} 4-component 61..252, and the
    # corner/v-band/h-band marker grammar. The choice is made on a dedicated
    # keyed stream and injected BEFORE the typed draws, so recorded draw ==
    # realized grid on every path (KRF-0004/v6). Generalized draws continue
    # outside the prior.
    arch = False
    if (texture is None
            and overrides.get("grid_h") in (None, 24)
            and overrides.get("grid_w") in (None, 24)
            and overrides.get("n_distinct_colors") in (None, 2, 3)
            and overrides.get("marker_position") in (None, "rng", "corner", "band_v", "band_h")
            and "sym_density" not in overrides
            and ctx.draw_rng("arch_prior").random() < _ARCH_PRIOR_PROB):
        arch = True
        ctx.overrides.setdefault("grid_h", 24)
        ctx.overrides.setdefault("grid_w", 24)
        ctx.overrides.setdefault("n_distinct_colors", rng.choice((2, 3)))
    band = difficulty or "medium"
    if band == "easy":
        h_lo, h_hi, d_lo, d_hi, c_lo, c_hi = 20, 22, 0.28, 0.38, 2, 2
    elif band == "hard":
        h_lo, h_hi, d_lo, d_hi, c_lo, c_hi = 26, 30, 0.42, 0.55, 3, 4
    else:
        h_lo, h_hi, d_lo, d_hi, c_lo, c_hi = 24, 24, 0.34, 0.46, 2, 3
    h = _even_int(ctx, overrides, "grid_h", h_lo, h_hi, 10, 30)
    w = _even_int(ctx, overrides, "grid_w", h_lo, h_hi, 10, 30)
    n_colors = _banded_int(ctx, overrides, "n_distinct_colors",
                           c_lo, c_hi, 2, 4)
    pos = overrides.get("marker_position") or "rng"
    if pos not in MARKER_POSITIONS:
        raise ValueError(f"unknown marker_position {pos!r}; valid: {MARKER_POSITIONS}")
    if pos == "rng":
        pos = rng.choice(("band_v", "band_v", "band_v", "band_v", "band_h", "band_h", "band_h", "corner", "corner", "corner"))
    if arch:
        g = _build_arch_grid(ctx, rng, pos, n_colors)
        if g is not None:
            return g
        arch = False  # fall through to the generalized path on rare failure
    density_explicit = "sym_density" in overrides and overrides["sym_density"] is not None
    if density_explicit:
        density = float(overrides["sym_density"])
        if not 0.2 <= density <= 0.85:
            raise ValueError(f"sym_density {density} outside [0.2, 0.85]")
    else:
        density = rng.uniform(d_lo, d_hi)
    # Official-modal prior: the four official grids have modal colors {0,2,0,3}
    # (~50/25/25). Half of internal draws pin the modal to 2 or 3 and grow
    # that color past the zero share (zeros stay in the canonical 0.28..0.36
    # band); the rest keep the free modal mix. An explicit sym_density always
    # wins over this prior.
    modal_target = 0
    if not density_explicit and rng.random() < 0.5:
        modal_target = 2 if rng.random() < 0.5 else 3
    if modal_target:
        rest = list(ctx.draw_distinct_colors(
            "palette_rest", n=n_colors - 1, exclude={0, 1, 7, 9, modal_target}))
        palette = [modal_target] + rest
    else:
        palette = list(ctx.draw_distinct_colors(
            "palette", n=n_colors, exclude={0, 1, 7, 9}))

    g = full_grid(h, w, 0)
    dominant, accents = palette[0], palette[1:]
    _paint_pattern(g, rng, dominant, accents, density,
                   exact_share=density_explicit)
    _plant_missing(g, rng, accents)
    # Honor the modal/density share targets: explicit sym_density is the
    # dominant color's total coverage in BOTH modes (byte-distinct extremes);
    # the modal prior lifts its target color past the zero share.
    if density_explicit:
        _top_up_share(g, rng, dominant, density)
    elif modal_target:
        zeros_share = rng.uniform(0.28, 0.36)
        _top_up_share(g, rng, modal_target,
                      zeros_share + rng.uniform(0.04, 0.10))

    # Prefer marker spots whose reconstruction carries exactly one non-zero
    # color AND at least one zero (every official patch is {0, one color}).
    mr = mc = None
    for _try in range(60):
        cr, cc = _marker_top_left(rng, h, w, pos)
        if len(_region_colors(g, cr, cc)) == 1 and _region_zero_orbit(g, cr, cc):
            mr, mc = cr, cc
            break
    if mr is None:
        # Fallback: force a lawful spot -- paint the four mirrored 5x5 quads
        # of the chosen spot with the region's majority color, then zero one
        # cell and its mirrors (symmetry and {0, one color} both hold).
        mr, mc = _marker_top_left(rng, h, w, pos)
        counts = {}
        for r in range(mr, mr + 5):
            for c in range(mc, mc + 5):
                if g[r][c] not in (0, 1):
                    counts[g[r][c]] = counts.get(g[r][c], 0) + 1
        fill = max(counts, key=counts.get) if counts else dominant
        for (r0, c0) in ((mr, mc), (mr, w - 5 - mc),
                         (h - 5 - mr, mc), (h - 5 - mr, w - 5 - mc)):
            for r in range(r0, r0 + 5):
                for c in range(c0, c0 + 5):
                    g[r][c] = fill
        zr, zc = mr + 2, mc + 2
        for (rr, cc) in ((zr, zc), (zr, w - 1 - zc), (h - 1 - zr, zc), (h - 1 - zr, w - 1 - zc)):
            g[rr][cc] = 0
    draw_rect(g, mr, mc, 5, 5, 1)
    # The marker may have occluded the only cells of an accent color; replant
    # any missing palette color outside the marker AND its mirror quads (the
    # reconstruction inputs), so symmetry and the recovered patch are
    # untouched. Dense fields fall back to overwriting a non-protected cell.
    protected = set()
    for (r0, c0) in ((mr, mc), (mr, w - 5 - mc),
                     (h - 5 - mr, mc), (h - 5 - mr, w - 5 - mc)):
        for r in range(max(0, r0), min(h, r0 + 5)):
            for c in range(max(0, c0), min(w, c0 + 5)):
                protected.add((r, c))
    for _pass in range(8):
        present = {v for row in g for v in row} - {0, 1}
        missing = [col for col in palette if col not in present]
        if not missing:
            break
        for col in missing:
            planted = False
            for _try in range(400):
                r = rng.randint(0, h - 1)
                c = rng.randint(0, w - 1)
                spots = ((r, c), (r, w - 1 - c), (h - 1 - r, c), (h - 1 - r, w - 1 - c))
                if any(p in protected for p in spots):
                    continue
                if all(g[rr][cc] == 0 for rr, cc in spots):
                    for rr, cc in spots:
                        g[rr][cc] = col
                    planted = True
                    break
            if not planted:
                # last resort (tiny grids where every orbit touches the
                # marker): paint only the NON-MARKER cells of a majority
                # orbit with the missing accent — the majority survives, the
                # accent appears, the marker stays solid
                counts = {v: sum(row.count(v) for row in g) for v in present}
                majority = max(present, key=counts.get)
                for _try in range(400):
                    r = rng.randint(0, h - 1)
                    c = rng.randint(0, w - 1)
                    spots = ((r, c), (r, w - 1 - c), (h - 1 - r, c), (h - 1 - r, w - 1 - c))
                    if (all(g[rr][cc] in (majority, 1) for rr, cc in spots)
                            and any(g[rr][cc] == majority for rr, cc in spots)):
                        for rr, cc in spots:
                            if g[rr][cc] != 1:
                                g[rr][cc] = col
                        planted = True
                        break
    return g


_ARCH_PRIOR_PROB = 0.34


def _arch_profile(rng, n_colors):
    """Sample one official archetype profile as a closed-form count plan.
    fg is the total non-bg, non-marker cell target (zeros = 575 - fg after
    the 25 marker cells, landing inside 176..246 with a 3-cell overshoot
    margin); d is the dominant-web target with strict modal bounds."""
    n_acc = n_colors - 1
    for _ in range(30):
        modal_t = 0 if rng.random() < 0.5 else (2 if rng.random() < 0.5 else 3)
        fg = rng.randint(329, 396)
        if modal_t == 0:
            # zeros stay the strict maximum even after +3 web overshoot:
            # dominant <= 568 - fg and every accent color <= z_final - 6,
            # with the accent goals still covering the paint budget
            d_lo = max(61, 2 * fg - 569, (3 * fg - 1044 if n_colors == 3 else 0))
            d_hi = min(249, 568 - fg)
        else:
            # dominant > zeros + 24 by a margin, accents stay <= d - 4
            d_lo = max(61, 601 - fg, -(-(fg + 4 * n_acc) // n_colors))
            d_hi = 249
        if d_lo <= d_hi:
            return modal_t, n_colors, fg, rng.randint(d_lo, d_hi)
    return None


def _arch_paint_patch(g, rng, mr, mc, color, p):
    """Paint the marker's orbit-patch: group the 25 marker cells into their
    mirror orbits (band markers share orbit cells across positions, so the
    decision must be per-ORBIT), paint each orbit uniformly in `color` with
    probability p, else leave it all zero. The center position's orbit stays
    zero, so the reconstructed output always mixes color and zeros
    (canonical patches hold 4-14 zeros of 25). Returns (painted cell count,
    set of zero-orbit cells the other painters must never touch)."""
    h, w = len(g), len(g[0])
    seen = {}
    for dr in range(5):
        for dc in range(5):
            r, c = mr + dr, mc + dc
            orbit = tuple(sorted([(r, c), (r, w - 1 - c), (h - 1 - r, c), (h - 1 - r, w - 1 - c)]))
            seen.setdefault(orbit, []).append((r, c))
    center_orbit = tuple(sorted([(mr + 2, mc + 2), (mr + 2, w - 1 - mc - 2),
                                 (h - 1 - mr - 2, mc + 2), (h - 1 - mr - 2, w - 1 - mc - 2)]))
    painted = 0
    zero_orbits = set()
    for orbit in seen:
        if orbit == center_orbit or rng.random() >= p:
            zero_orbits.update(orbit)
        else:
            for (rr, cc) in orbit:
                g[rr][cc] = color
            painted += len(orbit)
    return painted, zero_orbits


def _arch_paint_web(g, rng, dominant, blocked, target):
    """Light mirrored scatter, then grow the largest dominant-color
    4-component over non-blocked cells to >= target cells (canonical largest
    non-{0,1} component 61..252, by construction one connected web)."""
    h, w = len(g), len(g[0])
    for r in range(h // 2):
        for c in range(w // 2):
            if (r, c) in blocked or rng.random() >= 0.10:
                continue
            for (rr, cc) in ((r, c), (r, w - 1 - c),
                             (h - 1 - r, c), (h - 1 - r, w - 1 - c)):
                if (rr, cc) not in blocked and g[rr][cc] == 0:
                    g[rr][cc] = dominant
    for _grow in range(600):
        big = _largest_component(g, dominant)
        if len(big) >= target:
            break
        frontier = sorted({(r + dr, c + dc) for (r, c) in big
                           for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                           if 0 <= r + dr < h and 0 <= c + dc < w
                           and (r + dr, c + dc) not in blocked
                           and g[r + dr][c + dc] == 0})
        if not frontier:
            break
        r, c = frontier[rng.randrange(len(frontier))]
        for rr, cc in ((r, c), (r, w - 1 - c), (h - 1 - r, c), (h - 1 - r, w - 1 - c)):
            if (rr, cc) not in blocked and g[rr][cc] == 0:
                g[rr][cc] = dominant


def _arch_scatter_to_goal(g, rng, accents, goals, remaining, avoid=frozenset()):
    """Paint accent orbits (mirror-symmetric, 4 cells each) until `remaining`
    cells are placed or every color hits its goal; never paints `avoid`
    cells (the preserved zero orbits of the patch). Returns painted counts."""
    h, w = len(g), len(g[0])
    counts = {c: 0 for c in accents}
    for _ in range(800):
        if remaining <= 0:
            break
        open_cols = [c for c in accents if counts[c] + 4 <= goals[c]]
        if not open_cols:
            break
        col = rng.choice(open_cols)
        r = rng.randint(0, h - 1)
        c = rng.randint(0, w - 1)
        orbit = [(r, c), (r, w - 1 - c), (h - 1 - r, c), (h - 1 - r, w - 1 - c)]
        if any(p in avoid for p in orbit):
            continue
        if any(g[rr][cc] != 0 for rr, cc in orbit):
            continue
        for rr, cc in orbit:
            g[rr][cc] = col
        counts[col] += 4
        remaining -= 4
    return counts


def _arch_ok(g):
    """Complete input-and-answer official conjunction."""
    return is_canonical_profile(g)


def _arch_repair_zeros(g, rng, z_target, accents):
    """Flip whole mirror orbits (colored->0 adds 4 zeros, 0->accent removes 4)
    until the zero count lands in [176, 246]; orbits containing marker cells
    are never touched (the recovered patch is preserved)."""
    h, w = len(g), len(g[0])
    marker = {(r, c) for r in range(h) for c in range(w) if g[r][c] == 1}
    seen = set()
    orbits = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen:
                continue
            orbit = [(r, c), (r, w - 1 - c), (h - 1 - r, c), (h - 1 - r, w - 1 - c)]
            for p in orbit:
                seen.add(p)
            if not any(p in marker for p in orbit):
                orbits.append(orbit)
    for _ in range(200):
        zeros = sum(1 for row in g for v in row if v == 0)
        if 176 <= zeros <= 246:
            return True
        if zeros < 176:
            cand = [o for o in orbits if all(g[r][c] != 0 for r, c in o)]
            if not cand:
                return False
            for r, c in cand[rng.randrange(len(cand))]:
                g[r][c] = 0
        else:
            cand = [o for o in orbits if all(g[r][c] == 0 for r, c in o)]
            if not cand:
                return False
            col = rng.choice(accents) if accents else 2
            for r, c in cand[rng.randrange(len(cand))]:
                g[r][c] = col
    return 176 <= sum(1 for row in g for v in row if v == 0) <= 246


def _build_arch_grid(ctx, rng, pos, n_colors):
    """Construct one official-archetype grid by exact count plan: reserved
    grammar spot (the web never enters it), one connected dominant web of
    canonical size, a deterministic {0, patch_color} patch as the spot's four
    mirror quads, accent orbits to exact goals, then the complete official
    conjunction verified on the returned grid."""
    h = w = 24
    for _attempt in range(8):
        prof = _arch_profile(rng, n_colors)
        if prof is None:
            return None
        modal_t, n_c, fg_target, d_target = prof
        if modal_t:
            dominant = modal_t
            accents = list(ctx.draw_distinct_colors(
                "arch_palette_rest", n=n_c - 1, exclude={0, 1, 7, 9, modal_t}))
        else:
            cols = list(ctx.draw_distinct_colors(
                "arch_palette", n=n_c, exclude={0, 1, 7, 9}))
            dominant, accents = cols[0], cols[1:]
        patch_color = accents[0]
        g = full_grid(h, w, 0)
        spot = _marker_top_left(rng, h, w, pos)
        blocked = {(r, c) for r in range(spot[0], spot[0] + 5)
                   for c in range(spot[1], spot[1] + 5)}
        # deterministic {0, patch_color} orbit patch over the spot's mirror
        # quads (each painted orbit is uniformly colored; the center position
        # stays zero so the reconstructed output keeps at least one zero)
        mr, mc = spot
        fill_n, zero_orbits = _arch_paint_patch(g, rng, mr, mc, patch_color,
                                                rng.uniform(0.55, 0.85))
        # accent orbits to exact goals FIRST (empty field, easy placement),
        # then the dominant web grows into the leftover space; both avoid the
        # patch's preserved zero orbits
        if modal_t:
            goals = {c: d_target - 4 for c in accents}
            goals[patch_color] = d_target - 4 - fill_n
        else:
            z_final = 575 - fg_target
            goals = {c: z_final - 6 for c in accents}
            goals[patch_color] = z_final - 6 - fill_n
        remaining = fg_target - fill_n - d_target
        _arch_scatter_to_goal(g, rng, accents, goals, remaining, avoid=zero_orbits)
        _arch_paint_web(g, rng, dominant, blocked | zero_orbits, d_target)
        draw_rect(g, mr, mc, 5, 5, 1)
        _plant_missing(g, rng, accents, protected=zero_orbits)
        if _arch_ok(g):
            return g
    return None


def _region_colors(g, r0, c0):
    """Non-zero colors under a 5x5 marker at (r0, c0) -- what the oracle
    reconstructs when every cell's mirror chain resolves (symmetric field)."""
    return {g[r][c] for r in range(r0, r0 + 5) for c in range(c0, c0 + 5)
            if g[r][c] not in (0, 1)}


def _region_has_zero(g, r0, c0):
    return any(g[r][c] == 0 for r in range(r0, r0 + 5)
               for c in range(c0, c0 + 5))


def _region_zero_orbit(g, r0, c0):
    """Some cell in the region whose whole mirror orbit is zero — so the
    reconstructed output keeps at least one zero cell (no solid-single-color
    output collapse)."""
    h, w = len(g), len(g[0])
    for r in range(r0, r0 + 5):
        for c in range(c0, c0 + 5):
            if all(g[rr][cc] == 0 for rr, cc in
                   ((r, c), (r, w - 1 - c), (h - 1 - r, c), (h - 1 - r, w - 1 - c))):
                return True
    return False


def _paint_coarse_tiles(g, rng, palette):
    """Canonical-prior field: a few large single-color symmetric blocks per
    quadrant over a 0 background, so most 5x5 regions are monochrome."""
    h, w = len(g), len(g[0])
    for _ in range(rng.randint(2, 4)):
        col = palette[0] if rng.random() < 0.6 else rng.choice(palette)
        th = rng.randint(2, 5)
        tw = rng.randint(2, 5)
        r0 = rng.randint(0, h // 2 - th)
        c0 = rng.randint(0, w // 2 - tw)
        for r in range(r0, r0 + th):
            for c in range(c0, c0 + tw):
                for (rr, cc) in ((r, c), (r, w - 1 - c),
                                 (h - 1 - r, c), (h - 1 - r, w - 1 - c)):
                    g[rr][cc] = col


def _paint_pattern(g, rng, dominant, accents, density, exact_share=False):
    """Canonical texture: one dominant color forming a large connected
    symmetric web (canonical largest-object 61..252 cells, up to 44% of the
    grid, sometimes modal) plus small accents; zero fraction ~0.3. Per-cell
    assignment is mirrored through the quadrant; the dominant web is then
    grown symmetrically until its largest component reaches a canonical-size
    target, so connectivity is guaranteed rather than hoped for. With an
    explicit sym_density the growth target IS the requested share, so the
    extreme settings execute exactly."""
    h, w = len(g), len(g[0])
    p_dom = density
    p_acc = rng.uniform(0.04, 0.10) if accents else 0.0
    for r in range(h // 2):
        for c in range(w // 2):
            u = rng.random()
            if u < p_dom:
                col = dominant
            elif u < p_dom + p_acc:
                col = rng.choice(accents) if accents else 0
            else:
                continue
            for (rr, cc) in ((r, c), (r, w - 1 - c),
                             (h - 1 - r, c), (h - 1 - r, w - 1 - c)):
                g[rr][cc] = col
    # grow the dominant web until its largest component hits the target size
    if exact_share:
        target = int(density * h * w)
    else:
        u = rng.random()
        target = int(rng.uniform(130, 260)) if u < 0.25 else int(rng.uniform(55, 130))
    for _grow in range(400):
        big = _largest_component(g, dominant)
        if len(big) >= target:
            break
        frontier = sorted({(r + dr, c + dc) for (r, c) in big
                           for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                           if 0 <= r + dr < h and 0 <= c + dc < w
                           and g[r + dr][c + dc] == 0})
        if not frontier:
            break
        r, c = frontier[rng.randrange(len(frontier))]
        spots = [(r, c), (r, w - 1 - c), (h - 1 - r, c), (h - 1 - r, w - 1 - c)]
        for rr, cc in spots:
            if g[rr][cc] != 1:
                g[rr][cc] = dominant
    # guarantee every accent color is visible (n_distinct_colors is exact)
    present = {v for row in g for v in row} - {0}
    for col in accents:
        if col in present:
            continue
        for _try in range(60):
            r = rng.randint(0, h // 2 - 1)
            c = rng.randint(0, w // 2 - 1)
            spots = ((r, c), (r, w - 1 - c), (h - 1 - r, c), (h - 1 - r, w - 1 - c))
            if all(g[rr][cc] == 0 for rr, cc in spots):
                for rr, cc in spots:
                    g[rr][cc] = col
                break


def _top_up_share(g, rng, color, share):
    """Flip mirrored zero cells to `color` until its total coverage reaches
    `share` of the grid (explicit sym_density semantics and the official
    modal prior). Only zeros are touched, so accents stay visible."""
    h, w = len(g), len(g[0])
    target = int(share * h * w)
    for _ in range(h * w * 2):
        have = sum(1 for row in g for v in row if v == color)
        if have >= target:
            return
        zeros = [(r, c) for r in range(h) for c in range(w) if g[r][c] == 0]
        if not zeros:
            return
        r, c = zeros[rng.randrange(len(zeros))]
        for rr, cc in ((r, c), (r, w - 1 - c), (h - 1 - r, c), (h - 1 - r, w - 1 - c)):
            if g[rr][cc] == 0:
                g[rr][cc] = color


def _largest_component(g, color):
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    best = []
    for r in range(h):
        for c in range(w):
            if g[r][c] != color or seen[r][c]:
                continue
            stack, cells = [(r, c)], []
            seen[r][c] = True
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and g[nr][nc] == color):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            if len(cells) > len(best):
                best = cells
    return best


def _plant_missing(g, rng, colors, protected=frozenset()):
    """Guarantee every palette color is visible (n_distinct_colors exact):
    plant any unused color on a free quadrant cell and its mirrors. Cells in
    `protected` (the patch's preserved zero orbits) are never touched."""
    present = {v for row in g for v in row} - {0}
    h, w = len(g), len(g[0])
    for col in colors:
        if col in present:
            continue
        planted = False
        for _try in range(60):
            r = rng.randint(0, h // 2 - 1)
            c = rng.randint(0, w // 2 - 1)
            spots = ((r, c), (r, w - 1 - c), (h - 1 - r, c), (h - 1 - r, w - 1 - c))
            if any(p in protected for p in spots):
                continue
            if all(g[rr][cc] == 0 for rr, cc in spots):
                for rr, cc in spots:
                    g[rr][cc] = col
                planted = True
                break
        if not planted:
            # last resort (tiny grids where every orbit touches the marker):
            # paint only the NON-MARKER cells of a majority orbit with the
            # missing accent; protected zero orbits stay untouched
            counts = {v: sum(row.count(v) for row in g) for v in present}
            majority = max(present, key=counts.get)
            for _try in range(400):
                r = rng.randint(0, h - 1)
                c = rng.randint(0, w - 1)
                spots = ((r, c), (r, w - 1 - c), (h - 1 - r, c), (h - 1 - r, w - 1 - c))
                if any(p in protected for p in spots):
                    continue
                if (all(g[rr][cc] in (majority, 1) for rr, cc in spots)
                        and any(g[rr][cc] == majority for rr, cc in spots)):
                    for rr, cc in spots:
                        if g[rr][cc] != 1:
                            g[rr][cc] = col
                    planted = True
                    break


def _draw_from_degenerate(name, rng):
    h = w = 24
    g = full_grid(h, w, 0)
    if name == "dense_field":
        for r in range(h // 2):
            for c in range(w // 2):
                if rng.random() < 0.8:
                    col = rng.choice((2, 3, 5))
                    for (rr, cc) in ((r, c), (r, w - 1 - c),
                                     (h - 1 - r, c), (h - 1 - r, w - 1 - c)):
                        g[rr][cc] = col
        draw_rect(g, 10, 0, 5, 5, 1)   # h-band marker flush left
        return g
    raise ValueError(f"unknown edge texture {name!r}")
