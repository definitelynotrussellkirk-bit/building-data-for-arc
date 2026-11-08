"""Generator for ARC task 4fd85612056f: crop the tallest component.

The canonical rule treats every nonzero 4-connected region as one component,
regardless of color.  It orders components by bounding-box height, then cell
count, then leftmost column, and returns a tight crop of the winner while
preserving every original color.

The old generator accidentally taught "take the only irregular object": its
winner was always irregular and every distractor was rectangular.  This repair
uses a compact ten-slot curriculum.  Every ordinary grid has canonical-scale
component heights 3/2/1 and exactly three nonzero colors, but also contains a
shorter irregular component that is wider, larger, earlier, and left of the
winner.  Alternating winner palettes retain exact canonical monochrome structure while
a mixed-color branch specifically refutes the strongest shortcut left by the
canonical examples: segmenting objects by color instead of by nonzero
connectivity.  Rectangle, elbow, tee, and cross winners all occur, and a second
layout prevents a fixed rightmost rule.

All public axes are exact, returned-grid observable, and available in every
band.  Outputs remain owned by the unchanged canonical Racket authority.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4fd85612056f"
TASK_ID = GENERATOR_ID
RULE_HASH = "2ea4086e36a6"
VERSION = "2.0.0"

SUMMARY = (
    "Find nonzero 4-connected components without splitting on color; select "
    "the greatest bounding-box height (cell count, then leftmost column break "
    "ties), and return its tight color-preserving crop."
)

EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 10
SCHEDULE_PROFILES = tuple(f"slot_{index}" for index in range(LESSON_SCHEDULE_PERIOD))
MIN_STRICT_FRAC = 1.0
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

INVARIANTS = [
    "the input is an 8..11 by 10..13 integer grid with background 0",
    "there are exactly three nonzero 4-connected components",
    "their bounding-box heights are exactly 3, 2, and 1",
    "the height-3 component is therefore the unique tallest component",
    "the output is that component's tight crop with all source colors preserved",
]

TARGET_SHAPES = ("rectangle", "elbow", "tee", "cross")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "five canonical height profiles repeated over a ten-slot lesson schedule",
        "valid": "8..11",
        "doc": "Returned input-grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "five canonical width profiles repeated over a ten-slot lesson schedule",
        "valid": "10..13",
        "doc": "Returned input-grid width.",
    },
    "target_shape": {
        "type": "enum",
        "default": "canonical rectangle/elbow/tee/cross schedule",
        "valid": "rectangle|elbow|tee|cross",
        "doc": "Free binary shape of the unique height-3 winner.",
    },
}

# Compatibility metadata: malformed instances are test fixtures, never public
# texture modes or silent aliases.
PALETTE_KINDS: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_CARD4 = ((-1, 0), (0, -1), (0, 1), (1, 0))

# These five rows exactly cover the canonical (height, width, palette-size)
# profiles.  The associated output shape also mirrors the corresponding public
# pair, while colors and placements continue to vary by keyed seed.
_CANONICAL_PROFILE_ROWS = (
    (8, 13, "elbow"),
    (11, 11, "rectangle"),
    (10, 12, "tee"),
    (9, 10, "elbow"),
    (8, 10, "cross"),
)

_TARGET_CELLS: dict[str, tuple[tuple[int, int], ...]] = {
    "rectangle": (
        (0, 0), (0, 1),
        (1, 0), (1, 1),
        (2, 0), (2, 1),
    ),
    "elbow": ((0, 1), (1, 1), (2, 0), (2, 1)),
    "tee": ((0, 0), (1, 0), (1, 1), (1, 2), (2, 0)),
    "cross": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
}

# A 2x4 connected irregular component with seven cells.  It is shorter than
# every target but larger and wider than all target shapes.
_HEAVY_DECOY = (
    (0, 0), (0, 1), (0, 2),
    (1, 0), (1, 1), (1, 2), (1, 3),
)
_SMALL_DECOY = ((0, 0), (0, 1), (0, 2))


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    if not points:
        return ()
    min_row = min(row for row, _ in points)
    min_col = min(col for _, col in points)
    return tuple(sorted((row - min_row, col - min_col) for row, col in points))


def _shape_signature(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    """Translation/rotation/reflection invariant signature for a binary shape."""
    base = tuple(cells)
    variants: list[tuple[tuple[int, int], ...]] = []
    for reflected in (False, True):
        current = tuple((row, -col if reflected else col) for row, col in base)
        for _ in range(4):
            variants.append(_normalize(current))
            current = tuple((col, -row) for row, col in current)
    return min(variants) if variants else ()


_SHAPE_BY_SIGNATURE = {
    _shape_signature(cells): name for name, cells in _TARGET_CELLS.items()
}
if len(_SHAPE_BY_SIGNATURE) != len(_TARGET_CELLS):
    raise AssertionError("target shape bank contains duplicate free shapes")


def _bbox(cells: Sequence[tuple[int, int]]) -> tuple[int, int, int, int, int, int]:
    """Return (height, width, top, left, bottom, right)."""
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    top, bottom = min(rows), max(rows)
    left, right = min(cols), max(cols)
    return bottom - top + 1, right - left + 1, top, left, bottom, right


def _components(grid: list[list[int]], *, same_color: bool = False) -> list[tuple[tuple[int, int], ...]]:
    """Row-major 4-connected components of nonzero cells.

    ``same_color=False`` is the canonical object model: adjacent nonzero cells
    stay connected even when their colors differ.  ``same_color=True`` is kept
    only to implement the canonical-fitting rival rule.
    """
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[tuple[tuple[int, int], ...]] = []
    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] == 0 or (start_row, start_col) in seen:
                continue
            color = grid[start_row][start_col]
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells: list[tuple[int, int]] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for delta_row, delta_col in _CARD4:
                    neighbor = (row + delta_row, col + delta_col)
                    nr, nc = neighbor
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if neighbor in seen or grid[nr][nc] == 0:
                        continue
                    if same_color and grid[nr][nc] != color:
                        continue
                    seen.add(neighbor)
                    stack.append(neighbor)
            found.append(tuple(sorted(cells)))
    return found


def _selection_key(component: Sequence[tuple[int, int]]) -> tuple[int, int, int]:
    height, _, _, left, _, _ = _bbox(component)
    return height, len(component), -left


def _winner(grid: list[list[int]], *, same_color: bool = False):
    components = _components(grid, same_color=same_color)
    return max(components, key=_selection_key) if components else None


def _crop_component(grid: list[list[int]], component) -> list[list[int]]:
    if not component:
        return [[0]]
    height, width, top, left, _, _ = _bbox(component)
    occupied = set(component)
    return [
        [grid[top + row][left + col] if (top + row, left + col) in occupied else 0
         for col in range(width)]
        for row in range(height)
    ]


def _intended_output(grid: list[list[int]]) -> list[list[int]]:
    return _crop_component(grid, _winner(grid))


def _rival_same_color_components(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: split adjacent cells whenever their colors differ."""
    return _crop_component(grid, _winner(grid, same_color=True))


def _rival_largest_cell_count(grid: list[list[int]]) -> list[list[int]]:
    components = _components(grid)
    winner = max(
        components,
        key=lambda component: (
            len(component),
            _bbox(component)[0],
            -_bbox(component)[3],
        ),
        default=None,
    )
    return _crop_component(grid, winner)


def _rival_widest_component(grid: list[list[int]]) -> list[list[int]]:
    components = _components(grid)
    winner = max(
        components,
        key=lambda component: (
            _bbox(component)[1],
            len(component),
            -_bbox(component)[3],
        ),
        default=None,
    )
    return _crop_component(grid, winner)


def _rival_leftmost_component(grid: list[list[int]]) -> list[list[int]]:
    components = _components(grid)
    winner = min(
        components,
        key=lambda component: (
            _bbox(component)[3],
            _bbox(component)[2],
            -len(component),
        ),
        default=None,
    )
    return _crop_component(grid, winner)


def _rival_rightmost_component(grid: list[list[int]]) -> list[list[int]]:
    components = _components(grid)
    winner = max(
        components,
        key=lambda component: (
            _bbox(component)[3],
            _bbox(component)[2],
            len(component),
        ),
        default=None,
    )
    return _crop_component(grid, winner)


def _rival_first_nonrectangular(grid: list[list[int]]) -> list[list[int]]:
    components = _components(grid)
    winner = next(
        (
            component
            for component in components
            if len(component) != _bbox(component)[0] * _bbox(component)[1]
        ),
        components[0] if components else None,
    )
    return _crop_component(grid, winner)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "same_color_components": _rival_same_color_components,
    "largest_cell_count": _rival_largest_cell_count,
    "widest_component": _rival_widest_component,
    "leftmost_component": _rival_leftmost_component,
    "rightmost_component": _rival_rightmost_component,
    "first_nonrectangular": _rival_first_nonrectangular,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # Every canonical component is monochrome, so canonical labels cannot
    # distinguish this rival from the intended color-agnostic connectivity.
    "same_color_components": _rival_same_color_components,
}


def _grid_error(grid: Any) -> str | None:
    if not isinstance(grid, list) or not grid:
        return "grid must be a nonempty list"
    if not all(isinstance(row, list) and row for row in grid):
        return "grid rows must be nonempty lists"
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return "grid must be rectangular"
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return "grid cells must be integer ARC colors 0..9"
    return None


def _shape_name(component: Sequence[tuple[int, int]]) -> str | None:
    return _SHAPE_BY_SIGNATURE.get(_shape_signature(component))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the exact canonical-scale public manifold.

    Rectangular winners are deliberately lawful: one canonical demonstration
    has a solid 3x2 winner, and banning it was the previous profile-floor bug.
    """
    del difficulty, meta
    malformed = _grid_error(grid)
    if malformed:
        return [malformed]
    height, width = len(grid), len(grid[0])
    errors: list[str] = []
    if not 8 <= height <= 11:
        errors.append(f"grid height {height} outside 8..11")
    if not 10 <= width <= 13:
        errors.append(f"grid width {width} outside 10..13")
    palette = {value for row in grid for value in row}
    if 0 not in palette:
        errors.append("background color 0 is missing")
    if len(palette) != 4:
        errors.append(f"expected background plus three nonzero colors, found {sorted(palette)}")

    components = _components(grid)
    if len(components) != 3:
        errors.append(f"expected exactly three nonzero components, found {len(components)}")
        return errors
    heights = sorted((_bbox(component)[0] for component in components), reverse=True)
    if heights != [3, 2, 1]:
        errors.append(f"expected component bbox heights [3, 2, 1], found {heights}")
    target = max(components, key=_selection_key)
    shape = _shape_name(target)
    if shape not in TARGET_SHAPES:
        errors.append(f"height winner has unsupported binary shape signature {shape!r}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def _mixed_color_winner(grid) -> bool:
    target = _winner(grid)
    return bool(target) and len({grid[row][col] for row, col in target}) >= 2


def _dominant_short_decoy(grid) -> bool:
    target = _winner(grid)
    if not target:
        return False
    target_height, target_width, _, target_left, _, _ = _bbox(target)
    for component in _components(grid):
        if component == target:
            continue
        height, width, _, left, _, _ = _bbox(component)
        if (
            height < target_height
            and width > target_width
            and len(component) > len(target)
            and left < target_left
            and len(component) != height * width
        ):
            return True
    return False


def _rectangular_winner(grid) -> bool:
    target = _winner(grid)
    return bool(target) and len(target) == _bbox(target)[0] * _bbox(target)[1]


def _irregular_winner(grid) -> bool:
    target = _winner(grid)
    return bool(target) and len(target) != _bbox(target)[0] * _bbox(target)[1]


def _nonrightmost_winner(grid) -> bool:
    return _rival_rightmost_component(grid) != _intended_output(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "mixed_color_winner": _mixed_color_winner,
    "dominant_short_decoy": _dominant_short_decoy,
    "rectangular_winner": _rectangular_winner,
    "irregular_winner": _irregular_winner,
    "nonrightmost_winner": _nonrightmost_winner,
}
WITNESS_RIVALS = {
    "mixed_color_winner": ["same_color_components"],
    "dominant_short_decoy": [
        "largest_cell_count",
        "widest_component",
        "leftmost_component",
        "first_nonrectangular",
    ],
    "rectangular_winner": ["first_nonrectangular"],
    "irregular_winner": ["first_nonrectangular"],
    "nonrightmost_winner": ["rightmost_component"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Return named competitors that survive every labeled demonstration."""
    del query
    errors: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            errors.append(f"competitor {name!r} fits every demonstration")
    return errors


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _validate_request(seed, sample_index, difficulty, overrides) -> None:
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, not {type(seed).__name__}")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    if type(sample_index) is not int:
        raise TypeError(
            f"sample_index must be an integer, not {type(sample_index).__name__}"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")

    bounds = {"grid_h": (8, 11), "grid_w": (10, 13)}
    for name, value in overrides.items():
        if value is None:
            continue
        if name in bounds:
            if type(value) is not int:
                raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
            low, high = bounds[name]
            if not low <= value <= high:
                raise ValueError(f"{name} must be in {low}..{high}, got {value}")
        elif name == "target_shape":
            if type(value) is not str:
                raise TypeError(
                    f"target_shape must be a string, not {type(value).__name__}"
                )
            if value not in TARGET_SHAPES:
                raise ValueError(
                    f"target_shape must be one of {TARGET_SHAPES}, got {value!r}"
                )


def _axis_int(ctx, name: str, low: int, high: int, default: int) -> int:
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, low, high)
    return ctx.draw_choice(name, (default,))


def _axis_choice(ctx, name: str, legal: Sequence[str], default: str) -> str:
    if ctx.overrides.get(name) is not None:
        return ctx.draw_choice(name, tuple(legal))
    return ctx.draw_choice(name, (default,))


def _paint_solid(
    grid: list[list[int]],
    origin: tuple[int, int],
    cells: Sequence[tuple[int, int]],
    color: int,
) -> None:
    top, left = origin
    for row, col in cells:
        rr, cc = top + row, left + col
        if grid[rr][cc] != 0:
            raise AssertionError("internal component overlap")
        grid[rr][cc] = color


def _paint_checkerboard(
    grid: list[list[int]],
    origin: tuple[int, int],
    cells: Sequence[tuple[int, int]],
    colors: tuple[int, int],
) -> None:
    top, left = origin
    for row, col in cells:
        rr, cc = top + row, left + col
        if grid[rr][cc] != 0:
            raise AssertionError("internal component overlap")
        grid[rr][cc] = colors[(row + col) % 2]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    profile_height, profile_width, profile_shape = _CANONICAL_PROFILE_ROWS[
        sample_index % len(_CANONICAL_PROFILE_ROWS)
    ]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _axis_int(ctx, "grid_h", 8, 11, profile_height)
    width = _axis_int(ctx, "grid_w", 10, 13, profile_width)
    target_shape = _axis_choice(
        ctx, "target_shape", TARGET_SHAPES, profile_shape
    )

    grid = full_grid(height, width, 0)
    band_label = difficulty or "medium"
    target_color_a, target_color_b, decoy_color = ctx.draw_rng(
        f"colors:{band_label}"
    ).sample(tuple(range(1, 10)), 3)

    # The earlier irregular decoy is simultaneously shorter, larger, wider,
    # and left of the winner.  It is the first irregular component in row-major
    # order, preserving the exact audit counterexample mechanism.
    _paint_solid(grid, (1, 0), _HEAVY_DECOY, decoy_color)

    target_cells = _TARGET_CELLS[target_shape]
    target_width = max(col for _, col in target_cells) + 1
    layout = sample_index % 2
    if layout == 0:
        # Winner is neither leftmost nor rightmost and reaches the bottom edge.
        target_origin = (height - 3, max(4, (width - target_width) // 2))
        small_origin = (1, width - 3)
    else:
        # Winner is rightmost but not bottommost.  Together the two layouts
        # refute fixed-right and fixed-bottom selectors in every five-example
        # lesson window.
        target_origin = (height - 4, width - target_width)
        small_origin = (height - 1, 0)

    mixed_palette = sample_index % 2 == 0
    if mixed_palette:
        _paint_checkerboard(
            grid,
            target_origin,
            target_cells,
            (target_color_a, target_color_b),
        )
        small_color = target_color_a
    else:
        _paint_solid(grid, target_origin, target_cells, target_color_a)
        # Keep exactly three nonzero palette roles on canonical-structure rows.
        small_color = target_color_b
    _paint_solid(grid, small_origin, _SMALL_DECOY, small_color)

    errors = self_check(grid)
    if errors:
        raise AssertionError(f"internal generator invariant failed: {errors}")
    return grid


def observe_overrides(grid) -> dict[str, object]:
    errors = self_check(grid)
    if errors:
        raise ValueError(f"grid is outside the public generator manifold: {errors}")
    target = _winner(grid)
    shape = _shape_name(target)
    if shape is None:
        raise ValueError("cannot recover target_shape")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "target_shape": shape,
    }


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Small invalid scenes for validator regression probes."""
    tied = full_grid(8, 10, 0)
    for row in range(3):
        tied[row][0] = 1
        tied[row][9] = 2
    missing_component = full_grid(8, 10, 0)
    for row in range(3):
        missing_component[row][0] = 1
    return [
        ("tied_tallest", tied),
        ("single_component", missing_component),
    ]
