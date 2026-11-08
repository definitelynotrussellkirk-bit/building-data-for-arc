"""Generator for the exact-two-border yellow-component recolor task.

Every 4-connected yellow (4) component touching exactly two distinct grid
borders is recolored cyan (8).  Yellow components touching zero, one, three, or
four borders remain yellow.  The five-pair production schedule deliberately
includes opposite-border targets and three-border near misses, because the
canonical examples alone cannot distinguish the intended rule from the
plausible shortcuts "adjacent corners only" and "at least two borders".
"""
from __future__ import annotations

from collections.abc import Callable, Iterable

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "4d3c5600ffbd"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "af5bd9f68ba9"
SUMMARY = (
    "Recolor yellow components touching exactly two distinct borders to cyan; "
    "retain yellow components touching zero, one, three, or four borders."
)
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "input palette is exactly background 0 and yellow 4; cyan 8 is answer-only",
    "at least one yellow component touches exactly two borders",
    "at least one yellow component touches a number of borders other than two",
    "at least one adjacent-border target is present in every lawful scene",
    "same-color components are 4-connected and separated by background",
]

SCENE_PROFILES = ("canonical_anchor", "opposite_span", "three_side")
SCHEDULE_PROFILES = SCENE_PROFILES
_SCHEDULE_SEQUENCE = (
    "opposite_span",
    "three_side",
    "opposite_span",
    "three_side",
    "canonical_anchor",
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five-pair rotation-safe semantic schedule",
        "valid": "|".join(SCENE_PROFILES),
    },
    "transform": {
        "type": "int",
        "default": "keyed rng 0..7",
        "valid": "0..7",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# All four train inputs plus the test input from the selected canonical row.
# These are input anchors only; the Racket rule remains output authority.
_PUBLIC_ROWS = (
    (
        "404440000",
        "000000000",
        "400000000",
        "400000000",
        "400000000",
        "000444000",
        "000000000",
        "000000000",
        "444000000",
    ),
    (
        "044000444",
        "000000444",
        "000000444",
        "004440000",
        "000000000",
        "000000000",
        "000000000",
        "000000000",
        "400000000",
    ),
    (
        "444000000",
        "444000000",
        "444000000",
        "000044000",
        "000044000",
        "000000000",
        "000000000",
        "000000000",
        "400000000",
    ),
    (
        "00444400",
        "00000000",
        "00000000",
        "00444000",
        "00444000",
        "00000000",
        "00000444",
        "44000444",
    ),
    (
        "004444000",
        "000000000",
        "000000000",
        "000000000",
        "000044000",
        "000000000",
        "000000000",
        "440000000",
        "440000444",
    ),
)

_SIDES = ("top", "bottom", "left", "right")
_OPPOSITE_SIDE_SETS = {
    frozenset(("top", "bottom")),
    frozenset(("left", "right")),
}
_CORNER_SIDE_SETS = (
    ("top", "left"),
    ("top", "right"),
    ("bottom", "left"),
    ("bottom", "right"),
)

# Small shape families used only for retained components and corner targets.
# Special opposite-span and three-side components are constructed separately.
_BASE_SHAPES = (
    ((0, 0),),
    ((0, 0), (1, 0)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
)


def _empty_grid(height: int, width: int) -> list[list[int]]:
    return [[0 for _ in range(width)] for _ in range(height)]


def _parse_rows(rows: Iterable[str]) -> list[list[int]]:
    return [[int(value) for value in row] for row in rows]


def _rotate90(grid: list[list[int]]) -> list[list[int]]:
    return [
        [grid[len(grid) - 1 - row][col] for row in range(len(grid))]
        for col in range(len(grid[0]))
    ]


def _reflect(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _d4(grid: list[list[int]]) -> tuple[list[list[int]], ...]:
    transformed = []
    current = [row[:] for row in grid]
    for _ in range(4):
        transformed.append([row[:] for row in current])
        transformed.append(_reflect(current))
        current = _rotate90(current)
    return tuple(transformed)


def _grid_key(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _canonical_orientation(grid: list[list[int]]) -> list[list[int]]:
    return min(_d4(grid), key=_grid_key)


def _normalize_shape(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _shape_orientations(shape: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    shape = tuple(shape)
    height = max(row for row, _ in shape) + 1
    width = max(col for _, col in shape) + 1
    grid = _empty_grid(height, width)
    for row, col in shape:
        grid[row][col] = 1
    variants = {
        _normalize_shape(
            (row, col)
            for row, values in enumerate(transformed)
            for col, value in enumerate(values)
            if value
        )
        for transformed in _d4(grid)
    }
    return tuple(sorted(variants))


_SHAPE_FAMILIES = tuple(_shape_orientations(shape) for shape in _BASE_SHAPES)
_PUBLIC_GRIDS = tuple(_parse_rows(rows) for rows in _PUBLIC_ROWS)
_PUBLIC_KEYS = {
    _grid_key(transformed)
    for grid in _PUBLIC_GRIDS
    for transformed in _d4(grid)
}


def _touch_sides(
    cells: Iterable[tuple[int, int]], height: int, width: int
) -> tuple[str, ...]:
    cells = tuple(cells)
    sides = []
    if any(row == 0 for row, _ in cells):
        sides.append("top")
    if any(row == height - 1 for row, _ in cells):
        sides.append("bottom")
    if any(col == 0 for _, col in cells):
        sides.append("left")
    if any(col == width - 1 for _, col in cells):
        sides.append("right")
    return tuple(sides)


def _components(grid: list[list[int]]) -> list[dict[str, object]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row, next_col = current_row + dr, current_col + dc
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (
                        (next_row, next_col) in seen
                        or grid[next_row][next_col] != color
                    ):
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))
            found.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "sides": _touch_sides(cells, height, width),
                }
            )
    return found


def _free(
    cells: Iterable[tuple[int, int]],
    occupied: set[tuple[int, int]],
    height: int,
    width: int,
) -> bool:
    cells = tuple(cells)
    proposed = set(cells)
    for row, col in cells:
        if not (0 <= row < height and 0 <= col < width):
            return False
        if (row, col) in occupied:
            return False
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbor = (row + dr, col + dc)
            if neighbor in occupied and neighbor not in proposed:
                return False
    return True


def _paint(
    grid: list[list[int]], occupied: set[tuple[int, int]], cells: Iterable[tuple[int, int]]
) -> None:
    for row, col in cells:
        grid[row][col] = 4
        occupied.add((row, col))


def _place_component(
    grid: list[list[int]],
    occupied: set[tuple[int, int]],
    rng,
    *,
    exact_sides: tuple[str, ...] | None = None,
    touch_count: int | None = None,
    min_size: int = 1,
    max_size: int = 4,
) -> tuple[tuple[int, int], ...] | None:
    height, width = len(grid), len(grid[0])
    candidates = []
    for family in _SHAPE_FAMILIES:
        for shape in family:
            if not min_size <= len(shape) <= max_size:
                continue
            shape_height = max(row for row, _ in shape) + 1
            shape_width = max(col for _, col in shape) + 1
            for row0 in range(height - shape_height + 1):
                for col0 in range(width - shape_width + 1):
                    cells = tuple((row0 + row, col0 + col) for row, col in shape)
                    sides = _touch_sides(cells, height, width)
                    if exact_sides is not None and set(sides) != set(exact_sides):
                        continue
                    if touch_count is not None and len(sides) != touch_count:
                        continue
                    if _free(cells, occupied, height, width):
                        candidates.append(cells)
    if not candidates:
        return None
    cells = rng.choice(candidates)
    _paint(grid, occupied, cells)
    return cells


def _put_opposite_span(
    grid: list[list[int]], occupied: set[tuple[int, int]], rng
) -> None:
    height, width = len(grid), len(grid[0])
    col = rng.choice(tuple(range(3, width - 3)))
    cells = [(row, col) for row in range(height)]
    bulge_row = rng.choice(tuple(range(2, height - 2)))
    bulge_direction = rng.choice((-1, 1))
    cells.append((bulge_row, col + bulge_direction))
    _paint(grid, occupied, cells)


def _put_three_side(
    grid: list[list[int]], occupied: set[tuple[int, int]], rng
) -> None:
    _height, width = len(grid), len(grid[0])
    cells = [(0, col) for col in range(width)]
    leg_col = rng.choice(tuple(range(2, width - 2)))
    leg_length = rng.choice((1, 2))
    cells.extend((row, leg_col) for row in range(1, leg_length + 1))
    _paint(grid, occupied, cells)


def _construct_synthetic(profile: str, rng) -> list[list[int]]:
    for _ in range(200):
        size = rng.choice((8, 9))
        grid = _empty_grid(size, size)
        occupied: set[tuple[int, int]] = set()

        if profile == "opposite_span":
            _put_opposite_span(grid, occupied, rng)
            corner_choices = list(_CORNER_SIDE_SETS)
        elif profile == "three_side":
            _put_three_side(grid, occupied, rng)
            # The top border is already occupied by the three-side near miss.
            corner_choices = [("bottom", "left"), ("bottom", "right")]
        else:
            raise ValueError(f"not a synthetic profile: {profile!r}")

        corner = rng.choice(corner_choices)
        if _place_component(
            grid,
            occupied,
            rng,
            exact_sides=corner,
            min_size=2,
            max_size=4,
        ) is None:
            continue
        if _place_component(
            grid,
            occupied,
            rng,
            touch_count=1,
            min_size=2,
            max_size=4,
        ) is None:
            continue
        if _place_component(
            grid,
            occupied,
            rng,
            touch_count=0,
            min_size=1,
            max_size=4,
        ) is None:
            continue

        # Add one optional retained object for geometric diversity, but never
        # at the cost of the required task witnesses.
        if rng.randrange(2):
            _place_component(
                grid,
                occupied,
                rng,
                touch_count=rng.choice((0, 1)),
                min_size=1,
                max_size=3,
            )

        canonical = _canonical_orientation(grid)
        if len({_grid_key(candidate) for candidate in _d4(canonical)}) != 8:
            continue
        if not _analyze(canonical)["reasons"]:
            return canonical
    raise RuntimeError(f"unable to construct strict {profile!r} scene")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Five consecutive pairs contain two of each decisive counterexample."""
    del seed, difficulty
    return _SCHEDULE_SEQUENCE[int(sample_index) % len(_SCHEDULE_SEQUENCE)]


def _validate_call(difficulty, overrides: dict[str, object]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    if "scene_profile" in overrides and overrides["scene_profile"] is not None:
        profile = overrides["scene_profile"]
        if not isinstance(profile, str) or profile not in SCENE_PROFILES:
            raise ValueError(f"scene_profile must be one of {SCENE_PROFILES}, found {profile!r}")
    if "transform" in overrides and overrides["transform"] is not None:
        transform = overrides["transform"]
        if isinstance(transform, bool) or not isinstance(transform, int) or not 0 <= transform <= 7:
            raise ValueError("transform must be an integer in 0..7")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    scheduled = schedule_profile(seed, sample_index, difficulty)
    profile = ctx.draw_choice(
        "scene_profile",
        SCENE_PROFILES if overrides.get("scene_profile") is not None else (scheduled,),
    )
    scene_rng = ctx.draw_rng(f"scene:{difficulty or 'unbanded'}")
    if profile == "canonical_anchor":
        grid = [row[:] for row in scene_rng.choice(_PUBLIC_GRIDS)]
        grid = _canonical_orientation(grid)
    else:
        grid = _construct_synthetic(profile, scene_rng)

    transform = ctx.draw_choice("transform", tuple(range(8)))
    result = _d4(_canonical_orientation(grid))[transform]
    errors = self_check(result, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructed invalid {profile!r} scene: {errors}")
    observed = observe_overrides(result)
    if observed != {"scene_profile": profile, "transform": transform}:
        raise RuntimeError(
            f"override observability failure: requested {(profile, transform)!r}, observed {observed!r}"
        )
    return [row[:] for row in result]


def _analyze(grid) -> dict[str, object]:
    if not isinstance(grid, list) or not grid:
        return {"strict": False, "reasons": ["grid_must_be_nonempty_list"]}
    if not all(isinstance(row, list) for row in grid):
        return {"strict": False, "reasons": ["rows_must_be_lists"]}
    width = len(grid[0]) if grid else 0
    if width == 0 or any(len(row) != width for row in grid):
        return {"strict": False, "reasons": ["grid_must_be_rectangular_and_nonempty"]}
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {"strict": False, "reasons": ["cells_must_be_integer_colors_0_to_9"]}

    height = len(grid)
    flat = [value for row in grid for value in row]
    palette = tuple(sorted(set(flat)))
    reasons = []
    if not (8 <= height <= 9 and 8 <= width <= 9):
        reasons.append("dimension_range")
    if palette != (0, 4):
        reasons.append("input_palette_must_be_exactly_0_and_4")
    if 8 in palette:
        reasons.append("cyan_answer_leakage")

    yellow = [obj for obj in _components(grid) if obj["color"] == 4]
    touch_sets = [frozenset(obj["sides"]) for obj in yellow]
    touch_counts = [len(sides) for sides in touch_sets]
    foreground = flat.count(4)
    if not 3 <= len(yellow) <= 8:
        reasons.append("yellow_component_count")
    if yellow and any(not 1 <= len(obj["cells"]) <= 18 for obj in yellow):
        reasons.append("yellow_component_size")
    if not 4 <= foreground <= int(height * width * 0.45):
        reasons.append("foreground_density")
    if not any(count == 2 for count in touch_counts):
        reasons.append("missing_exactly_two_border_target")
    if not any(count != 2 for count in touch_counts):
        reasons.append("missing_retained_contrast")
    if not any(
        len(sides) == 2 and sides not in _OPPOSITE_SIDE_SETS for sides in touch_sets
    ):
        reasons.append("missing_adjacent_two_border_target")
    d4_unique = len({_grid_key(candidate) for candidate in _d4(grid)})
    if d4_unique != 8:
        reasons.append("dihedral_symmetry_hides_transform")

    canonical_anchor = _grid_key(grid) in _PUBLIC_KEYS
    has_opposite = any(sides in _OPPOSITE_SIDE_SETS for sides in touch_sets)
    has_three = any(len(sides) == 3 for sides in touch_sets)
    if canonical_anchor:
        scene_profile = "canonical_anchor"
    elif has_opposite:
        scene_profile = "opposite_span"
    elif has_three:
        scene_profile = "three_side"
    else:
        scene_profile = "unrecognized"
        reasons.append("unrecognized_scene_profile")

    return {
        "strict": not reasons,
        "reasons": reasons,
        "height": height,
        "width": width,
        "palette": palette,
        "foreground": foreground,
        "yellow_component_count": len(yellow),
        "touch_sets": tuple(touch_sets),
        "touch_counts": tuple(touch_counts),
        "target_count": sum(count == 2 for count in touch_counts),
        "retained_count": sum(count != 2 for count in touch_counts),
        "has_opposite_two": has_opposite,
        "has_adjacent_two": any(
            len(sides) == 2 and sides not in _OPPOSITE_SIDE_SETS for sides in touch_sets
        ),
        "has_three": has_three,
        "has_one": any(count == 1 for count in touch_counts),
        "has_zero": any(count == 0 for count in touch_counts),
        "scene_profile": scene_profile,
        "d4_unique": d4_unique,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task-specific teaching manifold from returned pixels only."""
    del difficulty, meta
    return list(_analyze(grid)["reasons"])


def strict_canonical_like(grid) -> list[str]:
    """Strict task-domain predicate used by the semantic and profile gates."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, object]:
    """Recover both exact controls from pixels rather than RNG bookkeeping."""
    analysis = _analyze(grid)
    if analysis["reasons"]:
        raise ValueError(f"cannot observe overrides on invalid grid: {analysis['reasons']}")
    canonical = _canonical_orientation(grid)
    transform = next(
        index for index, candidate in enumerate(_d4(canonical)) if candidate == grid
    )
    return {"scene_profile": analysis["scene_profile"], "transform": transform}


def solve_python(grid):
    """Input-pure test mirror; the selected Racket program remains authority."""
    output = [row[:] for row in grid]
    if not grid:
        return output
    for obj in _components(grid):
        if obj["color"] == 4 and len(obj["sides"]) == 2:
            for row, col in obj["cells"]:
                output[row][col] = 8
    return output


def _candidate_output(grid, mode: str):
    output = [row[:] for row in grid]
    yellow = [obj for obj in _components(grid) if obj["color"] == 4]
    sizes = [len(obj["cells"]) for obj in yellow]
    for obj in yellow:
        sides = frozenset(obj["sides"])
        touches = len(sides)
        size = len(obj["cells"])
        should_paint = False
        if mode == "intended":
            should_paint = touches == 2
        elif mode == "identity":
            should_paint = False
        elif mode == "all_yellow":
            should_paint = True
        elif mode == "any_border":
            should_paint = touches >= 1
        elif mode == "one_border_only":
            should_paint = touches == 1
        elif mode == "adjacent_two_only":
            should_paint = touches == 2 and sides not in _OPPOSITE_SIDE_SETS
        elif mode == "opposite_two_only":
            should_paint = sides in _OPPOSITE_SIDE_SETS
        elif mode == "at_least_two":
            should_paint = touches >= 2
        elif mode == "largest_yellow":
            should_paint = bool(sizes) and size == max(sizes)
        elif mode == "smallest_yellow":
            should_paint = bool(sizes) and size == min(sizes)
        else:
            raise ValueError(f"unknown rival mode: {mode}")
        if should_paint:
            for row, col in obj["cells"]:
                output[row][col] = 8
    return output


def _rival(mode: str) -> Callable[[list[list[int]]], list[list[int]]]:
    return lambda grid: _candidate_output(grid, mode)


SEMANTIC_RIVALS = {
    name: _rival(name)
    for name in (
        "identity",
        "all_yellow",
        "any_border",
        "one_border_only",
        "adjacent_two_only",
        "opposite_two_only",
        "at_least_two",
        "largest_yellow",
        "smallest_yellow",
    )
}
CANONICAL_SHORTCUTS = {
    "adjacent_two_only": SEMANTIC_RIVALS["adjacent_two_only"],
    "at_least_two": SEMANTIC_RIVALS["at_least_two"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _facts(grid) -> dict[str, object]:
    return _analyze(grid)


SEMANTIC_WITNESSES = {
    "opposite_two_border": lambda grid: bool(_facts(grid)["has_opposite_two"]),
    "three_border_retained": lambda grid: bool(_facts(grid)["has_three"]),
    "one_border_retained": lambda grid: bool(_facts(grid)["has_one"]),
    "interior_retained": lambda grid: bool(_facts(grid)["has_zero"]),
    "adjacent_two_border": lambda grid: bool(_facts(grid)["has_adjacent_two"]),
}
WITNESS_RIVALS = {
    "opposite_two_border": ["adjacent_two_only"],
    "three_border_retained": ["at_least_two", "any_border"],
    "one_border_retained": ["any_border", "all_yellow", "one_border_only"],
    "interior_retained": ["all_yellow"],
    "adjacent_two_border": ["opposite_two_only", "one_border_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Name every declared rival that fits demos but changes the query label."""
    reasons = []
    for name, rival in sorted(LESSON_COMPETITORS.items()):
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(
                    f"rival {name} fits all demonstrations but changes the query answer"
                )
    return reasons
