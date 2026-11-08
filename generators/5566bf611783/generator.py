"""Generator for arc_additional_puzzle_bank_volume20:H140.

Color-5 walls partition the input into 4-connected chambers.  In each
chamber, the output preserves existing 2/3 markers and fills every zero with
the marker majority: 2 when red wins, 3 when green wins, and 8 on an exact
tie.

The five official demonstrations share a linked two-column/one-bridge wall
profile.  Version 5 keeps those profiles as deterministic schedule anchors,
but also schedules explicit discriminator instances.  Every four consecutive
default draws follow anchor/discriminator/broad/discriminator, so any
three-demonstration rotation contains a chamber where red is the majority even
though green is present.  That chamber refutes the strongest canonical
shortcut, "green present dominates", while retaining broad nuisance variation
in dimensions, wall topology, marker locations, and optional ties.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5566bf611783"
VERSION = "5.0.0"  # strict override contract + scheduled rival witnesses
TASK_ID = "5566bf611783"
RULE_HASH = "06016d46a01f"
SUMMARY = (
    "0-bg grid with color-5 walls (full divider columns/rows plus "
    "connecting segments) carving regions that hold a sparse scatter of "
    "color-2 and color-3 markers. Rule: per 4-connected non-5 region, "
    "fill its 0-cells with the majority of {2,3} (tie -> 8)."
)

INVARIANTS = [
    "palette is exactly {0, 2, 3, 5}",
    "at least one full color-5 divider line (row or column)",
    "walls partition the grid into at least two 4-connected regions",
    "every region carries 1..6 markers (colors 2/3)",
    "grid dims stay within 8..16 x 9..18",
]

TOPOLOGY_KINDS = ("canonical_cross", "cols_only", "mixed_grid", "segments")
DEGENERATE_TEXTURES: tuple = ()
HELPFUL_TEXTURES = TOPOLOGY_KINDS

# One complete linked official profile is used on every schedule anchor.
# A profile is:
#   (height, width, full-divider columns, bridge row,
#    (left, top-middle, bottom-middle, right) (n2, n3) marker counts).
# Marker positions inside their named chamber remain nuisance variation.
_CANONICAL_PROFILES = (
    (9, 13, (4, 8), 4, ((3, 0), (1, 0), (0, 1), (0, 3))),
    (10, 14, (5, 9), 5, ((3, 0), (1, 0), (0, 1), (0, 3))),
    (9, 12, (3, 8), 4, ((2, 2), (1, 0), (0, 1), (1, 2))),
    (10, 13, (4, 8), 5, ((2, 0), (1, 0), (1, 0), (0, 4))),
    (9, 13, (4, 8), 4, ((3, 0), (2, 0), (0, 1), (0, 3))),
)
_CANONICAL_SIGNATURES = frozenset(_CANONICAL_PROFILES)

_H_LO, _H_HI = 8, 16
_W_LO, _W_HI = 9, 18

AXES = {
    "grid_h":        {"type": "int", "default": "band rng 8..11 easy, "
                          "9..12 medium, 12..16 hard; schedule anchors use "
                          "canonical 9..10", "valid": "8..16"},
    "grid_w":        {"type": "int", "default": "band rng 9..12 easy, "
                          "11..15 medium, 14..18 hard; schedule anchors use "
                          "canonical 12..14", "valid": "9..18"},
    "div_cols":      {"type": "int", "default": "band rng 1..2 easy, "
                          "1..3 medium/hard (2 on schedule anchors)",
                      "valid": "1..3"},
    "div_rows":      {"type": "int", "default": "band rng 0..1 (0 on "
                          "schedule anchors)", "valid": "0..2"},
    "tie_mode":      {"type": "bool", "default": "rng 20% true (engineers "
                          "one exact-tie region)", "valid": "true|false"},
    "topology_kind": {"type": "str", "default": "rng helpful",
                      "valid": "|".join(TOPOLOGY_KINDS)},
    "texture":       {"type": "str", "default": "alias for topology_kind",
                      "valid": "|".join(TOPOLOGY_KINDS)},
}

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

_ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("canonical_anchor", "discriminator", "broad")
_SCHEDULE = ("canonical_anchor", "discriminator", "broad", "discriminator")
MIN_STRICT_FRAC = 1.0
AXIS_ALIASES = {"texture": "topology_kind"}

# Every public override tuple rejected by generate() is declared here.  Equal
# alias values are accepted; only contradictory aliases are incompatible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = (
    [
        {"topology_kind": "canonical_cross", "div_cols": value}
        for value in (1, 3)
    ]
    + [
        {"texture": "canonical_cross", "div_cols": value}
        for value in (1, 3)
    ]
    + [
        {"topology_kind": "canonical_cross", "div_rows": value}
        for value in (1, 2)
    ]
    + [
        {"texture": "canonical_cross", "div_rows": value}
        for value in (1, 2)
    ]
    + [
        {"topology_kind": kind, "div_rows": value}
        for kind in ("cols_only", "segments")
        for value in (1, 2)
    ]
    + [
        {"texture": kind, "div_rows": value}
        for kind in ("cols_only", "segments")
        for value in (1, 2)
    ]
    + [{"topology_kind": "mixed_grid", "div_rows": 0}]
    + [{"texture": "mixed_grid", "div_rows": 0}]
    + [
        {"topology_kind": left, "texture": right}
        for left in TOPOLOGY_KINDS
        for right in TOPOLOGY_KINDS
        if left != right
    ]
)


def _validate_request(seed, sample_index, difficulty, overrides) -> None:
    """Reject coercive or undeclared public inputs before building GenCtx."""
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer (not bool/float/string)")
    if type(sample_index) is not int:
        raise TypeError(
            "sample_index must be a literal integer (not bool/float/string)"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _ALLOWED_DIFFICULTIES:
        if difficulty is not None and type(difficulty) is not str:
            raise TypeError("difficulty must be None, 'easy', 'medium', or 'hard'")
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown!r}")

    for name in ("grid_h", "grid_w", "div_cols", "div_rows"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} override must be a literal integer")
    tie_mode = overrides.get("tie_mode")
    if tie_mode is not None and type(tie_mode) is not bool:
        raise TypeError("tie_mode override must be a literal boolean")
    for name in ("topology_kind", "texture"):
        value = overrides.get(name)
        if value is not None:
            if type(value) is not str:
                raise TypeError(f"{name} override must be a string")
            if value not in TOPOLOGY_KINDS:
                raise ValueError(
                    f"unknown {name} {value!r}; valid: {TOPOLOGY_KINDS}"
                )


def schedule_profile(seed, sample_index, difficulty=None):
    """Public finite schedule used by the semantic census."""
    _validate_request(seed, sample_index, difficulty, {})
    return _SCHEDULE[sample_index % LESSON_SCHEDULE_PERIOD]


def _regions(grid):
    """4-connected components of non-5 cells (the oracle's chambers)."""
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 5 or seen[r][c]:
                continue
            stack, cells = [(r, c)], []
            seen[r][c] = True
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _DIRS4:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and grid[nr][nc] != 5):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            out.append(cells)
    return out


def _full_lines(grid):
    """(rows that are all 5, columns that are all 5)."""
    h, w = len(grid), len(grid[0])
    rows = [r for r in range(h) if all(v == 5 for v in grid[r])]
    cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    return rows, cols


def _canonical_role_cells(h, w, cols, bridge_row):
    """Cells in the canonical left/top-mid/bottom-mid/right roles."""
    c0, c1 = cols
    return (
        [(r, c) for r in range(h) for c in range(c0)],
        [(r, c)
         for r in range(bridge_row)
         for c in range(c0 + 1, c1)],
        [(r, c)
         for r in range(bridge_row + 1, h)
         for c in range(c0 + 1, c1)],
        [(r, c) for r in range(h) for c in range(c1 + 1, w)],
    )


def canonical_profile_signature(grid):
    """Return the complete linked official-profile signature, or ``None``.

    This deliberately checks the exact wall layout before counting markers;
    dimensions, topology, and regional outcomes cannot be recombined into a
    broad "canonical-like" tuple.
    """
    if not grid or not grid[0]:
        return None
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return None
    full_rows, full_cols = _full_lines(grid)
    cols = tuple(full_cols)
    if full_rows or len(cols) != 2:
        return None
    c0, c1 = cols
    bridge_rows = [
        r for r in range(h)
        if all(grid[r][c] == 5 for c in range(c0, c1 + 1))
    ]
    if len(bridge_rows) != 1:
        return None
    bridge_row = bridge_rows[0]
    expected_walls = {(r, c) for r in range(h) for c in cols}
    expected_walls.update(
        (bridge_row, c) for c in range(c0, c1 + 1)
    )
    actual_walls = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 5
    }
    if actual_walls != expected_walls:
        return None
    role_counts = tuple(
        (
            sum(grid[r][c] == 2 for r, c in cells),
            sum(grid[r][c] == 3 for r, c in cells),
        )
        for cells in _canonical_role_cells(h, w, cols, bridge_row)
    )
    return h, w, cols, bridge_row, role_counts


def _draw_canonical_profile(g, profile, rng):
    """Draw one linked profile, randomizing markers only within each role."""
    h, w, cols, bridge_row, role_counts = profile
    if (len(g), len(g[0])) != (h, w):
        raise ValueError("canonical profile dimensions do not match canvas")
    c0, c1 = cols
    for c in cols:
        for r in range(h):
            g[r][c] = 5
    for c in range(c0, c1 + 1):
        g[bridge_row][c] = 5
    roles = _canonical_role_cells(h, w, cols, bridge_row)
    for cells, (n2, n3) in zip(roles, role_counts):
        if n2 + n3 > len(cells):
            raise ValueError("canonical marker profile does not fit chamber")
        spots = cells[:]
        rng.shuffle(spots)
        for r, c in spots[:n2]:
            g[r][c] = 2
        for r, c in spots[n2:n2 + n3]:
            g[r][c] = 3


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance: rectangular grid inside
    the declared envelope, palette exactly {0,2,3,5}, at least one full
    color-5 divider line, at least two 4-connected regions, and every
    region carrying 1..6 markers.  Band ranges are defaults only;
    difficulty is deliberately unused."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 9
           for row in grid for v in row):
        errs.append("color outside 0..9")
    if not (_H_LO <= h <= _H_HI and _W_LO <= w <= _W_HI):
        errs.append(f"dims {h}x{w} outside valid "
                    f"{_H_LO}..{_H_HI} x {_W_LO}..{_W_HI}")
    bad = {v for row in grid for v in row if v not in (0, 2, 3, 5)}
    if bad:
        errs.append(f"palette must stay within {{0,2,3,5}}, found "
                    f"{sorted(bad)}")
    frows, fcols = _full_lines(grid)
    if not frows and not fcols:
        errs.append("no full color-5 divider line (row or column)")
    regions = _regions(grid)
    if len(regions) < 2:
        errs.append("walls do not partition the grid into >=2 regions")
    for i, cells in enumerate(regions):
        marks = sum(1 for r, c in cells if grid[r][c] in (2, 3))
        if marks == 0:
            errs.append(f"region {i} has no 2/3 marker")
        elif marks > 6:
            errs.append(f"region {i} has {marks} markers (max 6)")
    return errs


def observe_overrides(grid) -> dict:
    """Realized per-draw values of the exact semantic axes (KRF-0002),
    derived from the returned grid: full 5-divider row/column counts and
    whether any region ties its {2,3} vote."""
    frows, fcols = _full_lines(grid)
    tie = False
    for cells in _regions(grid):
        c2 = sum(1 for r, c in cells if grid[r][c] == 2)
        c3 = sum(1 for r, c in cells if grid[r][c] == 3)
        if c2 == c3:
            tie = True
            break
    return {"div_rows": len(frows), "div_cols": len(fcols),
            "tie_mode": tie}


def _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    """Band-shaped random draw; an explicit override is validated against
    the full declared valid range (overrides are band-independent,
    KRF-0001)."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int_strict(label, valid_lo, valid_hi)
    return ctx.draw_int_strict(label, lo, hi)


def _sample_spaced(rng, lo, hi, k, gap):
    """k positions in [lo, hi] pairwise >= gap apart (None when infeasible)."""
    span = hi - lo + 1
    if span < k * gap - (gap - 1):
        return None
    for _ in range(40):
        picks = sorted(rng.sample(range(lo, hi + 1), k))
        if all(picks[i + 1] - picks[i] >= gap for i in range(k - 1)):
            return picks
    return None


def _draw_topology(g, kind, n_cols, n_rows, rng):
    """Lay the color-5 wall network; returns nothing (g mutated)."""
    h, w = len(g), len(g[0])
    if kind == "canonical_cross":
        cols = _sample_spaced(rng, 1, w - 2, 2, 3)
        if cols is None:
            raise ValueError(
                f"canonical_cross needs room for 2 divider columns with a "
                f"chamber between them on width {w}")
        for c in cols:
            for r in range(h):
                g[r][c] = 5
        seg_r = rng.randint(1, h - 2)
        for c in range(cols[0], cols[-1] + 1):
            g[seg_r][c] = 5
        return
    cols = _sample_spaced(rng, 1, w - 2, n_cols, 2) or \
        _sample_spaced(rng, 1, w - 2, n_cols, 1)
    if cols is None:
        raise ValueError(f"{n_cols} divider columns do not fit width {w}")
    rows = _sample_spaced(rng, 1, h - 2, n_rows, 2) or \
        _sample_spaced(rng, 1, h - 2, n_rows, 1)
    if rows is None:
        raise ValueError(f"{n_rows} divider rows do not fit height {h}")
    for c in cols:
        for r in range(h):
            g[r][c] = 5
    for r in rows:
        for c in range(w):
            g[r][c] = 5
    if kind == "segments":
        n_seg = rng.randint(1, 2)
        for _ in range(n_seg):
            sr = rng.randint(1, h - 2)
            if all(g[sr][c] == 5 for c in range(w)):
                continue
            if len(cols) >= 2 and rng.random() < 0.5:
                c0, c1 = sorted(rng.sample(cols, 2))
            else:
                c0 = cols[rng.randrange(len(cols))]
                c1 = rng.randint(c0, w - 1)
            for c in range(c0, c1 + 1):
                if g[sr][c] == 0:
                    g[sr][c] = 5


def _fill_markers(g, tie_mode, rng, *, force_red_mixed=False):
    """Scatter 1..6 markers per chamber.

    ``force_red_mixed`` creates the counterexample branch required by the
    lesson schedule: one chamber has exactly two 2s, one 3, and at least one
    zero, while another chamber has a 3-majority.  Thus both majority outputs
    remain represented and the green-present shortcut is visibly false.
    """
    regions = _regions(g)
    if len(regions) < 2:
        raise ValueError("wall network produced fewer than 2 regions")
    n = len(regions)

    forced_index = None
    if force_red_mixed:
        candidates = [index for index, cells in enumerate(regions) if len(cells) >= 4]
        if not candidates:
            raise ValueError("discriminator needs a chamber with at least four cells")
        forced_index = max(candidates, key=lambda index: len(regions[index]))
        green_index = next(index for index in range(n) if index != forced_index)
        outcomes = [rng.choice((2, 3)) for _ in range(n)]
        outcomes[forced_index] = 2
        outcomes[green_index] = 3
    else:
        outcomes = [2, 3] + [rng.choice((2, 3)) for _ in range(n - 2)]
        rng.shuffle(outcomes)

    if tie_mode:
        biggest = max(range(n), key=lambda index: len(regions[index]))
        outcomes[biggest] = 8

    for index, (cells, outcome) in enumerate(zip(regions, outcomes)):
        if index == forced_index:
            counts = (2, 1)
        elif outcome == 8:
            k = min(rng.choice((1, 2, 3)), len(cells) // 2)
            counts = (1, 0) if k < 1 else (k, k)
        else:
            total = rng.randint(1, min(6, len(cells)))
            win = rng.randint(total // 2 + 1, total)
            counts = (
                (win, total - win)
                if outcome == 2
                else (total - win, win)
            )
        spots = cells[:]
        rng.shuffle(spots)
        for marker_index, (row, col) in enumerate(spots[:sum(counts)]):
            g[row][col] = 2 if marker_index < counts[0] else 3


def rule_mirror(grid):
    """Pure Python mirror of the canonical chamber-majority rule."""
    output = [row[:] for row in grid]
    for cells in _regions(grid):
        n2 = sum(grid[row][col] == 2 for row, col in cells)
        n3 = sum(grid[row][col] == 3 for row, col in cells)
        fill = 2 if n2 > n3 else 3 if n3 > n2 else 8
        for row, col in cells:
            if grid[row][col] == 0:
                output[row][col] = fill
    return output


def _green_present_dominates(grid):
    """Canonical-fitting rival: any green in a non-tie chamber wins."""
    output = [row[:] for row in grid]
    for cells in _regions(grid):
        n2 = sum(grid[row][col] == 2 for row, col in cells)
        n3 = sum(grid[row][col] == 3 for row, col in cells)
        fill = 8 if n2 == n3 else 3 if n3 > 0 else 2
        for row, col in cells:
            if grid[row][col] == 0:
                output[row][col] = fill
    return output


def _has_red_majority_with_green(grid) -> bool:
    if self_check(grid):
        return False
    return any(
        sum(grid[row][col] == 2 for row, col in cells)
        > sum(grid[row][col] == 3 for row, col in cells)
        > 0
        and any(grid[row][col] == 0 for row, col in cells)
        for cells in _regions(grid)
    )


def strict_canonical_like(grid):
    """The canonical manifold is exactly the lawful chamber grammar."""
    return self_check(grid)


SEMANTIC_WITNESSES = {
    "red_majority_with_green": _has_red_majority_with_green,
}
SEMANTIC_RIVALS = {
    "green_present_dominates": _green_present_dominates,
}
WITNESS_RIVALS = {
    "red_majority_with_green": ["green_present_dominates"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    rng = ctx.draw_rng("layout")
    band = difficulty or "medium"
    if band == "easy":
        h_lo, h_hi, w_lo, w_hi = 8, 11, 9, 12
        c_lo, c_hi, r_lo, r_hi = 1, 2, 0, 1
    elif band == "hard":
        h_lo, h_hi, w_lo, w_hi = 12, 16, 14, 18
        c_lo, c_hi, r_lo, r_hi = 2, 3, 1, 2
    else:
        h_lo, h_hi, w_lo, w_hi = 9, 12, 11, 15
        c_lo, c_hi, r_lo, r_hi = 1, 3, 0, 1

    topology_override = overrides.get("topology_kind")
    texture_override = overrides.get("texture")
    if topology_override is not None:
        topology_override = ctx.draw_choice("topology_kind", TOPOLOGY_KINDS)
    if texture_override is not None:
        texture_override = ctx.draw_choice("texture", TOPOLOGY_KINDS)
    if (
        topology_override is not None
        and texture_override is not None
        and topology_override != texture_override
    ):
        raise ValueError(
            "incompatible overrides topology_kind/texture: aliases disagree"
        )
    explicit_topology = topology_override or texture_override
    cols_override = overrides.get("div_cols")
    rows_override = overrides.get("div_rows")

    has_override = any(value is not None for value in overrides.values())
    scheduled = "custom" if has_override else schedule_profile(
        seed, sample_index, difficulty
    )

    if scheduled == "canonical_anchor":
        profile_index = (sample_index // LESSON_SCHEDULE_PERIOD) % len(
            _CANONICAL_PROFILES
        )
        profile = _CANONICAL_PROFILES[profile_index]
        h, w, _, _, role_counts = profile
        ctx.draw_choice("topology_kind", ("canonical_cross",))
        ctx.draw_int_strict("div_cols", 2, 2)
        ctx.draw_int_strict("div_rows", 0, 0)
        ctx.draw_int_strict("grid_h", h, h)
        ctx.draw_int_strict("grid_w", w, w)
        tie_mode = any(n2 == n3 for n2, n3 in role_counts)
        ctx.draw_choice("tie_mode", (tie_mode,))
        grid = full_grid(h, w, 0)
        _draw_canonical_profile(grid, profile, rng)
        return grid

    if explicit_topology is not None:
        topology = explicit_topology
        if topology == "canonical_cross":
            if cols_override is not None and cols_override != 2:
                raise ValueError("topology canonical_cross requires div_cols=2")
            if rows_override is not None and rows_override != 0:
                raise ValueError("topology canonical_cross requires div_rows=0")
        if (
            topology in ("cols_only", "segments")
            and rows_override is not None
            and rows_override != 0
        ):
            raise ValueError(f"topology {topology} requires div_rows=0")
        if topology == "mixed_grid" and rows_override == 0:
            raise ValueError("topology mixed_grid requires div_rows>=1")
    else:
        pool = []
        for kind in TOPOLOGY_KINDS:
            if rows_override is not None:
                if kind == "mixed_grid" and rows_override == 0:
                    continue
                if (
                    kind in ("cols_only", "segments", "canonical_cross")
                    and rows_override != 0
                ):
                    continue
            if (
                cols_override is not None
                and kind == "canonical_cross"
                and cols_override != 2
            ):
                continue
            pool.append(kind)
        if not pool:
            raise ValueError(
                f"div_cols={cols_override} div_rows={rows_override} fits no topology"
            )
        topology = ctx.draw_choice("topology_kind", pool)

    if topology == "canonical_cross":
        n_cols = ctx.draw_int_strict("div_cols", 2, 2)
        n_rows = ctx.draw_int_strict("div_rows", 0, 0)
    elif topology == "cols_only":
        n_cols = _banded_int(ctx, overrides, "div_cols", c_lo, c_hi, 1, 3)
        n_rows = ctx.draw_int_strict("div_rows", 0, 0)
    elif topology == "mixed_grid":
        n_cols = _banded_int(ctx, overrides, "div_cols", c_lo, c_hi, 1, 3)
        n_rows = _banded_int(
            ctx, overrides, "div_rows", max(1, r_lo), r_hi, 1, 2
        )
    else:
        n_cols = _banded_int(ctx, overrides, "div_cols", c_lo, c_hi, 1, 3)
        n_rows = ctx.draw_int_strict("div_rows", 0, 0)

    height = _banded_int(ctx, overrides, "grid_h", h_lo, h_hi, _H_LO, _H_HI)
    width = _banded_int(ctx, overrides, "grid_w", w_lo, w_hi, _W_LO, _W_HI)
    if scheduled == "discriminator":
        tie_mode = ctx.draw_choice("tie_mode", (False,))
    else:
        tie_mode = ctx.draw_choice(
            "tie_mode", (False, False, False, False, True)
        )

    grid = full_grid(height, width, 0)
    if topology == "canonical_cross":
        _draw_topology(grid, "canonical_cross", 2, 0, rng)
    elif topology == "cols_only":
        _draw_topology(grid, "cols_only", n_cols, 0, rng)
    elif topology == "mixed_grid":
        _draw_topology(grid, "mixed_grid", n_cols, n_rows, rng)
    else:
        _draw_topology(grid, "segments", n_cols, 0, rng)
    _fill_markers(
        grid,
        tie_mode,
        rng,
        force_red_mixed=(scheduled == "discriminator"),
    )
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"constructed invalid generator instance: {errors}")
    return grid


def _validate_labeled_pair(pair, label):
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output grids"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label} input: {error}" for error in errors]
    if pair["output"] != rule_mirror(pair["input"]):
        return [f"{label} output disagrees with chamber majority"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named canonical-fitting rival remains live."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons = []
    for index, demo in enumerate(demos):
        reasons.extend(_validate_labeled_pair(demo, f"demo {index}"))
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
        return reasons
    query_errors = self_check(query["input"])
    reasons.extend(f"query input: {error}" for error in query_errors)
    if query.get("output") is not None and not query_errors:
        if query["output"] != rule_mirror(query["input"]):
            reasons.append("query output disagrees with chamber majority")
    if reasons:
        return reasons

    expected_query = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        if all(
            competitor(demo["input"]) == demo["output"] for demo in demos
        ) and competitor(query["input"]) != expected_query:
            reasons.append(
                f"named competitor {name!r} fits every demo but changes the query"
            )
    return reasons
