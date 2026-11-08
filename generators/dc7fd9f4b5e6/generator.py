"""Generator for 81c0276b.

Rule: a nonzero divider color forms a lattice (full rows/columns at offsets
4, 9, 14, ...) over a 0 background; each lattice cell may hold one small
same-color block.  The output is a staircase: one row per non-divider,
non-zero color, whose length equals that color's 4-connected block count,
rows sorted ascending and 0-padded to the maximum count.

Combinatorial axes (6): grid_h/w, color_count, divider_color, palette_kind,
shape_variety, texture.  Branches exercised: divider-colored distractor
blocks (excluded by the oracle), empty cells, partial last bands, varied
per-color counts (distinct, so the ascending sort is well-defined), and
optional non-2x2 single-component shapes (object-count vs cell-count
disambiguation).
Textures: no_distractors, single_color, packed.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dc7fd9f4b5e6"
VERSION = "2.0.0"  # distribution break: scattered dots on a solid nonzero background
# (canonical lattice topology never generated) -> canonical-style divider lattice
# with 2x2 cell blocks, divider-colored distractors, capacity-aware overrides,
# structural self_check, pinned RULE_HASH.
TASK_ID = "dc7fd9f4b5e6"
RULE_HASH = "ede07557d8d3"
SUMMARY = "Colors as staircase rows whose lengths = connected-object counts."

INVARIANTS = [
    "background 0 is the overall modal color",
    "the divider color is the modal nonzero color and fills the rows and "
    "columns at offsets 4, 9, 14, ... (every fifth line)",
    "counted colors are nonzero and distinct from the divider color",
    "each counted block is a 4-connected component inside one lattice cell",
    "per-color block counts are pairwise distinct, so the ascending "
    "staircase row order is well-defined",
    "divider-colored blocks may appear as distractors; the rule excludes "
    "them from the count",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_distractors", "single_color", "packed")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":        {"type": "int", "default": "band rng 11..24, raised when the "
                          "drawn counts need more lattice cells", "valid": "11..29"},
    "grid_w":        {"type": "int", "default": "band rng 11..24, raised when the "
                          "drawn counts need more lattice cells", "valid": "11..29"},
    "color_count":   {"type": "int", "default": "band 2..3 easy, 3..4 medium, "
                          "4..6 hard; capped by lattice capacity", "valid": "2..6"},
    "divider_color": {"type": "color", "default": "rng !0", "valid": "1..9"},
    "palette_kind":  {"type": "str", "default": "rng helpful",
                      "valid": "|".join(PALETTE_KINDS)},
    "shape_variety": {"type": "bool", "default": "false on easy; band rng "
                          "medium/hard", "valid": "true|false"},
    "texture":       {"type": "str", "default": "alias for palette_kind",
                      "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_VALID_LO, _VALID_HI = 11, 29


def _bands(d):
    """Band heights for a dimension: full bands of 4 plus a 1..5 last band."""
    rb = (d - 1) // 5 + 1
    return [4] * (rb - 1) + [d - 5 * (rb - 1)]


def _divider_lines(d):
    return [5 * i + 4 for i in range(len(_bands(d)) - 1)]


def _blockable(d):
    """Number of bands that can hold a block (need >=3 rows/cols)."""
    bands = _bands(d)
    return len(bands) if bands[-1] >= 3 else len(bands) - 1


def _k_max(capacity):
    """Max colors with pairwise-distinct positive counts summing <= capacity."""
    k = 0
    while (k + 1) * (k + 2) // 2 <= capacity:
        k += 1
    return k


def _min_dim(needed, other_blockable=None):
    """Smallest dimension d in the valid range whose blockable bands, times
    `other_blockable` (or itself), fit `needed` blocks. 30 when infeasible."""
    for d in range(_VALID_LO, _VALID_HI + 1):
        b = _blockable(d)
        if b * (other_blockable if other_blockable else b) >= needed:
            return d
    return _VALID_HI + 1


def _fit_counts(rng, k, cmax, capacity):
    """k pairwise-distinct counts from 1..cmax whose sum fits `capacity`;
    None when even the k smallest do not fit."""
    if k * (k + 1) // 2 > capacity:
        return None
    for _ in range(60):
        counts = rng.sample(range(1, cmax + 1), k)
        if sum(counts) <= capacity:
            return counts
    return list(range(1, k + 1))


def _components(grid, skip):
    """4-connected components of colors not in `skip` -> {color: [cells...]}."""
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    out = {}
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v in skip or seen[r][c]:
                continue
            stack, cells = [(r, c)], []
            seen[r][c] = True
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _DIRS4:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and grid[nr][nc] == v):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            out.setdefault(v, []).append(cells)
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance: rectangular 11..30 grid of
    colors 0..9; 0 is the modal color; the modal nonzero color D tiles the
    divider rows/columns at offsets 4, 9, 14, ...; every other nonzero cell
    sits strictly inside one lattice cell of at least 3x3; per-color
    4-connected component counts are pairwise distinct (an unambiguous
    staircase) and at least one counted color exists."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 9
           for row in grid for v in row):
        errs.append("color outside 0..9")
    if not (11 <= h <= 30 and 11 <= w <= 30):
        errs.append(f"dims {h}x{w} outside 11..30")
    freq = {}
    for row in grid:
        for v in row:
            freq[v] = freq.get(v, 0) + 1
    nonzero = {c: n for c, n in freq.items() if c != 0}
    if not nonzero:
        errs.append("no nonzero content")
        return errs
    if freq.get(0, 0) <= max(nonzero.values()):
        errs.append("background 0 is not the modal color")
    div = max(nonzero, key=lambda c: (nonzero[c], -c))
    div_rows = _divider_lines(h)
    div_cols = _divider_lines(w)
    for r in div_rows:
        if any(grid[r][c] != div for c in range(w)):
            errs.append(f"divider row {r} is not solid color {div}")
            break
    for c in div_cols:
        if any(grid[r][c] != div for r in range(h)):
            errs.append(f"divider col {c} is not solid color {div}")
            break
    band_h = _bands(h)
    band_w = _bands(w)
    div_row_set = set(div_rows)
    div_col_set = set(div_cols)
    counts = []
    for color, comps in _components(grid, skip={0, div}).items():
        counts.append(len(comps))
        for cells in comps:
            bis = {r // 5 for r, _ in cells}
            bjs = {c // 5 for _, c in cells}
            if len(bis) > 1 or len(bjs) > 1:
                errs.append(f"color {color} component spans lattice cells")
                continue
            r0, c0 = cells[0]
            if r0 in div_row_set or c0 in div_col_set:
                errs.append(f"color {color} block sits on a divider line")
            bi, bj = r0 // 5, c0 // 5
            if band_h[bi] < 3 or band_w[bj] < 3:
                errs.append(f"color {color} block in an undersized lattice cell")
    if not counts:
        errs.append("no counted (non-divider, nonzero) colors")
    if len(counts) != len(set(counts)):
        errs.append("per-color block counts are not distinct: staircase "
                    "row order is ambiguous")
    return errs


def _build_palette(kind, div, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    pool = [c for c in pool if c != 0 and c != div]
    rng.shuffle(pool)
    return pool


def _polyomino(rng, r0, c0, bh, bw, size):
    """Random 4-connected polyomino of `size` cells inside one band rect."""
    cells = [(r0 + rng.randrange(bh), c0 + rng.randrange(bw))]
    while len(cells) < size:
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = _DIRS4[rng.randrange(4)]
        nxt = (r + dr, c + dc)
        if (r0 <= nxt[0] < r0 + bh and c0 <= nxt[1] < c0 + bw
                and nxt not in cells):
            cells.append(nxt)
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    band = difficulty or "medium"
    texture = overrides.get("texture")
    palette_kind = (texture if texture in PALETTE_KINDS else None) or \
        overrides.get("palette_kind") or \
        ctx.draw_choice("palette_kind", list(PALETTE_KINDS))
    single = texture == "single_color"
    if single and overrides.get("color_count") is not None:
        raise ValueError("texture=single_color conflicts with color_count override")
    if band == "easy":
        k_lo, k_hi, cmax_band, d_lo, d_hi, sv_p, pd = 2, 3, 4, 11, 16, 0.0, 0.15
    elif band == "hard":
        k_lo, k_hi, cmax_band, d_lo, d_hi, sv_p, pd = 4, 6, 7, 16, 24, 0.5, 0.35
    else:
        k_lo, k_hi, cmax_band, d_lo, d_hi, sv_p, pd = 3, 4, 5, 13, 19, 0.25, 0.25
    if texture == "no_distractors":
        pd = 0.0
    elif texture == "packed":
        pd = 1.0
    if overrides.get("shape_variety") is not None:
        sv_p = 1.0 if ctx.draw_choice("shape_variety", [False, True]) else 0.0
    div = ctx.draw_color("divider_color", exclude={0})

    # Exact dimension overrides are honored verbatim (full valid range); a
    # combination that cannot host the requested counts is rejected loudly.
    h = ctx.draw_int("grid_h", _VALID_LO, _VALID_HI) \
        if overrides.get("grid_h") is not None else None
    w = ctx.draw_int("grid_w", _VALID_LO, _VALID_HI) \
        if overrides.get("grid_w") is not None else None
    cap_h = _blockable(h) if h is not None else None
    cap_w = _blockable(w) if w is not None else None
    # Capacity the counts must fit: exact when both dims are fixed; with one
    # dim fixed, the free dim can still grow to the valid maximum.
    capacity = None
    if cap_h is not None or cap_w is not None:
        capacity = (cap_h or _blockable(_VALID_HI)) * \
                   (cap_w or _blockable(_VALID_HI))

    if single:
        k = 1
    elif overrides.get("color_count") is not None:
        k = ctx.draw_int("color_count", 2, 6)
    else:
        k_hi_eff = min(k_hi, _k_max(capacity)) if capacity is not None else k_hi
        k = ctx.draw_int("color_count", min(k_lo, k_hi_eff), k_hi_eff)
    cmax = max(cmax_band, k)

    if capacity is not None:
        counts = _fit_counts(rng, k, cmax, capacity)
        if counts is None:
            raise ValueError(
                f"color_count={k} cannot keep distinct counts on a "
                f"{h or '?'}x{w or '?'} lattice ({capacity} blockable cells)")
    else:
        counts = rng.sample(range(1, cmax + 1), k)
    needed = sum(counts)

    if h is None:
        lo = max(d_lo, _min_dim(needed, cap_w))
        h = ctx.draw_int("grid_h", lo, max(d_hi, lo))
        cap_h = _blockable(h)
    if w is None:
        lo = max(d_lo, _min_dim(needed, cap_h))
        w = ctx.draw_int("grid_w", lo, max(d_hi, lo))
        cap_w = _blockable(w)
    if cap_h * cap_w < needed:
        raise ValueError(
            f"color_count={k} with counts {sorted(counts)} needs {needed} "
            f"lattice cells; {h}x{w} provides {cap_h * cap_w}")

    pool = _build_palette(palette_kind, div, rng)
    if len(pool) < k:
        pool += [c for c in rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 9)
                 if c not in pool and c != div]
    colors = pool[:k]

    g = full_grid(h, w, 0)
    for r in _divider_lines(h):
        for c in range(w):
            g[r][c] = div
    for c in _divider_lines(w):
        for r in range(h):
            g[r][c] = div

    band_h, band_w = _bands(h), _bands(w)
    cells = [(bi, bj) for bi in range(cap_h) for bj in range(cap_w)]
    rng.shuffle(cells)
    blocks = []
    for color, cnt in zip(colors, counts):
        blocks += [color] * cnt
    rng.shuffle(blocks)
    for (bi, bj), color in zip(cells, blocks):
        r0, c0 = 5 * bi, 5 * bj
        bh, bw = band_h[bi], band_w[bj]
        if sv_p > 0.0 and rng.random() < sv_p:
            shape = _polyomino(rng, r0, c0, bh, bw, rng.randint(3, min(6, bh * bw)))
            for r, c in shape:
                g[r][c] = color
        else:
            for dr in (1, 2):
                for dc in (1, 2):
                    g[r0 + dr][c0 + dc] = color
    # Divider-colored distractor blocks: excluded by the oracle (mode color).
    for bi, bj in cells[len(blocks):]:
        if rng.random() >= pd:
            continue
        r0, c0 = 5 * bi, 5 * bj
        for dr in (1, 2):
            for dc in (1, 2):
                g[r0 + dr][c0 + dc] = div
    return g
