"""Native parametric episode generator for ARC task d9d4f0ebb48b.

The default ``fill_color_mode=local`` is the exact approved canonical rule:
every monochrome plus expands to its own 3x3 footprint.  The nearby
``selector_source`` setting adds a real two-step dependency.  A contiguous
unary marker on the top row selects one of the true pluses in reading order;
its center color is the intermediate value, and every true-plus footprint is
then painted with that selected color.

This module is intentionally deterministic and side-effect free.  The native
adapter next to it is the only promotion entry point.
"""
from __future__ import annotations

import copy
import random
from typing import Any, Iterable


TASK_ID = "d9d4f0ebb48b"
PARAMETER_NAME = "fill_color_mode"
MODES = ("local", "selector_source")
DEFAULT_SETTINGS = {PARAMETER_NAME: "local"}

# This literal is guarded by tests and must remain byte-for-byte identical to
# the approved canonical source for the default setting.
CANONICAL_PROGRAM = "(rule! (let ((dummy 0)) (for*/fold ((out g)) ((r (in-range 1 (- (rows g) 1))) (c (in-range 1 (- (cols g) 1)))) (let ((v (at g r c))) (if (and (not (= v 0)) (= (at g (- r 1) c) v) (= (at g (+ r 1) c) v) (= (at g r (- c 1)) v) (= (at g r (+ c 1)) v)) (paint-cells out (positions-in-rect (- r 1) (- c 1) (+ r 1) (+ c 1)) v) out)))))"

SELECTOR_SOURCE_PROGRAM = "(rule! (let* ((centers (for*/list ((r (in-range 1 (- (rows g) 1))) (c (in-range 1 (- (cols g) 1))) #:when (let ((v (at g r c))) (and (not (= v 0)) (= (at g (- r 1) c) v) (= (at g (+ r 1) c) v) (= (at g r (- c 1)) v) (= (at g r (+ c 1)) v)))) (list r c))) (selector-count (for/sum ((c (in-range (cols g)))) (if (not (= (at g 0 c) 0)) 1 0))) (selected (list-ref centers (- selector-count 1))) (fill-color (at g (first selected) (second selected)))) (for*/fold ((out g)) ((r (in-range 1 (- (rows g) 1))) (c (in-range 1 (- (cols g) 1)))) (let ((v (at g r c))) (if (and (not (= v 0)) (= (at g (- r 1) c) v) (= (at g (+ r 1) c) v) (= (at g r (- c 1)) v) (= (at g r (+ c 1)) v)) (paint-cells out (positions-in-rect (- r 1) (- c 1) (+ r 1) (+ c 1)) fill-color) out)))))"

# The first seven entries are deliberately fixed so every supported 3-demo +
# 4-query episode includes the minimum case and a lawful 30x30 stress case.
_SIZE_SCHEDULE = (
    (9, 9),
    (14, 16),
    (30, 30),
    (12, 20),
    (24, 24),
    (10, 18),
    (18, 11),
    (27, 30),
    (30, 21),
    (13, 13),
)
_PLUS_PALETTE = (1, 2, 3, 4, 5, 6, 7)
_MARKER_PALETTE = (8, 9)


def _validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER_NAME}:
        raise ValueError(f"settings must contain only {PARAMETER_NAME}")
    mode = settings[PARAMETER_NAME]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"{PARAMETER_NAME} must be one of {MODES}")
    return mode


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _validate_grid(grid: Any) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 3 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 3 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must have 3..30 rows and columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


def program(settings: Any) -> str:
    """Materialize the exact Racket rule for one declared setting."""
    mode = _validate_settings(settings)
    return CANONICAL_PROGRAM if mode == "local" else SELECTOR_SOURCE_PROGRAM


def find_plus_centers(grid: list[list[int]]) -> list[tuple[int, int]]:
    """Return true monochrome-plus centers in reading order."""
    _validate_grid(grid)
    centers: list[tuple[int, int]] = []
    for row in range(1, len(grid) - 1):
        for col in range(1, len(grid[0]) - 1):
            value = grid[row][col]
            if value != 0 and all(
                grid[row + drow][col + dcol] == value
                for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1))
            ):
                centers.append((row, col))
    return centers


def selector_intermediate(grid: list[list[int]]) -> dict[str, Any]:
    """Compute step A of selector_source without consulting any output."""
    _validate_grid(grid)
    centers = find_plus_centers(grid)
    selector_count = sum(cell != 0 for cell in grid[0])
    if not centers:
        raise ValueError("selector_source requires at least one true plus")
    if not 1 <= selector_count <= len(centers):
        raise ValueError("top-row selector length must index an existing true plus")
    row, col = centers[selector_count - 1]
    return {
        "selector_count": selector_count,
        "selected_index": selector_count - 1,
        "selected_center": [row, col],
        "selected_color": grid[row][col],
        "centers": [[r, c] for r, c in centers],
    }


def _paint_footprint(out: list[list[int]], center: tuple[int, int], color: int) -> None:
    row, col = center
    for rr in range(row - 1, row + 2):
        for cc in range(col - 1, col + 2):
            out[rr][cc] = color


def apply_mode(grid: list[list[int]], mode: str) -> list[list[int]]:
    """Independent Python oracle for the two declared settings."""
    _validate_grid(grid)
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    centers = find_plus_centers(grid)
    out = copy.deepcopy(grid)
    if mode == "local":
        for center in centers:
            row, col = center
            _paint_footprint(out, center, grid[row][col])
        return out

    intermediate = selector_intermediate(grid)
    color = intermediate["selected_color"]
    for center in centers:
        _paint_footprint(out, center, color)
    return out


def _plus_centers(height: int, width: int, count: int) -> list[tuple[int, int]]:
    # Corners make reading order unambiguous and leave a central distractor area.
    candidates = [
        (2, 2),
        (2, width - 3),
        (height - 3, 2),
        (height - 3, width - 3),
    ]
    unique: list[tuple[int, int]] = []
    for center in candidates:
        if center not in unique:
            unique.append(center)
    if len(unique) < count:
        raise ValueError("grid is too small for the requested separated pluses")
    return sorted(unique[:count])


def _place_plus(grid: list[list[int]], center: tuple[int, int], color: int) -> None:
    row, col = center
    for drow, dcol in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
        if grid[row + drow][col + dcol] != 0:
            raise RuntimeError("planned plus overlaps occupied input")
        grid[row + drow][col + dcol] = color


def _shape_variants() -> tuple[tuple[tuple[int, int], ...], ...]:
    # None is a monochrome plus.  Several are deliberately close distractors.
    return (
        ((0, 0), (0, 1), (1, 0), (1, 1)),                    # 2x2 block
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),            # five-cell L
        ((0, 0), (0, 1), (0, 2), (1, 2)),                    # bent bar
        ((0, 0), (1, 0), (2, 0)),                            # vertical bar
        ((0, 0), (0, 1), (0, 2)),                            # horizontal bar
    )


def _candidate_anchors(height: int, width: int, rng: random.Random) -> list[tuple[int, int]]:
    # Row zero is protocol, not canvas: only the contiguous selector may use it.
    anchors = [(row, col) for row in range(1, height) for col in range(width)]
    rng.shuffle(anchors)
    # Try visible edge/boundary placements first so stress episodes are not
    # dominated by a quiet padded border.
    preferred = [
        (height - 2, 0),
        (height - 2, width - 2),
        (1, 0),
        (1, width - 2),
        (height - 1, 0),
    ]
    result: list[tuple[int, int]] = []
    for anchor in [*preferred, *anchors]:
        if anchor not in result:
            result.append(anchor)
    return result


def _try_shape(
    grid: list[list[int]],
    cells: Iterable[tuple[int, int]],
    color: int,
    expected_centers: list[tuple[int, int]],
) -> bool:
    cells = tuple(cells)
    height, width = len(grid), len(grid[0])
    if any(not (0 <= row < height and 0 <= col < width) for row, col in cells):
        return False
    if any(grid[row][col] != 0 for row, col in cells):
        return False
    for row, col in cells:
        grid[row][col] = color
    if find_plus_centers(grid) != expected_centers:
        for row, col in cells:
            grid[row][col] = 0
        return False
    return True


def _add_distractors(
    grid: list[list[int]],
    expected_centers: list[tuple[int, int]],
    rng: random.Random,
    target_nonzero: int,
) -> None:
    variants = list(_shape_variants())
    anchors = _candidate_anchors(len(grid), len(grid[0]), rng)
    color_cycle = [1, 2, 3, 4, 5, 6, 7, 9]
    attempts = 0
    while sum(cell != 0 for row in grid for cell in row) < target_nonzero:
        placed = False
        for anchor_index, (base_row, base_col) in enumerate(anchors):
            for shape_index, shape in enumerate(variants):
                attempts += 1
                color = color_cycle[(anchor_index + shape_index + attempts) % len(color_cycle)]
                cells = tuple((base_row + dr, base_col + dc) for dr, dc in shape)
                if _try_shape(grid, cells, color, expected_centers):
                    anchors.pop(anchor_index)
                    placed = True
                    break
            if placed:
                break
        if not placed:
            raise RuntimeError("could not add requested distractor density without a false plus")


def _episode_grid(seed: int, pair_index: int, height: int, width: int) -> list[list[int]]:
    rng = random.Random((seed << 16) ^ (pair_index * 0x9E3779B1) ^ 0xD9D4F0EB)
    if (height, width) == (9, 9):
        plus_count = 2
    elif min(height, width) >= 20:
        plus_count = 4
    else:
        plus_count = 3

    grid = [[0 for _ in range(width)] for _ in range(height)]
    centers = _plus_centers(height, width, plus_count)
    palette_offset = (seed + pair_index) % len(_PLUS_PALETTE)
    colors = [
        _PLUS_PALETTE[(palette_offset + index) % len(_PLUS_PALETTE)]
        for index in range(plus_count)
    ]
    for center, color in zip(centers, colors):
        _place_plus(grid, center, color)

    selector_count = pair_index % plus_count + 1
    marker_color = _MARKER_PALETTE[(seed + pair_index) % len(_MARKER_PALETTE)]
    for col in range(selector_count):
        grid[0][col] = marker_color

    if (height, width) == (30, 30):
        target = 74
    elif height * width >= 400:
        target = 42
    elif height * width >= 180:
        target = 28
    else:
        target = 14
    _add_distractors(grid, centers, rng, target)

    actual_centers = find_plus_centers(grid)
    if actual_centers != centers:
        raise RuntimeError(f"generator plus inventory drift: expected {centers}, found {actual_centers}")
    if grid[0][0] in colors:
        raise RuntimeError("marker color collided with a true-plus color")
    return grid


def generate(
    seed: Any,
    settings: Any,
    demos: Any,
    queries: Any,
) -> dict[str, Any]:
    """Return one native episode with private outputs and exact program source.

    Inputs depend only on ``seed`` and pair index, not on the selected setting,
    so matched-setting audits compare genuinely identical challenges.
    """
    _exact_int(seed, "seed", 0, 2**63 - 1)
    mode = _validate_settings(settings)
    demo_count = _exact_int(demos, "demos", 2, 6)
    query_count = _exact_int(queries, "queries", 4, 4)
    total = demo_count + query_count
    pairs: list[dict[str, list[list[int]]]] = []
    for pair_index in range(total):
        height, width = _SIZE_SCHEDULE[pair_index % len(_SIZE_SCHEDULE)]
        grid = _episode_grid(seed, pair_index, height, width)
        pairs.append({"input": grid, "output": apply_mode(grid, mode)})
    return {
        "train": pairs[:demo_count],
        "test": pairs[demo_count:],
        "program_solution": program(settings),
    }
