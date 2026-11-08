"""Generator for ARC task ``c074846d`` / ``3eff273eeb83``.

A single color-5 pivot has a contiguous, one-sided radial line of color 2.
The authoritative rule recolors the original line to 3 and draws a 90-degree
clockwise copy in color 2 around the pivot.  The generator jointly schedules
orientation and maximum-length witnesses so every three-demo query rotation
contains both source axes and a line that refutes truncating the copy at three
cells; size, short length, and pivot placement still vary by keyed RNG.
"""
from __future__ import annotations

from collections.abc import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3eff273eeb83"
VERSION = "2.1.0"  # strict indices, rotation-safe length witnesses, truthful rivals
TASK_ID = "3eff273eeb83"
RULE_HASH = "3ac43b22416f"  # sha256[:12] of whitespace-normalized canonical rule
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
_LENGTH_SCHEDULE = ("max", "max", "short", "max", "short")
SCHEDULE_CYCLE = 20  # lcm(direction period 4, length period 5); exhaustively task-tested

SUMMARY = (
    "The input contains exactly one color-5 pivot and a contiguous one-sided "
    "horizontal or vertical line of one to four color-2 cells attached to it. "
    "Recolor the original 2-line to 3, then rotate its offsets 90 degrees "
    "clockwise around the pivot and paint that copy color 2; keep the pivot 5."
)

INVARIANTS = [
    "rectangular 3..18 by 3..18 grid with background 0",
    "input palette is a subset of {0, 2, 5}",
    "exactly one color-5 pivot",
    "one to four color-2 cells form a contiguous one-sided radial line attached to the pivot",
    "the 90-degree clockwise copy of every line cell stays in bounds",
    "the generated input contains no color 3; color 3 is written only by the rule",
]

LINE_DIRECTIONS = (
    "horizontal_left",
    "horizontal_right",
    "vertical_up",
    "vertical_down",
)
SIZE_CLASSES = ("canonical", "expanded")
PIVOT_POSITIONS = ("center", "offset")
CANONICAL_PROFILES = ((3, 3), (5, 7), (6, 7), (7, 7), (9, 9), (9, 11))

AXES = {
    "line_length": {
        "type": "int",
        "default": "five-step witness schedule; keyed rng 1..3 on short slots",
        "valid": "1..4",
    },
    "line_direction": {
        "type": "str",
        "default": "sample_index cycle covering all four directions",
        "valid": "|".join(LINE_DIRECTIONS),
    },
    "size_class": {
        "type": "str",
        "default": "band-weighted canonical or expanded dimensions",
        "valid": "|".join(SIZE_CLASSES),
    },
    "pivot_position": {
        "type": "str",
        "default": "keyed rng center or observable non-center offset",
        "valid": "|".join(PIVOT_POSITIONS),
    },
}

_DIRECTION_DELTA = {
    "horizontal_left": (0, -1),
    "horizontal_right": (0, 1),
    "vertical_up": (-1, 0),
    "vertical_down": (1, 0),
}
_DELTA_DIRECTION = {value: key for key, value in _DIRECTION_DELTA.items()}


def _strict_int(value: object, name: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an integer, got {value!r}")
    return value


def _draw_choice(ctx, overrides, label: str, default_options: tuple[str, ...]) -> str:
    """Use the full declared domain for overrides and weighted defaults otherwise."""
    full_options = {
        "line_direction": LINE_DIRECTIONS,
        "size_class": SIZE_CLASSES,
        "pivot_position": PIVOT_POSITIONS,
    }[label]
    if overrides.get(label) is not None:
        return ctx.draw_choice(label, full_options)
    return ctx.draw_choice(label, default_options)


def _profile_options(difficulty: object) -> tuple[str, ...]:
    if difficulty == "easy":
        return ("canonical", "canonical", "expanded")
    if difficulty == "hard":
        return ("canonical", "expanded", "expanded")
    return ("canonical", "expanded")


def _expanded_profiles(difficulty: object) -> list[tuple[int, int]]:
    if difficulty == "easy":
        h_range, w_range = range(6, 11), range(7, 13)
    elif difficulty == "hard":
        h_range, w_range = range(10, 19), range(10, 19)
    else:
        h_range, w_range = range(8, 16), range(8, 17)
    return [(h, w) for h in h_range for w in w_range
            if (h, w) not in CANONICAL_PROFILES]


def _pivot_candidates(
    h: int,
    w: int,
    line_length: int,
    direction: str,
    pivot_position: str,
) -> list[tuple[int, int]]:
    dr, dc = _DIRECTION_DELTA[direction]
    center = (h // 2, w // 2)
    candidates: list[tuple[int, int]] = []
    for pr in range(h):
        for pc in range(w):
            if pivot_position == "center" and (pr, pc) != center:
                continue
            if pivot_position == "offset" and (pr, pc) == center:
                continue
            valid = True
            for distance in range(1, line_length + 1):
                source = (pr + dr * distance, pc + dc * distance)
                rotated = (pr + dc * distance, pc - dr * distance)
                if not (
                    0 <= source[0] < h
                    and 0 <= source[1] < w
                    and 0 <= rotated[0] < h
                    and 0 <= rotated[1] < w
                ):
                    valid = False
                    break
            if valid:
                candidates.append((pr, pc))
    return candidates


def _choose_layout(
    *,
    size_class: str,
    difficulty: object,
    line_length: int,
    direction: str,
    pivot_position: str,
    rng,
) -> tuple[int, int, int, int]:
    profiles = (
        list(CANONICAL_PROFILES)
        if size_class == "canonical"
        else _expanded_profiles(difficulty)
    )
    feasible: list[tuple[int, int, list[tuple[int, int]]]] = []
    for h, w in profiles:
        pivots = _pivot_candidates(h, w, line_length, direction, pivot_position)
        if pivots:
            feasible.append((h, w, pivots))
    if not feasible:
        raise RuntimeError(
            "no lawful layout for "
            f"size_class={size_class!r}, line_length={line_length}, "
            f"line_direction={direction!r}, pivot_position={pivot_position!r}"
        )
    h, w, pivots = rng.choice(feasible)
    pr, pc = rng.choice(pivots)
    return h, w, pr, pc


def generate(seed, sample_index, *, difficulty=None, **overrides):
    sample_index = _strict_int(sample_index, "sample_index")
    if sample_index < 0:
        raise ValueError(f"sample_index must be nonnegative, got {sample_index!r}")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(
            f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}"
        )

    if overrides.get("line_length") is not None:
        _strict_int(overrides["line_length"], "line_length")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    length_class = _LENGTH_SCHEDULE[sample_index % len(_LENGTH_SCHEDULE)]
    if overrides.get("line_length") is not None:
        line_length = ctx.draw_int("line_length", 1, 4)
    elif length_class == "max":
        line_length = ctx.draw_int("line_length", 4, 4)
    else:
        line_length = ctx.draw_int("line_length", 1, 3)

    # Any four consecutive pairs contain all directions and at least two length-4
    # witnesses. Holding out any one query therefore leaves three directions,
    # both axes, and a demonstration that refutes a copy truncated at length 3.
    scheduled_direction = LINE_DIRECTIONS[sample_index % len(LINE_DIRECTIONS)]
    direction = _draw_choice(
        ctx, overrides, "line_direction", (scheduled_direction,)
    )
    size_class = _draw_choice(
        ctx, overrides, "size_class", _profile_options(difficulty)
    )
    pivot_position = _draw_choice(
        ctx, overrides, "pivot_position", PIVOT_POSITIONS
    )

    rng = ctx.draw_rng("layout")
    h, w, pr, pc = _choose_layout(
        size_class=size_class,
        difficulty=difficulty,
        line_length=line_length,
        direction=direction,
        pivot_position=pivot_position,
        rng=rng,
    )

    grid = full_grid(h, w, 0)
    grid[pr][pc] = 5
    dr, dc = _DIRECTION_DELTA[direction]
    for distance in range(1, line_length + 1):
        grid[pr + dr * distance][pc + dc * distance] = 2
    return grid


def _parse_line(grid: list[list[int]]) -> tuple[dict[str, object], list[str]]:
    """Parse the exact lawful input grammar and return its observable signature."""
    if not grid or not grid[0]:
        return {}, ["grid must be non-empty"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {}, ["grid must be rectangular"]

    errors: list[str] = []
    height = len(grid)
    if not (3 <= height <= 18 and 3 <= width <= 18):
        errors.append(
            f"dimensions {height}x{width} outside declared 3..18 by 3..18"
        )
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("all cells must be integer ARC colors 0..9")
        return {}, errors

    illegal = sorted({value for row in grid for value in row} - {0, 2, 5})
    if illegal:
        errors.append(f"input palette contains illegal colors {illegal}; expected only 0,2,5")

    pivots = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    ]
    twos = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    if len(pivots) != 1:
        errors.append(f"expected exactly one color-5 pivot, found {len(pivots)}")
        return {}, errors
    if not (1 <= len(twos) <= 4):
        errors.append(f"expected 1..4 color-2 line cells, found {len(twos)}")
        return {}, errors

    pr, pc = pivots[0]
    offsets = {(r - pr, c - pc) for r, c in twos}
    direction = None
    for candidate, (dr, dc) in _DIRECTION_DELTA.items():
        expected = {(dr * distance, dc * distance)
                    for distance in range(1, len(twos) + 1)}
        if offsets == expected:
            direction = candidate
            break
    if direction is None:
        errors.append(
            "color-2 cells must be one contiguous, one-sided horizontal or "
            "vertical line attached to the pivot"
        )
        return {}, errors

    dr, dc = _DIRECTION_DELTA[direction]
    for distance in range(1, len(twos) + 1):
        rr, cc = pr + dc * distance, pc - dr * distance
        if not (0 <= rr < height and 0 <= cc < width):
            errors.append("the clockwise-rotated line would leave the grid")
            break

    signature = {
        "line_length": len(twos),
        "line_direction": direction,
        "size_class": (
            "canonical" if (height, width) in CANONICAL_PROFILES else "expanded"
        ),
        "pivot_position": (
            "center" if (pr, pc) == (height // 2, width // 2) else "offset"
        ),
    }
    return signature, errors


def observe_overrides(grid) -> dict[str, object]:
    signature, errors = _parse_line(grid)
    return {} if errors else signature


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    _, errors = _parse_line(grid)
    return errors


def strict_canonical_like(grid):
    """Every generated scene lies on the full authority-valid input manifold."""
    return self_check(grid)


def _transform(
    grid, *, rotation: str = "clockwise", mark_original: bool = True,
    clip_rotated: bool = False, copy_limit: int | None = None,
):
    """Task-local rival oracle used only for semantic tests, never generation."""
    signature, errors = _parse_line(grid)
    if errors:
        raise ValueError("invalid task input: " + "; ".join(errors))
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    pivot = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    )
    pr, pc = pivot
    output[pr][pc] = 5
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 2:
                continue
            output[r][c] = 3 if mark_original else 2
            dr, dc = r - pr, c - pc
            if copy_limit is not None and abs(dr) + abs(dc) > copy_limit:
                continue
            if rotation == "clockwise":
                rr, cc = pr + dc, pc - dr
            elif rotation == "counterclockwise":
                rr, cc = pr - dc, pc + dr
            elif rotation == "none":
                continue
            else:
                raise ValueError(f"unknown rotation {rotation!r}")
            if 0 <= rr < height and 0 <= cc < width:
                output[rr][cc] = 2
            elif not clip_rotated:
                raise ValueError("rotated rival cell leaves the grid")
    return output


def _counterclockwise(grid):
    return _transform(
        grid, rotation="counterclockwise", mark_original=True, clip_rotated=True
    )


def _recolor_only(grid):
    return _transform(grid, rotation="none", mark_original=True)


def _copy_without_recolor(grid):
    return _transform(grid, rotation="clockwise", mark_original=False)


def _copy_at_most_three(grid):
    """Plausible training-only rival: recolor all, but copy only distances 1..3."""
    return _transform(grid, rotation="clockwise", mark_original=True, copy_limit=3)


def _witness_direction(name: str) -> Callable[[list[list[int]]], bool]:
    return lambda grid: observe_overrides(grid).get("line_direction") == name


SEMANTIC_WITNESSES = {
    **{name: _witness_direction(name) for name in LINE_DIRECTIONS},
    "unit_line": lambda grid: observe_overrides(grid).get("line_length") == 1,
    "multi_cell_line": lambda grid: int(observe_overrides(grid).get("line_length", 0)) >= 2,
    "length_four": lambda grid: observe_overrides(grid).get("line_length") == 4,
    "canonical_scale": lambda grid: observe_overrides(grid).get("size_class") == "canonical",
    "expanded_scale": lambda grid: observe_overrides(grid).get("size_class") == "expanded",
    "center_pivot": lambda grid: observe_overrides(grid).get("pivot_position") == "center",
    "offset_pivot": lambda grid: observe_overrides(grid).get("pivot_position") == "offset",
}

SEMANTIC_RIVALS = {
    "counterclockwise_rotation": _counterclockwise,
    "recolor_without_copy": _recolor_only,
    "copy_without_recolor": _copy_without_recolor,
    "copy_at_most_three": _copy_at_most_three,
}
_ALWAYS_REFUTED_RIVALS = (
    "counterclockwise_rotation",
    "recolor_without_copy",
    "copy_without_recolor",
)
WITNESS_RIVALS = {
    name: list(_ALWAYS_REFUTED_RIVALS)
    for name in SEMANTIC_WITNESSES
}
WITNESS_RIVALS["length_four"].append("copy_at_most_three")
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# No declared wrong rule fits all seven labeled canonical pairs. The max-three
# rival fits the five public demonstrations, but canonical test 0 refutes it.
CANONICAL_SHORTCUTS = {}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(
            f"need at least {EXAMPLES_NEEDED} demonstrations, got {len(demos)}"
        )
        return reasons

    directions: set[str] = set()
    has_length_four = False
    for index, demo in enumerate(demos):
        grid = demo.get("input")
        expected = demo.get("output")
        signature, errors = _parse_line(grid)
        if errors:
            reasons.append(f"demo {index} has invalid input: {'; '.join(errors)}")
            continue
        directions.add(str(signature["line_direction"]))
        has_length_four |= signature["line_length"] == 4
        if _transform(grid) != expected:
            reasons.append(f"demo {index} does not exhibit the authoritative rule")

    axes_seen = {
        "horizontal" if direction.startswith("horizontal") else "vertical"
        for direction in directions
    }
    if len(directions) < 3 or axes_seen != {"horizontal", "vertical"}:
        reasons.append(
            "demonstrations must cover at least three absolute directions and "
            "both horizontal/vertical source axes"
        )
    if not has_length_four:
        reasons.append(
            "demonstrations need a length-4 line to refute copying at most three cells"
        )

    query_errors = self_check(query.get("input"))
    if query_errors:
        reasons.append("query input is invalid: " + "; ".join(query_errors))

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            reasons.append(f"named rival survived all demonstrations: {name}")
    return reasons


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    sample_index = _strict_int(sample_index, "sample_index")
    if sample_index < 0:
        raise ValueError(f"sample_index must be nonnegative, got {sample_index!r}")
    return LINE_DIRECTIONS[sample_index % len(LINE_DIRECTIONS)]


SCHEDULE_PROFILES = LINE_DIRECTIONS
