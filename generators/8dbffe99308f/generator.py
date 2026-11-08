"""Input sampler for anti-diagonal symmetry completion, task 8dbffe99308f.

The public examples place every source strictly above the anti-diagonal and
never pre-fill a reflected partner.  They therefore admit two useful but wrong
shortcuts: "copy only the above side downward" and "copy only into empty mirror
cells".  Normal lessons use a six-profile cyclic curriculum that alternates
ordinary directional inputs with unequal occupied-pair conflicts.  Every
consecutive three-demo window contains conflict evidence, and every consecutive
four-pair window contains two conflicts so any query rotation remains
identifiable.

The selected Racket authority is unchanged.  This module samples inputs,
validates the task-linked teaching manifold, and supplies Python-only analysis
oracles/rivals for reviewer checks.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "8dbffe99308f"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "e248d283a2c2"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Overlay a square zero-background grid with its anti-diagonal reflection. "
    "A nonzero cell at (r,c) writes the same color to "
    "(n-1-c,n-1-r) while the original remains. If both reflected partners are "
    "occupied, their values swap because the reflection is read from an "
    "immutable snapshot."
)

INVARIANTS = [
    "the input is a 6..10 square ARC grid with background color 0",
    "the input contains exactly 4..10 nonzero markers in four to six colors",
    "at least one marker is off the anti-diagonal",
    "at most one off-axis anti-diagonal mirror pair is pre-filled; if present, its colors differ",
    "the output overlays the immutable anti-diagonal reflection onto the input",
]

# Both public controls are exact and recoverable from returned pixels.  The
# teaching profile is deliberately an internal schedule rather than a misleading
# user override.
AXES = {
    "size": {
        "type": "int",
        "default": "six-slot canonical teaching schedule",
        "valid": "6..10",
        "doc": "Square grid side length.",
    },
    "markers": {
        "type": "int",
        "default": "difficulty-weighted six-slot teaching schedule",
        "valid": "4..10",
        "doc": "Exact number of nonzero input cells.",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

SCHEDULE_PROFILES = (
    "above_sparse",
    "unequal_conflict_below",
    "above_with_axis",
    "unequal_conflict_mixed",
    "below_sparse",
    "unequal_conflict_with_axis",
)

# The period spans the full size override domain while retaining canonical 6x6
# and 8x8 profiles in every band.
_PROFILE_SIZES = (6, 8, 7, 9, 10, 8)
_MARKER_ANCHORS = {
    "easy": (4, 5, 6, 5, 6, 7),
    "medium": (6, 7, 8, 6, 8, 7),
    "hard": (8, 9, 10, 8, 10, 9),
}
# Foreground color counts produce canonical exact (height,width,palette-size)
# profiles at slots 0, 1, and 5: (6,6,5) and (8,8,6).
_PROFILE_COLOR_COUNTS = (4, 5, 5, 5, 6, 5)
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(
        f"unknown difficulty {difficulty!r}; expected None, 'easy', 'medium', or 'hard'"
    )


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic curriculum profile for a stream position."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> str:
    if difficulty not in _VALID_DIFFICULTIES:
        _band(difficulty)  # raises the stable public diagnostic
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    for name in ("size", "markers"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(
                f"{name} must be an integer, not {type(value).__name__}"
            )
    return _band(difficulty)


def _draw_exact_int(
    ctx, overrides: dict[str, Any], name: str, default: int, lo: int, hi: int
) -> int:
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _anti_mirror(size: int, r: int, c: int) -> tuple[int, int]:
    return size - 1 - c, size - 1 - r


def _above_bases(size: int) -> list[tuple[int, int]]:
    """One representative from every non-fixed anti-diagonal orbit."""
    return [
        (r, c)
        for r in range(size)
        for c in range(size)
        if r + c < size - 1
    ]


def _take_sample(
    rng, pool: Sequence[tuple[int, int]], count: int
) -> list[tuple[int, int]]:
    if count < 0 or count > len(pool):
        raise ValueError(
            f"cannot choose {count} anti-diagonal orbits from a pool of {len(pool)}"
        )
    return list(rng.sample(list(pool), count))


def _profile_positions(
    size: int,
    markers: int,
    profile: str,
    rng,
) -> list[tuple[int, int]]:
    """Construct exactly ``markers`` cells with at most one mirror pair."""
    above_anchor = (0, 1)
    bases = _above_bases(size)
    remaining = [point for point in bases if point != above_anchor]

    if profile == "above_sparse":
        positions = [above_anchor]
        positions.extend(_take_sample(rng, remaining, markers - 1))

    elif profile == "below_sparse":
        chosen = [above_anchor]
        chosen.extend(_take_sample(rng, remaining, markers - 1))
        positions = [_anti_mirror(size, r, c) for r, c in chosen]

    elif profile == "unequal_conflict_below":
        conflict = rng.choice(bases)
        rest = [point for point in bases if point != conflict]
        chosen = _take_sample(rng, rest, markers - 2)
        positions = [conflict, _anti_mirror(size, *conflict)]
        positions.extend(_anti_mirror(size, *point) for point in chosen)

    elif profile == "unequal_conflict_mixed":
        conflict = rng.choice(bases)
        rest = [point for point in bases if point != conflict]
        chosen = _take_sample(rng, rest, markers - 2)
        positions = [conflict, _anti_mirror(size, *conflict)]
        for index, point in enumerate(chosen):
            positions.append(
                point if index % 2 == 0 else _anti_mirror(size, *point)
            )

    elif profile == "above_with_axis":
        fixed = (rng.randrange(size),)
        axis_point = (fixed[0], size - 1 - fixed[0])
        positions = [above_anchor, axis_point]
        positions.extend(_take_sample(rng, remaining, markers - 2))

    elif profile == "unequal_conflict_with_axis":
        conflict = rng.choice(bases)
        rest = [point for point in bases if point != conflict]
        fixed_row = rng.randrange(size)
        axis_point = (fixed_row, size - 1 - fixed_row)
        chosen = _take_sample(rng, rest, markers - 3)
        positions = [conflict, _anti_mirror(size, *conflict), axis_point]
        for index, point in enumerate(chosen):
            positions.append(
                point if index % 2 == 0 else _anti_mirror(size, *point)
            )

    else:
        raise ValueError(f"unknown schedule profile {profile!r}")

    if len(positions) != markers or len(set(positions)) != markers:
        raise RuntimeError(
            f"profile {profile!r} rendered {len(set(positions))} unique cells, "
            f"expected {markers}"
        )

    occupied = set(positions)
    pairs = sorted(
        point
        for point in occupied
        if point < _anti_mirror(size, *point)
        and _anti_mirror(size, *point) in occupied
    )
    expected_pairs = 1 if profile.startswith("unequal_conflict") else 0
    if len(pairs) != expected_pairs:
        raise RuntimeError(
            f"profile {profile!r} rendered {len(pairs)} mirror pairs, "
            f"expected {expected_pairs}"
        )
    return positions


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)):
        return []
    rows: list[list[int]] = []
    for row in grid:
        if not isinstance(row, (list, tuple)):
            return []
        rows.append(list(row))
    return rows


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the selected rule's sparse canonical-scale input manifold."""
    del difficulty, meta
    rows = _coerce_grid(grid)
    if not rows or not rows[0]:
        return ["grid must be a nonempty rectangular list of rows"]
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        return ["ragged grid: every row must have the same width"]

    height = len(rows)
    errors: list[str] = []
    if height != width:
        errors.append(f"grid must be square, got {height}x{width}")
    if not 6 <= height <= 10 or not 6 <= width <= 10:
        errors.append(f"grid side must be 6..10, got {height}x{width}")

    invalid = [
        (r, c, value)
        for r, row in enumerate(rows)
        for c, value in enumerate(row)
        if type(value) is not int or not 0 <= value <= 9
    ]
    if invalid:
        errors.append(
            f"cells must be integer ARC colors 0..9; first invalid {invalid[0]}"
        )
        return errors

    markers = [
        (r, c, value)
        for r, row in enumerate(rows)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not 4 <= len(markers) <= 10:
        errors.append(f"expected 4..10 nonzero markers, got {len(markers)}")

    colors = {value for _, _, value in markers}
    if markers and not 4 <= len(colors) <= 6:
        errors.append(f"expected four to six nonzero colors, got {len(colors)}")

    if height == width:
        size = height
        if not any(r + c != size - 1 for r, c, _ in markers):
            errors.append("at least one marker must be off the anti-diagonal")

        occupied = {(r, c): value for r, c, value in markers}
        conflicts = sorted(
            point
            for point in occupied
            if point < _anti_mirror(size, *point)
            and _anti_mirror(size, *point) in occupied
        )
        if len(conflicts) > 1:
            errors.append(
                "input contains more than one pre-filled anti-diagonal mirror pair; "
                f"first pairs are {conflicts[:2]}"
            )
        elif conflicts:
            point = conflicts[0]
            mirror = _anti_mirror(size, *point)
            if occupied[point] == occupied[mirror]:
                errors.append(
                    "pre-filled anti-diagonal mirror pair must use unequal colors "
                    f"so swap semantics are observable; pair starts at {point}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked lawful-manifold predicate used by the semantic gate."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact public axis from returned pixels."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe exact axes: " + "; ".join(errors))
    rows = _coerce_grid(grid)
    return {
        "size": len(rows),
        "markers": sum(value != 0 for row in rows for value in row),
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _validate_call(difficulty, overrides)
    profile_index = int(sample_index) % len(SCHEDULE_PROFILES)
    profile = schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    size = _draw_exact_int(
        ctx, overrides, "size", _PROFILE_SIZES[profile_index], 6, 10
    )
    markers = _draw_exact_int(
        ctx,
        overrides,
        "markers",
        _MARKER_ANCHORS[band][profile_index],
        4,
        10,
    )

    positions = _profile_positions(size, markers, profile, ctx.draw_rng("layout"))
    n_colors = min(markers, _PROFILE_COLOR_COUNTS[profile_index])
    colors = ctx.draw_distinct_colors("source_colors", n=n_colors, exclude={0})
    grid = full_grid(size, size, 0)
    for index, (r, c) in enumerate(positions):
        grid[r][c] = colors[index % len(colors)]

    errors = self_check(grid)
    if errors:
        raise RuntimeError("generated invalid anti-diagonal scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {"size": size, "markers": markers}
    if observed != expected:
        raise RuntimeError(f"rendered axes disagree with draws: {observed} != {expected}")
    return grid


def rule_mirror(grid) -> list[list[int]]:
    """Python analysis oracle; the selected Racket program remains authority."""
    rows = _coerce_grid(grid)
    size = len(rows)
    out = [row[:] for row in rows]
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            if value != 0:
                mr, mc = _anti_mirror(size, r, c)
                out[mr][mc] = value
    return out


def _rival_above_only(grid) -> list[list[int]]:
    """Wrong shortcut suggested by every public demonstration."""
    rows = _coerce_grid(grid)
    size = len(rows)
    out = [row[:] for row in rows]
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            if value != 0 and r + c < size - 1:
                mr, mc = _anti_mirror(size, r, c)
                out[mr][mc] = value
    return out


def _rival_below_only(grid) -> list[list[int]]:
    rows = _coerce_grid(grid)
    size = len(rows)
    out = [row[:] for row in rows]
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            if value != 0 and r + c > size - 1:
                mr, mc = _anti_mirror(size, r, c)
                out[mr][mc] = value
    return out


def _rival_fill_empty_only(grid) -> list[list[int]]:
    """Wrong shortcut: mirror only when the source snapshot's partner is 0."""
    rows = _coerce_grid(grid)
    size = len(rows)
    out = [row[:] for row in rows]
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            if value == 0:
                continue
            mr, mc = _anti_mirror(size, r, c)
            if rows[mr][mc] == 0:
                out[mr][mc] = value
    return out


def _rival_reflection_only(grid) -> list[list[int]]:
    rows = _coerce_grid(grid)
    size = len(rows)
    out = full_grid(size, size, 0)
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            if value != 0:
                mr, mc = _anti_mirror(size, r, c)
                out[mr][mc] = value
    return out


def _rival_main_diagonal(grid) -> list[list[int]]:
    rows = _coerce_grid(grid)
    out = [row[:] for row in rows]
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            if value != 0:
                out[c][r] = value
    return out


def _rival_rotate_180(grid) -> list[list[int]]:
    rows = _coerce_grid(grid)
    size = len(rows)
    out = [row[:] for row in rows]
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            if value != 0:
                out[size - 1 - r][size - 1 - c] = value
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "above_only": _rival_above_only,
    "below_only": _rival_below_only,
    "fill_empty_only": _rival_fill_empty_only,
    "reflection_only": _rival_reflection_only,
    "main_diagonal": _rival_main_diagonal,
    "rotate_180": _rival_rotate_180,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "above_only": _rival_above_only,
    "fill_empty_only": _rival_fill_empty_only,
}


def _lawful(grid) -> bool:
    return self_check(grid) == []


def _has_below_source(grid) -> bool:
    rows = _coerce_grid(grid)
    size = len(rows)
    return _lawful(rows) and any(
        rows[r][c] != 0
        for r in range(size)
        for c in range(size)
        if r + c > size - 1
    )


def _has_unequal_conflict(grid) -> bool:
    rows = _coerce_grid(grid)
    if not _lawful(rows):
        return False
    size = len(rows)
    return any(
        rows[r][c] != 0
        and rows[_anti_mirror(size, r, c)[0]][_anti_mirror(size, r, c)[1]] != 0
        and rows[r][c]
        != rows[_anti_mirror(size, r, c)[0]][_anti_mirror(size, r, c)[1]]
        for r in range(size)
        for c in range(size)
        if (r, c) < _anti_mirror(size, r, c)
    )


SEMANTIC_WITNESSES = {
    "below_source": _has_below_source,
    "unequal_conflict": _has_unequal_conflict,
}
WITNESS_RIVALS = {
    "below_source": ["above_only"],
    "unequal_conflict": ["fill_empty_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named plausible wrong rule remains viable."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output disagrees with the selected rule")

    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query is not an input/output pair")
        return reasons
    if rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output disagrees with the selected rule")

    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                rival(pair["input"]) == pair["output"] for pair in demos
            )
            if fits_demos and rival(query["input"]) != query["output"]:
                reasons.append(
                    f"rival {name!r} fits every demonstration but predicts a "
                    "different query answer"
                )
        except Exception as exc:
            reasons.append(f"rival {name!r} raised {type(exc).__name__}: {exc}")
    return reasons
