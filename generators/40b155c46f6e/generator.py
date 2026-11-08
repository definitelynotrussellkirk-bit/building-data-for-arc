"""Input distribution for row-majority cleanup (E68); Racket remains authority.

Three consecutive default draws contain a canonical-profile example and two
boundary witnesses. Positions and colors are generated, never canonical replay.
All four declared overrides are exact, observable, and valid in every band.
The executable rivals below are review diagnostics, not generated labels.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "40b155c46f6e"
TASK_ID = "40b155c46f6e"
RULE_HASH = "d149383b47c7"
VERSION = "3.0.0"
SUMMARY = (
    "Zero-background grids with 1..3 separated compact active rows. Each row "
    "has a repeated nonzero majority and one different singleton; the unchanged "
    "Racket rule recolors that singleton only. Active rows range over the whole "
    "canvas, including positive even indices. Three-draw lessons include endpoint "
    "odds, noncanonical run lengths, a third active row, and shared color roles."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
INVARIANTS = [
    "5..7 rows and 7..12 columns of integer colors 0..9; background is zero",
    "1..3 nonempty rows separated by at least one blank row; no parity restriction",
    "each active row is one compact run of 3..6 cells",
    "each active row has exactly two nonzero colors, one singleton and one repeated",
    "the authoritative transformation changes exactly one cell per active row",
]
AXES = {
    "grid_h": {"type": "int", "default": "5 in core; varied 5..7 otherwise", "valid": "5..7"},
    "grid_w": {"type": "int", "default": "8..9 in core; varied 7..12 otherwise", "valid": "7..12"},
    "n_active_rows": {"type": "int", "default": "2/core, 3/left, 1..3/right", "valid": "1..3"},
    "run_len": {"type": "int", "default": "4..5/core, 3 or 6/left, 3..6/right", "valid": "3..6"},
}
# These domains form a fully feasible Cartesian product: even 5x7 fits three
# separated length-six rows. Retired no-op controls are rejected, not aliased.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
SCHEDULE_PROFILES = ("core", "left_witness", "right_witness")


def schedule_profile(seed, sample_index, difficulty=None):
    """Profile only, not grid identity. Consecutive windows cover every phase."""
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _axis(ctx, name, low, high, default_choices):
    # Validate an explicit override against its entire advertised domain. Default
    # choice provenance is recorded under that same axis, never overwritten later.
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int(name, low, high)
    return ctx.draw_choice(name, default_choices)


@lru_cache(maxsize=9)
def _separated_rows(height, count):
    return tuple(rows for rows in combinations(range(height), count)
                 if all(b-a >= 2 for a, b in zip(rows, rows[1:])))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown or retired override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    if profile == "core":
        heights, widths, counts, lengths = (5,), (8, 9), (2,), (4, 5)
    else:
        # Difficulty changes weights, not supported controls or witness branches.
        heights = (5, 6, 7) + ((5, 5) if difficulty == "easy" else (7,) if difficulty == "hard" else ())
        widths = tuple(range(7, 13)) + ((7, 8) if difficulty == "easy" else (11, 12) if difficulty == "hard" else ())
        counts = (3,) if profile == "left_witness" else (1, 2, 3)
        lengths = (3, 6) if profile == "left_witness" else (3, 4, 5, 6)
    height = _axis(ctx, "grid_h", 5, 7, heights)
    width = _axis(ctx, "grid_w", 7, 12, widths)
    count = _axis(ctx, "n_active_rows", 1, 3, counts)
    length = _axis(ctx, "run_len", 3, 6, lengths)
    candidates = _separated_rows(height, count)
    if profile == "left_witness":
        # Reproduce the prior audit's missing positive-even-row witness without
        # fixing its location. Core/right still support EVERY separated row set.
        candidates = tuple(rows for rows in candidates if any(r > 0 and r % 2 == 0 for r in rows))
    active = ctx.draw_rng("row_positions").choice(candidates)
    color_rng = ctx.draw_rng("color_roles")
    if profile == "core":
        colors = color_rng.sample(range(1, 10), 2*count)
        roles = list(zip(colors[::2], colors[1::2]))
    elif profile == "left_witness" and count > 1:
        # A color can be the majority in one row and the odd cell in another.
        # A global singleton-color replacement shortcut therefore cannot fit.
        colors = color_rng.sample(range(1, 10), count)
        roles = [(colors[i], colors[(i+1) % count]) for i in range(count)]
    else:
        roles = [color_rng.sample(range(1, 10), 2) for _ in active]
    witness_row = ctx.draw_rng("endpoint_witness_row").randrange(count)
    grid = full_grid(height, width, 0)
    for index, (r, (majority, odd)) in enumerate(zip(active, roles)):
        row_rng = ctx.draw_rng(f"row_{r}_placement")
        start = row_rng.randint(0, width-length)
        if profile == "core":
            offset = row_rng.randint(1, length-2)
        elif index == witness_row:
            offset = 0 if profile == "left_witness" else length-1
        else:
            offset = row_rng.randrange(length)
        grid[r][start:start+length] = [majority]*length
        grid[r][start+offset] = odd
    return grid


def _facts(grid):
    """Facts for a well-formed grid; guards are applied by each caller."""
    found = []
    for r, row in enumerate(grid):
        cols = [c for c, value in enumerate(row) if value != 0]
        if not cols:
            continue
        counts = Counter(row[c] for c in cols)
        if len(counts) == 2 and sorted(counts.values())[0] == 1 and max(counts.values()) > 1:
            odd = min(counts, key=counts.get)
            major = max(counts, key=counts.get)
            found.append((r, cols, odd, major, row.index(odd)))
    return found


def observe_overrides(grid):
    rows = _facts(grid)
    lengths = sorted({len(cols) for _, cols, _, _, _ in rows})
    # Canonical examples can mix lengths. Generated exact-control instances do
    # not; report mixed lengths honestly instead of picking an arbitrary row.
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_active_rows": len(rows),
            "run_len": lengths[0] if len(lengths) == 1 else tuple(lengths)}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9 (booleans are not colors)"]
    errors = []
    if not 5 <= height <= 7 or not 7 <= width <= 12:
        errors.append("shape is outside the documented 5..7 by 7..12 domain")
    active = []
    for r, row in enumerate(grid):
        cols = [c for c, value in enumerate(row) if value]
        if not cols:
            continue
        active.append(r)
        if not 3 <= len(cols) <= 6:
            errors.append(f"row {r}: run length must be 3..6")
        if cols != list(range(cols[0], cols[-1]+1)):
            errors.append(f"row {r}: nonzero cells must form one compact run")
        counts = Counter(row[c] for c in cols)
        if len(counts) != 2 or min(counts.values()) != 1 or max(counts.values()) <= 1:
            errors.append(f"row {r}: expected a singleton odd and a repeated majority")
    if not 1 <= len(active) <= 3:
        errors.append("expected 1..3 active rows")
    if any(b-a < 2 for a, b in zip(active, active[1:])):
        errors.append("active rows require a blank separator")
    return errors


def strict_canonical_like(grid):
    """Semantic sampler manifold, NOT a claim of identical canonical dimensions."""
    return self_check(grid)


def _rival(grid, mode):
    """Total rival transformations on grids; never used for training labels."""
    out = [list(row) for row in grid]
    global_counts = Counter(value for row in grid for value in row if value)
    for index, (r, cols, odd, major, odd_col) in enumerate(_facts(grid)):
        if mode == "restricted_rows" and r > 0 and r % 2 == 0:
            continue
        if mode == "interior_only" and odd_col in (cols[0], cols[-1]):
            continue
        if mode == "lengths_4_or_5" and len(cols) not in (4, 5):
            continue
        if mode == "first_two_rows" and index >= 2:
            continue
        if mode == "global_singletons" and global_counts[odd] != 1:
            continue
        if mode in ("first_nonzero", "last_nonzero"):
            target = grid[r][cols[0] if mode == "first_nonzero" else cols[-1]]
            out[r] = [target if value else 0 for value in grid[r]]
        else:
            out[r][odd_col] = major
    return out


def _restricted_rows(grid):
    return _rival(grid, "restricted_rows")


def _first_nonzero(grid):
    return _rival(grid, "first_nonzero")


def _last_nonzero(grid):
    return _rival(grid, "last_nonzero")


def _interior_only(grid):
    return _rival(grid, "interior_only")


def _lengths_4_or_5(grid):
    return _rival(grid, "lengths_4_or_5")


def _first_two_rows(grid):
    return _rival(grid, "first_two_rows")


def _global_singletons(grid):
    return _rival(grid, "global_singletons")


def _has_even(grid):
    return any(r > 0 and r % 2 == 0 for r, *_ in _facts(grid))


def _has_first(grid):
    return any(c == cols[0] for _, cols, _, _, c in _facts(grid))


def _has_last(grid):
    return any(c == cols[-1] for _, cols, _, _, c in _facts(grid))


def _has_other_length(grid):
    return any(len(cols) not in (4, 5) for _, cols, *_ in _facts(grid))


def _has_third_row(grid):
    return len(_facts(grid)) >= 3


def _has_shared_odd(grid):
    counts = Counter(value for row in grid for value in row if value)
    return any(counts[odd] > 1 for _, _, odd, _, _ in _facts(grid))


SEMANTIC_WITNESSES = {
    "positive_even_row": _has_even, "odd_at_first": _has_first,
    "odd_at_last": _has_last, "other_run_length": _has_other_length,
    "third_active_row": _has_third_row, "shared_odd_color": _has_shared_odd,
}
SEMANTIC_RIVALS = {
    "restricted_rows": _restricted_rows, "first_nonzero": _first_nonzero,
    "last_nonzero": _last_nonzero, "interior_only": _interior_only,
    "lengths_4_or_5": _lengths_4_or_5, "first_two_rows": _first_two_rows,
    "global_singletons": _global_singletons,
}
WITNESS_RIVALS = {
    "positive_even_row": ["restricted_rows"],
    "odd_at_first": ["first_nonzero", "interior_only"],
    "odd_at_last": ["last_nonzero", "interior_only"],
    "other_run_length": ["lengths_4_or_5"],
    "third_active_row": ["first_two_rows"],
    "shared_odd_color": ["global_singletons"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Finite-rival teaching claim only; never a universal-induction assertion."""
    return [f"declared rival survives all demos: {name}"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)]
