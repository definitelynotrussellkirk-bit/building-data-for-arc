"""Input generator for ``Sort the Rows by Occupancy``.

The unchanged Racket authority performs one stable operation: count non-zero
cells in every row and sort the rows from greatest count to least, preserving
each row byte-for-byte.  Canonical demonstrations happen to make every row
monochromatic, so tempting wrong rules can sort by dominant-color frequency or
prioritize mixed/high-diversity rows.  Every generated input contains two
full-palette top rows whose occupancy and color-frequency rankings disagree.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "323fded12174"
TASK_ID = GENERATOR_ID
RULE_HASH = "d6c95e66f9b7"
VERSION = "2.1.0"

SUMMARY = (
    "Create 5..7 nonempty rows with distinct non-zero occupancies and two "
    "full-palette top rows arranged to refute dominant-frequency and "
    "mixed-row-priority shortcuts."
)

INVARIANTS = [
    "background is color 0 and every row contains both foreground and background",
    "row non-zero occupancies are all distinct and are not already descending",
    "the dimensions and number of non-zero colors match one canonical profile",
    "the two densest rows use every palette color while lower rows are monochromatic",
    "the second-densest row precedes the densest row in the unsorted input",
    "dominant-frequency and mixed/high-diversity priority sorts all disagree with occupancy",
]

# The third coordinate is the number of distinct NONZERO colors.  These are the
# five exact (height, width, nonzero-palette-size) profiles in the four training
# inputs plus held-out canonical input.  A single profile axis is more honest
# than independently advertising dimensions/color counts whose Cartesian
# product was never the intended curriculum.
_PROFILES: dict[str, tuple[int, int, int]] = {
    "5x8x4": (5, 8, 4),
    "5x8x5": (5, 8, 5),
    "6x10x3": (6, 10, 3),
    "7x8x4": (7, 8, 4),
    "7x9x5": (7, 9, 5),
}
_PROFILE_BY_SHAPE = {value: name for name, value in _PROFILES.items()}
_PROFILE_NAMES = tuple(_PROFILES)
_LAYOUTS = ("runs", "scattered")

AXES = {
    "profile": {
        "type": "str",
        "default": "difficulty-biased canonical profile",
        "valid": "5x8x4|5x8x5|6x10x3|7x8x4|7x9x5",
    },
    "cell_layout": {
        "type": "str",
        "default": "rng runs or scattered",
        "valid": "runs|scattered",
    },
}

# Every advertised profile/layout pair is constructive.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# Every ordinary draw is strict-canonical-profile support, by construction.
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 2


def _profile_options(difficulty: str | None) -> tuple[str, ...]:
    """Full-support profile choices with only a difficulty preference."""
    if difficulty == "easy":
        bias = ("5x8x4", "5x8x5") * 4
    elif difficulty == "hard":
        bias = ("7x8x4", "7x9x5", "6x10x3") * 4
    else:
        bias = _PROFILE_NAMES * 2
    return bias + _PROFILE_NAMES


def _layout_options(difficulty: str | None) -> tuple[str, ...]:
    # Both values remain reachable in every band.  Easy mildly favors the
    # visually simpler contiguous form; hard mildly favors the adversarial gaps.
    if difficulty == "easy":
        return ("runs", "runs", "scattered")
    if difficulty == "hard":
        return ("runs", "scattered", "scattered")
    return _LAYOUTS


def _occupancy(row: list[int] | tuple[int, ...]) -> int:
    return sum(value != 0 for value in row)


def _dominant_count(row: list[int] | tuple[int, ...]) -> int:
    counts = Counter(value for value in row if value != 0)
    return max(counts.values(), default=0)


def _sort_rows_by_occupancy(grid):
    """Independent Python mirror used only for semantic tests, never labels."""
    return [list(row) for row in sorted(grid, key=_occupancy, reverse=True)]


def _nonzero_color_count(row: list[int] | tuple[int, ...]) -> int:
    return len({value for value in row if value != 0})


def _sort_rows_by_dominant_count(grid):
    """Plausible wrong rule fitting every monochromatic canonical row."""
    return [list(row) for row in sorted(grid, key=_dominant_count, reverse=True)]


def _sort_rows_by_mixed_then_dominant(grid):
    """Prefer mixed rows, then dominant-color frequency."""
    return [
        list(row)
        for row in sorted(
            grid,
            key=lambda row: (_nonzero_color_count(row) > 1, _dominant_count(row)),
            reverse=True,
        )
    ]


def _sort_rows_by_color_count_then_dominant(grid):
    """Prefer more distinct colors, then dominant-color frequency."""
    return [
        list(row)
        for row in sorted(
            grid,
            key=lambda row: (_nonzero_color_count(row), _dominant_count(row)),
            reverse=True,
        )
    ]


def _is_contiguous(indices: list[int]) -> bool:
    return bool(indices) and indices == list(range(indices[0], indices[-1] + 1))


def _positions_for_row(
    width: int,
    count: int,
    layout: str,
    rng,
) -> list[int]:
    """Choose exact occupied columns; scattered is observably non-contiguous."""
    if layout == "runs":
        start = rng.randrange(width - count + 1)
        return list(range(start, start + count))

    # All scattered rows share a left anchor.  For count >= 2, reserve the last
    # column as an outlier and put the remaining cells in a left run.  Since
    # count <= width-1, at least one zero separates the run from the outlier.
    # This makes the layout axis exactly recoverable from pixels and also keeps
    # a large connected monochrome component across the lower rows.
    if count == 1:
        return [0]
    return list(range(count - 1)) + [width - 1]


def _balanced_palette_values(count: int, palette: tuple[int, ...]) -> list[int]:
    """Use every color and keep dominant frequency as small as possible."""
    base, extra = divmod(count, len(palette))
    values: list[int] = []
    for index, color in enumerate(palette):
        values.extend([color] * (base + (index < extra)))
    return values


def _skewed_palette_values(count: int, palette: tuple[int, ...]) -> list[int]:
    """Use every color while maximizing the first color's frequency."""
    if count < len(palette):
        raise ValueError("count must be at least the palette size")
    return [palette[0]] * (count - len(palette) + 1) + list(palette[1:])


def _grid_shape_profile(grid) -> str | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None
    if any(not isinstance(row, (list, tuple)) for row in grid) or not grid[0]:
        return None
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None
    colors = {
        value
        for row in grid
        for value in row
        if isinstance(value, int) and not isinstance(value, bool) and value != 0
    }
    return _PROFILE_BY_SHAPE.get((len(grid), width, len(colors)))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, identity, or profile-drift inputs."""
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return ["every row must be a sequence"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be nonempty and rectangular"]

    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers in 0..9"]

    profile = _grid_shape_profile(grid)
    if profile is None:
        colors = {value for row in grid for value in row if value != 0}
        errors.append(
            "grid must match a canonical (height,width,nonzero-colors) profile; "
            f"found {(len(grid), width, len(colors))}"
        )

    occupancies = [_occupancy(row) for row in grid]
    if any(count <= 0 or count >= width for count in occupancies):
        errors.append("every row must contain at least one nonzero and one zero cell")
    if len(set(occupancies)) != len(occupancies):
        errors.append(f"row occupancies must be pairwise distinct, found {occupancies}")
    if occupancies == sorted(occupancies, reverse=True):
        errors.append(f"rows are already sorted by descending occupancy: {occupancies}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The lawful grammar is deliberately anchored to all five exact profiles."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, object]:
    """Recover both advertised exact controls from returned pixels."""
    profile = _grid_shape_profile(grid)
    layout = None
    if isinstance(grid, (list, tuple)) and grid and all(
        isinstance(row, (list, tuple)) for row in grid
    ):
        occupied = [
            [column for column, value in enumerate(row) if value != 0]
            for row in grid
        ]
        if occupied and all(_is_contiguous(indices) for indices in occupied):
            layout = "runs"
        elif occupied and any(indices for indices in occupied):
            layout = "scattered"
    return {"profile": profile, "cell_layout": layout}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic lawful input; Racket remains output authority."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile_name = ctx.draw_choice("profile", _profile_options(difficulty))
    layout = ctx.draw_choice("cell_layout", _layout_options(difficulty))
    height, width, n_colors = _PROFILES[profile_name]

    palette = ctx.draw_distinct_colors("palette", n=n_colors, exclude={0})
    occupancy_rng = ctx.draw_rng("row_occupancies")

    # Pin the two largest legal occupancies and sample the rest.  Both top rows
    # can therefore use every palette color in every canonical profile.
    maximum, second = width - 1, width - 2
    occupancies = occupancy_rng.sample(range(1, width - 2), height - 2)
    occupancies.extend((maximum, second))
    occupancy_rng.shuffle(occupancies)

    # Stable color-frequency rivals must see second before maximum.  This also
    # proves the input is not already in descending occupancy order.
    maximum_index = occupancies.index(maximum)
    second_index = occupancies.index(second)
    if maximum_index < second_index:
        occupancies[maximum_index], occupancies[second_index] = (
            occupancies[second_index],
            occupancies[maximum_index],
        )

    grid = full_grid(height, width, 0)
    for row_index, count in enumerate(occupancies):
        positions = _positions_for_row(
            width,
            count,
            layout,
            ctx.draw_rng(f"row_positions_{row_index}"),
        )
        if count == maximum:
            values = _balanced_palette_values(count, palette)
        elif count == second:
            values = _skewed_palette_values(count, palette)
        else:
            values = [palette[0]] * count
        for column, value in zip(positions, values):
            grid[row_index][column] = value

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructed invalid occupancy-sort input: {errors}")
    intended = _sort_rows_by_occupancy(grid)
    rivals = {
        "dominant_color_count": _sort_rows_by_dominant_count,
        "mixed_first_then_dominant": _sort_rows_by_mixed_then_dominant,
        "color_count_then_dominant": _sort_rows_by_color_count_then_dominant,
    }
    surviving = [name for name, rival in rivals.items() if rival(grid) == intended]
    if surviving:
        raise RuntimeError(f"constructed input failed to refute rivals: {surviving}")
    return [list(row) for row in grid]


# ---------------------------------------------------------------------------
# Task-linked semantic contract
# ---------------------------------------------------------------------------

SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "dominant_color_count": _sort_rows_by_dominant_count,
    "mixed_first_then_dominant": _sort_rows_by_mixed_then_dominant,
    "color_count_then_dominant": _sort_rows_by_color_count_then_dominant,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _top_pair_refutes_color_priority(grid) -> bool:
    if self_check(grid):
        return False
    intended = _sort_rows_by_occupancy(grid)
    return all(rival(grid) != intended for rival in SEMANTIC_RIVALS.values())


SEMANTIC_WITNESSES = {
    "top_pair_refutes_color_priority": _top_pair_refutes_color_priority,
}
WITNESS_RIVALS = {
    "top_pair_refutes_color_priority": list(SEMANTIC_RIVALS),
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require valid labels and demos that eliminate the named shortcut."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    if self_check(query["input"]):
        reasons.append("query input is outside the lawful occupancy-sort grammar")

    valid_demos: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        if self_check(demo["input"]):
            reasons.append(f"demo {index} input is outside the lawful occupancy-sort grammar")
            continue
        expected = _sort_rows_by_occupancy(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output is not the authoritative occupancy sort")
            continue
        valid_demos.append(demo)

    for name, competitor in LESSON_COMPETITORS.items():
        if valid_demos and all(
            competitor(demo["input"]) == demo["output"] for demo in valid_demos
        ):
            reasons.append(f"named competitor {name!r} survives every demonstration")
    return reasons
