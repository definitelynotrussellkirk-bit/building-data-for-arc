"""Generator for ARC task ``c84e2a641055`` — drop one whole object.

Every nonzero cell belongs to one 4-connected object.  Translate that object
straight down by one shared offset until its lowest cell reaches the last row.
The shape and all cell colors are preserved.  A four-profile teaching schedule
includes uneven bottoms, multicolor objects, and objects larger than every
canonical example so lessons refute plausible column-, color-, and size-based
shortcuts.
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c84e2a641055"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "b08466eb063e"

SUMMARY = (
    "Move one connected nonzero object straight down by a single shared offset "
    "until its lowest cell touches the bottom row; preserve shape and colors."
)

INVARIANTS = [
    "the grid is 7..11 by 7..11 with integer ARC colors and background 0",
    "there is exactly one 4-connected nonzero object of 4..8 cells",
    "the object spans at least two rows and columns and is not a solid rectangle",
    "the object begins 1..4 rows above the floor",
    "the output is one rigid downward translation preserving every cell color",
]

_BOTTOM_PROFILES = ("flat", "uneven")
_TEACHING_PROFILES = (
    "mono_flat",
    "mono_uneven",
    "multi_flat_large",
    "multi_uneven_large",
)
SCHEDULE_PROFILES = _TEACHING_PROFILES
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.45

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled 7|8|9|10..11",
        "valid": "7..11",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled 7|8|9|10..11",
        "valid": "7..11",
    },
    "n_cells": {
        "type": "int",
        "default": "scheduled 4..8",
        "valid": "4..8",
    },
    "n_colors": {
        "type": "int",
        "default": "scheduled 1|2",
        "valid": "1..2",
    },
    "drop_distance": {
        "type": "int",
        "default": "scheduled 1..4",
        "valid": "1..4",
    },
    "bottom_profile": {
        "type": "str",
        "default": "scheduled flat|uneven",
        "valid": "flat|uneven",
    },
}

# Every Cartesian product of the public axis domains is constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Any four consecutive indexes contain all four teaching profiles."""
    del seed, difficulty
    return _TEACHING_PROFILES[int(sample_index) % len(_TEACHING_PROFILES)]


def _profile_defaults(sample_index: int, difficulty: Any) -> dict[str, Any]:
    profile = schedule_profile(0, sample_index, difficulty)
    if profile == "mono_flat":
        return dict(
            grid_h=9,
            grid_w=8,
            n_cells=4,
            n_colors=1,
            drop_distance=3,
            bottom_profile="flat",
        )
    if profile == "mono_uneven":
        return dict(
            grid_h=8,
            grid_w=9,
            n_cells=5,
            n_colors=1,
            drop_distance=2,
            bottom_profile="uneven",
        )
    if profile == "multi_flat_large":
        return dict(
            grid_h=7,
            grid_w=7,
            n_cells=6,
            n_colors=2,
            drop_distance=4,
            bottom_profile="flat",
        )

    block = int(sample_index) // len(_TEACHING_PROFILES)
    return dict(
        grid_h=10 + (block % 2),
        grid_w=10 + ((block // 2) % 2),
        n_cells=7 + (block % 2),
        n_colors=2,
        drop_distance=1,
        bottom_profile="uneven",
    )


def _scheduled_int(
    ctx,
    overrides: dict[str, Any],
    label: str,
    default: int,
    lo: int,
    hi: int,
) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_int_strict(label, default, default)


def _scheduled_choice(
    ctx,
    overrides: dict[str, Any],
    label: str,
    default: str,
    choices: tuple[str, ...],
) -> str:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, choices)
    return ctx.draw_choice(label, (default,))


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    min_row = min(row for row, _ in cells)
    min_col = min(column for _, column in cells)
    return tuple(sorted((row - min_row, column - min_col) for row, column in cells))


@lru_cache(maxsize=None)
def _polyominoes(n_cells: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Enumerate fixed 4-connected polyominoes, normalized by translation."""
    if n_cells == 1:
        return (((0, 0),),)
    grown: set[tuple[tuple[int, int], ...]] = set()
    for shape in _polyominoes(n_cells - 1):
        occupied = set(shape)
        for row, column in shape:
            for neighbor in (
                (row - 1, column),
                (row + 1, column),
                (row, column - 1),
                (row, column + 1),
            ):
                if neighbor not in occupied:
                    grown.add(_normalize((*occupied, neighbor)))
    return tuple(sorted(grown))


def _shape_size(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return (
        max(row for row, _ in shape) + 1,
        max(column for _, column in shape) + 1,
    )


def _shape_bottom_profile(shape: tuple[tuple[int, int], ...]) -> str:
    columns = {column for _, column in shape}
    bottoms = {
        max(row for row, candidate in shape if candidate == column)
        for column in columns
    }
    return "flat" if len(bottoms) == 1 else "uneven"


@lru_cache(maxsize=None)
def _candidate_shapes(
    n_cells: int,
    max_height: int,
    max_width: int,
    bottom_profile: str,
) -> tuple[tuple[tuple[int, int], ...], ...]:
    candidates = []
    for shape in _polyominoes(n_cells):
        height, width = _shape_size(shape)
        if height < 2 or width < 2:
            continue
        if height > max_height or width > max_width:
            continue
        if len(shape) == height * width:
            continue
        if _shape_bottom_profile(shape) != bottom_profile:
            continue
        candidates.append(shape)
    return tuple(candidates)


def _validate_grid(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    for row_index, row in enumerate(grid):
        for column_index, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return len(grid), width, [
                    f"cell ({row_index},{column_index}) is not an ARC color 0..9: {value!r}"
                ]
    return len(grid), width, []


def _object_cells(grid) -> list[tuple[int, int]]:
    return [
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value != 0
    ]


def _components(cells: Iterable[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            row, column = queue.popleft()
            for neighbor in (
                (row - 1, column),
                (row + 1, column),
                (row, column - 1),
                (row, column + 1),
            ):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def _grid_bottom_profile(grid) -> str:
    cells = _object_cells(grid)
    columns = {column for _, column in cells}
    bottoms = {
        max(row for row, candidate in cells if candidate == column)
        for column in columns
    }
    return "flat" if len(bottoms) == 1 else "uneven"


def observe_overrides(grid) -> dict[str, int | str]:
    cells = _object_cells(grid)
    max_row = max(row for row, _ in cells)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_cells": len(cells),
        "n_colors": len({grid[row][column] for row, column in cells}),
        "drop_distance": len(grid) - 1 - max_row,
        "bottom_profile": _grid_bottom_profile(grid),
    }


def rule_mirror(grid):
    """Python mirror of the selected Racket authority; never mutates input."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    cells = _object_cells(grid)
    if not cells:
        return [list(row) for row in grid]
    shift = height - 1 - max(row for row, _ in cells)
    out = full_grid(height, width, 0)
    for row, column in cells:
        out[row + shift][column] = grid[row][column]
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed inputs and weak impostors outside the supported domain."""
    del difficulty, meta
    height, width, errors = _validate_grid(grid)
    if errors:
        return errors
    if not 7 <= height <= 11:
        errors.append(f"height {height} outside 7..11")
    if not 7 <= width <= 11:
        errors.append(f"width {width} outside 7..11")

    cells = _object_cells(grid)
    if not 4 <= len(cells) <= 8:
        errors.append(f"expected 4..8 nonzero object cells, found {len(cells)}")
    components = _components(cells)
    if len(components) != 1:
        errors.append(f"expected exactly one 4-connected object, found {len(components)}")
        return errors

    rows = [row for row, _ in cells]
    columns = [column for _, column in cells]
    box_height = max(rows) - min(rows) + 1
    box_width = max(columns) - min(columns) + 1
    if box_height < 2 or box_width < 2:
        errors.append("object must span at least two rows and two columns")
    if len(cells) == box_height * box_width:
        errors.append("solid rectangular objects are excluded as weak impostors")

    colors = {grid[row][column] for row, column in cells}
    if not 1 <= len(colors) <= 2:
        errors.append(f"expected 1..2 nonzero colors, found {len(colors)}")

    drop_distance = height - 1 - max(rows)
    if not 1 <= drop_distance <= 4:
        errors.append(f"drop distance {drop_distance} outside 1..4")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Measured canonical manifold: public dimensions, size, and one color."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    observed = observe_overrides(grid)
    if (observed["grid_h"], observed["grid_w"]) not in {
        (9, 8),
        (8, 9),
        (9, 9),
        (7, 7),
    }:
        reasons.append(
            f"noncanonical dimensions {observed['grid_h']}x{observed['grid_w']}"
        )
    if observed["n_cells"] not in (4, 5):
        reasons.append(f"canonical objects have 4 or 5 cells, found {observed['n_cells']}")
    if observed["n_colors"] != 1:
        reasons.append(f"canonical objects are monochrome, found {observed['n_colors']} colors")
    if observed["drop_distance"] not in (2, 3, 4):
        reasons.append(
            f"canonical drop distance is 2, 3, or 4; found {observed['drop_distance']}"
        )
    return reasons


def _identity(grid):
    return [list(row) for row in grid]


def _column_gravity(grid):
    """Wrong rival: compress each occupied column independently."""
    height = len(grid)
    width = len(grid[0])
    out = full_grid(height, width, 0)
    for column in range(width):
        values = [grid[row][column] for row in range(height) if grid[row][column] != 0]
        for offset, value in enumerate(values):
            out[height - len(values) + offset][column] = value
    return out


def _per_color_gravity(grid):
    """Wrong canonical shortcut: treat each nonzero color as its own object."""
    height = len(grid)
    width = len(grid[0])
    out = full_grid(height, width, 0)
    colors = sorted({value for row in grid for value in row if value != 0})
    for color in colors:
        cells = [
            (row, column)
            for row, values in enumerate(grid)
            for column, value in enumerate(values)
            if value == color
        ]
        shift = height - 1 - max(row for row, _ in cells)
        for row, column in cells:
            out[row + shift][column] = color
    return out


def _cap_five_cells(grid):
    """Wrong canonical shortcut: only known 4/5-cell objects can fall."""
    if len(_object_cells(grid)) > 5:
        return _identity(grid)
    return rule_mirror(grid)


SEMANTIC_RIVALS: dict[str, Callable] = {
    "identity": _identity,
    "column_gravity": _column_gravity,
    "per_color_gravity": _per_color_gravity,
    "cap_five_cells": _cap_five_cells,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "per_color_gravity": _per_color_gravity,
    "cap_five_cells": _cap_five_cells,
}


def _valid_counterexample(grid, rival: Callable) -> bool:
    return not self_check(grid) and rival(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "moving_object": lambda grid: _valid_counterexample(grid, _identity),
    "uneven_bottom": lambda grid: _valid_counterexample(grid, _column_gravity),
    "multicolor_object": lambda grid: _valid_counterexample(grid, _per_color_gravity),
    "object_over_five_cells": lambda grid: _valid_counterexample(grid, _cap_five_cells),
}
WITNESS_RIVALS = {
    "moving_object": ["identity"],
    "uneven_bottom": ["column_gravity"],
    "multicolor_object": ["per_color_gravity"],
    "object_over_five_cells": ["cap_five_cells"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """A lesson is identifiable when exact demos refute every named rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")

    refuted = {name: False for name in LESSON_COMPETITORS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output is not the exact whole-object drop")
            continue
        for name, rival in LESSON_COMPETITORS.items():
            refuted[name] = refuted[name] or rival(demo["input"]) != expected

    for name, was_refuted in refuted.items():
        if not was_refuted:
            reasons.append(f"demonstrations do not refute rival {name!r}")
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")

    defaults = _profile_defaults(int(sample_index), difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _scheduled_int(ctx, overrides, "grid_h", defaults["grid_h"], 7, 11)
    width = _scheduled_int(ctx, overrides, "grid_w", defaults["grid_w"], 7, 11)
    n_cells = _scheduled_int(ctx, overrides, "n_cells", defaults["n_cells"], 4, 8)
    n_colors = _scheduled_int(ctx, overrides, "n_colors", defaults["n_colors"], 1, 2)
    drop_distance = _scheduled_int(
        ctx,
        overrides,
        "drop_distance",
        defaults["drop_distance"],
        1,
        4,
    )
    bottom_profile = _scheduled_choice(
        ctx,
        overrides,
        "bottom_profile",
        defaults["bottom_profile"],
        _BOTTOM_PROFILES,
    )

    shapes = _candidate_shapes(
        n_cells,
        height - drop_distance,
        width,
        bottom_profile,
    )
    if n_colors == 2:
        # Two non-bottom cells let both colors appear above the floor-facing
        # row.  This keeps one color absent from the bottom (so per-color
        # gravity is refutable) without encoding color as a pure vertical layer.
        shapes = tuple(
            shape
            for shape in shapes
            if sum(
                row < _shape_size(shape)[0] - 1
                for row, _column in shape
            ) >= 2
        )
    if not shapes:
        raise RuntimeError(
            "no constructible object for "
            f"n_cells={n_cells}, max_height={height - drop_distance}, "
            f"width={width}, bottom_profile={bottom_profile}"
        )
    # Keep the public axis schedule identical across bands while making the
    # difficulty argument observable through nuisance geometry.  Offsetting one
    # shared keyed draw guarantees three distinct shapes (every legal candidate
    # pool contains at least five) rather than relying on chance-separated salts.
    band_offset = {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    base_shape_index = ctx.draw_rng("shape").randrange(len(shapes))
    shape = shapes[(base_shape_index + band_offset) % len(shapes)]
    shape_height, shape_width = _shape_size(shape)
    top = height - drop_distance - shape_height
    left = ctx.draw_rng("position").randint(0, width - shape_width)
    palette = ctx.draw_distinct_colors("palette", n=n_colors, exclude={0})

    grid = full_grid(height, width, 0)
    bottom_row = shape_height - 1
    if n_colors == 1:
        assignments = {cell: palette[0] for cell in shape}
    else:
        non_bottom = [cell for cell in shape if cell[0] < bottom_row]
        ctx.draw_rng("color_assignment").shuffle(non_bottom)
        assignments = {
            cell: palette[0] if cell[0] == bottom_row else palette[1]
            for cell in shape
        }
        assignments[non_bottom[0]] = palette[0]
        assignments[non_bottom[1]] = palette[1]
        color_rng = ctx.draw_rng("color_tail")
        for cell in non_bottom[2:]:
            assignments[cell] = color_rng.choice(palette)
    for row, column in shape:
        grid[top + row][left + column] = assignments[(row, column)]

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"internal generator invariant failed: {errors}")
    requested = {
        "grid_h": height,
        "grid_w": width,
        "n_cells": n_cells,
        "n_colors": n_colors,
        "drop_distance": drop_distance,
        "bottom_profile": bottom_profile,
    }
    observed = observe_overrides(grid)
    if observed != requested:
        raise RuntimeError(f"internal override mismatch: requested={requested}, observed={observed}")
    return grid
