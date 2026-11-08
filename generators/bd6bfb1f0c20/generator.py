"""Constructive curriculum generator for ARC task ``bd6bfb1f0c20``.

The canonical transformation finds every non-zero four-connected object,
computes its four-neighbour perimeter, sorts objects by decreasing perimeter
(with color as the deterministic tie-break), and emits the ordered colors as
one row.

Every generated instance deliberately distinguishes that rule from the two
shortcuts that survived the previous sampler:

* an L tetromino and a square have equal area but perimeters 10 and 8, and the
  square receives the smaller color, so area-descending/color-ascending order
  reverses the first two answers;
* the three roles are never placed in canonical perimeter order, so row-major
  position order is also wrong.

The construction therefore makes each individual example a witness, while the
four-profile schedule retains both exact canonical input profiles in every
ordinary eight-example window.
"""
from __future__ import annotations

from itertools import permutations
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bd6bfb1f0c20"
TASK_ID = GENERATOR_ID
RULE_HASH = "4f629ec7a9de"
VERSION = "2.0.0"

SUMMARY = (
    "Sort the three distinct-color connected objects by four-neighbour "
    "perimeter descending (color ascending on ties), then output their colors "
    "as one row. Every draw refutes area order and row-major position order."
)

INVARIANTS = [
    "background is color 0",
    "there are exactly three separated four-connected objects in distinct colors",
    "object perimeters are distinct",
    "every generated draw contains areas 4, 4, 1 and perimeters 10, 8, 4",
    "every generated draw refutes area-descending and position-order shortcuts",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical anchors plus banded broad shapes",
        "valid": "8..16",
        "doc": "Exact input height; the domain contains every canonical height.",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical anchors plus banded broad shapes",
        "valid": "11..18",
        "doc": "Exact input width; the domain contains every canonical width.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = (
    "canonical_8x12",
    "canonical_9x13",
    "broad_compact",
    "broad_large",
)
MIN_STRICT_FRAC = 1.0

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_AXIS_LIMITS = {
    "grid_h": (8, 16),
    "grid_w": (11, 18),
}
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Canonical role order is exactly this tuple: perimeter 10, then 8, then 4.
_ROLE_L = 0
_ROLE_SQUARE = 1
_ROLE_SINGLETON = 2
_CANONICAL_ROLE_ORDER = (_ROLE_L, _ROLE_SQUARE, _ROLE_SINGLETON)

_L_BASE = ((0, 0), (1, 0), (2, 0), (2, 1))
_SQUARE = ((0, 0), (0, 1), (1, 0), (1, 1))
_SINGLETON = ((0, 0),)


def _normalise(cells: Any) -> tuple[tuple[int, int], ...]:
    points = tuple((int(row), int(col)) for row, col in cells)
    row0 = min(row for row, _ in points)
    col0 = min(col for _, col in points)
    return tuple(sorted((row - row0, col - col0) for row, col in points))


def _symmetries(cells: Any) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Return all unique rotations/reflections, normalised deterministically."""
    result: set[tuple[tuple[int, int], ...]] = set()
    points = tuple(cells)
    for reflected in (False, True):
        transformed = tuple((row, -col if reflected else col) for row, col in points)
        for turns in range(4):
            rotated = transformed
            for _ in range(turns):
                rotated = tuple((col, -row) for row, col in rotated)
            result.add(_normalise(rotated))
    return tuple(sorted(result))


_L_SHAPES = _symmetries(_L_BASE)
_ROLE_SHAPES = {
    _ROLE_L: _L_SHAPES,
    _ROLE_SQUARE: (_SQUARE,),
    _ROLE_SINGLETON: (_SINGLETON,),
}


def _validate_call(
    seed: Any,
    sample_index: Any,
    difficulty: Any,
    overrides: dict[str, Any],
) -> None:
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int:
        raise TypeError(
            f"sample_index must be an integer, not {type(sample_index).__name__}"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = _AXIS_LIMITS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    _validate_call(seed, sample_index, difficulty, {})
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _broad_shape(ctx, profile: str, difficulty: Any) -> tuple[int, int]:
    if profile == "broad_compact":
        ranges = {
            None: (range(8, 14), range(11, 16)),
            "easy": (range(8, 11), range(11, 14)),
            "medium": (range(9, 13), range(12, 16)),
            "hard": (range(11, 14), range(14, 17)),
        }
    else:
        ranges = {
            None: (range(11, 17), range(14, 19)),
            "easy": (range(10, 14), range(13, 16)),
            "medium": (range(12, 16), range(14, 18)),
            "hard": (range(14, 17), range(16, 19)),
        }
    heights, widths = ranges[difficulty]
    rng = ctx.draw_rng(f"{profile}_shape")
    return rng.choice(tuple(heights)), rng.choice(tuple(widths))


def _default_shape(ctx, profile: str, difficulty: Any) -> tuple[int, int]:
    if profile == "canonical_8x12":
        return 8, 12
    if profile == "canonical_9x13":
        return 9, 13
    return _broad_shape(ctx, profile, difficulty)


def _draw_exact_or_default(
    ctx,
    overrides: dict[str, Any],
    name: str,
    default: int,
) -> int:
    lo, hi = _AXIS_LIMITS[name]
    if overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    # A singleton keyed choice records exact default provenance while preserving
    # strict full-domain handling whenever an override is supplied.
    return ctx.draw_choice(name, (default,))


def _slot_origins(height: int, width: int) -> tuple[tuple[int, int], ...]:
    """Six separated 3x3 slots available on every declared canvas."""
    row_starts = (0, height - 3)
    col_starts = (0, (width - 3) // 2, width - 3)
    return tuple((row, col) for row in row_starts for col in col_starts)


def _role_colors(rng) -> dict[int, int]:
    # Area order ties the L and square at four cells, then sorts by color.
    # Giving the square the smaller color guarantees that rival reverses them.
    square_color, l_color = rng.choice(
        tuple((low, high) for low in range(1, 10) for high in range(low + 1, 10))
    )
    singleton_color = rng.choice(
        tuple(color for color in range(1, 10) if color not in {square_color, l_color})
    )
    return {
        _ROLE_L: l_color,
        _ROLE_SQUARE: square_color,
        _ROLE_SINGLETON: singleton_color,
    }


def _paint_role(
    grid: list[list[int]],
    *,
    role: int,
    color: int,
    slot: tuple[int, int],
    rng,
) -> None:
    shape = rng.choice(_ROLE_SHAPES[role])
    shape_h = max(row for row, _ in shape) + 1
    shape_w = max(col for _, col in shape) + 1
    # Keep every object top-aligned inside its slot.  Row-major ordering must
    # equal the selected slot ordering; a random vertical offset can otherwise
    # let a later column sort first because row precedes column lexicographically.
    offset_row = 0
    offset_col = rng.randint(0, 3 - shape_w)
    slot_row, slot_col = slot
    for row, col in shape:
        grid[slot_row + offset_row + row][slot_col + offset_col + col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    default_h, default_w = _default_shape(ctx, profile, difficulty)
    height = _draw_exact_or_default(ctx, overrides, "grid_h", default_h)
    width = _draw_exact_or_default(ctx, overrides, "grid_w", default_w)

    layout_rng = ctx.draw_rng("layout")
    slots = sorted(layout_rng.sample(_slot_origins(height, width), 3))
    role_orders = tuple(
        order
        for order in permutations(_CANONICAL_ROLE_ORDER)
        if order != _CANONICAL_ROLE_ORDER
    )
    position_order = layout_rng.choice(role_orders)
    colors = _role_colors(layout_rng)

    grid = full_grid(height, width, 0)
    for slot, role in zip(slots, position_order):
        _paint_role(
            grid,
            role=role,
            color=colors[role],
            slot=slot,
            rng=layout_rng,
        )
    return grid


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"]
    width = len(grid[0])
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, list):
            errors.append(f"row {row_index} is not a list")
            continue
        if len(row) != width:
            errors.append(f"row {row_index} has width {len(row)}, expected {width}")
            continue
        for col_index, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(
                    f"cell ({row_index},{col_index}) must be an integer color 0..9"
                )
                return errors
    return errors


def _color_components(grid: list[list[int]]) -> list[tuple[int, list[tuple[int, int]]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, list[tuple[int, int]]]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _DIR4:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, cells))
    return result


def _nonzero_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _DIR4:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] != 0
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(cells)
    return result


def _perimeter(cells: Any) -> int:
    occupied = set(cells)
    return sum(
        (row + dr, col + dc) not in occupied
        for row, col in occupied
        for dr, dc in _DIR4
    )


def self_check(grid, *, difficulty=None, meta=None):
    del meta
    errors = _grid_errors(grid)
    if errors:
        return errors
    if difficulty not in _VALID_DIFFICULTIES:
        return ["difficulty must be None, 'easy', 'medium', or 'hard'"]

    height, width = len(grid), len(grid[0])
    if not _AXIS_LIMITS["grid_h"][0] <= height <= _AXIS_LIMITS["grid_h"][1]:
        errors.append(f"grid height {height} outside declared range 8..16")
    if not _AXIS_LIMITS["grid_w"][0] <= width <= _AXIS_LIMITS["grid_w"][1]:
        errors.append(f"grid width {width} outside declared range 11..18")

    components = _color_components(grid)
    if len(components) != 3:
        errors.append(f"expected exactly 3 colored objects, found {len(components)}")
        return errors

    colors = [color for color, _ in components]
    if len(set(colors)) != 3:
        errors.append("the three objects must use distinct colors")
    if len(_nonzero_components(grid)) != 3:
        errors.append("colored objects touch when color is ignored")

    perimeters = [_perimeter(cells) for _, cells in components]
    if len(set(perimeters)) != 3:
        errors.append(f"object perimeters must be distinct, found {sorted(perimeters)}")
    return errors


# Canonical examples vary in component area, so the strict domain is the broad
# authority domain above rather than only this generator's 4/4/1 teaching form.
strict_canonical_like = self_check


def observe_overrides(grid) -> dict[str, int]:
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def _solve_perimeter(grid):
    ranked = sorted(
        _color_components(grid),
        key=lambda item: (-_perimeter(item[1]), item[0]),
    )
    return [[color for color, _ in ranked]]


def _solve_area(grid):
    ranked = sorted(
        _color_components(grid),
        key=lambda item: (-len(item[1]), item[0]),
    )
    return [[color for color, _ in ranked]]


def _solve_position(grid):
    ranked = sorted(_color_components(grid), key=lambda item: min(item[1]))
    return [[color for color, _ in ranked]]


def _area_differs_from_perimeter(grid) -> bool:
    return _solve_area(grid) != _solve_perimeter(grid)


def _position_differs_from_perimeter(grid) -> bool:
    return _solve_position(grid) != _solve_perimeter(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "area_differs_from_perimeter": _area_differs_from_perimeter,
    "position_differs_from_perimeter": _position_differs_from_perimeter,
}
SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "area_order": _solve_area,
    "position_order": _solve_position,
}
WITNESS_RIVALS = {
    "area_differs_from_perimeter": ["area_order"],
    "position_differs_from_perimeter": ["position_order"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    reasons: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                competitor(pair["input"]) == pair["output"] for pair in demos
            )
            changes_query = competitor(query["input"]) != query["output"]
        except Exception as exc:
            reasons.append(f"{name} competitor failed to score: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
