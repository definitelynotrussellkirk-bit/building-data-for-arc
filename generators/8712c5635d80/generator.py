"""Input generator for M84: transplant a shape into a colored frame.

A full color-9 column separates two equal square panels.  The left panel
contains one connected monochrome shape.  The right panel contains a complete
monochrome perimeter frame.  The unchanged Racket authority preserves the
frame and paints the left shape's coordinate mask into the right panel with the
frame color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "8712c5635d80"
TASK_ID = GENERATOR_ID
RULE_HASH = "2c2e07bc5619"
VERSION = "3.0.0"

SUMMARY = (
    "A color-9 column separates equal square panels. The left panel contains "
    "one connected monochrome shape strictly inside its border. The right "
    "panel contains a complete differently colored perimeter frame. Preserve "
    "the frame and stamp the left shape at the same coordinates in the frame "
    "color."
)

INVARIANTS = [
    "one full color-9 separator column divides two equal square panels",
    "the left panel contains one 4-connected 3..9-cell monochrome interior shape",
    "the right panel contains a complete monochrome perimeter frame and an empty interior",
    "source and frame colors are distinct nonzero non-9 ARC colors",
]

AXES = {
    "panel_size": {
        "type": "int",
        "default": "weighted 5..14 with canonical 5/6 anchors in every band",
        "valid": "5..14",
    },
    "shape_size": {
        "type": "int",
        "default": "difficulty-weighted 3..9",
        "valid": "3..9",
    },
    "palette_id": {
        "type": "int",
        "default": "uniform ordered pair of distinct colors 1..8",
        "valid": "0..55",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 2

_PALETTES = tuple(
    (source, frame)
    for source in range(1, 9)
    for frame in range(1, 9)
    if frame != source
)
_PALETTE_TO_ID = {palette: index for index, palette in enumerate(_PALETTES)}
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_call(difficulty, overrides) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _panel_options(difficulty) -> tuple[int, ...]:
    """Keep exact canonical profiles present in every curriculum band."""
    broad = tuple(range(5, 15))
    if difficulty == "easy":
        weighted = (5,) * 20 + (6,) * 16 + (7,) * 8
    elif difficulty == "hard":
        weighted = (5,) * 8 + (6,) * 8 + (10, 11, 12, 13, 14) * 4
    else:
        weighted = (5,) * 12 + (6,) * 12 + (7, 8, 9, 10) * 3
    return broad + weighted


def _shape_options(difficulty) -> tuple[int, ...]:
    broad = tuple(range(3, 10))
    if difficulty == "easy":
        return broad + (3,) * 8 + (4,) * 8 + (5,) * 4
    if difficulty == "hard":
        return broad + (6,) * 4 + (7,) * 6 + (8,) * 8 + (9,) * 8
    return broad + (4,) * 4 + (5,) * 6 + (6,) * 6 + (7,) * 4


def _connected_shape(rng, size: int, height: int, width: int) -> list[tuple[int, int]]:
    """Construct exactly ``size`` connected cells in a bounded rectangle."""
    if not (1 <= size <= height * width):
        raise ValueError(f"shape size {size} does not fit {height}x{width}")
    start = (rng.randrange(height), rng.randrange(width))
    cells = {start}
    frontier: set[tuple[int, int]] = set()

    def add_frontier(row: int, col: int) -> None:
        for dr, dc in _NEIGHBORS:
            point = (row + dr, col + dc)
            if (
                0 <= point[0] < height
                and 0 <= point[1] < width
                and point not in cells
            ):
                frontier.add(point)

    add_frontier(*start)
    while len(cells) < size:
        point = rng.choice(sorted(frontier))
        frontier.remove(point)
        cells.add(point)
        add_frontier(*point)
    return sorted(cells)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic canonical-shaped input; Racket owns labels."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    panel_size = ctx.draw_choice("panel_size", _panel_options(difficulty))
    shape_size = ctx.draw_choice("shape_size", _shape_options(difficulty))
    palette_id = ctx.draw_int_strict("palette_id", 0, len(_PALETTES) - 1)
    source_color, frame_color = _PALETTES[palette_id]

    grid = full_grid(panel_size, 2 * panel_size + 1, 0)
    separator = panel_size
    for row in range(panel_size):
        grid[row][separator] = 9

    shape = _connected_shape(
        ctx.draw_rng("shape_geometry"),
        shape_size,
        panel_size - 2,
        panel_size - 2,
    )
    for row, col in shape:
        grid[row + 1][col + 1] = source_color

    right0 = separator + 1
    right1 = len(grid[0]) - 1
    for col in range(right0, right1 + 1):
        grid[0][col] = frame_color
        grid[panel_size - 1][col] = frame_color
    for row in range(panel_size):
        grid[row][right0] = frame_color
        grid[row][right1] = frame_color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructed invalid generator instance: {errors}")
    return grid


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid rows have inconsistent widths"]
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return ["cells must be literal integer ARC colors 0..9"]
    return []


def _separator(grid) -> int | None:
    columns = [
        col
        for col in range(len(grid[0]))
        if all(grid[row][col] == 9 for row in range(len(grid)))
    ]
    return columns[0] if len(columns) == 1 else None


def _left_cells(grid, separator):
    return [
        (row, col, grid[row][col])
        for row in range(len(grid))
        for col in range(separator)
        if grid[row][col] != 0
    ]


def _is_connected(points: set[tuple[int, int]]) -> bool:
    if not points:
        return False
    seen = {next(iter(points))}
    agenda = list(seen)
    while agenda:
        row, col = agenda.pop()
        for dr, dc in _NEIGHBORS:
            point = (row + dr, col + dc)
            if point in points and point not in seen:
                seen.add(point)
                agenda.append(point)
    return seen == points


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical two-panel frame grammar."""
    errors = _grid_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    separator = _separator(grid)
    if separator is None:
        return ["expected exactly one full color-9 separator column"]
    if any(
        grid[row][col] == 9
        for row in range(height)
        for col in range(width)
        if col != separator
    ):
        errors.append("color 9 may occur only in the separator column")
    if not (height == separator == width - separator - 1):
        errors.append(
            f"expected equal square panels, got height={height}, separator={separator}, width={width}"
        )
    if not 5 <= height <= 14:
        errors.append(f"panel size {height} outside supported range 5..14")
    if errors:
        return errors

    left = _left_cells(grid, separator)
    if not 3 <= len(left) <= 9:
        errors.append(f"left shape must contain 3..9 cells, found {len(left)}")
    left_colors = {value for _, _, value in left}
    if len(left_colors) != 1 or not left_colors <= set(range(1, 9)):
        errors.append(f"left shape must use one color 1..8, found {sorted(left_colors)}")
    if any(
        row in (0, height - 1) or col in (0, separator - 1)
        for row, col, _ in left
    ):
        errors.append("left shape must stay strictly inside the panel border")
    if left and not _is_connected({(row, col) for row, col, _ in left}):
        errors.append("left shape must be 4-connected")

    right0 = separator + 1
    right1 = width - 1
    perimeter = {
        (row, col)
        for row in range(height)
        for col in range(right0, width)
        if row in (0, height - 1) or col in (right0, right1)
    }
    frame_colors = {grid[row][col] for row, col in perimeter}
    if len(frame_colors) != 1 or not frame_colors <= set(range(1, 9)):
        errors.append(
            f"right perimeter must be one nonzero non-9 color, found {sorted(frame_colors)}"
        )
    interior_nonzero = [
        (row, col, grid[row][col])
        for row in range(1, height - 1)
        for col in range(right0 + 1, right1)
        if grid[row][col] != 0
    ]
    if interior_nonzero:
        errors.append(f"right frame interior must be empty, found {interior_nonzero[:8]}")
    if len(left_colors) == 1 and len(frame_colors) == 1 and left_colors == frame_colors:
        errors.append("source and frame colors must differ")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Every accepted grid is on the declared canonical frame manifold."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    errors = self_check(grid)
    if errors:
        raise ValueError(f"cannot observe invalid grid: {errors}")
    separator = _separator(grid)
    assert separator is not None
    left = _left_cells(grid, separator)
    source_color = left[0][2]
    frame_color = grid[0][separator + 1]
    return {
        "panel_size": separator,
        "shape_size": len(left),
        "palette_id": _PALETTE_TO_ID[(source_color, frame_color)],
    }


def _reference_output(grid):
    """Independent Python geometry oracle matching the selected Racket rule."""
    separator = _separator(grid)
    if separator is None:
        raise ValueError("missing unique separator")
    marker = next(
        (
            grid[row][col]
            for row in range(len(grid))
            for col in range(separator + 1, len(grid[0]))
            if grid[row][col] != 0
        ),
        None,
    )
    if marker is None:
        raise ValueError("missing right-panel color")
    output = [list(row) for row in grid]
    for row in range(len(grid)):
        for col in range(separator):
            if grid[row][col] != 0:
                output[row][separator + 1 + col] = marker
    return output


def _single_marker_only(grid):
    """Rival learned from the old shortcut distribution.

    It keeps only the first right-panel marker, clears the rest of the frame,
    then stamps the left mask.  It matches the former one-marker lessons but
    fails on a real frame.
    """
    separator = _separator(grid)
    if separator is None:
        return [list(row) for row in grid]
    marker = next(
        (
            (row, col, grid[row][col])
            for row in range(len(grid))
            for col in range(separator + 1, len(grid[0]))
            if grid[row][col] != 0
        ),
        None,
    )
    if marker is None:
        return [list(row) for row in grid]
    output = [list(row) for row in grid]
    for row in range(len(grid)):
        for col in range(separator + 1, len(grid[0])):
            output[row][col] = 0
    output[marker[0]][marker[1]] = marker[2]
    for row in range(len(grid)):
        for col in range(separator):
            if grid[row][col] != 0:
                output[row][separator + 1 + col] = marker[2]
    return output


def _has_full_frame_context(grid) -> bool:
    return self_check(grid) == []


SEMANTIC_WITNESSES = {"full_frame_context": _has_full_frame_context}
SEMANTIC_RIVALS = {"single_marker_only": _single_marker_only}
WITNESS_RIVALS = {"full_frame_context": ["single_marker_only"]}
CANONICAL_SHORTCUTS = {"single_marker_only": _single_marker_only}
LESSON_COMPETITORS = {"single_marker_only": _single_marker_only}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to expose frame preservation, not marker-only data."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    reasons: list[str] = []
    witnessed_frame = False
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        findings = self_check(demo["input"])
        if findings:
            reasons.append(f"demo {index} input is outside the frame grammar: {findings[0]}")
            continue
        expected = _reference_output(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output does not match frame-preserving stamping")
            continue
        if _single_marker_only(demo["input"]) != demo["output"]:
            witnessed_frame = True
    if not witnessed_frame:
        reasons.append("demonstrations do not refute the single-marker-only shortcut")
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    else:
        findings = self_check(query["input"])
        if findings:
            reasons.append(f"query input is outside the frame grammar: {findings[0]}")
    return reasons
