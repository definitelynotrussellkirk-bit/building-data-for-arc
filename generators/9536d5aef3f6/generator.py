"""Generator for 9536d5aef3f6 — add the main-diagonal transpose.

The public demonstrations contain sources only above the main diagonal and no
occupied transpose pair.  They therefore fit both the directional shortcut
"copy the upper triangle downward" and the subtler shortcut "copy only into an
empty mirror cell".  Normal lessons rotate through upper-only, lower-only, and
unequal occupied-pair inputs.  Every consecutive three-demo window contains
both directional evidence and one conflict that requires simultaneous transpose
overlay semantics.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "9536d5aef3f6"
TASK_ID = "9536d5aef3f6"
VERSION = "2.2.0"
RULE_HASH = "2b970065d6a3"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Overlay a square zero-background grid with its main-diagonal transpose. "
    "Unpaired nonzero cells are copied to (c, r); if both transpose partners "
    "are occupied, their original values swap because the transpose is read "
    "from an immutable snapshot."
)

INVARIANTS = [
    "the input is a 5..10 square ARC grid with background color 0",
    "the input contains exactly 3..8 nonzero markers in three or four colors",
    "at least one marker is off the main diagonal",
    "at most one off-diagonal transpose pair is pre-filled; if present, its colors differ",
    "the output is the input overlaid with its main-diagonal transpose from an immutable snapshot",
]

# Both controls are exact: callers can recover their realized values from the
# returned pixels through observe_overrides().  Teaching profile is an internal
# deterministic schedule rather than a misleading public override surface.
AXES = {
    "size": {
        "type": "int",
        "default": "six-slot canonical teaching schedule",
        "valid": "5..10",
        "doc": "Square grid side length.",
    },
    "markers": {
        "type": "int",
        "default": "difficulty-weighted six-slot teaching schedule",
        "valid": "3..8",
        "doc": "Exact number of nonzero input cells.",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

SCHEDULE_PROFILES = (
    "upper_sparse",
    "lower_sparse",
    "unequal_conflict",
    "upper_with_diagonal",
    "lower_dense",
    "unequal_conflict_with_diagonal",
)

_PROFILE_SIZES = (5, 6, 7, 8, 9, 10)
_MARKER_ANCHORS = {
    "easy": (3, 4, 4, 5, 4, 5),
    "medium": (4, 5, 6, 5, 6, 7),
    "hard": (6, 7, 8, 6, 8, 7),
}
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
    """Return the deterministic lesson profile for one stream position."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> str:
    if difficulty not in _VALID_DIFFICULTIES:
        _band(difficulty)  # raises the public, stable diagnostic
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


def _draw_exact_int(ctx, overrides, name: str, default: int, lo: int, hi: int) -> int:
    """Draw an exact axis while exposing the full override domain honestly."""
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    # A profile anchor is intentional curriculum scheduling, not a hidden broad
    # random draw.  Across the six profiles the observed bounds span AXES.
    return ctx.draw_int(name, default, default)


def _upper_bases(size: int) -> list[tuple[int, int]]:
    """One representative (r<c) for each off-diagonal transpose orbit.

    The bottom-right adjacent orbit is reserved.  Excluding it guarantees that
    the sentinel at (0,1) or (1,0) distinguishes main-diagonal reflection from
    anti-diagonal reflection on every generated input.
    """
    reserved = (size - 2, size - 1)
    return [
        (r, c)
        for r in range(size)
        for c in range(r + 1, size)
        if (r, c) != reserved
    ]


def _take_sample(rng, pool: Sequence[tuple[int, int]], count: int) -> list[tuple[int, int]]:
    if count < 0 or count > len(pool):
        raise ValueError(
            f"cannot choose {count} transpose orbits from a pool of {len(pool)}"
        )
    return list(rng.sample(list(pool), count))


def _profile_positions(
    size: int,
    markers: int,
    profile: str,
    rng,
) -> list[tuple[int, int]]:
    """Construct exactly ``markers`` cells with at most one transpose pair."""
    upper_anchor = (0, 1)
    lower_anchor = (1, 0)
    all_bases = _upper_bases(size)
    remaining_bases = [p for p in all_bases if p != upper_anchor]

    if profile == "upper_sparse":
        positions = [upper_anchor]
        positions.extend(_take_sample(rng, remaining_bases, markers - 1))

    elif profile in {"lower_sparse", "lower_dense"}:
        chosen = [upper_anchor]
        chosen.extend(_take_sample(rng, remaining_bases, markers - 1))
        positions = [(c, r) for r, c in chosen]

    elif profile == "unequal_conflict":
        conflict_base = rng.choice(all_bases)
        r, c = conflict_base
        rest = [p for p in all_bases if p != conflict_base]
        chosen = _take_sample(rng, rest, markers - 2)
        positions = [conflict_base, (c, r)]
        for index, (sr, sc) in enumerate(chosen):
            positions.append((sr, sc) if index % 2 == 0 else (sc, sr))

    elif profile == "upper_with_diagonal":
        diagonal = (rng.randrange(size),) * 2
        positions = [upper_anchor, diagonal]
        positions.extend(_take_sample(rng, remaining_bases, markers - 2))

    elif profile == "unequal_conflict_with_diagonal":
        conflict_base = rng.choice(all_bases)
        r, c = conflict_base
        rest = [p for p in all_bases if p != conflict_base]
        diagonal = (rng.randrange(size),) * 2
        chosen = _take_sample(rng, rest, markers - 3)
        positions = [conflict_base, (c, r), diagonal]
        for index, (sr, sc) in enumerate(chosen):
            positions.append((sr, sc) if index % 2 == 0 else (sc, sr))

    else:  # contract guard: schedule_profile may not invent a silent mode
        raise ValueError(f"unknown schedule profile {profile!r}")

    if len(positions) != markers or len(set(positions)) != markers:
        raise RuntimeError(
            f"profile {profile!r} rendered {len(set(positions))} unique cells, "
            f"expected {markers}"
        )
    occupied = set(positions)
    pairs = sorted(
        (r, c)
        for r, c in occupied
        if r < c and (c, r) in occupied
    )
    expected_pairs = 1 if profile.startswith("unequal_conflict") else 0
    if len(pairs) != expected_pairs:
        raise RuntimeError(
            f"profile {profile!r} rendered {len(pairs)} transpose pairs, "
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
    if not 5 <= height <= 10 or not 5 <= width <= 10:
        errors.append(f"grid side must be 5..10, got {height}x{width}")

    invalid = [
        (r, c, value)
        for r, row in enumerate(rows)
        for c, value in enumerate(row)
        if type(value) is not int or not 0 <= value <= 9
    ]
    if invalid:
        errors.append(f"cells must be integer ARC colors 0..9; first invalid {invalid[0]}")
        return errors

    markers = [(r, c, value) for r, row in enumerate(rows) for c, value in enumerate(row) if value]
    if not 3 <= len(markers) <= 8:
        errors.append(f"expected 3..8 nonzero markers, got {len(markers)}")

    colors = {value for _, _, value in markers}
    if markers and not 3 <= len(colors) <= 4:
        errors.append(f"expected three or four nonzero colors, got {len(colors)}")

    if not any(r != c for r, c, _ in markers):
        errors.append("at least one marker must be off-diagonal")

    if height == width:
        occupied = {(r, c): value for r, c, value in markers}
        conflicts = sorted(
            (r, c)
            for r, c in occupied
            if r < c and (c, r) in occupied
        )
        if len(conflicts) > 1:
            errors.append(
                "input contains more than one pre-filled transpose pair; "
                f"first pairs are {conflicts[:2]}"
            )
        elif conflicts:
            r, c = conflicts[0]
            if occupied[(r, c)] == occupied[(c, r)]:
                errors.append(
                    "pre-filled transpose pair must use unequal colors so swap "
                    f"semantics are observable; pair starts at {(r, c)}"
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
        ctx, overrides, "size", _PROFILE_SIZES[profile_index], 5, 10
    )
    markers = _draw_exact_int(
        ctx, overrides, "markers", _MARKER_ANCHORS[band][profile_index], 3, 8
    )

    positions = _profile_positions(size, markers, profile, ctx.draw_rng("layout"))
    # Canonical inputs use four or five total colors (including background).
    n_colors = 3 if size == 5 else min(4, markers)
    colors = ctx.draw_distinct_colors("source_colors", n=n_colors, exclude={0})
    grid = full_grid(size, size, 0)
    for index, (r, c) in enumerate(positions):
        grid[r][c] = colors[index % len(colors)]

    errors = self_check(grid)
    if errors:
        raise RuntimeError("generated invalid mirror scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {"size": size, "markers": markers}
    if observed != expected:
        raise RuntimeError(f"rendered axes disagree with draws: {observed} != {expected}")
    return grid


def rule_mirror(grid) -> list[list[int]]:
    """Python analysis mirror; the selected Racket rule remains authority.

    Values are read from an immutable snapshot.  Thus, on an out-of-manifold
    input with two differently colored transpose partners, the two values swap,
    matching ``(overlay g (transpose g))`` rather than sequentially smearing one
    value over both cells.
    """
    rows = _coerce_grid(grid)
    out = [row[:] for row in rows]
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            if value != 0:
                out[c][r] = value
    return out


def _rival_upper_only(grid) -> list[list[int]]:
    """Wrong shortcut suggested by every public demonstration."""
    rows = _coerce_grid(grid)
    out = [row[:] for row in rows]
    for r in range(len(rows)):
        for c in range(r + 1, len(rows)):
            if rows[r][c] != 0:
                out[c][r] = rows[r][c]
    return out


def _rival_lower_only(grid) -> list[list[int]]:
    rows = _coerce_grid(grid)
    out = [row[:] for row in rows]
    for r in range(len(rows)):
        for c in range(r):
            if rows[r][c] != 0:
                out[c][r] = rows[r][c]
    return out


def _rival_fill_empty_only(grid) -> list[list[int]]:
    """Wrong shortcut: mirror a source only when its partner is background."""
    rows = _coerce_grid(grid)
    out = [row[:] for row in rows]
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            if value != 0 and rows[c][r] == 0:
                out[c][r] = value
    return out


def _rival_transpose_only(grid) -> list[list[int]]:
    rows = _coerce_grid(grid)
    return [[rows[c][r] for c in range(len(rows))] for r in range(len(rows))]


def _rival_anti_diagonal(grid) -> list[list[int]]:
    rows = _coerce_grid(grid)
    size = len(rows)
    out = [row[:] for row in rows]
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            if value != 0:
                out[size - 1 - c][size - 1 - r] = value
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "upper_only": _rival_upper_only,
    "lower_only": _rival_lower_only,
    "fill_empty_only": _rival_fill_empty_only,
    "transpose_only": _rival_transpose_only,
    "anti_diagonal": _rival_anti_diagonal,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "upper_only": _rival_upper_only,
    "fill_empty_only": _rival_fill_empty_only,
}


def _lawful(grid) -> bool:
    return self_check(grid) == []


def _has_upper_source(grid) -> bool:
    rows = _coerce_grid(grid)
    return _lawful(rows) and any(rows[r][c] != 0 for r in range(len(rows)) for c in range(r + 1, len(rows)))


def _has_lower_source(grid) -> bool:
    rows = _coerce_grid(grid)
    return _lawful(rows) and any(rows[r][c] != 0 for r in range(len(rows)) for c in range(r))


def _has_unequal_conflict(grid) -> bool:
    rows = _coerce_grid(grid)
    if not _lawful(rows):
        return False
    return any(
        rows[r][c] != 0
        and rows[c][r] != 0
        and rows[r][c] != rows[c][r]
        for r in range(len(rows))
        for c in range(r + 1, len(rows))
    )


def _preservation_matters(grid) -> bool:
    return _lawful(grid) and _rival_transpose_only(grid) != rule_mirror(grid)


def _main_axis_matters(grid) -> bool:
    return _lawful(grid) and _rival_anti_diagonal(grid) != rule_mirror(grid)


# Directional and occupied-pair witnesses cover two independent shortcut
# families that fit every public demonstration.
SEMANTIC_WITNESSES = {
    "lower_source": _has_lower_source,
    "unequal_conflict": _has_unequal_conflict,
}
WITNESS_RIVALS = {
    "lower_source": ["upper_only", "transpose_only", "anti_diagonal"],
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
        except Exception as exc:  # contract guard: hook failures must be loud
            reasons.append(f"rival {name!r} raised {type(exc).__name__}: {exc}")
    return reasons
