"""Constructive curriculum for ARC task 281123b4 / generator 9000d0ea6484.

Each input is a 4x19 grid containing four aligned 4x4 sections.  Full-height
color-3 columns at 4, 9, and 14 separate the sections.  The output is 4x4 and,
for every aligned cell, selects the first nonzero source in section order
2 -> 3 -> 0 -> 1.

Every generated grid is a complete lesson rather than a random texture: it
contains an empty position, a solo position for every section, and all six
pairwise overlaps.  Those eleven mandatory signatures identify the complete
priority order inside one example.  Five remaining cells provide a
controlled difficulty axis without removing any required witness.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from itertools import permutations
from typing import Any

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "9000d0ea6484"
TASK_ID = "9000d0ea6484"
VERSION = "3.0.0"
RULE_HASH = "c9256d51e807"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Generate the canonical 4x19 four-section layout with green divider "
    "columns.  Every input constructively includes zero fallback, all four "
    "solo-section cases, and all six pairwise overlaps, so the section "
    "priority 2 > 3 > 0 > 1 is identifiable.  Five extra aligned cells vary "
    "from simple to three/four-way overlaps with difficulty.  Section colors "
    "are distinct nonzero non-divider colors and are randomized away from the "
    "fixed public color-to-priority mapping unless explicitly overridden."
)

INVARIANTS = [
    "input is exactly 4x19 and output is exactly 4x4",
    "columns 4, 9, and 14 are full-height color-3 dividers",
    "each section uses one distinct color outside {0, 3}",
    "every input contains empty, four solo, and six pairwise witness cells",
    "the only section order consistent with the intended output is 2,3,0,1",
]

AXES = {
    "sec0_color": {
        "type": "color",
        "default": "keyed distinct non-{0,3}; avoids canonical sec0 color",
        "valid": "1..2|4..9",
    },
    "sec1_color": {
        "type": "color",
        "default": "keyed distinct non-{0,3}; avoids canonical sec1 color",
        "valid": "1..2|4..9",
    },
    "sec2_color": {
        "type": "color",
        "default": "keyed distinct non-{0,3}; avoids canonical sec2 color",
        "valid": "1..2|4..9",
    },
    "sec3_color": {
        "type": "color",
        "default": "keyed distinct non-{0,3}; avoids canonical sec3 color",
        "valid": "1..2|4..9",
    },
    "extra_overlap_count": {
        "type": "int",
        "default": "difficulty-aware keyed draw",
        "valid": "0..5",
    },
}

# Duplicate explicit section colors are the only cross-axis incompatibility.
# It is reported dynamically with ValueError.incompatible_axes so the shared
# override gate can distinguish it from an accidental rejection.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

_STARTS = (0, 5, 10, 15)
_DIVIDERS = (4, 9, 14)
_INTENDED_ORDER = (2, 3, 0, 1)
_CANONICAL_SECTION_COLORS = (8, 5, 9, 4)
_COLOR_AXES = tuple(f"sec{i}_color" for i in range(4))
_ALLOWED_COLORS = frozenset({1, 2, 4, 5, 6, 7, 8, 9})

# Tuples (rather than sets) make the source deterministic and readable.  They
# are converted to frozensets when compared with observed cell signatures.
_MANDATORY_SIGNATURES: tuple[tuple[int, ...], ...] = (
    (),
    (0,), (1,), (2,), (3,),
    (0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3),
)
_COMPLEX_EXTRA_SIGNATURES: tuple[tuple[int, ...], ...] = (
    (0, 1, 2, 3),
    (0, 2, 3),
    (1, 2, 3),
    (0, 1, 2),
    (0, 1, 3),
)
_SIMPLE_EXTRA_SIGNATURES: tuple[tuple[int, ...], ...] = (
    (), (0,), (1,), (2,), (3,),
)
_MANDATORY_SIGNATURE_SET = frozenset(map(frozenset, _MANDATORY_SIGNATURES))
_VALID_DIFFICULTIES = frozenset({"easy", "medium", "hard"})


def _validate_call_arguments(seed: Any, sample_index: Any, difficulty: Any) -> None:
    """Reject scalar coercions before they can change deterministic draw keys."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool or a coercible scalar)")
    if type(sample_index) is not int:
        raise TypeError(
            "sample_index must be a nonnegative integer "
            "(not bool or a coercible scalar)"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty is not None and (
        type(difficulty) is not str or difficulty not in _VALID_DIFFICULTIES
    ):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")


def _validate_explicit_overrides(overrides: dict[str, Any]) -> dict[str, int]:
    explicit: dict[str, int] = {}
    for axis in _COLOR_AXES:
        value = overrides.get(axis)
        if value is None:
            continue
        if type(value) is not int or value not in _ALLOWED_COLORS:
            raise ValueError(
                f"{axis} must be an integer ARC color in "
                f"{sorted(_ALLOWED_COLORS)}, got {value!r}"
            )
        explicit[axis] = value

    count = overrides.get("extra_overlap_count")
    if count is not None and (type(count) is not int or not 0 <= count <= 5):
        raise ValueError(
            "extra_overlap_count must be an integer in [0, 5], "
            f"got {count!r}"
        )

    by_color: dict[int, list[str]] = {}
    for axis, value in explicit.items():
        by_color.setdefault(value, []).append(axis)
    duplicate_axes = sorted(
        axis for axes in by_color.values() if len(axes) > 1 for axis in axes
    )
    if duplicate_axes:
        exc = ValueError(
            "section colors must be pairwise distinct; conflicting axes: "
            + ", ".join(duplicate_axes)
        )
        exc.incompatible_axes = tuple(duplicate_axes)  # type: ignore[attr-defined]
        raise exc
    return explicit


def _draw_section_colors(ctx, explicit: dict[str, int]) -> tuple[int, int, int, int]:
    colors: list[int] = []
    for index, axis in enumerate(_COLOR_AXES):
        # Reserve explicit colors on later axes.  This is the important part of
        # making every legal single-axis pin completable: an unpinned earlier
        # draw can never consume a caller's future requested color.
        future_explicit = {
            explicit[later]
            for later in _COLOR_AXES[index + 1 :]
            if later in explicit
        }
        excluded = {0, 3, *colors, *future_explicit}
        if axis not in explicit:
            # Public demonstrations permanently bind priority to 8/5/9/4.
            # Avoiding each section's public color by default turns palette
            # reassignment into a guaranteed shortcut counterexample while
            # preserving all colors as supported explicit overrides.
            excluded.add(_CANONICAL_SECTION_COLORS[index])
        colors.append(ctx.draw_color(axis, exclude=excluded))
    return tuple(colors)  # type: ignore[return-value]


def _signature_schedule(ctx, extra_overlap_count: int) -> list[tuple[int, ...]]:
    complex_extras = list(_COMPLEX_EXTRA_SIGNATURES)
    simple_extras = list(_SIMPLE_EXTRA_SIGNATURES)
    ctx.draw_rng("complex_extra_order").shuffle(complex_extras)
    ctx.draw_rng("simple_extra_order").shuffle(simple_extras)
    signatures = [
        *_MANDATORY_SIGNATURES,
        *complex_extras[:extra_overlap_count],
        *simple_extras[: 5 - extra_overlap_count],
    ]
    ctx.draw_rng("cell_permutation").shuffle(signatures)
    return signatures


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic, complete priority-order lesson."""
    _validate_call_arguments(seed, sample_index, difficulty)
    _validate_override_keys(overrides)
    explicit = _validate_explicit_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    colors = _draw_section_colors(ctx, explicit)
    extra_overlap_count = ctx.draw_int_diff("extra_overlap_count", 0, 5)
    signatures = _signature_schedule(ctx, extra_overlap_count)

    grid = [[0 for _ in range(19)] for _ in range(4)]
    for row in range(4):
        for divider in _DIVIDERS:
            grid[row][divider] = 3

    for position, active_sections in enumerate(signatures):
        row, col = divmod(position, 4)
        for section in active_sections:
            grid[row][_STARTS[section] + col] = colors[section]

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("internal generator error: " + "; ".join(errors))
    return grid


def _shape(grid: Any) -> tuple[int, int] | None:
    if not isinstance(grid, list) or not grid:
        return None
    if not all(isinstance(row, list) and row for row in grid):
        return None
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None
    return len(grid), width


def _section_colors(grid: list[list[int]]) -> tuple[int, int, int, int] | None:
    colors: list[int] = []
    for start in _STARTS:
        seen = {
            grid[row][start + col]
            for row in range(4)
            for col in range(4)
            if grid[row][start + col] != 0
        }
        if len(seen) != 1:
            return None
        colors.append(next(iter(seen)))
    return tuple(colors)  # type: ignore[return-value]


def _signatures(grid: list[list[int]]) -> list[frozenset[int]]:
    return [
        frozenset(
            section
            for section, start in enumerate(_STARTS)
            if grid[row][start + col] != 0
        )
        for row in range(4)
        for col in range(4)
    ]


def _structural_errors(grid: Any) -> list[str]:
    shape = _shape(grid)
    if shape is None:
        return ["grid must be a non-empty rectangular list of rows"]
    if shape != (4, 19):
        return [f"expected canonical 4x19 input, got {shape[0]}x{shape[1]}"]

    errors: list[str] = []
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"grid contains non-ARC value {value!r}")
                return errors

    for divider in _DIVIDERS:
        if any(grid[row][divider] != 3 for row in range(4)):
            errors.append(f"column {divider} must be a full-height color-3 divider")
    for row in range(4):
        for col in range(19):
            if col not in _DIVIDERS and grid[row][col] == 3:
                errors.append("color 3 may appear only in divider columns")
                break

    colors = _section_colors(grid)
    if colors is None:
        errors.append("each section must contain exactly one nonzero color")
    else:
        if any(color not in _ALLOWED_COLORS for color in colors):
            errors.append("section colors must be nonzero and different from divider color 3")
        if len(set(colors)) != 4:
            errors.append("the four section colors must be pairwise distinct")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Accept exactly the structural family shared by all canonical inputs."""
    return _structural_errors(grid)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate canonical inputs and the stronger synthetic teaching family.

    The public examples use the fixed palette (8,5,9,4) but do not each carry
    all eleven synthetic witnesses.  Noncanonical palettes are the generated
    curriculum and must carry the complete witness set; the canonical palette
    is retained as a lawful anchor profile under its original structural
    contract.
    """
    del difficulty, meta
    errors = _structural_errors(grid)
    if errors:
        return errors
    if _section_colors(grid) == _CANONICAL_SECTION_COLORS:
        return []
    observed = set(_signatures(grid))
    missing = _MANDATORY_SIGNATURE_SET - observed
    if missing:
        rendered = sorted(tuple(sorted(sig)) for sig in missing)
        errors.append(f"missing mandatory aligned-cell signatures: {rendered}")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact public axis from pixels in a generated input."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe axes from invalid grid: " + "; ".join(errors))
    colors = _section_colors(grid)
    assert colors is not None
    extras = list(_signatures(grid))
    for required in _MANDATORY_SIGNATURE_SET:
        extras.remove(required)
    if len(extras) != 5:
        raise ValueError(f"expected five extra signatures, found {len(extras)}")
    return {
        "sec0_color": colors[0],
        "sec1_color": colors[1],
        "sec2_color": colors[2],
        "sec3_color": colors[3],
        "extra_overlap_count": sum(len(signature) >= 2 for signature in extras),
    }


def _apply_priority(grid: Sequence[Sequence[int]], order: Sequence[int]) -> list[list[int]]:
    return [
        [
            next(
                (
                    grid[row][_STARTS[section] + col]
                    for section in order
                    if grid[row][_STARTS[section] + col] != 0
                ),
                0,
            )
            for col in range(4)
        ]
        for row in range(4)
    ]


def rule_mirror(grid) -> list[list[int]]:
    """Independent-language mirror of the selected Racket priority rule."""
    return _apply_priority(grid, _INTENDED_ORDER)


def _fixed_canonical_color_priority(grid) -> list[list[int]]:
    rank = {9: 0, 4: 1, 8: 2, 5: 3}
    output: list[list[int]] = []
    for row in range(4):
        out_row: list[int] = []
        for col in range(4):
            values = [
                grid[row][start + col]
                for start in _STARTS
                if grid[row][start + col] != 0
            ]
            out_row.append(
                min(values, key=lambda value: (rank.get(value, 100 + value), value))
                if values
                else 0
            )
        output.append(out_row)
    return output


def _numeric_max(grid) -> list[list[int]]:
    return [
        [max(grid[row][start + col] for start in _STARTS) for col in range(4)]
        for row in range(4)
    ]


def _numeric_min_nonzero(grid) -> list[list[int]]:
    output: list[list[int]] = []
    for row in range(4):
        out_row: list[int] = []
        for col in range(4):
            values = [grid[row][start + col] for start in _STARTS]
            nonzero = [value for value in values if value != 0]
            out_row.append(min(nonzero) if nonzero else 0)
        output.append(out_row)
    return output


def _priority_solver(order: Sequence[int]):
    return lambda grid: _apply_priority(grid, order)


def _zero_falls_back_to_section1(grid) -> list[list[int]]:
    """Plausible wrong rule: empty aligned cells inherit section 1's color."""
    output = rule_mirror(grid)
    colors = _section_colors(grid)
    if colors is None:
        return output
    for row in range(4):
        for col in range(4):
            if output[row][col] == 0:
                output[row][col] = colors[1]
    return output


def _ignore_section1(grid) -> list[list[int]]:
    """Plausible wrong rule: use only the first three priority sources."""
    return _apply_priority(grid, (2, 3, 0))


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "fixed_canonical_color_priority": _fixed_canonical_color_priority,
    "left_to_right_sections": _priority_solver((0, 1, 2, 3)),
    "right_to_left_sections": _priority_solver((3, 2, 1, 0)),
    "numeric_max": _numeric_max,
    "numeric_min_nonzero": _numeric_min_nonzero,
    "zero_falls_back_to_section1": _zero_falls_back_to_section1,
    "ignore_section1": _ignore_section1,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # All public examples use section colors (8,5,9,4), exactly encoding the
    # intended priority as 9 > 4 > 8 > 5.  Generated palettes break that tie.
    "fixed_canonical_color_priority": _fixed_canonical_color_priority,
}


def _has_signature(grid: Any, signature: frozenset[int]) -> bool:
    return not _structural_errors(grid) and signature in _signatures(grid)


def _complete_pairwise_witness(grid: Any) -> bool:
    if _structural_errors(grid):
        return False
    seen = set(_signatures(grid))
    return all(
        frozenset({first, second}) in seen
        for first in range(4)
        for second in range(first + 1, 4)
    )


def _all_solo_witness(grid: Any) -> bool:
    return (
        not _structural_errors(grid)
        and all(_has_signature(grid, frozenset({section})) for section in range(4))
    )


def _rival_counterexample(name: str):
    def witness(grid: Any) -> bool:
        return (
            not _structural_errors(grid)
            and SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)
        )

    return witness


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "zero_fallback": lambda grid: _has_signature(grid, frozenset()),
    "all_solo_sections": _all_solo_witness,
    "all_pairwise_priorities": _complete_pairwise_witness,
    "fixed_color_shortcut_counterexample": _rival_counterexample(
        "fixed_canonical_color_priority"
    ),
    "numeric_max_counterexample": _rival_counterexample("numeric_max"),
    "numeric_min_counterexample": _rival_counterexample("numeric_min_nonzero"),
}
WITNESS_RIVALS = {
    "zero_fallback": ["zero_falls_back_to_section1"],
    "all_solo_sections": ["ignore_section1"],
    "all_pairwise_priorities": [
        "left_to_right_sections",
        "right_to_left_sections",
    ],
    "fixed_color_shortcut_counterexample": ["fixed_canonical_color_priority"],
    "numeric_max_counterexample": ["numeric_max"],
    "numeric_min_counterexample": ["numeric_min_nonzero"],
}

def _valid_output_grid(grid: Any) -> bool:
    return (
        isinstance(grid, list)
        and len(grid) == 4
        and all(isinstance(row, list) and len(row) == 4 for row in grid)
        and all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
    )


def lesson_identifiable(demos, query) -> list[str]:
    """Verify outputs and reject every alternate section ordering and rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    lawful_demos: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input invalid: {'; '.join(errors)}")
            continue
        if not _valid_output_grid(pair["output"]):
            reasons.append(f"demo {index} output must be a 4x4 ARC grid")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with priority 2>3>0>1")
            continue
        lawful_demos.append(pair)

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append("query input invalid: " + "; ".join(query_errors))
    if "output" in query and query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with priority 2>3>0>1")
    if reasons:
        return reasons

    surviving_orders = [
        order
        for order in permutations(range(4))
        if all(_apply_priority(pair["input"], order) == pair["output"] for pair in lawful_demos)
    ]
    if surviving_orders != [_INTENDED_ORDER]:
        reasons.append(
            "demonstrations do not uniquely identify the section order; "
            f"survivors={surviving_orders}"
        )

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in lawful_demos):
            reasons.append(f"named rival {name!r} survives every demonstration")
    return reasons
