"""Generator for 90f3ed37.

Rule: rows containing color 8 form contiguous groups separated by empty
rows.  The first group is the template; its block of rows is copied onto
every later group: for the k-th template row, every 8-cell strictly beyond
the later group's frontier (its rightmost 8) is painted color 1 on the row
(grp_start + k) — including rows past the later group's own rows.  The
output preserves the input and adds these blue extension cells.

Combinatorial axes (4): grid_h/w, n_groups, scatter, texture.  Branches
exercised: group counts 2..4, template/target block sizes 1..3, scattered
(gappy) vs contiguous row patterns, heterogeneous row maxima inside a
target group (per-group vs per-row frontier disambiguation), stamp rows
that extend past the target group into empty rows, and leading/trailing
empty-row jitter.
Textures: no_scatter, single_target, crowded (all rule-valid).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2e52a91a0421"
VERSION = "2.1.1"  # KRF-0002 (override-contract v4): observe_overrides(grid) added
# for the exact semantic axes (n_groups, scatter); scatter=True draws now
# guarantee at least one gappy row so the realized value matches the request.
# 2.1.0: canonical topology was never generated (fixed 2x2-row groups,
# contiguous col-1-anchored runs, h 8..12 vs canonical 15x10 with 2-4 groups of
# 1-3 scattered rows) -> canonical-style group blocks with scattered patterns;
# structural self_check + pinned RULE_HASH added; grid_w was declared fixed 10
# but drawn 10..14 (axis lie) -> honest band ranges; degenerate no_template
# crashed the oracle (first of empty groups) -> rule-valid textures.
TASK_ID = "2e52a91a0421"
RULE_HASH = "9d0733ff96f2"
SUMMARY = "Stamp the first 8-row group's pattern in 1 beyond each later group's frontier."

INVARIANTS = [
    "inputs use only colors 0 and 8; 0 is the modal color",
    "rows containing 8 form two or more contiguous groups separated by "
    "empty rows; the first group is the template",
    "the template's rightmost 8 is strictly beyond every later group's "
    "frontier, so every group receives blue",
    "the template block is stamped in 1 at each later group's start row "
    "(only beyond that group's frontier); stamp rows may extend past the "
    "group's own rows into the empty rows below",
    "row patterns may be scattered (gappy), so a fill-the-run shortcut "
    "disagrees with the oracle",
]

DEGENERATE_TEXTURES = ("no_scatter", "single_target", "crowded")

AXES = {
    "grid_h":   {"type": "int", "default": "band rng 12..18", "valid": "12..18"},
    "grid_w":   {"type": "int", "default": "band rng 10..12", "valid": "10..12"},
    "n_groups": {"type": "int", "default": "band 2 easy, 2..3 medium, 3..4 hard",
                 "valid": "2..4"},
    "scatter":  {"type": "bool", "default": "band rng (p 0.3 easy, 0.55 medium, "
                 "0.8 hard); true guarantees >= 1 gappy row", "valid": "true|false"},
    "texture":  {"type": "str", "default": "none (plain draw)",
                 "valid": "|".join(DEGENERATE_TEXTURES)},
}

_VALID_H = (12, 18)
_VALID_W = (10, 12)
_VALID_G = (2, 4)


def _pattern(rng, w, lo_c, hi_c, scatter):
    """One row's 8-columns: a subset of [lo_c, hi_c] achieving both bounds;
    a contiguous run when not scatter."""
    hi_c = min(hi_c, w - 1)
    lo_c = max(0, min(lo_c, hi_c))
    if not scatter:
        return list(range(lo_c, hi_c + 1))
    span = hi_c - lo_c + 1
    if span <= 2:
        return list(range(lo_c, hi_c + 1))
    count = rng.randint(max(2, (span + 2) // 3), span)
    cols = {lo_c, hi_c}
    while len(cols) < count:
        cols.add(rng.randint(lo_c, hi_c))
    return sorted(cols)


def _groups_of_8(g):
    """Contiguous row groups containing 8 -> list of row-index lists."""
    groups, cur = [], []
    for r, row in enumerate(g):
        if any(v == 8 for v in row):
            cur.append(r)
        elif cur:
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    return groups


def _has_gappy_row(g):
    """Whether some row's 8-cells do not fill their own span."""
    for row in g:
        cols = [c for c, v in enumerate(row) if v == 8]
        if cols and len(cols) < max(cols) - min(cols) + 1:
            return True
    return False


def observe_overrides(grid) -> dict:
    """Realized per-draw values of the exact semantic axes (KRF-0002):
    n_groups = number of contiguous 8-row groups; scatter = at least one
    row whose 8-cells do not fill their span.  Both are derived from the
    grid itself."""
    return {
        "n_groups": len(_groups_of_8(grid)),
        "scatter": _has_gappy_row(grid),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance: rectangular grid inside
    the declared envelope (_VALID_H x _VALID_W, matching AXES grid_h/grid_w)
    of colors 0..9 with palette inside {0, 8}; 0 modal; rows containing 8
    form at least two contiguous groups separated by empty rows; the first
    (template) group's rightmost 8 is strictly beyond every later group's
    frontier so the oracle paints blue in every group."""
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
    freq = {}
    for row in grid:
        for v in row:
            freq[v] = freq.get(v, 0) + 1
    if set(freq) - {0, 8}:
        errs.append(f"palette outside {{0, 8}}: {sorted(set(freq) - {0, 8})}")
    if freq.get(0, 0) * 2 <= h * w:
        errs.append("background 0 is not modal")
    groups = _groups_of_8(grid)
    if not groups:
        errs.append("no rows contain 8: the oracle has no template group")
        return errs
    if len(groups) < 2:
        errs.append("fewer than two 8-row groups: no target for the stamp")
        return errs
    tpl_max = max(c for r in groups[0] for c in range(w) if grid[r][c] == 8)
    for grp in groups[1:]:
        frontier = max(c for r in grp for c in range(w) if grid[r][c] == 8)
        if frontier >= tpl_max:
            errs.append(f"group at row {grp[0]} frontier {frontier} reaches "
                        f"the template's rightmost 8 ({tpl_max}): no blue "
                        "would be painted")
    return errs


def _layout(rng, h, g_count, n_tpl, target_sizes, lead, gaps):
    """Row layout: lead blanks, template block, then gap/target blocks.
    Returns (tpl_rows, [target_rows...]) or None when it cannot fit while
    keeping the whole template stamp in-bounds for the last group."""
    need_trailing = n_tpl - 1  # stamp rows past the last group's own rows
    pos = lead
    tpl_rows = list(range(pos, pos + n_tpl))
    pos += n_tpl
    targets = []
    for i, tsz in enumerate(target_sizes):
        pos += gaps[i]
        rows = list(range(pos, pos + tsz))
        targets.append(rows)
        pos += tsz
    if targets and targets[-1][0] + n_tpl - 1 > h - 1:
        return None
    if pos > h:
        return None
    return tpl_rows, targets


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    band = difficulty or "medium"
    texture = overrides.get("texture")
    if texture is not None and texture not in DEGENERATE_TEXTURES:
        raise ValueError(f"unknown texture {texture!r}")
    if band == "easy":
        h_lo, h_hi, g_lo, g_hi, scatter_p = 12, 15, 2, 2, 0.3
    elif band == "hard":
        h_lo, h_hi, g_lo, g_hi, scatter_p = 14, 18, 3, 4, 0.8
    else:
        h_lo, h_hi, g_lo, g_hi, scatter_p = 13, 16, 2, 3, 0.55

    # Exact overrides execute over the full declared valid range (or reject
    # loudly); band ranges apply to plain draws only.
    h = (ctx.draw_int("grid_h", *_VALID_H) if overrides.get("grid_h") is not None
         else ctx.draw_int("grid_h", h_lo, h_hi))
    w = (ctx.draw_int("grid_w", *_VALID_W) if overrides.get("grid_w") is not None
         else ctx.draw_int("grid_w", 10, 12))
    if texture == "single_target":
        if overrides.get("n_groups") is not None:
            raise ValueError("texture=single_target conflicts with n_groups override")
        g_count = 2
    elif texture == "crowded":
        g_count = (ctx.draw_int("n_groups", *_VALID_G)
                   if overrides.get("n_groups") is not None else 4)
    elif overrides.get("n_groups") is not None:
        g_count = ctx.draw_int("n_groups", *_VALID_G)
    else:
        g_count = ctx.draw_int("n_groups", g_lo, g_hi)
    if texture == "no_scatter":
        if overrides.get("scatter") is not None:
            raise ValueError("texture=no_scatter conflicts with scatter override")
        scatter = False
    elif overrides.get("scatter") is not None:
        scatter = ctx.draw_choice("scatter", [False, True])
    else:
        scatter = rng.random() < scatter_p

    # Block sizes and layout (retried until the stamp stays in-bounds).
    layout = None
    for _ in range(40):
        n_tpl = rng.randint(1, 3) if band != "easy" else rng.randint(1, 2)
        if texture == "crowded":
            n_tpl = 3
        target_sizes = [rng.randint(1, 3 if band == "hard" else 2)
                        for _ in range(g_count - 1)]
        if texture == "crowded":
            target_sizes = [1] * (g_count - 1)
        lead = rng.randint(0, 2)
        gaps = [1 if texture == "crowded" else rng.randint(1, 2)
                for _ in range(g_count - 1)]
        layout = _layout(rng, h, g_count, n_tpl, target_sizes, lead, gaps)
        if layout is not None:
            break
    if layout is None:
        raise ValueError(
            f"cannot lay out {g_count} row groups with a {n_tpl}-row "
            f"template on a {h}x{w} grid")
    tpl_rows, targets = layout

    g = full_grid(h, w, 0)
    # Template rows: wide patterns reaching near the right edge; the block's
    # overall rightmost 8 sits at w-1 with high probability (canonical form).
    tpl_max_seen = -1
    reach_col = w - 1 if rng.random() < 0.8 else w - 2
    reach_row = rng.randrange(len(tpl_rows))
    for i, r in enumerate(tpl_rows):
        hi_c = reach_col if i == reach_row else rng.randint(max(4, w - 4), w - 1)
        cols = _pattern(rng, w, rng.randint(0, 2), hi_c, scatter)
        for c in cols:
            g[r][c] = 8
        tpl_max_seen = max(tpl_max_seen, max(cols))
    # Target groups: frontier strictly left of the template's reach; rows
    # inside one group may have heterogeneous rightmost columns.
    for rows in targets:
        frontier = rng.randint(1, min(5, tpl_max_seen - 1))
        f_row = rng.randrange(len(rows))
        for i, r in enumerate(rows):
            hi_c = frontier if i == f_row else rng.randint(0, frontier)
            cols = _pattern(rng, w, rng.randint(0, min(2, hi_c)), hi_c, scatter)
            for c in cols:
                g[r][c] = 8
    # scatter=True is an exact per-draw claim (KRF-0002): at least one row
    # must be gappy.  If the random patterns all came out contiguous, reopen
    # one interior hole in a template row (its span is the widest).
    if scatter and not _has_gappy_row(g):
        for r in tpl_rows:
            cols = [c for c in range(w) if g[r][c] == 8]
            if len(cols) >= 3:
                g[r][cols[len(cols) // 2]] = 0
                break
    return g
