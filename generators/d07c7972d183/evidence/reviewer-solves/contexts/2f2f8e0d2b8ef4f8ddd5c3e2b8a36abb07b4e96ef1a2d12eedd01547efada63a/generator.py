"""Binary row-period continuation for ARC 017c7c7b.

Generate inputs only. The unchanged canonical Racket rule supplies labels:
continue the least row period to h + floor(h/2), recoloring every 1 to 2.
The diagnostic rivals below are authoring checks, never label authorities.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "d07c7972d183"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "6358a7ca0f4d"
SUMMARY = (
    "A binary 0/1 grid has a least row period of 2..6 with at least two "
    "repeated-row cues. Continue that period to h + floor(h/2) rows and "
    "replace every 1 by 2 throughout the output. First-row repetitions "
    "inside a motif and either top-left color are lawful. Default lessons "
    "interleave canonical-size, broad, and randomized distinguishing inputs."
)
INVARIANTS = [
    "input palette is exactly {0, 1}",
    "the emitted grid's smallest row period is in [2, 6]",
    "period <= height - 2, with at least two repeated-row cues",
    "input dimensions are 4..18 rows by 3..12 columns",
    "foreground/background each occur in at least two motif rows",
    "the canonical Racket rule is pinned by normalized RULE_HASH",
]
AXES = {
    "grid_h": {"type": "int", "default": "scheduled 6/9 or mixed draws in 4..18", "valid": "4..18"},
    "grid_w": {"type": "int", "default": "scheduled 3 or mixed draws in 3..12", "valid": "3..12"},
    "period": {"type": "int", "default": "scheduled or mixed draws in 2..6", "valid": "2..6"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"grid_h": h, "period": p}
    for h in range(4, 8) for p in range(2, 7) if p > h - 2
]
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 8
SCHEDULE_PROFILES = ("canonical", "distinguishing", "broad")
_DENSITY_PROBABILITY = {"sparse": 0.18, "balanced": 0.32, "dense": 0.68, "disconnected": 0.45}


def schedule_profile(seed, sample_index, difficulty=None):
    """Eight positions: three canonical, four distinguishing, one broad."""
    return ("canonical", "distinguishing", "broad", "distinguishing",
            "canonical", "distinguishing", "canonical", "distinguishing")[sample_index % 8]


def _draw_axis(ctx, name, lo, hi):
    # A uniform quarter keeps every legal value reachable in every band;
    # the remaining draws use the shared difficulty bias and same exact bounds.
    if ctx.draw_int(name + "_uniform_roll", 0, 3) == 0:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int_diff(name, lo, hi)


def _draw_period_and_height(ctx, overrides):
    height = overrides.get("grid_h")
    period = overrides.get("period")
    if height is not None and period is not None and period > height - 2:
        raise ValueError(f"period={period} requires grid_h >= {period + 2}; got {height}")
    period_hi = min(6, height - 2) if height is not None else 6
    period = _draw_axis(ctx, "period", 2, period_hi)
    height = _draw_axis(ctx, "grid_h", period + 2, 18)
    return period, height


def _draw_width(ctx, minimum=3):
    return _draw_axis(ctx, "grid_w", minimum, 12)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return a deterministic input; explicit controls select general sampling."""
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for key, lo, hi in (("grid_h", 4, 18), ("grid_w", 3, 12), ("period", 2, 6)):
        value = overrides.get(key)
        if value is not None and (type(value) is not int or not lo <= value <= hi):
            raise ValueError(f"{key} must be an integer in {lo}..{hi}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    controlled = any(value is not None for value in overrides.values())
    if not controlled and profile == "distinguishing":
        period = ctx.draw_int("period", 6, 6)
        height = ctx.draw_int("grid_h", 9, 9)
        connected = ctx.draw_int("witness_morphology", 0, 3) != 0
        width = _draw_width(ctx, minimum=5 if connected else 3)
        motif = _draw_distinguishing_rows(width, sample_index,
            ctx.draw_rng("distinguishing_rows"), connected=connected)
    else:
        if not controlled and profile == "canonical":
            height = ctx.draw_int("grid_h", 6, 6)
            width = ctx.draw_int("grid_w", 3, 3)
            period = ctx.draw_int("period", 2, 4)
        else:
            period, height = _draw_period_and_height(ctx, overrides)
            width = _draw_width(ctx)
        roll = ctx.draw_int("density_profile_roll", 0, 9)
        density = "sparse" if roll <= 5 else ("balanced" if roll <= 7 else ("dense" if roll == 8 else "disconnected"))
        motif = _draw_base_rows(period, width, height=height,
            probability=_DENSITY_PROBABILITY[density], connected=density != "disconnected",
            prefer_zero_majority=density != "dense", rng=ctx.draw_rng("base_rows"))
    return [list(motif[r % period]) for r in range(height)]


def _draw_distinguishing_rows(width, sample_index, rng, *, connected=False):
    """Construct a varied P=6 motif whose separate-column continuation is wrong.

    Motif A,B,A,D,C,E has one column 000010; over nine rows that column
    looks 5-periodic. Column zero disproves whole-row period 5. A repeats
    prematurely, and h=9 distinguishes floor-half from three other extents.
    The two scheduled witness positions choose different D rows. Their grids
    cannot be duplicates, even when the random A/B/C draws happen to coincide.
    """
    if connected:
        # Sparse contiguous rows share a spine; C joins the special edge cell.
        # At width >= 5 this anchor bound keeps zeros the strict majority even
        # when D and E both equal A, so connectivity is not a modal-color trick.
        anchor = rng.randint(1, (2 * width - 5) // 5)
        left = rng.randint(1, anchor)
        a = [int(col <= anchor) for col in range(width)]
        b = [int(left <= col <= anchor) for col in range(width)]
        c = [1] * width
    else:
        special = rng.randrange(1, width)
        other = rng.choice([col for col in range(1, width) if col != special])
        a, b, c = [[int(rng.random() < 0.32) for _ in range(width)] for _ in range(3)]
        a[0], a[special] = 1, 0
        b[0], b[special], b[other] = 0, 0, 1
        c[0], c[special] = 1, 1
    d = a if sample_index % 4 == 1 else b
    e = rng.choice((a, b))
    return [list(row) for row in (a, b, a, d, c, e)]


def _draw_spined_row(width, anchor, probability, rng):
    left = right = anchor
    while left > 0 and rng.random() < probability:
        left -= 1
    while right + 1 < width and rng.random() < probability:
        right += 1
    return [int(left <= col <= right) for col in range(width)]


def _draw_base_rows(period, width, *, height, probability, connected, prefer_zero_majority, rng):
    """Keep the prior morphology mixture, testing period on the emitted grid.

    No cell is fixed to background and no row is required to be unique.
    A finite motif such as A,B,A may look 2-periodic before repetition; its
    emitted sequence A,B,A,A,B,A correctly has period 3.
    """
    anchor = rng.randrange(width)
    for _ in range(512):
        rows = ([_draw_spined_row(width, anchor, probability, rng) for _ in range(period)]
                if connected else [[int(rng.random() < probability) for _ in range(width)] for _ in range(period)])
        flat = [v for row in rows for v in row]
        ones = sum(flat)
        emitted = [rows[r % period] for r in range(height)]
        if (ones >= period + 1 and flat.count(0) >= period
                and sum(1 in row for row in rows) >= 2
                and sum(0 in row for row in rows) >= 2
                and sum(len(set(row)) > 1 for row in rows) >= 2
                and ((ones <= len(flat) // 2) == prefer_zero_majority)
                and _minimal_row_period(emitted) == period):
            return rows
    # Bounded, exact-period fallbacks retain the same domain constraints.
    if not prefer_zero_majority:
        first = [0] + [1] * (width - 1)
        other = [1] * (width - 1) + [0]
    else:
        first, other = [0] * width, [0] * width
        extra = (anchor + 1) % width
        first[anchor] = first[extra] = other[anchor] = 1
    return [first] + [list(other) for _ in range(period - 1)]


def _minimal_row_period(grid):
    for period in range(1, len(grid) + 1):
        if all(grid[r] == grid[r % period] for r in range(len(grid))):
            return period
    return len(grid)


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "period": _minimal_row_period(grid)}


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the declared periodic grammar, including malformed-cell input."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"]
    height, width = len(grid), len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and non-empty"]
    errors = []
    if not 4 <= height <= 18:
        errors.append(f"height {height} outside 4..18")
    if not 3 <= width <= 12:
        errors.append(f"width {width} outside 3..12")
    values = [v for row in grid for v in row]
    if any(type(v) is not int or v not in (0, 1) for v in values):
        return errors + ["input palette must contain only integer colors 0 and 1"]
    if set(values) != {0, 1}:
        errors.append("input palette must contain both 0 and 1")
    if height + height // 2 > 30:
        errors.append("extended output would exceed ARC's 30-row limit")
    if sum(len(set(row)) > 1 for row in grid) < 2:
        errors.append("at least two rows must visibly contain both colors")
    if errors:
        return errors
    period = _minimal_row_period(grid)
    if not 2 <= period <= 6:
        return [f"smallest row period {period} outside 2..6"]
    if period > height - 2:
        return [f"period {period} leaves fewer than two visible repeated-row cues"]
    rows = grid[:period]
    motif = [v for row in rows for v in row]
    if sum(motif) < period + 1:
        errors.append("period motif is too sparse to show a substantive foreground")
    if motif.count(0) < period:
        errors.append("period motif is too dense to show a substantive background")
    if sum(1 in row for row in rows) < 2:
        errors.append("foreground must be supported by at least two motif rows")
    if sum(0 in row for row in rows) < 2:
        errors.append("background must be supported by at least two motif rows")
    return errors


def strict_canonical_like(grid):
    """The stated binary periodic domain, not an exact shape/palette proxy."""
    return self_check(grid)


def _diagnostic_output(grid, *, period=None, height=None):
    """Python authoring mirror for rivals; production labels still use Racket."""
    p = _minimal_row_period(grid) if period is None else period
    h = len(grid) + len(grid) // 2 if height is None else height
    return [[2 if v == 1 else v for v in grid[r % p]] for r in range(h)]


def _corner_zero(grid):
    out = _diagnostic_output(grid)
    out[0][0] = 0
    return out


def _first_recurrence(grid):
    p = next((r for r in range(1, len(grid)) if grid[r] == grid[0]), len(grid))
    return _diagnostic_output(grid, period=p)


def _columnwise(grid):
    columns = list(zip(*grid))
    periods = [next(p for p in range(1, len(col) + 1)
                    if all(col[r] == col[r % p] for r in range(len(col)))) for col in columns]
    return [[2 if col[r % p] == 1 else col[r % p] for col, p in zip(columns, periods)]
            for r in range(len(grid) + len(grid) // 2)]


def _fixed_nine(grid):
    return _diagnostic_output(grid, height=9)


def _add_three(grid):
    return _diagnostic_output(grid, height=len(grid) + 3)


def _ceil_half(grid):
    return _diagnostic_output(grid, height=len(grid) + (len(grid) + 1) // 2)


def _repeat_input(grid):
    return _diagnostic_output(grid, period=len(grid))


def _early_repeat(grid):
    return any(grid[r] == grid[0] for r in range(1, _minimal_row_period(grid)))


def _column_alias(grid):
    return _columnwise(grid) != _diagnostic_output(grid)


SEMANTIC_RIVALS = {
    "corner_zero": _corner_zero,
    "first_recurrence": _first_recurrence,
    "columnwise": _columnwise,
    "fixed_nine": _fixed_nine,
    "add_three": _add_three,
    "ceil_half": _ceil_half,
    "repeat_input": _repeat_input,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name] for name in
                       ("columnwise", "fixed_nine", "add_three", "ceil_half")}
SEMANTIC_WITNESSES = {
    "foreground_corner": lambda g: g[0][0] == 1,
    "premature_first_repeat": _early_repeat,
    "finite_column_alias": _column_alias,
    "noncanonical_height": lambda g: len(g) != 6,
    "nonthree_extension": lambda g: len(g) // 2 != 3,
    "odd_height": lambda g: len(g) % 2 == 1,
    "continuation_phase": lambda g: _repeat_input(g) != _diagnostic_output(g),
}
WITNESS_RIVALS = {
    "foreground_corner": ["corner_zero"],
    "premature_first_repeat": ["first_recurrence"],
    "finite_column_alias": ["columnwise"],
    "noncanonical_height": ["fixed_nine"],
    "nonthree_extension": ["add_three"],
    "odd_height": ["ceil_half"],
    "continuation_phase": ["repeat_input"],
}
