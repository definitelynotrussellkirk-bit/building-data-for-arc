"""Generator for dc155169ea57 (ARC task 84ba50d3) -- shapes fall to a red line; thin ones pass through.

Rule (canonical, color-literal): the grid has an azure (8) background, one
full-width red (2) row ("the line"), and blue (1) 4-connected shapes above
it. Every shape falls downward. A "thin" shape (every row holds a single
cell, i.e. a vertical bar or singleton) falls through the line until its
lowest cell lands on the grid's last row, and punches an 8-hole in the line
at each column it occupies. A "wide" shape (some row holds >=2 cells) falls
until its lowest wide row rests on the row just above the line; any thin
tail below that wide row overwrites line cells and can extend below the
line. Original shape cells above the line are erased to the 8 background.

The generator emits canonical-style instances: 8 background, exactly one
full 2-row with >=3 free rows above and below it, and 1..6 mutually
non-touching color-1 shapes above it (singletons, vertical bars, wide
polyominoes). Canonical dims 7x7, 9x9, 11x11, 18x18 lie inside the
envelope (was: 0 background, h 14..26 / w 14..24 -- outside every
canonical demo).

Combinatorial axes: grid_h, grid_w, line_row, n_shapes, thin_frac, texture.
Branches witnessed: thin singleton pass-through, thin bar pass-through,
wide domino/polyomino resting on the line, wide shape whose tail overlaps
the line, shapes touching row 0, mixed thin+wide crowds.
Degenerates: all_wide, all_thin, one_shape.
"""
from __future__ import annotations

import math

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dc155169ea57"
VERSION = "3.4.0"
TASK_ID = "dc155169ea57"
RULE_HASH = "c0f1818b0fb2"
SUMMARY = (
    "8-bg grid with one full row of 2 (the line) and color-1 shapes above "
    "it. Thin shapes (vertical bars, incl. singletons) fall through the "
    "line to the last row and punch 8-holes in it; wide shapes fall until "
    "their lowest wide row rests just above the line (thin tails may "
    "overlap the line); originals erase to the 8 background. Grid size, "
    "line row, thin/wide mix, shape sizes and positions vary; canonical "
    "dims 7..18 sit inside the generated envelope."
)

INVARIANTS = [
    "background is color 8; palette is exactly {1, 2, 8} (oracle is color-literal)",
    "exactly one row is all color 2 (the line); no other cell is 2",
    "every color-1 shape is a 4-connected component strictly above the line",
    "thin shapes (vertical bars incl. singletons) pass through to the last row and hole the line at 8",
    "wide shapes rest their lowest wide row just above the line; tails may overlap it",
    "at least one shape visibly moves (no identity draws)",
]

DEGENERATE_TEXTURES = ("all_wide", "all_thin", "one_shape")
HELPFUL_TEXTURES = ()
LAWFUL_DEGENERATE_TEXTURES = DEGENERATE_TEXTURES

# Explicit overrides are diagnostic draws; the ordinary lesson schedule has
# two distinct separating witnesses in every four consecutive samples.
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("thin_above_wide", "ordinary", "wide_above_thin")
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]

AXES = {
    "grid_h":    {"type": "int", "default": "band rng 7..30", "valid": "7..30"},
    "grid_w":    {"type": "int", "default": "band rng 7..30", "valid": "7..30"},
    "line_row":  {"type": "int", "default": "band rng mid..h-4", "valid": "3..26"},
    "n_shapes":  {"type": "int", "default": "band rng 1..6", "valid": "1..6"},
    "thin_frac": {"type": "float", "default": "rng 0.3..0.6", "valid": "0.0..1.0", "exact": False,
                  "description": "approximate rounded composition, with mixed-branch floors"},
    "texture":   {"type": "str", "default": "none",
                  "valid": "|".join(("none",) + DEGENERATE_TEXTURES)},
}


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _poly(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    return _norm(cells)


def _row_counts(cells):
    rows = {}
    for r, c in cells:
        rows[r] = rows.get(r, 0) + 1
    return rows


def observe_overrides(grid):
    """Report per-draw realized values of exact semantic axes (KRF-0002),
    derived from the returned grid itself: line_row is the unique full
    color-2 row; n_shapes is the number of 4-connected color-1 components
    strictly above it. Grids without a full 2-row report line_row None."""
    h, w = len(grid), len(grid[0])
    line_rows = [r for r in range(h) if all(v == 2 for v in grid[r])]
    if not line_rows:
        return {"line_row": None, "n_shapes": 0}
    line = line_rows[0]
    return {"line_row": line,
            "n_shapes": len(_components(grid, 1, below=line))}


def profile_signature(grid):
    """Complete linked profile used by the canonical-prior audit."""
    h, w = len(grid), len(grid[0])
    observed = observe_overrides(grid)
    line = observed["line_row"]
    shapes = _components(grid, 1, below=line)
    n_wide = sum(_has_wide_row(shape) for shape in shapes)
    return (
        h,
        w,
        line,
        len(shapes),
        n_wide,
        len(shapes) - n_wide,
    )


def rule_mirror(grid):
    """Python parity oracle; materialized training outputs remain Racket-only."""
    h, w = len(grid), len(grid[0])
    line = next(
        r for r in range(h) if all(value == 2 for value in grid[r])
    )
    shapes = _components(grid, 1, below=line)
    result = [
        [8 if r < line and value == 1 else value
         for value in row]
        for r, row in enumerate(grid)
    ]
    pass_columns = set()
    for shape in shapes:
        row_counts = _row_counts(shape)
        wide_rows = [
            row for row, count in row_counts.items() if count > 1
        ]
        if wide_rows:
            delta = line - 1 - max(wide_rows)
        else:
            delta = h - 1 - max(row for row, _ in shape)
            pass_columns.update(col for _, col in shape)
        for row, col in shape:
            new_row = row + delta
            if 0 <= new_row < h:
                result[new_row][col] = 1
    for col in pass_columns:
        result[line][col] = 8
    return result


def _has_wide_row(cells):
    return any(v > 1 for v in _row_counts(cells).values())


def _wide_shape(rng, size):
    for _ in range(30):
        s = _poly(rng, size)
        if _has_wide_row(s):
            return s
    return [(0, 0), (0, 1)]   # fallback domino (wide)


def _thin_shape(rng, k):
    return [(i, 0) for i in range(k)]   # vertical bar


def _components(grid, color, *, below):
    """Maximal 4-connected components of `color` in rows < below."""
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for r in range(below):
        for c in range(w):
            if grid[r][c] != color or seen[r][c]:
                continue
            stack, cells = [(r, c)], []
            seen[r][c] = True
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _CARD:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < below and 0 <= nc < w
                            and not seen[nr][nc] and grid[nr][nc] == color):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance: rectangular 7..30 grid,
    palette exactly {1, 2, 8} with modal 8; exactly one full row of 2 (the
    line) with >=3 free rows above and below and no other 2 cells; every
    color-1 cell strictly above the line; at least one shape; and the rule
    visibly fires (some thin bar/singleton, or a wide shape whose lowest
    wide row is above the line). Rejects identity/no-op instances and any
    destructive mutation of the line or shapes."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"exceeds ARC 30x30 limit: {h}x{w}")
    if h < 7 or w < 7:
        errs.append(f"below 7x7 canonical floor: {h}x{w}")
    flat = [v for row in grid for v in row]
    if any(not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 9
           for v in flat):
        errs.append("color outside 0..9")
    if set(flat) - {1, 2, 8}:
        errs.append("palette outside {1, 2, 8}")
    if flat and flat.count(8) <= max(flat.count(1), flat.count(2)):
        errs.append("background 8 is not the unique modal color")
    line_rows = [r for r in range(h) if all(v == 2 for v in grid[r])]
    if len(line_rows) != 1:
        errs.append(f"expected exactly one full 2-row, got {len(line_rows)}")
    if errs:
        return errs
    line = line_rows[0]
    if line < 3 or line > h - 4:
        errs.append(f"line row {line} lacks 3 free rows above/below in h={h}")
    if any(grid[r][c] == 2 for r in range(h) for c in range(w) if r != line):
        errs.append("color-2 cell outside the line")
    if any(grid[r][c] == 1 for r in range(line, h) for c in range(w)):
        errs.append("color-1 cell on or below the line")
    comps = _components(grid, 1, below=line)
    if not comps:
        errs.append("no color-1 shapes above the line")
    fires = False
    for cells in comps:
        wide_rows = [r for r, cnt in _row_counts(cells).items() if cnt > 1]
        if not wide_rows or max(wide_rows) < line - 1:
            fires = True   # thin bars always fall; wide shape still airborne
    if comps and not fires:
        errs.append("identity draw: no shape moves under the rule")
    return errs


def _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    """Band-shaped random draw; an override must execute exactly on any
    band, so it is validated against the full declared range (KRF-0001)."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, lo, hi)


def _band_params(difficulty):
    """(h range, w range, n range, thin bar max, wide size max) per band."""
    if difficulty == "easy":
        return (7, 11), (7, 11), (1, 3), 3, 4
    if difficulty == "hard":
        return (15, 30), (15, 30), (3, 6), 7, 8
    return (10, 16), (10, 16), (2, 4), 5, 6     # medium / default


def generate(seed, sample_index, *, difficulty=None, **overrides):
    overrides = _validated_overrides(seed, sample_index, difficulty, overrides)
    scheduled_witness = not overrides and sample_index % 2 == 0
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    texture = overrides.get("texture")
    if texture == "none":
        # Explicit 'none' names the normal path (AXES declares it); it is not
        # an unknown texture and takes no special handling.
        texture = None
    if texture is not None:
        if texture in DEGENERATE_TEXTURES:
            extra = sorted(k for k, v in overrides.items()
                           if k != "texture" and v is not None)
            if extra:
                raise _incompatible(
                    f"degenerate texture {texture!r} is a fixed diagnostic "
                    f"layout; it takes no other overrides, got {extra}",
                    "texture", *extra)
            return _draw_from_degenerate(texture, rng)
        raise ValueError(f"unknown texture {texture!r}; "
                         f"valid: {DEGENERATE_TEXTURES}")

    hr, wr, nr, thin_max, wide_max = _band_params(difficulty)
    wide_min = 3 if scheduled_witness else 2
    if scheduled_witness:
        nr = (max(2, nr[0]), nr[1])
        hr = (max(9, hr[0]), hr[1])

    # Canonical-form prior (KRF-0003): ~30% of fully-unoverridden draws pin
    # one of the four exact official linked tuples
    # (side, line_row, n_shapes, n_wide, n_thin), recorded through keyed
    # draws; shapes/positions/widths within each form stay random.
    canon_thin = None
    if not any(k in overrides for k in
               ("grid_h", "grid_w", "line_row", "n_shapes", "thin_frac")):
        if ctx.draw_rng("canonical_prior").random() < 0.30:
            mixed_forms = [(9, 5, 3, 1, 2), (11, 6, 3, 1, 2),
                           (18, 8, 5, 3, 2)]
            # Witness slots require both branches. The compensated ordinary
            # prior retains a 1/4 marginal for each canonical linked form.
            forms = (mixed_forms if scheduled_witness else
                     [(7, 3, 1, 0, 1)] * 3 + mixed_forms)
            ch, cl, cn, cwide, cthin = ctx.draw_choice("canonical_form", forms)
            # Record through keyed draws AND make the pinned values visible
            # to this function's downstream override branches (gen_ctx holds
            # its own copy of the caller's overrides).
            for label, value in (("grid_h", ch), ("grid_w", ch),
                                 ("line_row", cl), ("n_shapes", cn)):
                overrides[label] = value
                ctx.overrides[label] = value
                ctx.draw_int(label, value, value)
            canon_thin = cthin

    # Thin/wide mix is resolved before the width draw because it sets the
    # width budget: thin bars need 1 column, wide shapes need >=2, and bands
    # keep >=1 empty column between them.
    frac_ov = overrides.get("thin_frac")
    if canon_thin is not None:
        frac = canon_thin / ctx.overrides["n_shapes"]
    elif frac_ov is not None:
        frac = float(frac_ov)
        if not 0.0 <= frac <= 1.0:
            raise ValueError(f"thin_frac must lie in [0, 1], got {frac_ov}")
    else:
        frac = ctx.draw_rng("thin_frac").uniform(0.3, 0.6)

    def _composition(count):
        n_thin = min(int(round(count * frac)), count)
        if frac > 0:
            n_thin = max(1, n_thin)      # a normal draw always has a passer
        if frac < 1 and count >= 2:
            n_thin = min(n_thin, count - 1)  # and (usually) a resting wide
        return n_thin, count - n_thin

    # Shape count vs width budget: with n_wide wide shapes the bands need
    # w >= n + n_wide + (n - 1). Exact overrides win; an impossible explicit
    # (n, w) pair fails loudly. When only the caller's width is fixed, the
    # random shape count shrinks to fit (never below 1).
    if overrides.get("n_shapes") is not None:
        n = ctx.draw_int("n_shapes", 1, 6)
        n_thin, n_wide = _composition(n)
        budget = n + (wide_min - 1) * n_wide + (n - 1)
        w = _banded_int(ctx, overrides, "grid_w",
                        max(wr[0], budget), max(wr[1], budget), 7, 30)
        if w < budget:
            raise _incompatible(
                f"n_shapes={n} with {n_wide} wide needs grid_w >= {budget}, "
                f"got {w}", "n_shapes", "grid_w")
    else:
        w = _banded_int(ctx, overrides, "grid_w", wr[0], wr[1], 7, 30)
        feasible_counts = []
        for candidate in range(nr[0], nr[1] + 1):
            candidate_thin, candidate_wide = _composition(candidate)
            budget = candidate + (wide_min - 1) * candidate_wide + (candidate - 1)
            if budget <= w:
                feasible_counts.append(candidate)
        if not feasible_counts:
            # A fixed narrow width overrides a band's preferred count floor;
            # choose a feasible count BEFORE recording it in GenCtx.
            feasible_counts = [candidate for candidate in range(1, nr[0])
                               if 2 * candidate + (wide_min - 1) * _composition(candidate)[1] - 1 <= w]
        if not feasible_counts:
            raise ValueError(f"grid_w={w} cannot fit any lawful shape")
        # Draw from the feasible domain up front. The old path drew a larger
        # n_shapes and silently decremented it, so returned-grid observation
        # disagreed with GenCtx provenance on narrow width overrides.
        n = ctx.draw_choice("n_shapes", feasible_counts)
        n_thin, n_wide = _composition(n)

    # Line row vs height: the line keeps >=3 free rows above and below.
    if overrides.get("line_row") is not None:
        line = ctx.draw_int("line_row", 3, 26)
        h = _banded_int(ctx, overrides, "grid_h",
                        max(hr[0], line + 4), min(max(hr[1], line + 4), 30),
                        7, 30)
        if line > h - 4:
            raise _incompatible(f"line_row={line} needs grid_h >= {line + 4}, got {h}",
                                "line_row", "grid_h")
    else:
        h = _banded_int(ctx, overrides, "grid_h", hr[0], hr[1], 7, 30)
        line_floor = 5 if scheduled_witness else 3
        line = ctx.draw_int("line_row", max(line_floor, min(h - 4, h // 2 - 2)), h - 4)

    flags = [True] * n_thin + [False] * n_wide
    rng.shuffle(flags)

    # Place shapes left-to-right in column bands separated by >=1 empty
    # column, so intended shapes stay distinct 4-connected components. The
    # reserve keeps enough columns for the remaining shapes' minimum widths,
    # so a wide shape is never squeezed into a thin bar.
    min_sw = [1 if t else wide_min for t in flags]
    g = full_grid(h, w, 8)
    col = rng.randint(0, min(2, w - (sum(min_sw) + n - 1)))
    for i in range(n):
        reserve = sum(min_sw[i + 1:]) + (n - 1 - i)
        max_sw = (w - col) - reserve
        if flags[i]:
            shape = _thin_shape(rng, rng.randint(1, min(thin_max, line - 1)))
        else:
            shape = None
            for _try in range(40):
                cand = _wide_shape(rng, rng.randint(wide_min, wide_max))
                sh = max(r for r, c in cand) + 1
                sw = max(c for r, c in cand) + 1
                if sh <= line - 1 and wide_min <= sw <= max_sw:
                    shape = cand
                    break
            if shape is None:
                shape = [(0, c) for c in range(wide_min)]  # feasible support bar
        sh = max(r for r, c in shape) + 1
        sw = max(c for r, c in shape) + 1
        # shapes may sit anywhere above the line, including flush against it
        # (bottom row line-1); a wide shape whose lowest wide row lands there
        # is "resting" (dr=0) -- lawful and witnessed by canonical outputs.
        top_hi = line - sh
        if n_thin == 0 and i == 0:
            # all-wide draw (thin_frac=0): designate a visible faller so the
            # instance is never an identity under the rule.
            counts = _row_counts(shape)
            max_wide = max(r for r, cnt in counts.items() if cnt > 1)
            top_hi = min(top_hi, line - 2 - max_wide)
        top = rng.randint(0, top_hi)
        for (r, c) in shape:
            g[top + r][col + c] = 1
        if i < n - 1:
            gap_max = (w - (col + sw)) - sum(min_sw[i + 1:]) - (n - 2 - i)
            col += sw + rng.randint(1, min(2, gap_max))
    for c in range(w):
        g[line][c] = 2
    if scheduled_witness:
        _inject_projection_witness(g, line, ctx.draw_rng("projection_witness"),
                                   thin_first=sample_index % 4 == 0)

    errs = self_check(g, difficulty=difficulty)
    if errs:
        raise ValueError(f"internal layout violated self_check: {errs}")
    return g


def _draw_from_degenerate(name, rng):
    h, w = 16, 16
    line = 11
    g = full_grid(h, w, 8)
    if name in ("all_wide", "one_shape"):
        for (r, c) in [(2, 2), (2, 3), (3, 2)]:
            g[r][c] = 1
    if name == "all_thin":
        for r in range(2, 6):
            g[r][4] = 1
        g[6][9] = 1
    if name == "all_wide":
        for (r, c) in [(4, 8), (4, 9), (5, 8), (5, 9)]:
            g[r][c] = 1
    for c in range(w):
        g[line][c] = 2
    return g


def _incompatible(message, *axes):
    error = ValueError(message)
    error.incompatible_axes = tuple(axes)
    return error


def _validated_overrides(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise ValueError("seed must be an integer, not bool or a coercible scalar")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty is not None and (type(difficulty) is not str or
                                  difficulty not in ("easy", "medium", "hard")):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override keys: {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "line_row", "n_shapes"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")
    fraction = overrides.get("thin_frac")
    if fraction is not None and (type(fraction) not in (int, float) or
                                not 0 <= fraction <= 1 or not math.isfinite(fraction)):
        raise ValueError("thin_frac must be a finite number in [0, 1]")
    texture = overrides.get("texture")
    if texture is not None and type(texture) is not str:
        raise ValueError("texture must be a string")
    return {key: value for key, value in overrides.items()
            if value is not None and not (key == "texture" and value == "none")}


def _inject_projection_witness(grid, line, rng, *, thin_first):
    """Replace two donors inside one original column band; preserve counts."""
    components = _components(grid, 1, below=line)
    thin = rng.choice([shape for shape in components if not _has_wide_row(shape)])
    wide = rng.choice([shape for shape in components if _has_wide_row(shape)])
    left = min(c for _, c in wide)
    right = max(c for _, c in wide)
    for r, c in thin + wide:
        grid[r][c] = 8
    # Each witness teaches connectivity AND the lowest qualifying support
    # row. The wide donor has an upper >=3-cell row, a lower 2-cell row,
    # and a 1-cell tail. Keep a blank row before the detached singleton.
    if thin_first:
        thin_row = rng.randrange(line - 4)
        wide_row = rng.randrange(thin_row + 2, line - 2)
    else:
        wide_row = rng.randrange(line - 4)
        thin_row = rng.randrange(wide_row + 4, line)
    width = rng.randint(3, right - left + 1)
    wide_left = rng.randint(left, right - width + 1)
    lower_left = rng.randrange(wide_left, wide_left + width - 1)
    tail_col = lower_left + rng.randrange(2)
    thin_col = rng.choice([c for c in range(wide_left, wide_left + width)
                           if c != tail_col])
    grid[thin_row][thin_col] = 1
    for col in range(wide_left, wide_left + width):
        grid[wide_row][col] = 1
    grid[wide_row + 1][lower_left] = 1
    grid[wide_row + 1][lower_left + 1] = 1
    grid[wide_row + 2][tail_col] = 1


def projection_group_rival(grid):
    """Group blue cells by contiguous occupied column runs, ignoring rows."""
    h, w = len(grid), len(grid[0])
    line = next(r for r in range(h) if all(value == 2 for value in grid[r]))
    occupied = [c for c in range(w) if any(grid[r][c] == 1 for r in range(line))]
    runs = []
    for col in occupied:
        if not runs or col != runs[-1][-1] + 1:
            runs.append([])
        runs[-1].append(col)
    groups = [[(r, c) for c in run for r in range(line) if grid[r][c] == 1]
              for run in runs]
    result = [[8 if r < line and value == 1 else value
               for value in row] for r, row in enumerate(grid)]
    pass_columns = set()
    for group in groups:
        wide_rows = [r for r, count in _row_counts(group).items() if count > 1]
        if wide_rows:
            delta = line - 1 - max(wide_rows)
        else:
            delta = h - 1 - max(r for r, _ in group)
            pass_columns.update(c for _, c in group)
        for r, c in group:
            if 0 <= r + delta < h:
                result[r + delta][c] = 1
    for col in pass_columns:
        result[line][col] = 8
    return result


def _projection_refuted(grid):
    return rule_mirror(grid) != projection_group_rival(grid)


def strict_canonical_like(grid):
    return self_check(grid)


def schedule_profile(seed, sample_index, difficulty=None):
    return ("thin_above_wide" if sample_index % 4 == 0 else
            "wide_above_thin" if sample_index % 4 == 2 else "ordinary")


def _support_row_rival(grid, mode):
    """Keep connected objects and thin passage; use a competing support row."""
    h, w = len(grid), len(grid[0])
    line = next(r for r, row in enumerate(grid) if all(value == 2 for value in row))
    groups = _components(grid, 1, below=line)
    result = [[8 if r < line and value == 1 else value
               for value in row] for r, row in enumerate(grid)]
    pass_columns = set()
    for shape in groups:
        counts = _row_counts(shape)
        wide_rows = [r for r, count in counts.items() if count > 1]
        if wide_rows:
            if mode == "lowest_cell":
                anchor = max(counts)
            elif mode == "highest_support":
                anchor = min(wide_rows)
            elif mode == "max_width":
                widest = max(counts.values())
                anchor = max(r for r in wide_rows if counts[r] == widest)
            else:
                raise ValueError("unknown support-row rival")
            delta = line - 1 - anchor
        else:
            delta = h - 1 - max(counts)
            pass_columns.update(c for _, c in shape)
        for r, c in shape:
            if 0 <= r + delta < h:
                result[r + delta][c] = 1
    for c in pass_columns:
        result[line][c] = 8
    return result


def lowest_cell_rival(grid):
    return _support_row_rival(grid, "lowest_cell")


def highest_support_rival(grid):
    return _support_row_rival(grid, "highest_support")


def max_width_rival(grid):
    return _support_row_rival(grid, "max_width")


def _support_rows_refuted(grid):
    expected = rule_mirror(grid)
    return all(rival(grid) != expected for rival in
               (lowest_cell_rival, highest_support_rival, max_width_rival))


SEMANTIC_RIVALS = {
    "projection_groups": projection_group_rival,
    "lowest_cell": lowest_cell_rival,
    "highest_support": highest_support_rival,
    "max_width": max_width_rival,
}
CANONICAL_SHORTCUTS = {name: rival for name, rival in SEMANTIC_RIVALS.items()
                       if name != "lowest_cell"}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {"disconnected_projection": _projection_refuted,
                      "support_rows": _support_rows_refuted}
WITNESS_RIVALS = {"disconnected_projection": ["projection_groups"],
                  "support_rows": ["lowest_cell", "highest_support", "max_width"]}
