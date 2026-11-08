"""Generator for 3143493b7c83 (ARC task 15113be4).

Rule: the input is a 4-line-separated lattice of 3x3 cells filled with 0/1
noise, plus one MARKER: an 8x8 box with 4-walls whose 6x6 interior holds a
2x-upscaled KEY bitmap (th x tw cells, th/tw in 2..3) in the unique
non-{0,1,4} color, top-aligned with the off-key area cleared to 0.  The rule
recovers the key by halving the marker bbox, then for every 4-aligned
lattice cell whose 1-cells contain the key bitmap at the same offsets,
recolors those 1-cells to the marker color.

Combinatorial axes (8): cells_r, cells_c (lattice size, grid = 4n-1; the
default draw is the canonical 23x23 6x6 lattice 60% of the time, per the
official inputs), key_h, key_w (key bitmap dims from the official
2x3/3x2/3x3 family; 2x2 only via exact override), n_matches (planted
key-containing cells), marker_color, decoy_mode (near-miss decoy cells),
corner_box (marker box anchored in a grid corner, the canonical placement
in all four official inputs, vs free interior placement as the
generalization share).

Branches exercised: key shapes spanning their th x tw box (incl. thin 2x3 /
3x2 and diagonal keys), matching cells embedded in noise, near-miss decoy
cells (one key cell missing), empty and dense cells, marker box overlapping
cells and separator lines, all 7 lawful marker colors.

Degenerate textures: none.  A no-marker / two-marker / no-match variant is
either oracle-crashing, ambiguous under the rule's first-non-{0,1,4} pick,
or contrary to the canonical domain (every canonical pair recolors cells),
so no texture axis is declared (KRF-0001).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3143493b7c83"
VERSION = "3.1.0"  # morphology veto fix: default-only archetype prior (0.32,
# all bands) constructing complete official profiles - 6x6 lattice, corner
# box, one of the four executably extracted official key bitmaps, official
# density 95..142/288, n_matches 2..4 - while generalized draws retain band
# sizes and random spanning keys (KRF-0003 morphology class).
TASK_ID = "3143493b7c83"
RULE_HASH = "1e21086e1719"
SUMMARY = (
    "4-separated lattice of noisy 3x3 cells; the unique non-{0,1,4} marker "
    "is a 2x-upscaled key bitmap in a walled 8x8 box; lattice cells whose "
    "1-pattern contains the key are recolored to the marker color."
)

INVARIANTS = [
    "grid size is 4n-1 x 4m-1 (3x3 cells separated by full 4-lines)",
    "outside the marker box, separator lines are solid 4 and cell interiors "
    "use only 0/1",
    "exactly one marker color (not 0, 1, or 4); its cells form a clean "
    "2x-upscaled key bitmap (each 2x2 block of its bbox is solid marker or "
    "solid 0), key dims in 2..3 and spanning its box",
    "the marker sits in an 8x8 box (6x6 interior, top-aligned stamp) with "
    "solid 4 walls",
    "at least one lattice cell's 1-pattern contains the key",
]

PALETTE_KINDS: tuple = ()
DEGENERATE_TEXTURES: tuple = ()
HELPFUL_TEXTURES: tuple = ()

AXES = {
    "cells_r":      {"type": "int", "default": "band rng 4..6",
                     "valid": "4..7"},
    "cells_c":      {"type": "int", "default": "band rng 4..6",
                     "valid": "4..7"},
    "key_h":        {"type": "int", "default": "band pair set (official "
                     "2x3/3x2/3x3 family)", "valid": "2..3"},
    "key_w":        {"type": "int", "default": "band pair set (official "
                     "2x3/3x2/3x3 family)", "valid": "2..3"},
    "n_matches":    {"type": "int", "default": "band rng 1..3",
                     "valid": "1..4"},
    "marker_color": {"type": "color", "default": "rng !{0,1,4}",
                     "valid": "2|3|5|6|7|8|9"},
    "decoy_mode":   {"type": "str",
                     "default": "band rng subset (near-miss decoy cells)",
                     "valid": "none|few|several"},
    "corner_box":   {"type": "bool",
                     "default": "rng p=0.8 true (canonical grid-corner "
                                "marker box)",
                     "valid": "true|false"},
}

DECOY_MODES = ("none", "few", "several")
_DECOY_COUNT = {"none": 0, "few": 1, "several": 3}

_CELLS_LO, _CELLS_HI = 4, 7     # lattice cells per side; grid = 4n-1 (15..27)
_KEY_LO, _KEY_HI = 2, 3
_MATCH_LO, _MATCH_HI = 1, 4
_BOX = 6                        # marker interior is always _BOX x _BOX

# The four official key bitmaps, executably extracted from the canonical
# inputs with ONE extractor (halve the unique marker color's bbox, collect
# the solid 2x2 blocks).  D4 is lawful for this oracle (rot90/fliplr
# commute through the bridge), so D4 variants are nuisance, but the
# headline official shapes are these exact bitmaps.
OFFICIAL_KEYS = (
    ((2, 3), ((0, 0), (0, 2), (1, 1))),
    ((3, 3), ((0, 2), (1, 0), (1, 1), (2, 1))),
    ((3, 3), ((0, 0), (1, 1), (2, 2))),
    ((3, 3), ((0, 2), (1, 0), (1, 1), (1, 2), (2, 0))),
)
# Official ordinary-cell 1-density: 95..142 marks over the 288 box-clear
# lattice positions (the four official values are 95/119/121/142).
_DENSITY_LO, _DENSITY_HI = 95, 142
# Default-only archetype prior (morphology veto fix): share of default
# draws on every band that constructs the complete official profile.
_ARCHETYPE_P = 0.32


def _parse_stamp(grid):
    """Locate and validate the marker stamp.  Returns (errs, info) where info
    is (sp, r0, c0, th, tw, key) on success."""
    h, w = len(grid), len(grid[0])
    sp_colors = sorted({v for row in grid for v in row if v not in (0, 1, 4)})
    if len(sp_colors) != 1:
        return ([f"expected exactly one marker color, found {len(sp_colors)}"],
                None)
    sp = sp_colors[0]
    cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == sp]
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    bh, bw = r1 - r0 + 1, c1 - c0 + 1
    if bh % 2 or bw % 2:
        return [f"marker bbox {bh}x{bw} is not a clean 2x upscale"], None
    th, tw = bh // 2, bw // 2
    errs = []
    if th not in (2, 3) or tw not in (2, 3):
        errs.append(f"key dims {th}x{tw} outside 2..3")
    key = []
    for tr in range(th):
        for tc in range(tw):
            blk = {grid[r0 + 2 * tr + dr][c0 + 2 * tc + dc]
                   for dr in range(2) for dc in range(2)}
            if blk == {sp}:
                key.append((tr, tc))
            elif blk != {0}:
                errs.append(f"marker block ({tr},{tc}) is not solid 0/{sp}")
    rows_used = {tr for tr, _ in key}
    cols_used = {tc for _, tc in key}
    if len(rows_used) != th or len(cols_used) != tw:
        errs.append("key does not span its box")
    if len(key) < 3:
        errs.append(f"key has only {len(key)} cell(s); canonical keys have >=3")
    if errs:
        return errs, None
    return [], (sp, r0, c0, th, tw, key)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance: a grid in the declared
    15/19/23/27 envelope (4n-1 lattice sizes) whose 3x3 cells hold only 0/1
    and whose separator lines are solid 4, plus exactly one marker color
    forming a clean spanning 2x key stamp inside a walled 8x8 box.  Zero
    marker colors crashes the oracle's first-color pick, several make it
    ambiguous, and a broken stamp makes the recovered key ill-defined, so
    all are rejected; grids with 2/4-recolored cells (outputs), torn
    separators, or off-envelope sizes (11, 31) are rejected too."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h not in (15, 19, 23, 27) or w not in (15, 19, 23, 27):
        errs.append(f"grid {h}x{w} outside declared 15/19/23/27 envelope")
    if any(not 0 <= v <= 9 for row in grid for v in row):
        errs.append("color outside 0..9")
    stamp_errs, info = _parse_stamp(grid)
    errs.extend(stamp_errs)
    if info is None:
        return errs
    sp, r0, c0, th, tw, key = info
    # Marker box: 8x8 with 4 walls around the 6x6 interior at (r0, c0).
    if r0 < 1 or c0 < 1 or r0 + _BOX >= h or c0 + _BOX >= w:
        errs.append("marker box walls do not fit inside the grid")
        return errs
    wall_broken = 0
    for rr in range(r0 - 1, r0 + _BOX + 1):
        for cc in (c0 - 1, c0 + _BOX):
            if grid[rr][cc] != 4:
                wall_broken += 1
    for cc in range(c0 - 1, c0 + _BOX + 1):
        for rr in (r0 - 1, r0 + _BOX):
            if grid[rr][cc] != 4:
                wall_broken += 1
    if wall_broken:
        errs.append(f"marker box wall broken at {wall_broken} cell(s)")
    # Scene integrity outside the box; interior beyond the stamp stays {0,sp}.
    for rr in range(h):
        for cc in range(w):
            v = grid[rr][cc]
            on_wall = ((rr in (r0 - 1, r0 + _BOX) and
                        c0 - 1 <= cc <= c0 + _BOX) or
                       (cc in (c0 - 1, c0 + _BOX) and
                        r0 - 1 <= rr <= r0 + _BOX))
            in_interior = (r0 <= rr < r0 + _BOX and c0 <= cc < c0 + _BOX)
            if in_interior:
                if v not in (0, sp):
                    errs.append(f"marker interior cell ({rr},{cc}) is {v}, "
                                f"expected 0/{sp}")
            elif on_wall:
                pass  # covered by the wall check
            else:
                on_sep = rr % 4 == 3 or cc % 4 == 3
                if on_sep and v != 4:
                    errs.append(f"separator broken at ({rr},{cc})")
                elif not on_sep and v not in (0, 1):
                    errs.append(f"cell ({rr},{cc}) holds {v}, expected 0/1")
            if len(errs) > 12:
                return errs
    return errs


def _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    """Band-shaped random draw; overrides validated against the full valid
    range (an override must execute on any band, per the AXES contract)."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, lo, hi)


def _draw_key(rng, th, tw, k_lo, k_hi):
    """A random th x tw bitmap that spans its whole box."""
    spots = [(tr, tc) for tr in range(th) for tc in range(tw)]
    for _ in range(40):
        k = rng.randint(k_lo, min(k_hi, th * tw - 1))
        key = rng.sample(spots, k)
        if len({tr for tr, _ in key}) == th and len({tc for _, tc in key}) == tw:
            return key
    # deterministic fallback: three corners always span the box
    return [(0, 0), (th - 1, tw - 1), (0, tw - 1)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    overrides = dict(overrides)
    if overrides.get("corner_box") is not None:
        raw = overrides["corner_box"]
        overrides["corner_box"] = (raw if isinstance(raw, bool)
                                   else str(raw).strip().lower()
                                   in ("1", "true", "yes"))
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    band = difficulty or "medium"
    if band == "easy":
        c_lo, c_hi, k_pairs, p, m_lo, m_hi, d_opts = \
            4, 5, [(2, 3), (3, 2)], 0.35, 1, 2, ["none", "few"]
    elif band == "hard":
        c_lo, c_hi, k_pairs, p, m_lo, m_hi, d_opts = \
            6, 7, [(3, 3)], 0.50, 2, 4, ["few", "several"]
    else:
        c_lo, c_hi, k_pairs, p, m_lo, m_hi, d_opts = \
            5, 6, [(2, 3), (3, 2), (3, 3)], 0.42, 2, 3, ["few", "several"]
    # Canonical prior (KRF-0003): all four official inputs are 23x23 with
    # 2x3/3x3 keys, so the default draw is the canonical 6x6 lattice 60% of
    # the time; band-specific sizes are the generalization share.  Exact
    # overrides always win over the prior.
    cr_pinned = "cells_r" in overrides and overrides["cells_r"] is not None
    cc_pinned = "cells_c" in overrides and overrides["cells_c"] is not None
    rng = ctx.draw_rng("layout")
    # Morphology archetype prior (veto fix): default-only, all bands.  Any
    # shape override bypasses it and stays exact; the generalized share
    # keeps band sizes and random spanning keys.
    shape_override = any(
        overrides.get(k) is not None
        for k in ("cells_r", "cells_c", "key_h", "key_w", "n_matches",
                  "corner_box", "marker_color"))
    archetype = not shape_override and rng.random() < _ARCHETYPE_P
    if archetype:
        nr = ctx.draw_int("cells_r", 6, 6)
        nc = ctx.draw_int("cells_c", 6, 6)
    elif not cr_pinned and not cc_pinned and rng.random() < 0.6:
        nr = ctx.draw_int("cells_r", 6, 6)
        nc = ctx.draw_int("cells_c", 6, 6)
    else:
        nr = _banded_int(ctx, overrides, "cells_r", c_lo, c_hi,
                         _CELLS_LO, _CELLS_HI)
        nc = _banded_int(ctx, overrides, "cells_c", c_lo, c_hi,
                         _CELLS_LO, _CELLS_HI)
    kh_pinned = "key_h" in overrides and overrides["key_h"] is not None
    kw_pinned = "key_w" in overrides and overrides["key_w"] is not None
    official_key = None
    if archetype:
        (th, tw), official_key = OFFICIAL_KEYS[
            rng.randrange(len(OFFICIAL_KEYS))]
        th = ctx.draw_int("key_h", th, th)
        tw = ctx.draw_int("key_w", tw, tw)
    elif kh_pinned or kw_pinned:
        th = _banded_int(ctx, overrides, "key_h", _KEY_LO, _KEY_HI,
                         _KEY_LO, _KEY_HI)
        tw = _banded_int(ctx, overrides, "key_w", _KEY_LO, _KEY_HI,
                         _KEY_LO, _KEY_HI)
    else:
        th, tw = k_pairs[rng.randrange(len(k_pairs))]
        th = ctx.draw_int("key_h", th, th)
        tw = ctx.draw_int("key_w", tw, tw)
    if archetype:
        n_match = ctx.draw_int("n_matches", 2, 4)
        p = rng.randint(_DENSITY_LO, _DENSITY_HI) / 288.0
    else:
        n_match = _banded_int(ctx, overrides, "n_matches", m_lo, m_hi,
                              _MATCH_LO, _MATCH_HI)
    sp = ctx.draw_color("marker_color", exclude=(0, 1, 4))
    if "decoy_mode" in overrides and overrides["decoy_mode"] is not None:
        decoy_mode = ctx.draw_choice("decoy_mode", list(DECOY_MODES))
    else:
        decoy_mode = ctx.draw_choice("decoy_mode", d_opts)
    n_decoys = _DECOY_COUNT[decoy_mode]
    h, w = 4 * nr - 1, 4 * nc - 1

    # Marker box position first (so planted cells avoid its footprint); the
    # whole 8x8 box stays in-grid, as in every canonical pair.  All four
    # official inputs anchor the box in a grid corner (interior at (1,1),
    # (1,w-7), (h-7,1), or (h-7,w-7), walls on grid edges/separators), so
    # corner placement is the dominant default and free interior placement
    # the documented generalization share.
    if "corner_box" in overrides and overrides["corner_box"] is not None:
        corner = ctx.draw_choice("corner_box", [False, True])
    elif archetype:
        # Archetype profile: marker box anchored in a grid corner, exactly
        # as in every official input (KRF-0004: recorded under the label).
        corner = ctx.draw_choice("corner_box", [True])
    else:
        # KRF-0004: the default path also records the realized value under
        # the declared axis label (weighted 80/20 corner prior).
        corner = ctx.draw_choice("corner_box",
                                 [True, True, True, True, False])
    if corner:
        r0 = rng.choice([1, h - _BOX - 1])
        c0 = rng.choice([1, w - _BOX - 1])
    else:
        # corner_box=False is exact: never place on a corner anchor.
        corners = {(1, 1), (1, w - _BOX - 1), (h - _BOX - 1, 1),
                   (h - _BOX - 1, w - _BOX - 1)}
        spots = [(r, c) for r in range(1, h - _BOX)
                 for c in range(1, w - _BOX) if (r, c) not in corners]
        r0, c0 = spots[rng.randrange(len(spots))]

    def box_touches(rs, cs):
        return not (rs + 2 < r0 - 1 or rs > r0 + _BOX or
                    cs + 2 < c0 - 1 or cs > c0 + _BOX)

    free = [(rs, cs) for rs in range(0, h, 4) for cs in range(0, w, 4)
            if not box_touches(rs, cs)]
    rng.shuffle(free)
    if len(free) < n_match + n_decoys:
        raise ValueError(
            f"cannot plant {n_match} matches + {n_decoys} decoys: only "
            f"{len(free)} lattice cells clear of the marker box on a "
            f"{nr}x{nc} lattice")

    if archetype and official_key is not None:
        key = [tuple(cell) for cell in official_key]
    else:
        key = _draw_key(rng, th, tw, 3, 5 if th * tw >= 6 else 4)
    keyset = set(key)

    g = full_grid(h, w, 0)
    # Separator lines.
    for rr in range(3, h, 4):
        for cc in range(w):
            g[rr][cc] = 4
    for cc in range(3, w, 4):
        for rr in range(h):
            g[rr][cc] = 4
    # Random 1-noise in every cell.
    def fill_noise(rs, cs):
        for dr in range(3):
            for dc in range(3):
                if rng.random() < p:
                    g[rs + dr][cs + dc] = 1
    for rs in range(0, h, 4):
        for cs in range(0, w, 4):
            fill_noise(rs, cs)
    # Plant matches (key embedded in extra noise) and near-miss decoys in
    # cells the marker box does not touch.
    fi = 0
    planted = set()
    for _ in range(n_match):
        rs, cs = free[fi]; fi += 1
        planted.add((rs, cs))
        for dr in range(3):
            for dc in range(3):
                g[rs + dr][cs + dc] = 1 if ((dr, dc) in keyset
                                            or rng.random() < p) else 0
    for _ in range(n_decoys):
        if fi >= len(free):
            break
        rs, cs = free[fi]; fi += 1
        miss = key[rng.randrange(len(key))]
        for dr in range(3):
            for dc in range(3):
                if (dr, dc) == miss:
                    g[rs + dr][cs + dc] = 0
                elif (dr, dc) in keyset:
                    g[rs + dr][cs + dc] = 1
                else:
                    g[rs + dr][cs + dc] = 1 if rng.random() < p else 0
    # Marker box: 4-walls, cleared 6x6 interior, 2x key stamp at the
    # interior's top-left (the canonical train[1] layout for short keys).
    for rr in range(r0 - 1, r0 + _BOX + 1):
        g[rr][c0 - 1] = 4
        g[rr][c0 + _BOX] = 4
    for cc in range(c0 - 1, c0 + _BOX + 1):
        g[r0 - 1][cc] = 4
        g[r0 + _BOX][cc] = 4
    for rr in range(r0, r0 + _BOX):
        for cc in range(c0, c0 + _BOX):
            g[rr][cc] = 0
    for tr, tc in key:
        for dr in range(2):
            for dc in range(2):
                g[r0 + 2 * tr + dr][c0 + 2 * tc + dc] = sp
    # Match audit: n_matches is an exact realized count (see
    # observe_overrides), so accidental matches in noise cells are removed.
    # A matching cell always has every key position outside the box
    # footprint (box cells are never 1), so one of them can be cleared.
    for rs in range(0, h, 4):
        for cs in range(0, w, 4):
            if (rs, cs) in planted:
                continue
            if not all(g[rs + tr][cs + tc] == 1 for tr, tc in key):
                continue
            for tr, tc in key:
                rr, cc = rs + tr, cs + tc
                if not (r0 - 1 <= rr <= r0 + _BOX and
                        c0 - 1 <= cc <= c0 + _BOX):
                    g[rr][cc] = 0
                    break
    if archetype:
        # Archetype profile: ordinary-cell 1-density lands inside the
        # official 95..142/288 range exactly.  Only non-key-offset cell
        # positions are flipped, so every cell's key-containment status
        # (planted matches and accidental non-matches) is preserved.
        eligible = [(rs + dr, cs + dc)
                    for rs in range(0, h, 4) for cs in range(0, w, 4)
                    if not box_touches(rs, cs)
                    for dr in range(3) for dc in range(3)
                    if (dr, dc) not in keyset]

        def marks_now():
            return sum(
                g[rs + dr][cs + dc] == 1
                for rs in range(0, h, 4) for cs in range(0, w, 4)
                if not box_touches(rs, cs)
                for dr in range(3) for dc in range(3))
        for _ in range(200):
            marks = marks_now()
            if _DENSITY_LO <= marks <= _DENSITY_HI:
                break
            if marks < _DENSITY_LO:
                zeros = [(rr, cc) for rr, cc in eligible if g[rr][cc] != 1]
                if not zeros:
                    break
                rr, cc = zeros[rng.randrange(len(zeros))]
                g[rr][cc] = 1
            else:
                ones = [(rr, cc) for rr, cc in eligible if g[rr][cc] == 1]
                if not ones:
                    break
                rr, cc = ones[rng.randrange(len(ones))]
                g[rr][cc] = 0
    return g


def observe_overrides(grid):
    """Realized per-draw values of the exact semantic axes (wave-3 override
    contract): lattice size, key dims, marker color, the number of lattice
    cells whose 1-pattern contains the key, and whether the marker box sits
    in a grid corner (the canonical anchor)."""
    errs, info = _parse_stamp(grid)
    if errs or info is None:
        return {}
    sp, r0, c0, th, tw, key = info
    h, w = len(grid), len(grid[0])
    n = 0
    for rs in range(0, h, 4):
        for cs in range(0, w, 4):
            if all(rs + tr < h and cs + tc < w and
                   grid[rs + tr][cs + tc] == 1 for tr, tc in key):
                n += 1
    corners = {(1, 1), (1, w - _BOX - 1), (h - _BOX - 1, 1),
               (h - _BOX - 1, w - _BOX - 1)}
    return {"cells_r": (h + 1) // 4, "cells_c": (w + 1) // 4,
            "key_h": th, "key_w": tw, "n_matches": n, "marker_color": sp,
            "corner_box": (r0, c0) in corners}
