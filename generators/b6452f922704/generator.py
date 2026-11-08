"""Input sampler for the local bounding-box overlap gallery task.

Each of three maroon frames contains one blue shape, one red shape, and one
key-color cell directly above it.  The selected Racket authority emits a solid
key-colored rectangle whose size is the intersection of the two shape bounding
boxes, then packs the three rectangles left-to-right with one-column gaps and
vertical centering.

This sampler does not produce labels.  It deliberately includes a shorter part
beside a part at least two rows taller, so every generated instance distinguishes
vertical centering from the strongest canonical-fitting shortcut (top alignment).
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b6452f922704"
TASK_ID = GENERATOR_ID
RULE_HASH = "abfc4a89f098"
VERSION = "2.0.0"
SUMMARY = (
    "Three equal maroon frames contain red/blue shapes with overlapping bounding "
    "boxes and local key colors; repeated keys are lawful, and every draw teaches "
    "vertical centering in the output gallery."
)

INVARIANTS = [
    "background is 0 and all nonzero cells belong to a frame, its key, or its interior shapes",
    "exactly three equal 6..8 by 6..8 hollow color-9 frames appear left-to-right",
    "each frame has exactly one key cell of color 3..8 directly above it",
    "each frame interior contains nonempty color-1 and color-2 shapes whose bounding boxes overlap",
    "key colors may repeat; key_variety records exactly how many distinct key colors occur",
    "generated overlap heights include a height-1 part and a height-3-or-more part",
]

AXES = {
    "frame_h": {
        "type": "int",
        "default": "weighted 6..8; favors canonical height 7",
        "valid": "6..8",
    },
    "frame_w": {
        "type": "int",
        "default": "weighted 6..8; favors canonical width 7",
        "valid": "6..8",
    },
    "key_variety": {
        "type": "int",
        "default": "weighted 1..3; favors repeated canonical key colors",
        "valid": "1..3",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

_FRAME_HEIGHT_CHOICES = {
    None: (6, 7, 7, 7, 7, 7, 8),
    "easy": (6, 7, 7, 7, 7, 7, 8),
    "medium": (6, 7, 7, 7, 7, 7, 8),
    "hard": (6, 7, 7, 7, 7, 7, 8, 8),
}
_FRAME_WIDTH_CHOICES = _FRAME_HEIGHT_CHOICES
_KEY_VARIETY_CHOICES = {
    None: (1, 1, 1, 2, 2, 2, 3),
    "easy": (1, 1, 1, 2, 2, 2, 3),
    "medium": (1, 1, 1, 2, 2, 2, 3),
    "hard": (1, 1, 2, 2, 2, 2, 3, 3),
}
_KEY_COLORS = (3, 4, 5, 6, 7, 8)


def _difficulty_key(difficulty: Any) -> str | None:
    if difficulty is None:
        return None
    if difficulty in ("easy", "medium", "hard"):
        return difficulty
    if isinstance(difficulty, (int, float)) and not isinstance(difficulty, bool):
        value = float(difficulty)
        if not 0.0 <= value <= 1.0:
            raise ValueError("numeric difficulty must be in [0, 1]")
        if value < 1 / 3:
            return "easy"
        if value < 2 / 3:
            return "medium"
        return "hard"
    raise ValueError(f"unknown difficulty {difficulty!r}")


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    bounds = {"frame_h": (6, 8), "frame_w": (6, 8), "key_variety": (1, 3)}
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _key_sequence(rng: Any, variety: int) -> list[int]:
    colors = rng.sample(list(_KEY_COLORS), variety)
    if variety == 1:
        result = [colors[0], colors[0], colors[0]]
    elif variety == 2:
        result = [colors[0], colors[0], colors[1]]
        rng.shuffle(result)
    else:
        result = list(colors)
        rng.shuffle(result)
    return result


def _opposed_l_shapes(
    height: int,
    width: int,
    overlap_h: int,
    overlap_w: int,
    *,
    flip_vertical: bool,
    flip_horizontal: bool,
    swap_colors: bool,
) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    """Construct disjoint connected shapes with an exact bbox intersection.

    Shape A is an L on the top/left of a (height-1)x(width-1) box.  Shape B is
    the opposite L on the bottom/right of an (overlap_h+1)x(overlap_w+1) box.
    Their cells cannot collide, while their bounding boxes overlap by exactly
    ``overlap_h`` rows and ``overlap_w`` columns.  Whole-interior flips provide
    four orientations without changing that geometry.
    """
    if not (1 <= overlap_h <= height - 1 and 1 <= overlap_w <= width - 1):
        raise ValueError("requested overlap does not fit the frame interior")

    a_height, a_width = height - 1, width - 1
    a = {(0, col) for col in range(a_width)} | {
        (row, 0) for row in range(a_height)
    }

    b_height, b_width = overlap_h + 1, overlap_w + 1
    b_row0, b_col0 = height - b_height, width - b_width
    b = {(height - 1, col) for col in range(b_col0, width)} | {
        (row, width - 1) for row in range(b_row0, height)
    }

    def transform(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
        result = set()
        for row, col in cells:
            if flip_vertical:
                row = height - 1 - row
            if flip_horizontal:
                col = width - 1 - col
            result.add((row, col))
        return result

    blue, red = transform(a), transform(b)
    if blue & red:
        raise RuntimeError("constructive shapes collided")
    if swap_colors:
        blue, red = red, blue
    return blue, red


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic lawful input grid; labels remain Racket-owned."""
    _validate_overrides(overrides)
    band = _difficulty_key(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    frame_h = ctx.draw_choice("frame_h", _FRAME_HEIGHT_CHOICES[band])
    frame_w = ctx.draw_choice("frame_w", _FRAME_WIDTH_CHOICES[band])
    key_variety = ctx.draw_choice("key_variety", _KEY_VARIETY_CHOICES[band])

    interior_h, interior_w = frame_h - 2, frame_w - 2
    height = frame_h + 4
    width = 3 * frame_w + 4
    grid = full_grid(height, width, 0)
    rng = ctx.draw_rng("layout")

    keys = _key_sequence(rng, key_variety)
    overlap_heights = [1, 3, rng.randint(1, interior_h - 1)]
    overlap_widths = [rng.randint(1, interior_w - 1) for _ in range(3)]
    rng.shuffle(overlap_heights)

    frame_row = 2
    for index, frame_col in enumerate(1 + i * (frame_w + 1) for i in range(3)):
        bottom = frame_row + frame_h - 1
        right = frame_col + frame_w - 1
        for col in range(frame_col, right + 1):
            grid[frame_row][col] = 9
            grid[bottom][col] = 9
        for row in range(frame_row, bottom + 1):
            grid[row][frame_col] = 9
            grid[row][right] = 9

        key_col = rng.randint(frame_col, right)
        grid[frame_row - 1][key_col] = keys[index]

        blue, red = _opposed_l_shapes(
            interior_h,
            interior_w,
            overlap_heights[index],
            overlap_widths[index],
            flip_vertical=bool(rng.randrange(2)),
            flip_horizontal=bool(rng.randrange(2)),
            swap_colors=bool(rng.randrange(2)),
        )
        for row, col in blue:
            grid[frame_row + 1 + row][frame_col + 1 + col] = 1
        for row, col in red:
            grid[frame_row + 1 + row][frame_col + 1 + col] = 2

    return grid


def _valid_rectangular_grid(grid: Any) -> str | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return "expected a nonempty rectangular grid"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "expected nonempty rows"
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return "ragged grid"
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return "cells must be integer ARC colors 0..9"
    return None


def _components_of_color(
    grid: list[list[int]] | tuple[tuple[int, ...], ...], color: int
) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    components: list[list[tuple[int, int]]] = []
    while unseen:
        start = unseen.pop()
        cells = [start]
        stack = [start]
        while stack:
            row, col = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                point = (row + dr, col + dc)
                if point in unseen:
                    unseen.remove(point)
                    stack.append(point)
                    cells.append(point)
        components.append(cells)
    return components


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), max(rows), min(cols), max(cols)


def _frame_records(grid: Any) -> list[dict[str, Any]]:
    malformed = _valid_rectangular_grid(grid)
    if malformed:
        raise ValueError(malformed)

    components = _components_of_color(grid, 9)
    if len(components) != 3:
        raise ValueError(f"expected exactly three color-9 frames, found {len(components)}")

    records: list[dict[str, Any]] = []
    all_interior: set[tuple[int, int]] = set()
    all_key_positions: set[tuple[int, int]] = set()
    frame_sizes: set[tuple[int, int]] = set()
    for cells in components:
        r0, r1, c0, c1 = _bbox(cells)
        frame_h, frame_w = r1 - r0 + 1, c1 - c0 + 1
        frame_sizes.add((frame_h, frame_w))
        if not (6 <= frame_h <= 8 and 6 <= frame_w <= 8):
            raise ValueError(
                f"frame at {(r0, c0)} has size {frame_h}x{frame_w}, expected 6..8 by 6..8"
            )
        perimeter = {
            (row, col)
            for row in range(r0, r1 + 1)
            for col in range(c0, c1 + 1)
            if row in (r0, r1) or col in (c0, c1)
        }
        if set(cells) != perimeter:
            raise ValueError(f"frame at {(r0, c0)} is not a complete hollow rectangle")
        if r0 == 0:
            raise ValueError(f"frame at {(r0, c0)} has no row for a key")

        key_positions = [
            (r0 - 1, col)
            for col in range(c0, c1 + 1)
            if grid[r0 - 1][col] not in (0, 9)
        ]
        if len(key_positions) != 1:
            raise ValueError(
                f"frame at {(r0, c0)} expected exactly one key above, found {len(key_positions)}"
            )
        key_position = key_positions[0]
        key = grid[key_position[0]][key_position[1]]
        if key not in _KEY_COLORS:
            raise ValueError(f"frame at {(r0, c0)} key color {key} is not in 3..8")
        all_key_positions.add(key_position)

        interior = {
            (row, col)
            for row in range(r0 + 1, r1)
            for col in range(c0 + 1, c1)
        }
        all_interior.update(interior)
        if any(grid[row][col] not in (0, 1, 2) for row, col in interior):
            raise ValueError(f"frame at {(r0, c0)} interior contains a non 0/1/2 color")
        blue = [(row, col) for row, col in interior if grid[row][col] == 1]
        red = [(row, col) for row, col in interior if grid[row][col] == 2]
        if not blue or not red:
            raise ValueError(f"frame at {(r0, c0)} needs both blue and red shapes")
        br0, br1, bc0, bc1 = _bbox(blue)
        rr0, rr1, rc0, rc1 = _bbox(red)
        overlap_h = min(br1, rr1) - max(br0, rr0) + 1
        overlap_w = min(bc1, rc1) - max(bc0, rc0) + 1
        if overlap_h <= 0 or overlap_w <= 0:
            raise ValueError(f"frame at {(r0, c0)} has non-overlapping shape bboxes")

        records.append(
            {
                "origin": (r0, c0),
                "frame_h": frame_h,
                "frame_w": frame_w,
                "key": key,
                "overlap_h": overlap_h,
                "overlap_w": overlap_w,
            }
        )

    if len(frame_sizes) != 1:
        raise ValueError(f"frames must have one common size, found {sorted(frame_sizes)}")

    permitted_nonzero = all_interior | all_key_positions | {
        point for cells in components for point in cells
    }
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0 and (row, col) not in permitted_nonzero:
                raise ValueError(f"stray color {value} outside frames at {(row, col)}")

    return sorted(records, key=lambda record: record["origin"])


def observe_overrides(grid):
    """Recover every advertised exact axis from returned pixels."""
    records = _frame_records(grid)
    return {
        "frame_h": records[0]["frame_h"],
        "frame_w": records[0]["frame_w"],
        "key_variety": len({record["key"] for record in records}),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task signal and return diagnostics rather than raising."""
    try:
        records = _frame_records(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    if len(records) != 3:  # defensive; _frame_records already enforces this
        return [f"expected exactly three frames, found {len(records)}"]
    return []


def strict_canonical_like(grid):
    """Lawful task instances, including canonical examples with repeated keys."""
    return self_check(grid)


def _top_align(grid):
    """Plausible wrong rule: pack the correct rectangles against the top row."""
    records = _frame_records(grid)
    height = max(record["overlap_h"] for record in records)
    width = sum(record["overlap_w"] for record in records) + len(records) - 1
    output = full_grid(height, width, 0)
    left = 0
    for record in records:
        for row in range(record["overlap_h"]):
            for col in range(left, left + record["overlap_w"]):
                output[row][col] = record["key"]
        left += record["overlap_w"] + 1
    return output


def _vertical_centering_witness(grid) -> bool:
    records = _frame_records(grid)
    tallest = max(record["overlap_h"] for record in records)
    return any((tallest - record["overlap_h"]) // 2 > 0 for record in records)


def lesson_identifiable(demos, query) -> list[str]:
    """Finite contract: demonstrations must refute the named top-align rival."""
    if not isinstance(demos, list) or not demos:
        return ["no labeled demonstrations"]
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return [f"demonstration {index} is not a labeled pair"]
        try:
            rival = _top_align(pair["input"])
        except (TypeError, ValueError) as exc:
            return [f"demonstration {index} is invalid: {exc}"]
        if rival != pair["output"]:
            return []
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query is not a labeled pair"]
    try:
        changes_query = _top_align(query["input"]) != query["output"]
    except (TypeError, ValueError) as exc:
        return [f"query is invalid: {exc}"]
    if changes_query:
        return ["top-align rival fits every demonstration but changes the query"]
    return []


SEMANTIC_WITNESSES = {"vertical_centering": _vertical_centering_witness}
SEMANTIC_RIVALS = {"top_align": _top_align}
WITNESS_RIVALS = {"vertical_centering": ["top_align"]}
CANONICAL_SHORTCUTS = {"top_align": _top_align}
LESSON_COMPETITORS = {"top_align": _top_align}
