"""Native parametric prototype for bdb419bbf286.

The canonical ``fixed_three`` setting preserves the exact authority: select the
first color-2 object, derive a vector from the first row-major 3 and 4, and
paint translations k=0,1,2.  ``to_boundary`` uses the same input-dependent
shape/vector intermediate, then keeps translating until every later copy is
outside the canvas.  Every authored scene includes later marker decoys that
make a last-marker shortcut visibly wrong.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "bdb419bbf286"
HERE = Path(__file__).resolve().parent
REPEAT_RULES = ("fixed_three", "to_boundary")
_INTERNAL_RULES = {
    "last_marker_fixed_three",
    "last_marker_to_boundary",
    "fixed_one",
    "fixed_two",
    "fixed_four",
    "fixed_five",
    "fixed_six",
}
_DEMO_DIMS = ((14, 16), (16, 19), (18, 21), (20, 23), (22, 25), (24, 27))
_QUERY_DIMS = ((16, 20), (21, 24), (26, 28), (30, 30))
_DEMO_VECTORS = ((1, 1), (0, 2), (-1, 1), (2, 0), (-1, -1), (1, -2))
_QUERY_VECTORS = ((1, 2), (-1, 1), (0, -2), (1, 1))
_SHAPES = (
    ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (1, 0), (1, 1), (1, 2), (2, 2), (3, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (3, 2), (4, 2), (4, 3)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (3, 1), (3, 2), (3, 3)),
    ((0, 1), (0, 2), (1, 0), (1, 1), (2, 1), (2, 2), (2, 3), (3, 0), (3, 1), (4, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2), (3, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 1), (2, 2), (3, 1), (3, 2), (4, 2), (4, 3), (5, 2), (5, 3)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2), (3, 3), (4, 3)),
    ((0, 0), (0, 1), (1, 1), (2, 0), (2, 1), (2, 2), (3, 2), (4, 1), (4, 2), (4, 3), (5, 3), (5, 4)),
)
_DISTRACTOR_COLORS = (1, 5, 6, 7, 9)


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def normalize_settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"repeat_rule"}:
        raise ValueError("settings must contain exactly repeat_rule")
    value = settings["repeat_rule"]
    if type(value) is not str or value not in REPEAT_RULES:
        raise ValueError(f"repeat_rule must be one of {REPEAT_RULES}")
    return {"repeat_rule": value}


def program(settings: Any) -> str:
    rule = normalize_settings(settings)["repeat_rule"]
    filename = "canonical.rkt" if rule == "fixed_three" else "to_boundary.rkt"
    return (HERE / filename).read_text(encoding="utf-8")


def _validate_grid(grid: Any) -> tuple[int, int]:
    if (
        type(grid) is not list
        or not 5 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 5 <= len(grid[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(grid[0])
            or any(type(value) is not int or not 0 <= value <= 9 or value == 8 for value in row)
            for row in grid
        )
    ):
        raise ValueError("grid must be a 5..30 rectangular ARC grid without input color 8")
    return len(grid), len(grid[0])


def _components(grid: list[list[int]], color: int) -> list[frozenset[tuple[int, int]]]:
    unseen = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    result: list[frozenset[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component = {start}
        pending = [start]
        while pending:
            row, col = pending.pop()
            for point in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    pending.append(point)
        result.append(frozenset(component))
    return result


def _translated_cells(
    shape: Iterable[tuple[int, int]],
    vector: tuple[int, int],
    height: int,
    width: int,
    count: int,
) -> tuple[frozenset[tuple[int, int]], ...]:
    dr, dc = vector
    return tuple(
        frozenset(
            (row + k * dr, col + k * dc)
            for row, col in shape
            if 0 <= row + k * dr < height and 0 <= col + k * dc < width
        )
        for k in range(count)
    )


def _paint(height: int, width: int, copies: Iterable[Iterable[tuple[int, int]]]) -> list[list[int]]:
    output = [[0 for _ in range(width)] for _ in range(height)]
    for cells in copies:
        for row, col in cells:
            output[row][col] = 8
    return output


def analyze(grid: Any) -> dict[str, Any]:
    height, width = _validate_grid(grid)
    shapes = _components(grid, 2)
    marker_3 = tuple(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 3
    )
    marker_4 = tuple(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 4
    )
    if len(shapes) != 1:
        raise ValueError("expected exactly one connected color-2 source object")
    if len(marker_3) != 2 or len(marker_4) != 2:
        raise ValueError("expected exactly two row-major markers of each color 3 and 4")
    shape = shapes[0]
    first_vector = (marker_4[0][0] - marker_3[0][0], marker_4[0][1] - marker_3[0][1])
    last_vector = (marker_4[-1][0] - marker_3[-1][0], marker_4[-1][1] - marker_3[-1][1])
    if first_vector == (0, 0) or last_vector == (0, 0):
        raise ValueError("marker vectors must be nonzero")
    horizon = height + width
    boundary_copies = _translated_cells(shape, first_vector, height, width, horizon)
    boundary_copy_count = sum(bool(cells) for cells in boundary_copies)
    if boundary_copy_count < 5:
        raise ValueError("authored source/vector must expose at least five nonempty translations")
    return {
        "height": height,
        "width": width,
        "shape": shape,
        "marker_3": marker_3,
        "marker_4": marker_4,
        "first_vector": first_vector,
        "last_vector": last_vector,
        "boundary_copy_count": boundary_copy_count,
        "boundary_copies": boundary_copies,
    }


def _rule_name(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"repeat_rule"}:
        raise ValueError("settings must contain exactly repeat_rule")
    value = settings["repeat_rule"]
    if type(value) is not str or value not in set(REPEAT_RULES) | _INTERNAL_RULES:
        raise ValueError("unknown repeat_rule")
    return value


def finish_python(grid: Any, settings: Any) -> list[list[int]]:
    rule = _rule_name(settings)
    facts = analyze(grid)
    if rule.startswith("last_marker"):
        vector = facts["last_vector"]
    else:
        vector = facts["first_vector"]
    if rule in ("to_boundary", "last_marker_to_boundary"):
        count = facts["height"] + facts["width"]
    else:
        count = {
            "fixed_one": 1,
            "fixed_two": 2,
            "fixed_three": 3,
            "last_marker_fixed_three": 3,
            "fixed_four": 4,
            "fixed_five": 5,
            "fixed_six": 6,
        }[rule]
    copies = _translated_cells(facts["shape"], vector, facts["height"], facts["width"], count)
    return _paint(facts["height"], facts["width"], copies)


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:boundary-repeat-v1:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _shift_shape(
    shape: Iterable[tuple[int, int]],
    height: int,
    width: int,
    vector: tuple[int, int],
) -> frozenset[tuple[int, int]]:
    shape = tuple(shape)
    shape_height = max(row for row, _ in shape) + 1
    shape_width = max(col for _, col in shape) + 1
    dr, dc = vector
    top = 0 if dr > 0 else height - shape_height if dr < 0 else (height - shape_height) // 2
    left = 0 if dc > 0 else width - shape_width if dc < 0 else (width - shape_width) // 2
    return frozenset((top + row, left + col) for row, col in shape)


def _first_marker_pair(
    rng: random.Random,
    height: int,
    width: int,
    vector: tuple[int, int],
    occupied: set[tuple[int, int]],
) -> tuple[tuple[int, int], tuple[int, int]]:
    dr, dc = vector
    candidates = []
    for row in range(height):
        for col in range(width):
            other = (row + dr, col + dc)
            if not (0 <= other[0] < height and 0 <= other[1] < width):
                continue
            if (row, col) in occupied or other in occupied:
                continue
            cutoff = max(row * width + col, other[0] * width + other[1])
            occupied_indices = {rr * width + cc for rr, cc in occupied}
            free_after = (
                height * width
                - 1
                - cutoff
                - sum(index > cutoff for index in occupied_indices)
            )
            if cutoff < (height * width * 2) // 3 and free_after >= 8:
                candidates.append(((row, col), other))
    if not candidates:
        raise RuntimeError("cannot place true marker pair")
    return rng.choice(candidates[: max(1, min(40, len(candidates)))])


def _copy_union(
    shape: Iterable[tuple[int, int]],
    vector: tuple[int, int],
    height: int,
    width: int,
    count: int,
) -> frozenset[tuple[int, int]]:
    return frozenset().union(*_translated_cells(shape, vector, height, width, count))


def _later_marker_pair(
    rng: random.Random,
    height: int,
    width: int,
    shape: frozenset[tuple[int, int]],
    first_3: tuple[int, int],
    first_4: tuple[int, int],
    vector: tuple[int, int],
) -> tuple[tuple[int, int], tuple[int, int]]:
    occupied = set(shape) | {first_3, first_4}
    cutoff = max(first_3[0] * width + first_3[1], first_4[0] * width + first_4[1])
    free = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if row * width + col > cutoff and (row, col) not in occupied
    ]
    true_fixed = _copy_union(shape, vector, height, width, 3)
    true_boundary = _copy_union(shape, vector, height, width, height + width)
    candidate_cells = free[-40:]
    candidate_pairs = [
        (later_3, later_4)
        for later_3 in candidate_cells
        for later_4 in candidate_cells
        if later_3 != later_4
    ]
    rng.shuffle(candidate_pairs)
    for later_3, later_4 in candidate_pairs:
        rival_vector = (later_4[0] - later_3[0], later_4[1] - later_3[1])
        if rival_vector in ((0, 0), vector):
            continue
        if _copy_union(shape, rival_vector, height, width, 3) == true_fixed:
            continue
        if _copy_union(shape, rival_vector, height, width, height + width) == true_boundary:
            continue
        return later_3, later_4
    raise RuntimeError("cannot place discriminating later markers")


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    dims = _DEMO_DIMS if split == "train" else _QUERY_DIMS
    vectors = _DEMO_VECTORS if split == "train" else _QUERY_VECTORS
    height, width = dims[index]
    vector = vectors[index]
    rng = _rng(seed, split, index)
    shape_template = _SHAPES[(index + seed + (0 if split == "train" else 6)) % len(_SHAPES)]
    shape = _shift_shape(shape_template, height, width, vector)
    first_3, first_4 = _first_marker_pair(rng, height, width, vector, set(shape))
    later_3, later_4 = _later_marker_pair(rng, height, width, shape, first_3, first_4, vector)

    grid = [[0 for _ in range(width)] for _ in range(height)]
    for row, col in shape:
        grid[row][col] = 2
    grid[first_3[0]][first_3[1]] = 3
    grid[first_4[0]][first_4[1]] = 4
    grid[later_3[0]][later_3[1]] = 3
    grid[later_4[0]][later_4[1]] = 4

    free = [(row, col) for row in range(height) for col in range(width) if grid[row][col] == 0]
    rng.shuffle(free)
    distractor_count = 64 if (height, width) == (30, 30) else max(10, (height * width) // 24)
    for offset, (row, col) in enumerate(free[:distractor_count]):
        grid[row][col] = _DISTRACTOR_COLORS[(offset + seed + index) % len(_DISTRACTOR_COLORS)]

    facts = analyze(grid)
    if facts["first_vector"] != vector:
        raise AssertionError("first-marker vector drifted")
    if facts["last_vector"] == vector:
        raise AssertionError("last-marker rival was not separated")
    if finish_python(grid, {"repeat_rule": "fixed_three"}) == finish_python(
        grid, {"repeat_rule": "to_boundary"}
    ):
        raise AssertionError("repeat settings collapsed")
    return grid


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _exact_int(seed, "seed", 0, 2**63 - 1)
    demos = _exact_int(demos, "demos", 2, 6)
    queries = _exact_int(queries, "queries", 1, 4)
    normalized = normalize_settings(settings)
    train_inputs = [_scene(seed, "train", index) for index in range(demos)]
    test_inputs = [_scene(seed, "test", index) for index in range(queries)]
    all_inputs = train_inputs + test_inputs
    if len({repr(grid) for grid in all_inputs}) != len(all_inputs):
        raise RuntimeError("episode inputs must be distinct")

    def pair(grid: list[list[int]]) -> dict[str, Any]:
        return {"input": copy.deepcopy(grid), "output": finish_python(grid, normalized)}

    return {
        "train": [pair(grid) for grid in train_inputs],
        "test": [pair(grid) for grid in test_inputs],
        "program_solution": program(normalized),
        "settings": copy.deepcopy(normalized),
        "metadata": {
            "schema": "bdb419bbf286-boundary-repeat-v1",
            "seed": seed,
            "max_lawful_canvas": [30, 30],
            "sequential_dependency": {
                "step_a": "select the first source object and first row-major marker pair, then derive their translation vector",
                "intermediate": "the input-specific source-cell set and signed translation vector",
                "step_b": "translate that source repeatedly along the derived vector, either three times or until no copy remains in bounds",
            },
        },
    }
