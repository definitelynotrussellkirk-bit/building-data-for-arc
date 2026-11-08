"""Native perimeter-rank family with an input-color selected bbox fill.

The default is the exact canonical perimeter ranking rule.  The alternative
first produces that ranked 2/4/8 intermediate, then uses the common original
object color to choose one rank and fills that ranked component's bounding box.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json
import random
from typing import Any, Iterable

HOME = Path(__file__).resolve().parent
TASK_ID = "cbd933916656"
MODES = ("rank_only", "selector_bbox")
PROGRAM_FILES = {
    "rank_only": "canonical.rkt",
    "selector_bbox": "selector_bbox.rkt",
}
RANK_COLORS = (2, 4, 8)
SELECTOR_TO_RANK = {1: 0, 3: 1, 5: 2}
NEIGHBORS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

# height, width, compact-hole dims, L-arm lengths, ring dims, selector color
TRAIN_PROFILES = (
    (15, 20, (4, 4), (5, 6), (5, 5), 1),
    (17, 22, (4, 5), (6, 6), (5, 6), 3),
    (19, 24, (5, 5), (7, 6), (6, 6), 5),
    (21, 25, (5, 6), (7, 7), (6, 7), 5),
    (24, 27, (6, 6), (8, 7), (7, 8), 1),
    (26, 29, (6, 7), (8, 8), (8, 8), 3),
)
QUERY_PROFILES = (
    (16, 21, (4, 5), (6, 6), (5, 6), 3),
    (20, 24, (5, 6), (7, 7), (6, 7), 5),
    (24, 28, (6, 6), (8, 7), (7, 8), 1),
    (30, 30, (7, 8), (9, 9), (9, 10), 5),
)


def _mode(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"finish_mode"}:
        raise ValueError("settings must contain exactly finish_mode")
    mode = settings["finish_mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError("finish_mode must be rank_only or selector_bbox")
    return mode


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def validate_grid(grid: Any) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(grid[0])
            or any(type(value) is not int or not 0 <= value <= 9 for value in row)
            for row in grid
        )
    ):
        raise ValueError("grid must be rectangular 1..30 by 1..30 with exact integer colors 0..9")
    return [row[:] for row in grid]


def program(settings: dict[str, Any]) -> str:
    return (HOME / PROGRAM_FILES[_mode(settings)]).read_text()


def components_nonzero(grid: Any) -> list[set[tuple[int, int]]]:
    source = validate_grid(grid)
    height, width = len(source), len(source[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if source[r][c] != 0}
    result: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        color = source[start[0]][start[1]]
        unseen.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            row, column = stack.pop()
            for dr, dc in NEIGHBORS4:
                neighbor = (row + dr, column + dc)
                if neighbor in unseen and source[neighbor[0]][neighbor[1]] == color:
                    unseen.remove(neighbor)
                    cells.add(neighbor)
                    stack.append(neighbor)
        result.append(cells)
    result.sort(key=lambda cells: min(cells))
    return result


def bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    material = tuple(cells)
    if not material:
        raise ValueError("bbox requires cells")
    return (
        min(r for r, _ in material),
        min(c for _, c in material),
        max(r for r, _ in material),
        max(c for _, c in material),
    )


def cardinal_perimeter(cells: Iterable[tuple[int, int]]) -> int:
    material = set(cells)
    if not material:
        raise ValueError("perimeter requires cells")
    return sum(
        1
        for row, column in material
        for dr, dc in NEIGHBORS4
        if (row + dr, column + dc) not in material
    )


def ranked_components(grid: Any) -> list[set[tuple[int, int]]]:
    return sorted(components_nonzero(grid), key=lambda cells: (cardinal_perimeter(cells), len(cells), bbox(cells)))


def _common_color(grid: list[list[int]]) -> int:
    colors = {value for row in grid for value in row if value != 0}
    if len(colors) != 1:
        raise ValueError("scene needs one common nonzero component color")
    return next(iter(colors))


def selector_rank(grid: Any) -> int:
    source = validate_grid(grid)
    color = _common_color(source)
    if color not in SELECTOR_TO_RANK:
        raise ValueError("selector color must be 1, 3, or 5")
    return SELECTOR_TO_RANK[color]


def rank_only(grid: Any) -> list[list[int]]:
    source = validate_grid(grid)
    ranked = ranked_components(source)
    if len(ranked) != 3:
        raise ValueError("scene needs exactly three components")
    result = [[0] * len(source[0]) for _ in source]
    for color, cells in zip(RANK_COLORS, ranked):
        for row, column in cells:
            result[row][column] = color
    return result


def selector_bbox(grid: Any) -> list[list[int]]:
    source = validate_grid(grid)
    ranked = ranked_components(source)
    if len(ranked) != 3:
        raise ValueError("scene needs exactly three components")
    rank = selector_rank(source)
    result = rank_only(source)
    r0, c0, r1, c1 = bbox(ranked[rank])
    color = RANK_COLORS[rank]
    for row in range(r0, r1 + 1):
        for column in range(c0, c1 + 1):
            result[row][column] = color
    return result


def transform(grid: Any, settings: dict[str, Any]) -> list[list[int]]:
    return rank_only(grid) if _mode(settings) == "rank_only" else selector_bbox(grid)


def _normalize(cells: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    material = set(cells)
    low_row = min(row for row, _ in material)
    low_column = min(column for _, column in material)
    return {(row - low_row, column - low_column) for row, column in material}


def _rotate(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    height = max(row for row, _ in cells) + 1
    return _normalize((column, height - 1 - row) for row, column in cells)


def _orient(cells: set[tuple[int, int]], rng: random.Random) -> set[tuple[int, int]]:
    result = set(cells)
    for _ in range(rng.randrange(4)):
        result = _rotate(result)
    if rng.randrange(2):
        width = max(column for _, column in result) + 1
        result = _normalize((row, width - 1 - column) for row, column in result)
    return result


def _compact_hole(height: int, width: int) -> set[tuple[int, int]]:
    cells = {(row, column) for row in range(height) for column in range(width)}
    cells.remove((height // 2, width // 2))
    return cells


def _l_path(vertical: int, horizontal: int) -> set[tuple[int, int]]:
    return {(row, 0) for row in range(vertical)} | {(vertical - 1, column) for column in range(horizontal)}


def _ring(height: int, width: int) -> set[tuple[int, int]]:
    return {
        (row, column)
        for row in range(height)
        for column in range(width)
        if row in (0, height - 1) or column in (0, width - 1)
    }


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = f"{TASK_ID}:{seed}:{split}:{index}".encode()
    return random.Random(int.from_bytes(sha256(raw).digest(), "big"))


def _profile(split: str, index: int):
    profiles = TRAIN_PROFILES if split == "train" else QUERY_PROFILES
    if not 0 <= index < len(profiles):
        raise ValueError("profile index outside the authored bank")
    return profiles[index]


def _translate(cells: set[tuple[int, int]], top: int, left: int) -> set[tuple[int, int]]:
    return {(row + top, column + left) for row, column in cells}


def _draw_scene(seed: int, split: str, index: int) -> list[list[int]]:
    height, width, compact_dims, l_dims, ring_dims, color = _profile(split, index)
    rng = _rng(seed, split, index)
    shapes = [
        _orient(_compact_hole(*compact_dims), rng),
        _orient(_l_path(*l_dims), rng),
        _orient(_ring(*ring_dims), rng),
    ]
    rng.shuffle(shapes)
    grid = [[0] * width for _ in range(height)]
    placed: list[set[tuple[int, int]]] = []
    for slot, shape in enumerate(shapes):
        shape_h = max(row for row, _ in shape) + 1
        shape_w = max(column for _, column in shape) + 1
        if slot == 0:
            top, left = 1, 1
        elif slot == 1:
            top, left = 1, width - shape_w - 1
        else:
            top, left = height - shape_h - 1, (width - shape_w) // 2
        cells = _translate(shape, top, left)
        if any(not (0 <= row < height and 0 <= column < width) for row, column in cells):
            raise AssertionError("shape escaped the profile")
        halo = {
            (row + dr, column + dc)
            for row, column in cells
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
        }
        if any(halo & other for other in placed):
            raise AssertionError("profile components are not separated")
        placed.append(cells)
        for row, column in cells:
            grid[row][column] = color
    components = components_nonzero(grid)
    if len(components) != 3:
        raise AssertionError("profile did not create exactly three components")
    perimeters = [cardinal_perimeter(cells) for cells in components]
    if len(set(perimeters)) != 3:
        raise AssertionError("profile component perimeters are not distinct")
    by_perimeter = [frozenset(cells) for cells in ranked_components(grid)]
    by_area = [frozenset(cells) for cells in sorted(components, key=lambda cells: (len(cells), bbox(cells)))]
    if by_perimeter == by_area:
        raise AssertionError("profile fails to distinguish perimeter rank from area rank")
    if any(len(cells) == (bbox(cells)[2] - bbox(cells)[0] + 1) * (bbox(cells)[3] - bbox(cells)[1] + 1) for cells in components):
        raise AssertionError("every component must gain cells when its bbox is filled")
    return grid


def _pair(grid: list[list[int]], settings: dict[str, Any]) -> dict[str, Any]:
    return {"input": deepcopy(grid), "output": transform(grid, settings)}


def fit_settings(demos: list[dict[str, Any]]) -> list[dict[str, str]]:
    survivors = []
    for mode in MODES:
        setting = {"finish_mode": mode}
        if demos and all(transform(pair["input"], setting) == pair["output"] for pair in demos):
            survivors.append(setting)
    return survivors


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 3, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    mode = _mode(settings)
    chosen = {"finish_mode": mode}
    train = [_pair(_draw_scene(seed, "train", index), chosen) for index in range(demos)]
    test = [_pair(_draw_scene(seed, "test", index), chosen) for index in range(queries)]
    if fit_settings(train) != [chosen]:
        raise RuntimeError("demonstrations do not uniquely identify finish_mode")
    encoded = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(encoded) != len(set(encoded)):
        raise RuntimeError("episode contains duplicate inputs")
    return {"train": train, "test": test, "program_solution": program(chosen)}
