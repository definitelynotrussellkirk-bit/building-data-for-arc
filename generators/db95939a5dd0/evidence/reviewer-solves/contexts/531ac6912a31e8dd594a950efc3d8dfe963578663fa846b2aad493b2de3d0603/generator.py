"""Generator for db95939a5dd0 (ARC task 4364c1c4) -- two-color compounds split left/right.

Rule (canonical): the background is the grid's mode color. Every 4-connected
non-background component consists of EXACTLY TWO colors stacked vertically
(each color class itself 4-connected, the upper color's rows strictly above
the lower color's rows). For each component independently, the color with
the smaller min-row (top) shifts LEFT by 1 and the other (bottom) shifts
RIGHT by 1; the output is a fresh background canvas holding only the
shifted cells.

Canonical demos are 12..16 x 12..13 (exact set {(12,12),(16,12),(12,13),
(14,13)}) with 1-2 compounds; color regions are blobs 1..5 rows tall and
2..7 cols wide (rectangles, L-shapes, 1-cell notches); the two compounds in
a scene may share one color (test0). Every cell has shift room (no border
clipping), and compounds never collide after shifting: when two compounds
share rows, their bboxes keep >=2 empty columns between them.

Combinatorial axes: grid_h, grid_w, n_shapes, max_region_width (bound),
palette_kind, texture.
Branches witnessed: one vs two compounds, notched/L-shaped regions,
color sharing across compounds, row-overlapping compounds with collision
gap, all canonical dimension pairs via the canonical prior.
Degenerates: one_shape, two_shapes, notched.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "db95939a5dd0"
VERSION = "3.1.0"  # canonical-archetype prior: exact official region profiles (dims/count/bbox/cells/notches/sharing) at >=25% per band; record bbox facts corrected via shared extractor
TASK_ID = "db95939a5dd0"
RULE_HASH = "a742202e03fb"
SUMMARY = (
    "Mode-color background grid (12..16 x 12..14, canonical prior on the "
    "exact official dim pairs). 1..2 4-connected compounds, each exactly "
    "two colors stacked vertically: an upper blob (1..5 rows, 2..7 cols, "
    "possibly L-shaped or 1-cell notched) touching a lower blob; both "
    "color classes 4-connected. Rule: each compound's top color shifts "
    "left 1, its bottom color shifts right 1, onto a fresh background. "
    "Compounds keep collision-free separation (row-disjoint or >=2 empty "
    "bbox columns when rows overlap) and every cell keeps shift room."
)

INVARIANTS = [
    "no color-0 cells (the oracle's mode excludes 0; background is the most frequent non-zero color)",
    "background is the strict mode color",
    "1..2 compounds, each with exactly 2 colors, both classes 4-connected",
    "the upper color's rows sit strictly above the lower color's rows",
    "region bboxes are 1..5 rows by 2..7 cols (canonical envelope)",
    "every cell has shift room (columns 1..w-2); compounds are collision-free",
]

PALETTE_KINDS = ("canonical", "broad")
DEGENERATE_TEXTURES = ("one_shape", "two_shapes", "notched")
HELPFUL_TEXTURES = ()

AXES = {
    "grid_h":          {"type": "int", "default": "band rng 12..16 (canonical prior)", "valid": "12..16"},
    "grid_w":          {"type": "int", "default": "band rng 12..14 (canonical prior)", "valid": "12..14"},
    "n_shapes":        {"type": "int", "default": "band rng 1..2", "valid": "1..2"},
    "max_region_width":{"type": "int", "default": "band 6..7 (bound)", "valid": "4..7"},
    "palette_kind":    {"type": "str", "default": "rng 0.7 canonical / 0.3 broad",
                        "valid": "|".join(PALETTE_KINDS)},
    "texture":         {"type": "str", "default": "none",
                        "valid": "|".join(DEGENERATE_TEXTURES)},
}

_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_DIMS = ((12, 12), (16, 12), (12, 13), (14, 13))
_CANONICAL_COLORS = (1, 2, 3, 4, 6, 7, 8)


def _components(grid):
    """Maximal 4-connected non-background components. Mirrors the oracle's
    background: the most frequent NON-ZERO color (Racket's (mode g)
    excludes 0 by default)."""
    h, w = len(grid), len(grid[0])
    flat = [v for row in grid for v in row]
    nonzero = [v for v in flat if v != 0]
    bg = max(set(nonzero), key=nonzero.count) if nonzero else 0
    seen = [[False] * w for _ in range(h)]
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == bg or seen[r][c]:
                continue
            stack, cells = [(r, c)], []
            seen[r][c] = True
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _CARD:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and grid[nr][nc] != bg):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            comps.append(cells)
    return bg, comps


def _classes(cells, grid):
    """Split a component into its two color classes; returns
    (top_color, top_cells, bot_color, bot_cells) or None."""
    colors = {}
    for (r, c) in cells:
        colors.setdefault(grid[r][c], []).append((r, c))
    if len(colors) != 2:
        return None
    (c1, cells1), (c2, cells2) = sorted(colors.items(),
                                        key=lambda kv: min(r for r, c in kv[1]))
    return c1, cells1, c2, cells2


def _connected(cells):
    S = set(cells)
    start = next(iter(S))
    seen = {start}
    stack = [start]
    while stack:
        r, c = stack.pop()
        for dr, dc in _CARD:
            n = (r + dr, c + dc)
            if n in S and n not in seen:
                seen.add(n)
                stack.append(n)
    return seen == S


def _rule_output(grid):
    """Independent Python re-implementation of the canonical oracle:
    per 2-color compound, top color (smaller min-row) shifts left 1 and
    bottom color shifts right 1 onto a fresh mode-color canvas."""
    bg, comps = _components(grid)
    h, w = len(grid), len(grid[0])
    out = [[bg] * w for _ in range(h)]
    for cells in comps:
        split = _classes(cells, grid)
        if split is None:
            continue
        top, top_cells, bot, bot_cells = split
        for (r, c) in top_cells:
            out[r][c - 1] = top
        for (r, c) in bot_cells:
            out[r][c + 1] = bot
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance: rectangular grid inside
    the declared 12..16 x 12..14 envelope; background is the strict mode
    color; 1..2 non-background components, each with EXACTLY two colors,
    both color classes 4-connected, the upper class's rows strictly above
    the lower's; region bboxes within the canonical 1..5 x 2..7 envelope;
    every cell inside columns 1..w-2 (shift room, no clipping); two
    compounds row-disjoint or >=2 empty bbox columns apart (shift
    collision-free); and the rule visibly fires. Rejects 3-color
    compounds, row-interleaved color classes, border-clipping shapes,
    colliding compounds, and identity draws."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 16 or w > 14:
        errs.append(f"outside declared 12..16 x 12..14 envelope: {h}x{w}")
    if h < 12 or w < 12:
        errs.append(f"below 12x12 canonical floor: {h}x{w}")
    flat = [v for row in grid for v in row]
    if any(not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 9
           for v in flat):
        errs.append("color outside 0..9")
    if 0 in set(flat):
        errs.append("color 0 present (the oracle's mode excludes 0, so 0 "
                    "becomes a foreground color -- outside the canonical family)")
    if errs:
        return errs
    bg, comps = _components(grid)
    counts = {v: flat.count(v) for v in set(flat)}
    if any(v != bg and n >= counts[bg] for v, n in counts.items()):
        errs.append("background is not the strict mode color")
    if not 1 <= len(comps) <= 2:
        errs.append(f"compound count {len(comps)} outside declared 1..2")
    if errs:
        return errs
    spans = []
    for cells in comps:
        split = _classes(cells, grid)
        if split is None:
            errs.append("compound does not have exactly 2 colors")
            return errs
        top, top_cells, bot, bot_cells = split
        for color, cls in ((top, top_cells), (bot, bot_cells)):
            if not _connected(cls):
                errs.append(f"color class {color} is not 4-connected")
            bh = max(r for r, c in cls) - min(r for r, c in cls) + 1
            bw = max(c for r, c in cls) - min(c for r, c in cls) + 1
            if not (1 <= bh <= 5 and 2 <= bw <= 7):
                errs.append(f"region bbox {bh}x{bw} outside canonical 1..5 x 2..7")
            if min(c for r, c in cls) < 1 or max(c for r, c in cls) > w - 2:
                errs.append("region lacks shift room (border clipping)")
        top_r2 = max(r for r, c in top_cells)
        bot_r1 = min(r for r, c in bot_cells)
        if top_r2 >= bot_r1:
            errs.append("color classes are not strictly stacked vertically")
        spans.append((min(r for r, c in cells), max(r for r, c in cells),
                      min(c for r, c in cells), max(c for r, c in cells)))
    if len(spans) == 2:
        (a_r1, a_r2, a_c1, a_c2), (b_r1, b_r2, b_c1, b_c2) = spans
        rows_disjoint = a_r2 < b_r1 or b_r2 < a_r1
        col_gap = max(b_c1 - a_c2, a_c1 - b_c2) - 1
        if not rows_disjoint and col_gap < 2:
            errs.append("compounds collide after shifting (row overlap, "
                        "bbox column gap < 2)")
    if errs:
        return errs
    if _rule_output(grid) == grid:
        errs.append("identity draw: the shifts change nothing")
    return errs


def observe_overrides(grid) -> dict:
    """Realized per-draw values of the exact semantic axes (KRF-0001/0002),
    derived from the grid itself: the number of non-background compounds."""
    _bg, comps = _components(grid)
    return {"n_shapes": len(comps)}


def profile_features(grid):
    """ONE executable feature extractor, used for canonical pairs AND
    generated grids alike (no divergent hand-coded tables). Returns the
    linked profile: (h, w, compound count, per-compound (top bbox, top
    cells, top holes, bottom bbox, bottom cells, bottom holes), and the
    shared-color flag between compounds."""
    h, w = len(grid), len(grid[0])
    bg, comps = _components(grid)
    compounds = []
    color_sets = []
    for cells in comps:
        top, top_cells, bot, bot_cells = _classes(cells, grid)

        def sig(cls):
            r1 = min(r for r, c in cls); r2 = max(r for r, c in cls)
            c1 = min(c for r, c in cls); c2 = max(c for r, c in cls)
            area = (r2 - r1 + 1) * (c2 - c1 + 1)
            return ((r2 - r1 + 1, c2 - c1 + 1), len(cls), area - len(cls))

        compounds.append((sig(top_cells), sig(bot_cells)))
        color_sets.append({grid[r][c] for (r, c) in cells})
    shared = len(color_sets) == 2 and bool(color_sets[0] & color_sets[1])
    return {"h": h, "w": w, "n": len(comps), "compounds": compounds,
            "shared": shared, "bg": bg}


def _cells(row_map):
    """Expand [(row, cols), ...] into a frozenset of (r, c)."""
    return frozenset((r, c) for r, cols in row_map for c in cols)


# Exact canonical region shapes, extracted from the four unique official
# inputs by profile_features (normalized to each region's bbox origin).
# Each archetype: (h, w, shared, (compound, ...)) with compound =
# (top_cells, bottom_cells), the two classes left-aligned and stacked.
_ARCHETYPES = (
    (12, 12, False, (
        (_cells([(0, (0, 4, 5, 6)), (1, (0, 4, 5, 6)),
                 (2, range(7)), (3, range(7))]),
         _cells([(0, range(7)), (1, (0, 1, 2, 3, 6))])),)),
    (16, 12, False, (
        (_cells([(0, (0, 1, 2, 3)), (1, (0, 1, 2, 3)),
                 (2, range(7)), (3, range(7))]),
         _cells([(0, range(7)), (1, range(7)), (2, range(7)), (3, range(7)),
                 (4, (0, 1, 2, 5, 6))])),)),
    (12, 13, False, (
        (_cells([(0, range(3))]),
         _cells([(0, range(3))])),
        (_cells([(0, (0, 1)), (1, (0, 1)), (2, range(4)), (3, range(4)),
                 (4, range(4))]),
         _cells([(0, range(4)), (1, range(4))])),)),
    (14, 13, True, (
        (_cells([(0, (0, 3)), (1, range(4)), (2, range(4))]),
         _cells([(0, range(4))])),
        (_cells([(0, range(3)), (1, range(3))]),
         _cells([(0, range(3)), (1, (0, 2))])),)),
)


def _archetype_sig(arch):
    """The strict profile signature of an archetype: dims, count, the
    multiset of per-compound region signatures, and the sharing flag."""
    h, w, shared, comps = arch
    def sig(cells):
        r2 = max(r for r, c in cells)
        c2 = max(c for r, c in cells)
        area = (r2 + 1) * (c2 + 1)
        return ((r2 + 1, c2 + 1), len(cells), area - len(cells))
    return (h, w, len(comps),
            tuple(sorted((sig(top), sig(bot)) for top, bot in comps)),
            shared)


def _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    """Band-shaped random draw; an override must execute exactly on any
    band, so it is validated against the full declared range (KRF-0001)."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, lo, hi)


def _band_params(difficulty):
    """(h range, w range, shapes range, max region width, region row cap,
    canonical-dim prior, archetype prior). The archetype prior (default
    draws only) reproduces one of the four exact official profiles --
    dims, compound count, exact region shapes/cells/notches, and the
    sharing flag -- at >=25% in every band, while the generalized blob
    family stays reachable outside it."""
    if difficulty == "easy":
        return (12, 13), (12, 13), (1, 2), 6, 4, 0.5, 0.4
    if difficulty == "hard":
        return (13, 16), (12, 14), (2, 2), 7, 5, 0.35, 0.3
    return (12, 15), (12, 14), (1, 2), 7, 5, 0.5, 0.4     # medium / default


def _blob(rng, rows, cols, max_w, notched):
    """One color region: a rows x cols rectangle (cols <= max_w), L-shaped
    (one side column shortened), or with a single 1-cell notch."""
    h_ = rng.randint(1, rows)
    w_ = rng.randint(2, cols)
    w_ = min(w_, max_w)
    cells = {(r, c) for r in range(h_) for c in range(w_)}
    style = rng.random()
    if style < 0.25 and h_ >= 2 and w_ >= 3:
        # L-shape: drop the top row's left or right run
        side = rng.random() < 0.5
        drop = w_ - 1
        cells = {(r, c) for (r, c) in cells
                 if not (r == 0 and (c < drop if side else c >= 1))}
    elif style < 0.45 and h_ >= 2 and h_ * w_ >= 6:
        # single 1-cell notch at a random cell (never disconnects a >=2-row
        # rectangle)
        r, c = rng.randrange(h_), rng.randrange(w_)
        cells.discard((r, c))
    return sorted(cells)


def _place_compound(rng, g, cells_used, spans, top, bot, rows_cap, cols_cap,
                    max_w, notched):
    """Place one two-color compound; returns its bbox span or None."""
    h, w = len(g), len(g[0])
    for _try in range(200):
        top_cells = _blob(rng, rows_cap, cols_cap, max_w, notched)
        bot_cells = _blob(rng, rows_cap, cols_cap, max_w, notched)
        th = max(r for r, c in top_cells) + 1
        bh = max(r for r, c in bot_cells) + 1
        tw = max(c for r, c in top_cells) + 1
        bw = max(c for r, c in bot_cells) + 1
        width = max(tw, bw)
        if width > w - 2 or th + bh > h - 2:
            continue
        r0 = rng.randint(1, h - 1 - (th + bh))
        c0 = rng.randint(1, w - 1 - width)
        abs_top = {(r0 + r, c0 + c) for r, c in top_cells}
        abs_bot = {(r0 + th + r, c0 + c) for r, c in bot_cells}
        # the compound must be one component: top and bottom touch somewhere
        touching = any((r + 1, c) in abs_bot for (r, c) in abs_top)
        if not touching:
            continue
        if (abs_top | abs_bot) & cells_used:
            continue
        # collision-free vs existing compounds: row-disjoint or >=2 col gap
        r1, r2 = r0, r0 + th + bh - 1
        c1 = min(c for r, c in abs_top | abs_bot)
        c2 = max(c for r, c in abs_top | abs_bot)
        clash = False
        for (o_r1, o_r2, o_c1, o_c2) in spans:
            # (a) no cardinal adjacency: compounds must not merge into one
            # component (an empty row or column somewhere between them)
            no_merge = (r2 + 1 < o_r1 or o_r2 + 1 < r1
                        or c2 + 1 < o_c1 or o_c2 + 1 < c1)
            # (b) no shift collision: when rows overlap, bboxes keep >=2
            # empty columns so right-shifted and left-shifted cells never
            # land on the same cell
            rows_overlap = not (r2 < o_r1 or o_r2 < r1)
            shift_clash = rows_overlap and not (c2 + 2 < o_c1 or o_c2 + 2 < c1)
            if not no_merge or shift_clash:
                clash = True
                break
        if clash:
            continue
        for (r, c) in abs_top:
            g[r][c] = top
        for (r, c) in abs_bot:
            g[r][c] = bot
        cells_used |= abs_top | abs_bot
        span = (r1, r2, c1, c2)
        spans.append(span)
        return span
    return None


def _place_archetype_compound(rng, g, cells_used, spans, top_cells, bot_cells,
                              top, bot):
    """Place one archetype compound (exact canonical region shapes, classes
    left-aligned and stacked) at a random lawful position: shift room, no
    overlap/merge, no shift collision vs existing compounds."""
    h, w = len(g), len(g[0])
    th = max(r for r, c in top_cells) + 1
    bh = max(r for r, c in bot_cells) + 1
    width = max(max(c for r, c in top_cells), max(c for r, c in bot_cells)) + 1
    for _try in range(200):
        r0 = rng.randint(1, h - 1 - (th + bh))
        c0 = rng.randint(1, w - 1 - width)
        abs_top = {(r0 + r, c0 + c) for r, c in top_cells}
        abs_bot = {(r0 + th + r, c0 + c) for r, c in bot_cells}
        touching = any((r + 1, c) in abs_bot for (r, c) in abs_top)
        if not touching:
            continue
        if (abs_top | abs_bot) & cells_used:
            continue
        r1, r2 = r0, r0 + th + bh - 1
        c1 = min(c for r, c in abs_top | abs_bot)
        c2 = max(c for r, c in abs_top | abs_bot)
        clash = False
        for (o_r1, o_r2, o_c1, o_c2) in spans:
            no_merge = (r2 + 1 < o_r1 or o_r2 + 1 < r1
                        or c2 + 1 < o_c1 or o_c2 + 1 < c1)
            rows_overlap = not (r2 < o_r1 or o_r2 < r1)
            shift_clash = rows_overlap and not (c2 + 2 < o_c1 or o_c2 + 2 < c1)
            if not no_merge or shift_clash:
                clash = True
                break
        if clash:
            continue
        for (r, c) in abs_top:
            g[r][c] = top
        for (r, c) in abs_bot:
            g[r][c] = bot
        cells_used |= abs_top | abs_bot
        span = (r1, r2, c1, c2)
        spans.append(span)
        return span
    return None


def _generate_archetype(ctx, rng, difficulty):
    """Default-only canonical-archetype draw: one of the four exact
    official profiles (dims, compound count, exact region
    shapes/cells/notches, sharing flag) with fresh colors and positions."""
    arch = _ARCHETYPES[rng.randrange(len(_ARCHETYPES))]
    ah, aw, shared, comps = arch
    h = ctx.draw_int("grid_h", ah, ah)
    w = ctx.draw_int("grid_w", aw, aw)
    n = ctx.draw_int("n_shapes", len(comps), len(comps))
    pool = list(_CANONICAL_COLORS)
    rng.shuffle(pool)
    bg = pool[0]
    colors = pool[1:]
    order = sorted(range(len(comps)),
                   key=lambda i: -(len(comps[i][0]) + len(comps[i][1])))
    placed_ok = False
    for _layout in range(40):
        g = full_grid(h, w, bg)
        cells_used = set()
        spans = []
        placed_ok = True
        for i in order:
            top_cells, bot_cells = comps[i]
            top = colors[(2 * i) % len(colors)]
            bot = colors[(2 * i + 1) % len(colors)]
            if i == 1 and shared:
                top = colors[1]                    # shares compound 0's bottom
            placed = _place_archetype_compound(rng, g, cells_used, spans,
                                               top_cells, bot_cells, top, bot)
            if placed is None:
                placed_ok = False
                break
        if placed_ok:
            break
    if not placed_ok:
        raise ValueError(f"could not place archetype compound on {h}x{w}")
    prof = profile_features(g)
    got = (prof["h"], prof["w"], prof["n"],
           tuple(sorted(prof["compounds"])), prof["shared"])
    if got != _archetype_sig(arch):
        raise ValueError(f"archetype profile mismatch: {got} != "
                         f"{_archetype_sig(arch)}")
    errs = self_check(g, difficulty=difficulty)
    if errs:
        raise ValueError(f"archetype layout violated self_check: {errs}")
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    texture = overrides.get("texture")
    if texture is not None:
        if texture in DEGENERATE_TEXTURES:
            extra = sorted(k for k, v in overrides.items()
                           if k != "texture" and v is not None)
            if extra:
                raise ValueError(
                    f"degenerate texture {texture!r} is a fixed diagnostic "
                    f"layout; it takes no other overrides, got {extra}")
            return _draw_from_degenerate(texture, rng)
        raise ValueError(f"unknown texture {texture!r}; "
                         f"valid: {DEGENERATE_TEXTURES}")

    hr, wr, sr, max_w, rows_cap, p_canon, p_arche = _band_params(difficulty)
    if not overrides and ctx.draw_rng("arche_prior").random() < p_arche:
        return _generate_archetype(ctx, rng, difficulty)
    canon = ctx.draw_rng("canon_prior").random() < p_canon
    if canon and overrides.get("grid_h") is None and overrides.get("grid_w") is None:
        # exact canonical pair, recorded as provenance via degenerate draws
        ch, cw = _CANONICAL_DIMS[rng.randrange(len(_CANONICAL_DIMS))]
        h = ctx.draw_int("grid_h", ch, ch)
        w = ctx.draw_int("grid_w", cw, cw)
    else:
        h = _banded_int(ctx, overrides, "grid_h", hr[0], hr[1], 12, 16)
        w = _banded_int(ctx, overrides, "grid_w", wr[0], wr[1], 12, 14)
    n = _banded_int(ctx, overrides, "n_shapes", sr[0], sr[1], 1, 2)
    max_w = _banded_int(ctx, overrides, "max_region_width", max_w, max_w, 4, 7)

    palette_kind = overrides.get("palette_kind")
    if palette_kind is None:
        palette_kind = ("canonical"
                        if ctx.draw_rng("palette_kind").random() < 0.7
                        else "broad")
    if palette_kind not in PALETTE_KINDS:
        raise ValueError(f"unknown palette_kind {palette_kind!r}")
    pool = list(_CANONICAL_COLORS if palette_kind == "canonical"
                else range(1, 10))
    rng.shuffle(pool)
    bg = pool[0]
    colors = pool[1:]

    # Whole-layout retries: blob shapes/positions are re-rolled per attempt
    # (they are a distribution, not an exact axis); the drawn compound count
    # is never silently shed -- only a genuinely infeasible explicit
    # combination fails loudly.
    g = None
    for _layout in range(60):
        g = full_grid(h, w, bg)
        cells_used = set()
        spans = []
        share = n == 2 and rng.random() < 0.35  # canonical test0 shares a color
        ok = True
        for i in range(n):
            top = colors[(2 * i) % len(colors)]
            bot = colors[(2 * i + 1) % len(colors)]
            if i == 1 and share:
                bot = colors[1]                # reuse compound 0's bottom color
            if _place_compound(rng, g, cells_used, spans, top, bot, rows_cap,
                               max_w, max_w, notched=True) is None:
                ok = False
                break
        if ok:
            break
    else:
        raise ValueError(f"could not place {n} compounds on {h}x{w}")

    errs = self_check(g, difficulty=difficulty)
    if errs:
        raise ValueError(f"internal layout violated self_check: {errs}")
    return g


def _draw_from_degenerate(name, rng):
    """Fixed minimal layouts; every one is a lawful, self_check-clean draw."""
    g = full_grid(12, 12, 1)
    if name == "one_shape":
        for (r, c) in [(2, 3), (2, 4), (2, 5), (3, 3), (3, 4), (3, 5)]:
            g[r][c] = 4
        for (r, c) in [(4, 3), (4, 4), (4, 5), (5, 3), (5, 4), (5, 5)]:
            g[r][c] = 2
        return g
    if name == "two_shapes":
        for (r, c) in [(2, 2), (2, 3), (3, 2), (3, 3)]:
            g[r][c] = 4
        for (r, c) in [(4, 2), (4, 3), (5, 2), (5, 3)]:
            g[r][c] = 2
        for (r, c) in [(2, 8), (2, 9), (3, 8), (3, 9)]:
            g[r][c] = 6
        for (r, c) in [(4, 8), (4, 9), (5, 8), (5, 9)]:
            g[r][c] = 3
        return g
    if name == "notched":
        for (r, c) in [(2, 2), (2, 3), (2, 4), (3, 2), (3, 4)]:
            g[r][c] = 7
        for (r, c) in [(4, 2), (4, 3), (4, 4), (5, 2), (5, 3)]:
            g[r][c] = 5
        return g
    raise ValueError(f"unknown degenerate texture {name!r}")
