"""Generator for 2037f2c7 — two aligned figures, mark zero/nonzero disagreements.

Rule: take the top two big (>5 cell) 8-connected multicolor objects, crop each
to its bbox (f1 = upper, f2 = lower, same dims); output has one row per row
where the two crops DIFFER IN VALUE, and in such a row marks 8 at columns
where EXACTLY ONE crop is zero (zero/nonzero xor), else 0.

Canonical form: the two figures are the SAME picture built from coherent
color regions (same-color 4-component count 13..32 per grid), 8-15 x 6-10
bbox, 2-6 colors excluding 8, fill 0.667..0.924, with zero-set edits in
exactly 2-4 rows carrying 1..7 xor marks each (every official scene has at
least one multi-mark row).  This generator emits that manifold: a Voronoi
color-region picture, per-row multi-cell zero-set edits (new holes and
repairs), a full-pair archetype prior over the four observed linked figure
occupancy/XOR morphologies, and two separated 8-connected placements, the
top one first.
Textures: min_diff, dense_pair, sparse_pair (all rule-valid).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f4a707214fb5"
VERSION = "3.3.0"
# FEASIBLE domain given the keyed grid (the old retry redrew the same infeasible
# 15x10 via the deterministic label); (2) diff rows carry 1..7 xor marks via
# multi-cell zero-set edits with a guaranteed multi-mark row (was exactly one
# edit per row); (3) coherent Voronoi color regions replace cellwise speckle
# (same-color 4-comps 13..32 canonical vs 41..175 speckle); (4) exact-profile
# prior over the four observed joint canonical profiles at >=25% per band;
# self_check now enforces declared n_colors 2..6 and n_diff_rows 1..6.
# 3.0.0: canonical manifold rewrite (shared picture + structural self_check +
# observe_overrides + pinned RULE_HASH).
TASK_ID = "f4a707214fb5"
RULE_HASH = "1c036934c687"
SUMMARY = "Two same-dim crops of one picture; mark zero/nonzero disagreements in differing rows."

INVARIANTS = [
    "exactly two 8-connected objects, both larger than 5 cells, with "
    "identical bbox dimensions; the upper one comes first",
    "at every position nonzero in both crops, the two colors are equal "
    "(one shared picture), so value-differing rows are exactly the "
    "zero-pattern-differing rows",
    "the two crops' zero-sets differ in exactly n_diff_rows (1..6) rows, "
    "each carrying 1..7 xor marks, with at least one multi-mark row",
    "the picture uses 2..6 coherent color regions excluding 8 (the output "
    "mark color); same-color 4-component count stays in the canonical "
    "13..32 neighborhood",
]

DEGENERATE_TEXTURES = ("min_diff", "dense_pair", "sparse_pair")

AXES = {
    "grid_h":        {"type": "int", "default": "band rng 20..30",
                      "valid": "20..30"},
    "grid_w":        {"type": "int", "default": "band rng 20..30",
                      "valid": "20..30"},
    "figure_height": {"type": "int", "default": "band 8..11 easy, 8..13 "
                      "medium, 10..15 hard; feasible-domain draw",
                      "valid": "6..15"},
    "figure_width":  {"type": "int", "default": "band 6..8 easy, 6..9 "
                      "medium, 7..10 hard; feasible-domain draw",
                      "valid": "6..10"},
    "n_diff_rows":   {"type": "int", "default": "band 1..2 easy, 2..3 "
                      "medium, 2..4 hard", "valid": "1..6"},
    "n_colors":      {"type": "int", "default": "band 2..3 easy, 3..5 "
                      "medium, 4..6 hard", "valid": "2..6"},
    "texture":       {"type": "str", "default": "none (plain draw)",
                      "valid": "none|min_diff|dense_pair|sparse_pair"},
}

_DIRS8 = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
               if (dr, dc) != (0, 0))
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_VALID_H = (20, 30)
_VALID_W = (20, 30)
_VALID_FH = (6, 15)
_VALID_FW = (6, 10)
_VALID_DIFF = (1, 6)
_VALID_NC = (2, 6)
_MARK = 8
# Full linked public archetypes.  Row strings are the two figure crops in
# top-to-bottom order.  Color labels are nuisances and are remapped on every
# draw; shared horizontal/vertical reflection is also a lawful nuisance.
# Keeping both occupancies (rather than only their marginal dimensions,
# fills, and component counts) preserves the answer-bearing row-wise XOR.
_CANONICAL_ARCHETYPES = (
    (25, 25, (
        "00444400",
        "11466411",
        "33333333",
        "13466431",
        "10466400",
        "00006000",
        "13066430",
        "11466410",
        "24477442",
        "24477442",
        "20077002",
    ), (
        "00444400",
        "11466411",
        "33333333",
        "13466431",
        "13466431",
        "13466431",
        "13466431",
        "11466411",
        "24477442",
        "24477442",
        "20077002",
    )),
    (23, 25, (
        "0044400",
        "3346433",
        "3246423",
        "3246423",
        "3246423",
        "3246423",
        "3246423",
        "3246423",
        "3246423",
        "3246423",
        "3246423",
        "3246423",
        "3246423",
        "3346433",
        "0044400",
    ), (
        "0044400",
        "3346433",
        "3246423",
        "3246423",
        "3246423",
        "3246423",
        "3246423",
        "3246423",
        "3246423",
        "0246420",
        "0046400",
        "0246420",
        "3246423",
        "3346433",
        "0044400",
    )),
    (22, 22, (
        "333333",
        "444444",
        "033330",
        "237732",
        "237732",
        "237732",
        "037730",
        "033330",
    ), (
        "333333",
        "444444",
        "033330",
        "237732",
        "237732",
        "000700",
        "030730",
        "033330",
    )),
    (24, 25, (
        "0111001110",
        "0044664400",
        "3142662413",
        "0042660000",
        "0012662100",
        "0002222000",
        "0111111110",
        "0133333310",
        "0111111110",
    ), (
        "0111001110",
        "0044664400",
        "3142662413",
        "3142662413",
        "3112662113",
        "0002222000",
        "0111111110",
        "0133333310",
        "0111111110",
    )),
)
_PROFILE_PRIOR = 0.3
_MARK_WEIGHTS = [(1, 0.20), (2, 0.27), (3, 0.10), (4, 0.18), (5, 0.10),
                 (6, 0.10), (7, 0.05)]


def _validate_call(difficulty, overrides):
    """Reject unsupported controls rather than coercing or falling through."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in (
        "grid_h", "grid_w", "figure_height", "figure_width",
        "n_diff_rows", "n_colors",
    ):
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise ValueError(f"{label} must be an integer")
    value = overrides.get("texture")
    if value is not None and not isinstance(value, str):
        raise ValueError("texture must be a string")


def _components8(grid):
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
                for dr, dc in _DIRS8:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and grid[nr][nc] != 0):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            out.append(cells)
    return out


def _color_comps4(grid):
    """Total same-color 4-connected component count over all colors."""
    h, w = len(grid), len(grid[0])
    total = 0
    for color in sorted({v for row in grid for v in row} - {0}):
        seen = set()
        for r in range(h):
            for c in range(w):
                if grid[r][c] == color and (r, c) not in seen:
                    total += 1
                    stack = [(r, c)]
                    seen.add((r, c))
                    while stack:
                        cr, cc = stack.pop()
                        for dr, dc in _DIRS4:
                            n = (cr + dr, cc + dc)
                            if (0 <= n[0] < h and 0 <= n[1] < w
                                    and n not in seen
                                    and grid[n[0]][n[1]] == color):
                                seen.add(n)
                                stack.append(n)
    return total


def _n4_picture(pic):
    """Same-color 4-connected component count of a small picture grid."""
    h, w = len(pic), len(pic[0])
    seen = [[False] * w for _ in range(h)]
    n = 0
    for r in range(h):
        for c in range(w):
            if pic[r][c] == 0 or seen[r][c]:
                continue
            n += 1
            stack, v = [(r, c)], pic[r][c]
            seen[r][c] = True
            while stack:
                cr, cc = stack.pop()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and pic[nr][nc] == v):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
    return n


def _big_figures(grid):
    """The two big (>5 cell) objects sorted by min row, as (cells, bbox)."""
    figs = []
    for cells in _components8(grid):
        if len(cells) <= 5:
            continue
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        figs.append((cells, (min(rs), min(cs), max(rs), max(cs))))
    figs.sort(key=lambda fb: fb[1][0])
    return figs


def _diff_rows(grid, b1, b2, fh, fw):
    n = 0
    for rr in range(fh):
        if any((grid[b1[0] + rr][b1[1] + cc] == 0)
               != (grid[b2[0] + rr][b2[1] + cc] == 0)
               for cc in range(fw)):
            n += 1
    return n


def _row_grid(rows):
    return [[int(v) for v in row] for row in rows]


def _reflect_grid(grid, *, vertical, horizontal):
    out = [row[:] for row in grid]
    if vertical:
        out.reverse()
    if horizontal:
        out = [list(reversed(row)) for row in out]
    return out


def _pair_signature(h, w, f1, f2):
    """Color-invariant complete linked morphology of an ordered figure pair."""
    colors = {
        v for grid in (f1, f2) for row in grid for v in row if v != 0
    }
    occ1 = tuple(tuple(int(v != 0) for v in row) for row in f1)
    occ2 = tuple(tuple(int(v != 0) for v in row) for row in f2)
    return (
        h,
        w,
        len(colors),
        _n4_picture(f1) + _n4_picture(f2),
        occ1,
        occ2,
    )


def canonical_profile_signature(grid):
    """Return the complete answer-bearing profile of a lawful returned grid.

    Placement and color labels are intentionally ignored.  The ordered binary
    occupancy of both crops is retained because it determines every output
    row/cell; dimensions, palette cardinality, and coherent-region count stay
    linked in the same signature.
    """
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return None
    figures = _big_figures(grid)
    if len(figures) != 2:
        return None
    crops = []
    for _, (r0, c0, r1, c1) in figures:
        crops.append([
            [grid[r][c] for c in range(c0, c1 + 1)]
            for r in range(r0, r1 + 1)
        ])
    f1, f2 = crops
    if (len(f1), len(f1[0])) != (len(f2), len(f2[0])):
        return None
    return _pair_signature(len(grid), len(grid[0]), f1, f2)


def _canonical_signatures():
    signatures = set()
    for h, w, rows1, rows2 in _CANONICAL_ARCHETYPES:
        f1, f2 = _row_grid(rows1), _row_grid(rows2)
        for vertical in (False, True):
            for horizontal in (False, True):
                signatures.add(_pair_signature(
                    h,
                    w,
                    _reflect_grid(
                        f1, vertical=vertical, horizontal=horizontal
                    ),
                    _reflect_grid(
                        f2, vertical=vertical, horizontal=horizontal
                    ),
                ))
    return frozenset(signatures)


_CANONICAL_SIGNATURES = _canonical_signatures()


def is_canonical_profile(grid):
    signature = canonical_profile_signature(grid)
    return signature is not None and signature in _CANONICAL_SIGNATURES


def rule_mirror(grid):
    """Independent Python spelling of the stored Racket rule for parity tests."""
    figures = _big_figures(grid)
    if len(figures) < 2:
        raise ValueError("rule requires two big figures")
    crops = []
    for _, (r0, c0, r1, c1) in figures[:2]:
        crops.append([
            [grid[r][c] for c in range(c0, c1 + 1)]
            for r in range(r0, r1 + 1)
        ])
    f1, f2 = crops
    if (len(f1), len(f1[0])) != (len(f2), len(f2[0])):
        raise ValueError("rule requires same-size figure crops")
    out = []
    for r in range(len(f1)):
        if any(f1[r][c] != f2[r][c] for c in range(len(f1[0]))):
            out.append([
                _MARK
                if (f1[r][c] == 0) != (f2[r][c] == 0)
                else 0
                for c in range(len(f1[0]))
            ])
    return out


def _decode_archetype(archetype, palette, *, vertical, horizontal):
    _, _, rows1, rows2 = archetype
    originals = sorted({
        int(v)
        for rows in (rows1, rows2)
        for row in rows
        for v in row
        if v != "0"
    })
    if len(originals) != len(palette):
        raise ValueError(
            f"archetype needs {len(originals)} colors, got {len(palette)}"
        )
    mapping = dict(zip(originals, palette))

    def decode(rows):
        grid = [
            [0 if v == "0" else mapping[int(v)] for v in row]
            for row in rows
        ]
        return _reflect_grid(
            grid, vertical=vertical, horizontal=horizontal
        )

    return decode(rows1), decode(rows2)


def observe_overrides(grid) -> dict:
    """Realized per-draw values of the exact semantic axes (KRF-0002),
    derived from the grid itself: figure bbox dims of the two big objects,
    n_diff_rows (rows whose zero-patterns differ = output row count), and
    n_colors (distinct non-0 non-8 colors across the figures)."""
    figs = _big_figures(grid)
    out = {"figure_height": 0, "figure_width": 0, "n_diff_rows": 0, "n_colors": 0}
    if len(figs) < 2:
        return out
    (c1, b1), (c2, b2) = figs[0], figs[1]
    fh1 = b1[2] - b1[0] + 1; fw1 = b1[3] - b1[1] + 1
    fh2 = b2[2] - b2[0] + 1; fw2 = b2[3] - b2[1] + 1
    same = (fh1, fw1) == (fh2, fw2)
    out["figure_height"] = fh1 if same else -1
    out["figure_width"] = fw1 if same else -1
    colors = set()
    for cells, _ in (c1, b1), (c2, b2):
        for r, c in cells:
            v = grid[r][c]
            if v not in (0, _MARK):
                colors.add(v)
    out["n_colors"] = len(colors)
    if same:
        out["n_diff_rows"] = _diff_rows(grid, b1, b2, fh1, fw1)
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance: rectangular grid inside
    the declared envelope (_VALID_H x _VALID_W, matching AXES grid_h/grid_w)
    of colors 0..9; exactly two 8-connected objects, both > 5 cells, with
    identical bbox dims inside the declared figure ranges; no cell of color
    8; at every position nonzero in both crops the colors are equal (one
    shared picture); crops' zero-sets differ in exactly 1..6 rows with at
    least one multi-mark row; the palette has 2..6 colors."""
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
    if any(v == _MARK for row in grid for v in row):
        errs.append("grid contains the output mark color 8")
    figs = _big_figures(grid)
    if len(figs) != 2:
        errs.append(f"expected exactly two big (>5 cell) objects, found {len(figs)}")
        return errs
    (c1, b1), (c2, b2) = figs[0], figs[1]
    fh1 = b1[2] - b1[0] + 1; fw1 = b1[3] - b1[1] + 1
    fh2 = b2[2] - b2[0] + 1; fw2 = b2[3] - b2[1] + 1
    if (fh1, fw1) != (fh2, fw2):
        errs.append(f"bbox dims differ: {fh1}x{fw1} vs {fh2}x{fw2}")
        return errs
    if not (_VALID_FH[0] <= fh1 <= _VALID_FH[1]
            and _VALID_FW[0] <= fw1 <= _VALID_FW[1]):
        errs.append(f"figure bbox {fh1}x{fw1} outside the declared "
                    f"{_VALID_FH[0]}..{_VALID_FH[1]} x {_VALID_FW[0]}..{_VALID_FW[1]}")
    colors = set()
    for cells, _ in (c1, b1), (c2, b2):
        for r, c in cells:
            v = grid[r][c]
            if v not in (0, _MARK):
                colors.add(v)
    if not (_VALID_NC[0] <= len(colors) <= _VALID_NC[1]):
        errs.append(f"palette has {len(colors)} colors outside the declared "
                    f"{_VALID_NC[0]}..{_VALID_NC[1]}")
    mismatch = 0
    n_diff = 0
    multi = 0
    overwide_rows = 0
    for rr in range(fh1):
        row_marks = 0
        for cc in range(fw1):
            v1 = grid[b1[0] + rr][b1[1] + cc]
            v2 = grid[b2[0] + rr][b2[1] + cc]
            if v1 != 0 and v2 != 0 and v1 != v2:
                mismatch += 1
            if (v1 == 0) != (v2 == 0):
                row_marks += 1
        n_diff += row_marks > 0
        multi += row_marks > 1
        overwide_rows += row_marks > 7
    if mismatch:
        errs.append(f"{mismatch} positions nonzero in both crops have "
                    "different colors (not one shared picture)")
    if not (_VALID_DIFF[0] <= n_diff <= _VALID_DIFF[1]):
        errs.append(f"zero-sets differ in {n_diff} rows outside the declared "
                    f"{_VALID_DIFF[0]}..{_VALID_DIFF[1]}")
    if n_diff and not multi:
        errs.append("no multi-mark diff row (every official scene has one)")
    if overwide_rows:
        errs.append(
            f"{overwide_rows} diff rows exceed the declared 7-mark maximum"
        )
    return errs


def _conn8(filled):
    if not filled:
        return False
    start = next(iter(filled))
    seen = {start}
    stack = [start]
    while stack:
        r, c = stack.pop()
        for dr, dc in _DIRS8:
            n = (r + dr, c + dc)
            if n in filled and n not in seen:
                seen.add(n)
                stack.append(n)
    return len(seen) == len(filled)


def _picture(rng, fh, fw, colors, fill):
    """Coherent color-region picture: Voronoi territories colored per seed,
    then zero-punched to `fill`.  Candidates must be 8-connected, nonzero
    on all four bbox edges, use every requested color, and keep the
    same-color 4-component count in the canonical 10..40 window."""
    seeds_n = max(len(colors), int(round(len(colors) * 1.5)))
    for _ in range(80):
        seeds = []
        for i in range(seeds_n):
            seeds.append((rng.randrange(fh), rng.randrange(fw),
                          colors[i % len(colors)]))
        pic = [[0] * fw for _ in range(fh)]
        for r in range(fh):
            for c in range(fw):
                best = min(seeds, key=lambda s: (abs(s[0] - r) + abs(s[1] - c),
                                                 seeds.index(s)))
                pic[r][c] = best[2]
        # zero-punch to the requested fill
        for r in range(fh):
            for c in range(fw):
                if rng.random() > fill:
                    pic[r][c] = 0
        filled = {(r, c) for r in range(fh) for c in range(fw) if pic[r][c] != 0}
        if len(filled) <= 5 or not _conn8(filled):
            continue
        if (not any(pic[0][c] != 0 for c in range(fw))
                or not any(pic[fh - 1][c] != 0 for c in range(fw))
                or not any(pic[r][0] != 0 for r in range(fh))
                or not any(pic[r][fw - 1] != 0 for r in range(fh))):
            continue
        if {v for row in pic for v in row if v != 0} != set(colors):
            continue
        n4 = _color_comps4(pic)
        if 4 <= n4 <= 16:   # coherent regions in the canonical per-figure window
            return pic
    return None


def _mark_count(rng):
    total = sum(w for _, w in _MARK_WEIGHTS)
    x = rng.random() * total
    for v, wgt in _MARK_WEIGHTS:
        x -= wgt
        if x <= 0:
            return v
    return 1


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    band = difficulty or "medium"
    if overrides.get("texture") is not None:
        texture_name = ctx.draw_choice(
            "texture", ["none", *DEGENERATE_TEXTURES]
        )
    else:
        texture_name = ctx.draw_choice("texture", ["none"])
    texture = None if texture_name == "none" else texture_name
    if band == "easy":
        fhr, fwr, dr_lo, dr_hi, ncr, fill = (8, 11), (6, 8), 1, 2, (2, 3), 0.8
    elif band == "hard":
        fhr, fwr, dr_lo, dr_hi, ncr, fill = (10, 15), (7, 10), 2, 4, (4, 6), 0.7
    else:
        fhr, fwr, dr_lo, dr_hi, ncr, fill = (8, 13), (6, 9), 2, 3, (3, 5), 0.75
    if texture == "dense_pair":
        fill = 0.9
    elif texture == "sparse_pair":
        fill = 0.667

    # Full-pair prior: redraw one of the four observed answer-bearing figure
    # pairs at a declared rate. Exact overrides and named textures bypass it.
    profile = None
    profiled_axes = {"grid_h", "grid_w", "figure_height", "figure_width",
                     "n_diff_rows", "n_colors"}
    if not (profiled_axes & {k for k, v in overrides.items() if v is not None}
            or texture):
        prior_rng = ctx.draw_rng(f"canonical_prior|{band}")
        if prior_rng.random() < _PROFILE_PRIOR:
            profile = ctx.draw_choice(
                f"canonical_form|{band}",
                list(_CANONICAL_ARCHETYPES),
            )
    if profile:
        profile_fh = len(profile[2])
        profile_fw = len(profile[2][0])
        profile_n_diff = sum(
            any((a == "0") != (b == "0") for a, b in zip(row1, row2))
            for row1, row2 in zip(profile[2], profile[3])
        )
        profile_n_colors = len({
            v
            for rows in profile[2:4]
            for row in rows
            for v in row
            if v != "0"
        })

    # Exact overrides execute over the full declared valid range (or reject
    # loudly); band ranges apply to plain draws only.
    if overrides.get("grid_h") is not None:
        h = ctx.draw_int("grid_h", *_VALID_H)
    elif profile:
        h = ctx.draw_int("grid_h", profile[0], profile[0])
    else:
        h = ctx.draw_int("grid_h", 20, 30)
    if overrides.get("grid_w") is not None:
        w = ctx.draw_int("grid_w", *_VALID_W)
    elif profile:
        w = ctx.draw_int("grid_w", profile[1], profile[1])
    else:
        # A pinned figure_width needs room for the side-by-side layout:
        # draw the free width from the feasible domain (w >= 2*fw+1).
        w_lo_eff = 20
        if overrides.get("figure_width") is not None:
            w_lo_eff = max(w_lo_eff, 2 * overrides["figure_width"] + 1)
        w = ctx.draw_int("grid_w", w_lo_eff, 30)

    # Figure dims from the FEASIBLE domain given the keyed grid: the pair
    # must stack (h >= 2fh+1) or sit side-by-side (w >= 2fw+1).
    fh_lo, fh_hi = (_VALID_FH if overrides.get("figure_height") is not None
                    else fhr)
    fw_lo, fw_hi = (_VALID_FW if overrides.get("figure_width") is not None
                    else fwr)
    if profile:
        fh_lo = fh_hi = profile_fh
        fw_lo = fw_hi = profile_fw
    # Feasibility must use the FINAL pinned width when present, not the
    # band minimum: a pinned wide figure forces the stacked layout check.
    fw_feas = overrides.get("figure_width") or fw_lo
    fh_opts = [v for v in range(fh_lo, fh_hi + 1)
               if h >= 2 * v + 1 or w >= 2 * fw_feas + 1]
    if not fh_opts:
        raise ValueError(f"no feasible figure_height for a {h}x{w} grid "
                         f"(need h >= 2*fh+1 or w >= 2*fw+1)")
    fh = (ctx.draw_int("figure_height", *_VALID_FH)
          if overrides.get("figure_height") is not None
          else ctx.draw_choice("figure_height", fh_opts))
    fw_opts = [v for v in range(fw_lo, fw_hi + 1)
               if h >= 2 * fh + 1 or w >= 2 * v + 1]
    if not fw_opts:
        raise ValueError(f"no feasible figure_width {fw_lo}..{fw_hi} with "
                         f"figure_height={fh} on a {h}x{w} grid")
    fw = (ctx.draw_int("figure_width", *_VALID_FW)
          if overrides.get("figure_width") is not None
          else ctx.draw_choice("figure_width", fw_opts))
    if texture == "min_diff":
        # A forced semantic mode must record its realized exact axis too.
        # Compatible explicit 1 is consumed; all other explicit values reject.
        n_diff = ctx.draw_choice("n_diff_rows", [1])
    elif overrides.get("n_diff_rows") is not None:
        n_diff = ctx.draw_int("n_diff_rows", *_VALID_DIFF)
    elif profile:
        n_diff = ctx.draw_int(
            "n_diff_rows", profile_n_diff, profile_n_diff
        )
    else:
        n_diff = ctx.draw_int("n_diff_rows", dr_lo, dr_hi)
    if n_diff > fh:
        raise ValueError(f"n_diff_rows={n_diff} exceeds figure_height={fh}")
    if overrides.get("n_colors") is not None:
        n_colors = ctx.draw_int("n_colors", *_VALID_NC)
    elif profile:
        n_colors = ctx.draw_int(
            "n_colors", profile_n_colors, profile_n_colors
        )
    else:
        n_colors = ctx.draw_int("n_colors", *ncr)
    fill = min(0.924, max(0.667, fill))

    palette = list(ctx.draw_distinct_colors(
        f"palette|{band}", n=n_colors, exclude=(0, _MARK)
    ))
    if profile:
        transform_rng = ctx.draw_rng(f"canonical_transform|{band}")
        pic, f2 = _decode_archetype(
            profile,
            palette,
            vertical=bool(transform_rng.getrandbits(1)),
            horizontal=bool(transform_rng.getrandbits(1)),
        )
        if _pair_signature(h, w, pic, f2) not in _CANONICAL_SIGNATURES:
            raise AssertionError("decoded archetype lost its linked profile")
    else:
        pic = _picture(rng, fh, fw, palette, fill)
        if pic is None:
            raise ValueError(
                f"cannot draw a coherent {fh}x{fw} picture with "
                f"{n_colors} colors"
            )
        f2 = [row[:] for row in pic]
        diff_rows = rng.sample(range(fh), n_diff)
        marks = [_mark_count(rng) for _ in diff_rows]
        if all(m == 1 for m in marks):
            marks[rng.randrange(len(marks))] = 2 + rng.randrange(min(3, fw - 1))
        used = sorted({v for row in pic for v in row if v != 0})

        def _try_edit(rr, c):
            old = f2[rr][c]
            trial = [row[:] for row in f2]
            trial[rr][c] = rng.choice(used) if old == 0 else 0
            filled2 = {(r, cc) for r in range(fh) for cc in range(fw)
                       if trial[r][cc] != 0}
            if len(filled2) <= 5 or not _conn8(filled2):
                return False
            if (not any(trial[0][cc] != 0 for cc in range(fw))
                    or not any(trial[fh - 1][cc] != 0 for cc in range(fw))
                    or not any(trial[r][0] != 0 for r in range(fh))
                    or not any(trial[r][fw - 1] != 0 for r in range(fh))):
                return False
            return trial

        def _edit_row(rr, n_marks, at_least=1):
            cols = list(range(fw))
            rng.shuffle(cols)
            made = 0
            for c in cols:
                if made >= min(n_marks, fw):
                    break
                trial = _try_edit(rr, c)
                if trial:
                    f2[:] = trial
                    made += 1
            return made >= at_least

        edited_ok = False
        for _attempt in range(25):
            f2 = [row[:] for row in pic]
            # Designated multi-mark row first: the row requesting the most
            # marks must actually reach at least two.
            order = sorted(range(len(diff_rows)), key=lambda i: -marks[i])
            ok = True
            for i in order:
                rr = diff_rows[i]
                need = marks[i]
                floor = 2 if need >= 2 else 1
                if not _edit_row(rr, need, at_least=floor):
                    ok = False
                    break
            if ok:
                edited_ok = True
                break
        if not edited_ok:
            raise ValueError(f"cannot realize {n_diff} diff rows with a "
                             "multi-mark row without disconnecting the second "
                             "figure")

    # Placement: f1 topmost, the two objects 8-separated (Chebyshev >= 2),
    # otherwise free (columns may overlap, canonical mixes both layouts).
    def _try_place(r1, r2, c1, c2):
        cells1 = [(r1 + r, c1 + c) for r in range(fh) for c in range(fw)
                  if pic[r][c] != 0]
        cells2 = [(r2 + r, c2 + c) for r in range(fh) for c in range(fw)
                  if f2[r][c] != 0]
        set1 = set(cells1)
        # The fh x fw RECTANGLES must keep a one-cell gap on every side:
        # a second-figure cell painted inside the first figure's rectangle
        # corrupts the observer's row-aligned diff with a spurious row,
        # even when it lands on a zero.
        if not (r1 + fh + 1 <= r2 or r2 + fh + 1 <= r1
                or c1 + fw + 1 <= c2 or c2 + fw + 1 <= c1):
            return None
        if any((r, c) in set1 for r, c in cells2):
            return None
        if any((r + dr, c + dc) in set1 for r, c in cells2 for dr, dc in _DIRS8):
            return None
        g = full_grid(h, w, 0)
        for r, c in cells1:
            g[r][c] = pic[r - r1][c - c1]
        for r, c in cells2:
            g[r][c] = f2[r - r2][c - c2]
        return g

    for _ in range(60):
        r1 = rng.randint(0, max(0, h - 2 * fh - 3))
        r2 = rng.randint(r1 + 1, h - fh)
        c1 = rng.randint(0, w - fw)
        c2 = rng.randint(0, w - fw)
        g = _try_place(r1, r2, c1, c2)
        if g is not None:
            return g
    r1_max = max(0, h - 2 * fh - 3)
    for r1 in range(0, r1_max + 1):
        for r2 in range(r1 + 1, h - fh + 1):
            for c1 in range(0, w - fw + 1):
                for c2 in range(0, w - fw + 1):
                    g = _try_place(r1, r2, c1, c2)
                    if g is not None:
                        return g
    raise ValueError(f"cannot place two separated {fh}x{fw} figures on a "
                     f"{h}x{w} grid")
