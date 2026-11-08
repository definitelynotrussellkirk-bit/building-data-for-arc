"""Generator for cb227835 -- two L-shaped paths between two 8 endpoints.

Rule: the input is a 0-background grid carrying exactly two color-8 cells.
The oracle draws two paths between them (reading order): diagonal-first
(min(|dr|,|dc|) diagonal steps, then ||dr|-|dc|| straight steps along the
major axis) and straight-first (the same two segments swapped). Path cells
become 3, the endpoints stay 8, everything else becomes 0.

Canonical demos are 0-grids with exactly two 8s on h 11..13 x w 13..14,
endpoints anywhere including the border (train[0] uses row 0), deltas
always unequal and at least 2 in both axes (so the two paths visibly
diverge). This generator reproduces that family exactly: uniform endpoint
placement (borders allowed), unequal >=2 deltas, plus the declared edge
texture square_diagonal (|dr| == |dc|, where both constructions coincide
into one diagonal -- crash-free, rule-lawful). Replaces a build that
excluded w=14, border endpoints, and gap 2, and carried five dead axes and
oracle-crashing degenerate textures.

Combinatorial axes (6): grid_h, grid_w, row_gap, col_gap, orientation,
texture.
Branches witnessed: left_to_right / right_to_left pairs, border
endpoints, small/large gaps, major-row vs major-col splits,
square-diagonal coincidence (edge texture).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "db63430eeffa"
VERSION = "2.2.0"
TASK_ID = "db63430eeffa"
RULE_HASH = "3e3bf77eb552"
SUMMARY = ("0-grid with exactly two 8 endpoints; oracle draws diagonal-first "
           "and straight-first L-paths (3) between them. Canonical family: "
           "unequal >=2 row/col deltas, endpoints anywhere incl. borders.")

# Rivals refuted by construction: 'one diagonal between the endpoints' is
# refuted by every draw with |dr| != |dc| (two distinct L-arms always
# appear); 'diagonal-first only' is refuted by the straight-first arm;
# 'endpoints avoid borders' is refuted by border-touching endpoints
# (canonical train[0] uses row 0); 'equal gaps work the same' is relegated
# to the declared square_diagonal edge texture (paths coincide there).
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "the scene has exactly two color-8 endpoints on a 0 background",
    "the endpoints are separated in both row and column (no crash)",
    "normal draws keep |dr| != |dc| with both >= 2 (canonical demos: two visibly distinct L-arms)",
    "endpoints may sit on any border row or column (canonical train[0])",
    "grid envelope h 7..16 x w 7..18 (canonical 11..13 x 13..14)",
]

# The rule reads endpoints in reading order, so p1 is always the
# topmost endpoint: only two true geometries exist (the four corner
# labels would collapse to byte-identical grids).
ORIENTATIONS = ("left_to_right", "right_to_left")
DEGENERATE_TEXTURES = ("square_diagonal",)
# This edge case is rule-lawful: the two canonical constructions coincide.
LAWFUL_DEGENERATE_TEXTURES = DEGENERATE_TEXTURES

AXES = {
    "grid_h":      {"type": "int", "default": "band rng 9..16", "valid": "7..16"},
    "grid_w":      {"type": "int", "default": "band rng 11..18", "valid": "7..18"},
    "row_gap":     {"type": "int", "default": "band rng 2..h-1", "valid": "2..15"},
    "col_gap":     {"type": "int", "default": "band rng 2..w-1", "valid": "2..17"},
    "orientation": {"type": "str", "default": "rng",
                    "valid": "rng|" + "|".join(ORIENTATIONS)},
    "texture":     {"type": "str", "default": "none",
                    "valid": "none|" + "|".join(DEGENERATE_TEXTURES)},
}


_INTEGER_AXES = ("grid_h", "grid_w", "row_gap", "col_gap")


def _validate_generate_request(seed, sample_index, difficulty, overrides):
    """Reject controls the generator cannot honor exactly.

    Validation happens before ``gen_ctx`` so booleans/floats/strings are not
    normalized into valid-looking values and unknown names cannot disappear.
    ``None`` remains the documented no-override value for known axes only.
    """
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer (not bool)")
    if difficulty is not None and (
        type(difficulty) is not str
        or difficulty not in {"easy", "medium", "hard"}
    ):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an exact integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    for label in _INTEGER_AXES:
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise TypeError(
                f"{label} override must be an exact integer (not bool)"
            )
    for label in ("orientation", "texture"):
        value = overrides.get(label)
        if value is not None and type(value) is not str:
            raise TypeError(f"{label} override must be a string or None")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance (all 4 unique canonical
    pairs satisfy them): rectangular grid inside the declared envelope
    h 7..16 x w 7..18; cells use only {0, 8}; exactly two 8 endpoints,
    separated by at least two rows and columns (the declared gap domain;
    0, 1, or 3+ eights and adjacent/same-row/same-column pairs are rejected).
    The square_diagonal texture (|dr| == |dc|) is lawful and accepted."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    bad = sorted({v for row in grid for v in row} - {0, 8})
    if bad:
        errs.append(f"colors outside {{0,8}}: {bad}")
        return errs
    if not 7 <= h <= 16:
        errs.append(f"height {h} outside declared envelope 7..16")
    if not 7 <= w <= 18:
        errs.append(f"width {w} outside declared envelope 7..18")
    eights = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    if len(eights) != 2:
        errs.append(f"expected exactly two 8 endpoints, found {len(eights)}")
        return errs
    (r1, c1), (r2, c2) = eights
    row_gap = abs(r2 - r1)
    col_gap = abs(c2 - c1)
    if row_gap < 2:
        errs.append(
            f"row gap {row_gap} is below the declared minimum 2"
        )
    if col_gap < 2:
        errs.append(
            f"column gap {col_gap} is below the declared minimum 2"
        )
    return errs


def observe_overrides(grid):
    """Realized exact-axis values (KRF-0002): the endpoint deltas, derived
    from the grid itself."""
    eights = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
              if v == 8]
    (r1, c1), (r2, c2) = eights
    return {"row_gap": abs(r2 - r1), "col_gap": abs(c2 - c1)}


def profile_signature(grid):
    """Complete linked profile used by the exact canonical-prior audit."""
    eights = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    ]
    (r1, c1), (r2, c2) = eights
    direction = "left_to_right" if c1 < c2 else "right_to_left"
    return (
        len(grid),
        len(grid[0]),
        abs(r2 - r1),
        abs(c2 - c1),
        direction,
    )


def rule_mirror(grid):
    """Python parity oracle; materialized training outputs remain Racket-only."""
    h, w = len(grid), len(grid[0])
    eights = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    ]
    (r1, c1), (r2, c2) = eights
    dr, dc = r2 - r1, c2 - c1
    row_step = 1 if dr > 0 else -1 if dr < 0 else 0
    col_step = 1 if dc > 0 else -1 if dc < 0 else 0
    diagonal_steps = min(abs(dr), abs(dc))
    straight_steps = abs(abs(dr) - abs(dc))
    major_is_row = abs(dr) > abs(dc)
    path = set()

    def walk(diagonal_first):
        row, col = r1, c1
        segments = (
            (("diagonal", diagonal_steps), ("straight", straight_steps))
            if diagonal_first
            else (("straight", straight_steps), ("diagonal", diagonal_steps))
        )
        for kind, steps in segments:
            for _ in range(steps):
                path.add((row, col))
                if kind == "diagonal":
                    row += row_step
                    col += col_step
                elif major_is_row:
                    row += row_step
                else:
                    col += col_step
        path.add((row, col))

    walk(diagonal_first=True)
    walk(diagonal_first=False)
    out = full_grid(h, w, 0)
    for row, col in path:
        out[row][col] = 3
    out[r1][c1] = 8
    out[r2][c2] = 8
    return out


def _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    """Band-shaped random draw; overrides validated against the full valid
    range (an override must execute exactly on any band, KRF-0001)."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int_strict(label, valid_lo, valid_hi)
    return ctx.draw_int_strict(label, lo, hi)


def _draw_gap(ctx, label, lo, hi, exclude):
    """Keyed draw in [lo, hi] avoiding one excluded value, with recorded
    provenance for the exact-axis contract (no silent post-draw nudges)."""
    lo2, hi2 = lo, hi
    if exclude is not None and exclude == lo2:
        lo2 += 1
    elif exclude is not None and exclude == hi2:
        hi2 -= 1
    for _ in range(5):
        v = ctx.draw_int(label, lo2, hi2)
        if v != exclude:
            return v
    v2 = exclude + 1 if exclude < hi2 else exclude - 1
    return ctx.draw_int(label, v2, v2)


def _band_params(difficulty):
    if difficulty == "easy":
        return (9, 11), (11, 13)
    if difficulty == "hard":
        return (13, 16), (14, 18)
    return (11, 13), (13, 14)   # medium / default: the canonical dims


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_generate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    texture = overrides.get("texture")
    extra = sorted(k for k, v in overrides.items()
                   if k != "texture" and v is not None)
    if texture in DEGENERATE_TEXTURES:
        if extra:
            raise ValueError(
                f"edge texture {texture!r} is a fixed layout; it takes no "
                f"other overrides, got {extra}")
        return _draw_square_diagonal(ctx)
    if texture not in (None, "none"):
        raise ValueError(f"unknown texture {texture!r}; valid: "
                         f"none|{'|'.join(DEGENERATE_TEXTURES)}")
    (h_lo, h_hi), (w_lo, w_hi) = _band_params(difficulty)

    # Canonical-form prior (KRF-0003): ~25% of fully-unoverridden draws pin
    # one of the four official linked tuples (h, w, |dr|, |dc|, direction)
    # through keyed draws; endpoint positions stay random (border cells
    # included, exactly as canonical).
    if not any(k in overrides for k in
               ("grid_h", "grid_w", "row_gap", "col_gap", "orientation")):
        if ctx.draw_rng("canonical_prior").random() < 0.25:
            ch, cw, crg, ccg, cori = ctx.draw_choice(
                "canonical_form",
                [(12, 14, 7, 9, "right_to_left"),
                 (13, 13, 9, 6, "left_to_right"),
                 (11, 14, 2, 10, "right_to_left"),
                 (13, 14, 11, 7, "left_to_right")])
            for label, value in (("grid_h", ch), ("grid_w", cw),
                                 ("row_gap", crg), ("col_gap", ccg)):
                overrides[label] = value
                ctx.overrides[label] = value
                ctx.draw_int_strict(label, value, value)
            overrides["orientation"] = cori
            ctx.overrides["orientation"] = cori
            ctx.draw_choice("orientation", [cori])
    h = _banded_int(ctx, overrides, "grid_h", h_lo, h_hi, 7, 16)
    w = _banded_int(ctx, overrides, "grid_w", w_lo, w_hi, 7, 18)

    # Gaps pick a feasible domain BEFORE drawing (no post-draw nudges): an
    # explicit gap is honored exactly, an internally drawn gap excludes the
    # other gap's value so internal draws always show two distinct arms.
    # Explicit equal gaps are the lawful square_diagonal coincidence branch.
    row_over = "row_gap" in overrides and overrides["row_gap"] is not None
    col_over = "col_gap" in overrides and overrides["col_gap"] is not None
    if row_over:
        row_gap = ctx.draw_int_strict("row_gap", 2, 15)
    if col_over:
        col_gap = ctx.draw_int_strict("col_gap", 2, 17)
    if not row_over:
        row_gap = _draw_gap(ctx, "row_gap", 2, min(h - 1, 15),
                            col_gap if col_over else None)
    if not col_over:
        col_gap = _draw_gap(ctx, "col_gap", 2, min(w - 1, 17), row_gap)
    # Fit the dims to explicit gaps: internal dims grow to accommodate;
    # an explicit dim that cannot host its gap fails loudly.
    if row_gap > h - 1:
        if "grid_h" in overrides and overrides["grid_h"] is not None:
            raise ValueError(f"row_gap {row_gap} does not fit grid_h {h}")
        h = row_gap + 1
    if col_gap > w - 1:
        if "grid_w" in overrides and overrides["grid_w"] is not None:
            raise ValueError(f"col_gap {col_gap} does not fit grid_w {w}")
        w = col_gap + 1

    orientation = overrides.get("orientation") or "rng"
    if orientation == "rng":
        orientation = rng.choice(ORIENTATIONS)
    if orientation not in ORIENTATIONS:
        raise ValueError(f"unknown orientation {orientation!r}; valid: {ORIENTATIONS}")
    r_lo = rng.randint(0, h - 1 - row_gap)
    c_lo = rng.randint(0, w - 1 - col_gap)
    r_hi, c_hi = r_lo + row_gap, c_lo + col_gap
    if orientation == "left_to_right":
        p1, p2 = (r_lo, c_lo), (r_hi, c_hi)
    else:
        p1, p2 = (r_lo, c_hi), (r_hi, c_lo)
    g = full_grid(h, w, 0)
    g[p1[0]][p1[1]] = 8
    g[p2[0]][p2[1]] = 8
    return g


def _draw_square_diagonal(ctx):
    """|dr| == |dc|: both path constructions coincide into one diagonal.
    Declared edge case; crash-free and rule-lawful. Dims and gaps are keyed
    draws under their declared labels (KRF-0004 provenance)."""
    h = ctx.draw_int("grid_h", 9, 12)
    w = ctx.draw_int("grid_w", 11, 14)
    gap = ctx.draw_int("row_gap", 3, min(h - 1, 6))
    ctx.draw_int("col_gap", gap, gap)   # records the shared square gap
    rng = ctx.draw_rng("layout")
    r_lo = rng.randint(0, h - 1 - gap)
    c_lo = rng.randint(0, w - 1 - gap)
    g = full_grid(h, w, 0)
    g[r_lo][c_lo] = 8
    g[r_lo + gap][c_lo + gap] = 8
    return g
