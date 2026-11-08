"""Curriculum generator for ARC task ``af840d59f24c``.

The authoritative rule is global: collect every column that contains at least
one zero, sort those columns left-to-right, then replace each zero by the
one-indexed rank of its column.  Non-zero cells are preserved.

Four observable profiles supply canonical support and teaching witnesses.  The
ten-position schedule puts two canonical and two mixed-color profiles in every
five-pair window, so four-demo query rotations teach nonzero preservation.
Rows and occupied columns are
permuted to prevent fixed construction templates from revealing the ranks.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "af840d59f24c"
TASK_ID = GENERATOR_ID
RULE_HASH = "dbb5a0b9e901"
VERSION = "2.1.1"
SUMMARY = "Replace every zero by the left-to-right rank of its global zero-containing column."

PROFILES = (
    "canonical_sparse",
    "wide_many",
    "dense_mixed",
    "scrambled_order",
)
SCHEDULE_PROFILES = (
    "canonical_sparse", "dense_mixed", "wide_many", "dense_mixed", "canonical_sparse",
    "canonical_sparse", "dense_mixed", "scrambled_order", "dense_mixed", "canonical_sparse",
)
EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "4..8 distinct columns contain zeros",
    "zero-column ranks are global and ordered left-to-right",
    "at least eight zeros expose repeated use of the same column rank",
    "non-zero cells are preserved",
    "generated instances refute row-local, first-seen, and frequency rank shortcuts",
    "generated instances refute the old first-seen and frequency templates",
    "every five consecutive pairs include two nonzero-preservation witnesses",
    "full zero-column separators have other zero columns on both sides",
]

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "cyclic schedule by sample_index",
        "valid": "|".join(PROFILES),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the public cyclic curriculum profile for one stream position."""
    _validate_stream(seed, sample_index)
    del difficulty
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _validate_stream(seed, sample_index):
    if type(seed) is not int:
        raise TypeError("seed must be an integer, not a coercible scalar")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer, not a coercible scalar")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


def _validate_request(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")
    if "scene_profile" in overrides and overrides["scene_profile"] is not None:
        value = overrides["scene_profile"]
        if type(value) is not str:
            raise TypeError("scene_profile override must be a string")
        if value not in PROFILES:
            raise ValueError(f"scene_profile must be one of {PROFILES}, got {value!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic instance.

    Difficulty is accepted as a standard harness band but does not distort the
    semantic schedule.  The task is conceptually the same in every band; hidden
    keyed randomness changes positions while the observable profile stays fixed.
    """
    _validate_stream(seed, sample_index)
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    options = PROFILES if overrides.get("scene_profile") is not None else (scheduled,)
    profile = ctx.draw_choice("scene_profile", options)
    rng = ctx.draw_rng(f"profile-layout:{profile}:{difficulty or 'mixed'}")

    if profile == "canonical_sparse":
        grid = _sparse_profile(rng, height=10, width=10, zero_count=4, base=5)
    elif profile == "wide_many":
        zero_count = rng.choice((6, 7, 8))
        grid = _sparse_profile(rng, height=14, width=15, zero_count=zero_count, base=9)
    elif profile == "dense_mixed":
        grid = _dense_profile(rng, height=12, width=16, zero_count=6)
    elif profile == "scrambled_order":
        grid = _sparse_profile(rng, height=10, width=14, zero_count=5, base=6)
    else:  # draw_choice and request validation make this unreachable.
        raise AssertionError(f"unhandled profile {profile!r}")

    grid = _vary_layout(rng, grid)
    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructed unlawful {profile} sample: {'; '.join(errors)}")
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}:
        raise RuntimeError(f"profile observer mismatch: requested {profile!r}, observed {observed!r}")
    return [row[:] for row in grid]


def _vary_layout(rng, grid):
    """Break construction-order leaks while preserving each profile's domain."""
    columns = sorted({c for row in grid for c, value in enumerate(row) if value == 0})
    rows = list(range(len(grid)))
    rivals = (rival_first_seen, rival_frequency,
              rival_first_seen_template, rival_frequency_template)

    def permute(column_order, row_order):
        result = [row[:] for row in grid]
        for target, source in zip(columns, column_order, strict=True):
            for r in rows:
                result[r][target] = grid[r][source]
        return [result[r] for r in row_order]

    def acceptable(candidate):
        full = [c for c in columns if all(row[c] == 0 for row in candidate)]
        # Both separated background regions must contain transformed zeros.
        # Thus every dense example refutes first-component-only attribution.
        if full and not columns[0] < full[0] < columns[-1]:
            return False
        expected = rule_mirror(candidate)
        return all(rival(candidate) != expected for rival in rivals)

    for _ in range(64):
        column_order, row_order = columns[:], rows[:]
        rng.shuffle(column_order)
        rng.shuffle(row_order)
        candidate = permute(column_order, row_order)
        if acceptable(candidate):
            return candidate

    # All current count templates have a lawful reversed-column witness.
    # This deterministic fallback avoids a rare random rejection exhaustion.
    candidate = permute(list(reversed(columns)), rows)
    if acceptable(candidate):
        return candidate
    raise RuntimeError("profile lacks a witness against the layout-template rivals")


# Target zero counts by number of distinct zero columns.  Every vector is
# non-monotone in horizontal order, so a frequency-ranked rival is wrong.
_COUNT_PATTERNS = {
    4: (2, 4, 3, 1),
    5: (2, 4, 3, 1, 2),
    6: (2, 5, 4, 1, 3, 2),
    7: (2, 5, 4, 1, 3, 2, 4),
    8: (2, 5, 4, 1, 3, 2, 4, 5),
}


def _first_seen_order(size: int) -> list[int]:
    """A deterministic non-horizontal order, beginning at the right edge."""
    order = [size - 1]
    lo, hi = 0, size - 2
    while lo <= hi:
        order.append(lo)
        lo += 1
        if lo <= hi:
            order.append(hi)
            hi -= 1
    return order


def _choose_columns(rng, width: int, count: int) -> list[int]:
    columns = sorted(rng.sample(range(width), count))
    if len(columns) != count:
        raise RuntimeError("failed to choose distinct zero columns")
    return columns


def _sparse_profile(rng, *, height: int, width: int, zero_count: int, base: int):
    """Build a profile with one reserved zero-free row and no full zero column."""
    grid = full_grid(height, width, base)
    columns = _choose_columns(rng, width, zero_count)
    order = _first_seen_order(zero_count)
    first_row = {column_index: row for row, column_index in enumerate(order)}
    extra_rows = list(range(zero_count, height - 1))
    counts = _COUNT_PATTERNS[zero_count]
    if max(counts) - 1 > len(extra_rows):
        raise RuntimeError("profile dimensions do not support requested zero counts")

    for column_index, column in enumerate(columns):
        rows = {first_row[column_index]}
        needed = counts[column_index] - 1
        if needed:
            # Every repeated column shares the first extra row, ensuring at
            # least one row demonstrates multiple global ranks at once.
            rows.add(extra_rows[0])
            remaining = needed - 1
            tail = extra_rows[1:]
            offset = column_index % max(1, len(tail))
            rotated = tail[offset:] + tail[:offset]
            rows.update(rotated[:remaining])
        for row in rows:
            grid[row][column] = 0
    return grid


def _dense_profile(rng, *, height: int, width: int, zero_count: int):
    """Build a two-colour profile containing one fully zero-filled column."""
    grid = full_grid(height, width, 8)
    columns = _choose_columns(rng, width, zero_count)
    full_index = zero_count // 2
    full_column = columns[full_index]
    for row in range(height):
        grid[row][full_column] = 0

    other_indices = [index for index in range(zero_count) if index != full_index]
    # Row zero contains only the middle full column.  This single row already
    # refutes row-local ranking (local rank 1 versus global rank full_index+1).
    first_order = list(reversed(other_indices))
    first_row = {column_index: row + 1 for row, column_index in enumerate(first_order)}
    target_counts = {
        column_index: count
        for column_index, count in zip(other_indices, (3, 5, 2, 4, 6), strict=True)
    }
    extra_rows = list(range(len(other_indices) + 1, height))
    for column_index in other_indices:
        rows = {first_row[column_index]}
        needed = target_counts[column_index] - 1
        if needed:
            rows.add(extra_rows[0])
            remaining = needed - 1
            tail = extra_rows[1:]
            offset = column_index % max(1, len(tail))
            rotated = tail[offset:] + tail[:offset]
            rows.update(rotated[:remaining])
        for row in rows:
            grid[row][columns[column_index]] = 0

    # Add a small, observable decoy colour without touching any zero.  Scan
    # order is stable; a keyed offset changes placement while preserving a
    # large modal majority of colour 8.
    candidates = [
        (row, column)
        for row in range(height)
        for column in range(width)
        if grid[row][column] != 0
    ]
    start = rng.randrange(len(candidates))
    for offset in range(6):
        row, column = candidates[(start + offset * 17) % len(candidates)]
        grid[row][column] = 9
    return grid


def _analysis(grid):
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty sequence of rows"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return None, ["every row must be a nonempty sequence"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None, ["grid must be rectangular"]

    zero_by_column = Counter()
    zero_by_row = Counter()
    nonzero = Counter()
    for row_index, row in enumerate(grid):
        for column_index, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append("all cells must be integer ARC colours 0..9")
                continue
            if value == 0:
                zero_by_column[column_index] += 1
                zero_by_row[row_index] += 1
            else:
                nonzero[value] += 1
    if errors:
        return None, errors
    return {
        "height": len(grid),
        "width": width,
        "zero_by_column": zero_by_column,
        "zero_by_row": zero_by_row,
        "nonzero": nonzero,
    }, []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the declared task manifold, including canonical examples."""
    del difficulty, meta
    analysis, errors = _analysis(grid)
    if errors:
        return errors
    assert analysis is not None
    height = analysis["height"]
    zero_by_column = analysis["zero_by_column"]
    zero_by_row = analysis["zero_by_row"]
    nonzero = analysis["nonzero"]

    column_count = len(zero_by_column)
    if not 4 <= column_count <= 8:
        errors.append(f"need 4..8 distinct zero columns, found {column_count}")
    total_zeros = sum(zero_by_column.values())
    if total_zeros < 8:
        errors.append(f"need at least eight zero cells, found {total_zeros}")
    if not nonzero:
        errors.append("need preserved non-zero cells")
    if len(zero_by_row) < 3:
        errors.append("zeros must occur in at least three rows")
    if zero_by_row and max(zero_by_row.values()) < 2:
        errors.append("at least one row must contain multiple zeros")
    if len(set(zero_by_column.values())) < 2:
        errors.append("zero-column frequencies must not all be equal")

    full_columns = [column for column, count in zero_by_column.items() if count == height]
    if len(full_columns) > 1:
        errors.append("at most one zero column may span the full height")
    if full_columns:
        if not any(count == 1 for count in zero_by_row.values()):
            errors.append("a full-column sample needs a row where it is the only zero")
    elif len(zero_by_row) == height:
        errors.append("a non-dense sample needs at least one zero-free row")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """All generated profiles are lawful instances of the exact same rule."""
    return self_check(grid)


def rule_mirror(grid):
    """Pure diagnostic mirror; canonical Racket remains label authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    zero_columns = sorted(
        {column for row in grid for column, value in enumerate(row) if value == 0}
    )
    ranks = {column: index + 1 for index, column in enumerate(zero_columns)}
    return [
        [ranks[column] if value == 0 else value for column, value in enumerate(row)]
        for row in grid
    ]


def observe_overrides(grid) -> dict[str, str]:
    """Recover the exact public profile from pixels alone."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    analysis, _ = _analysis(grid)
    assert analysis is not None
    height, width = analysis["height"], analysis["width"]
    palette = set(analysis["nonzero"])
    zero_count = len(analysis["zero_by_column"])
    full = any(count == height for count in analysis["zero_by_column"].values())
    modal = min(analysis["nonzero"], key=lambda color: (-analysis["nonzero"][color], color))

    if (height, width, palette, zero_count, full) == (10, 10, {5}, 4, False):
        profile = "canonical_sparse"
    elif width > 10 and palette == {9} and 6 <= zero_count <= 8 and not full:
        profile = "wide_many"
    elif width > 10 and palette == {8, 9} and modal == 8 and full:
        profile = "dense_mixed"
    elif width > 10 and palette == {6} and zero_count == 5 and not full:
        profile = "scrambled_order"
    else:
        raise ValueError("grid does not match any declared scene_profile")
    return {"scene_profile": profile}


def semantic_observables(grid) -> dict[str, object]:
    analysis, errors = _analysis(grid)
    if errors:
        return {"errors": errors}
    assert analysis is not None
    truth = rule_mirror(grid)
    return {
        **observe_overrides(grid),
        "zero_columns": tuple(sorted(analysis["zero_by_column"])),
        "zero_counts": tuple(
            analysis["zero_by_column"][column]
            for column in sorted(analysis["zero_by_column"])
        ),
        "shortcut_disagreements": {
            name: rival(grid) != truth for name, rival in SEMANTIC_RIVALS.items()
        },
    }


def _identity(grid):
    return [list(row) for row in grid]


def rival_base5_only(grid):
    nonzero = Counter(value for row in grid for value in row if value != 0)
    if nonzero and min(nonzero, key=lambda c: (-nonzero[c], c)) == 5:
        return rule_mirror(grid)
    return _identity(grid)


def rival_ten_by_ten_only(grid):
    if len(grid) == 10 and len(grid[0]) == 10:
        return rule_mirror(grid)
    return _identity(grid)


def rival_clamp_after_four(grid):
    columns = sorted({c for row in grid for c, value in enumerate(row) if value == 0})
    ranks = {column: min(index + 1, 4) for index, column in enumerate(columns)}
    return [
        [ranks[column] if value == 0 else value for column, value in enumerate(row)]
        for row in grid
    ]


def rival_row_local(grid):
    output = deepcopy(grid)
    for row_index, row in enumerate(grid):
        columns = [column for column, value in enumerate(row) if value == 0]
        ranks = {column: index + 1 for index, column in enumerate(columns)}
        for column in columns:
            output[row_index][column] = ranks[column]
    return output


def rival_first_seen(grid):
    first: dict[int, tuple[int, int]] = {}
    for row_index, row in enumerate(grid):
        for column, value in enumerate(row):
            if value == 0:
                first.setdefault(column, (row_index, column))
    columns = sorted(first, key=lambda column: first[column])
    ranks = {column: index + 1 for index, column in enumerate(columns)}
    return [
        [ranks[column] if value == 0 else value for column, value in enumerate(row)]
        for row in grid
    ]


def rival_frequency(grid):
    counts = Counter(
        column for row in grid for column, value in enumerate(row) if value == 0
    )
    columns = sorted(counts, key=lambda column: (-counts[column], column))
    ranks = {column: index + 1 for index, column in enumerate(columns)}
    return [
        [ranks[column] if value == 0 else value for column, value in enumerate(row)]
        for row in grid
    ]


def rival_first_seen_template(grid):
    """Recover v2.0's prescribed first-seen sequence without horizontal ranks."""
    columns = list(dict.fromkeys(
        c for row in grid for c, value in enumerate(row) if value == 0
    ))
    size = len(columns)
    if any(all(row[c] == 0 for row in grid) for c in columns):
        middle = size // 2
        order = [middle] + [index for index in reversed(range(size)) if index != middle]
    else:
        order = _first_seen_order(size)
    ranks = {column: rank + 1 for column, rank in zip(columns, order, strict=True)}
    return [[ranks[c] if value == 0 else value for c, value in enumerate(row)]
            for row in grid]


def rival_frequency_template(grid):
    """Recover v2.0's count-to-rank table, sorting horizontally only for ties."""
    counts = Counter(c for row in grid for c, value in enumerate(row) if value == 0)
    if len(grid) in counts.values():
        if len(counts) != 6:
            return _identity(grid)
        template = (3, 5, 2, len(grid), 4, 6)
    else:
        template = _COUNT_PATTERNS.get(len(counts))
        if template is None:
            return _identity(grid)
    ranks = {}
    for count in set(template) | set(counts.values()):
        columns = sorted(c for c, actual in counts.items() if actual == count)
        expected_ranks = [index + 1 for index, actual in enumerate(template) if actual == count]
        if len(columns) != len(expected_ranks):
            return _identity(grid)
        ranks.update(zip(columns, expected_ranks, strict=True))
    return [[ranks[c] if value == 0 else value for c, value in enumerate(row)]
            for row in grid]


def rival_erase_nonmodal(grid):
    """Rank zeros correctly but incorrectly collapse all other colors."""
    counts = Counter(value for row in grid for value in row if value != 0)
    modal = min(counts, key=lambda color: (-counts[color], color))
    expected = rule_mirror(grid)
    return [[expected[r][c] if value == 0 else modal for c, value in enumerate(row)]
            for r, row in enumerate(grid)]


CANONICAL_SHORTCUTS: dict[str, Callable] = {
    "base5_only": rival_base5_only,
    "ten_by_ten_only": rival_ten_by_ten_only,
    "clamp_after_four": rival_clamp_after_four,
    "erase_nonmodal": rival_erase_nonmodal,
}
SEMANTIC_RIVALS: dict[str, Callable] = {
    **CANONICAL_SHORTCUTS,
    "row_local_rank": rival_row_local,
    "first_seen_rank": rival_first_seen,
    "frequency_rank": rival_frequency,
    "first_seen_template": rival_first_seen_template,
    "frequency_template": rival_frequency_template,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _refutes(rival):
    def witness(grid):
        return not self_check(grid) and rival(grid) != rule_mirror(grid)

    return witness


SEMANTIC_WITNESSES = {
    "non5_background": _refutes(rival_base5_only),
    "non10_shape": _refutes(rival_ten_by_ten_only),
    "more_than_four_columns": _refutes(rival_clamp_after_four),
    "global_not_row_local": _refutes(rival_row_local),
    "horizontal_not_first_seen": _refutes(rival_first_seen),
    "horizontal_not_frequency": _refutes(rival_frequency),
    "horizontal_not_first_seen_template": _refutes(rival_first_seen_template),
    "horizontal_not_frequency_template": _refutes(rival_frequency_template),
    "preserved_nonmodal_color": _refutes(rival_erase_nonmodal),
}
WITNESS_RIVALS = {
    "non5_background": ["base5_only"],
    "non10_shape": ["ten_by_ten_only"],
    "more_than_four_columns": ["clamp_after_four"],
    "global_not_row_local": ["row_local_rank"],
    "horizontal_not_first_seen": ["first_seen_rank"],
    "horizontal_not_frequency": ["frequency_rank"],
    "horizontal_not_first_seen_template": ["first_seen_template"],
    "horizontal_not_frequency_template": ["frequency_template"],
    "preserved_nonmodal_color": ["erase_nonmodal"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Validate labels and reject any declared competitor surviving the demos."""
    if not isinstance(demos, (list, tuple)):
        return ["demonstrations must be a sequence"]
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    valid_demos = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is unlawful: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the rule")
        valid_demos.append(demo)

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is unlawful: {query_errors[0]}")
    else:
        expected_query = rule_mirror(query["input"])
        if "output" in query and query["output"] != expected_query:
            reasons.append("query output disagrees with the rule")
    if reasons:
        return reasons

    expected_query = rule_mirror(query["input"])
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in valid_demos):
            if rival(query["input"]) != expected_query:
                reasons.append(f"competitor {name!r} fits demos but changes the query")
            else:
                reasons.append(f"competitor {name!r} remains unfalsified by demonstrations")
    return reasons
