"""Native bbox-key family with an input-derived size relay.

The default is the exact canonical rule: every green object takes the key color
above its bounding-box top-left corner.  The alternative first finds the unique
largest green object and reads its bbox key as a target cell count; only green
objects of that size are then recolored by their own bbox keys.  Python labels
are claims and native qualification re-executes them through protected Racket.
"""
from __future__ import annotations

from collections import deque
import hashlib
from itertools import cycle
from pathlib import Path
import random
from typing import Iterable

TASK_ID = "b71c45e9a3c0"
VERSION = "largest-key-size-relay-v1"
SCOPES = ("all_objects", "largest_key_size")
DEFAULT_SETTINGS = {"scope": "all_objects"}
DEMO_DIMS = ((12, 14), (14, 15), (16, 18), (19, 20), (23, 24), (26, 27))
QUERY_DIMS = ((15, 17), (21, 22), (27, 29), (30, 30))
DEMO_GROUPS = (4, 4, 5, 5, 6, 6)
QUERY_GROUPS = (4, 5, 6, 6)
_STEPS = ((-1, 0), (0, -1), (0, 1), (1, 0))
_KEY_COLORS = (1, 2, 4, 5, 6, 7, 8, 9)


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _scope(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {"scope"}:
        raise ValueError("settings must contain exactly scope")
    value = settings["scope"]
    if type(value) is not str or value not in SCOPES:
        raise ValueError(f"scope must be one of {SCOPES}")
    return value


def _validate_grid(grid: object) -> list[list[int]]:
    if (type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]
            or len(grid) > 30 or len(grid[0]) > 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                   for row in grid)):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return grid


def _components(grid: list[list[int]], color: int = 3) -> list[tuple[tuple[int, int], ...]]:
    _validate_grid(grid)
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    groups = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for dr, dc in _STEPS:
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    queue.append(point)
        groups.append(tuple(sorted(cells)))
    return sorted(groups, key=lambda cells: (min(cells), cells))


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def _key_position(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    top, left, _, _ = _bbox(cells)
    return top - 1, left


def _key(grid: list[list[int]], cells: Iterable[tuple[int, int]]) -> int:
    r, c = _key_position(cells)
    if not 0 <= r < len(grid):
        raise ValueError("object has no row for its bbox key")
    value = grid[r][c]
    if value in (0, 3):
        raise ValueError("missing non-background bbox key")
    return value


def _largest(groups: list[tuple[tuple[int, int], ...]]) -> tuple[tuple[int, int], ...]:
    if not groups:
        raise ValueError("missing green objects")
    ordered = sorted(groups, key=lambda cells: (-len(cells), min(cells), cells))
    if len(ordered) > 1 and len(ordered[0]) == len(ordered[1]):
        raise ValueError("largest green object must be unique")
    return ordered[0]


def relay_intermediate(grid: list[list[int]]) -> dict:
    groups = _components(_validate_grid(grid))
    largest = _largest(groups)
    target_size = _key(grid, largest)
    selected = tuple(cells for cells in groups if len(cells) == target_size)
    if len(selected) != 1:
        raise ValueError("largest bbox key must select exactly one object size")
    return {
        "largest_component": largest,
        "largest_size": len(largest),
        "largest_key_position": _key_position(largest),
        "target_size": target_size,
        "selected_components": selected,
    }


def _paint_selected(grid: list[list[int]], selected: Iterable[tuple[tuple[int, int], ...]],
                    *, key_reader=None) -> list[list[int]]:
    output = [row[:] for row in grid]
    read = _key if key_reader is None else key_reader
    for cells in selected:
        color = read(grid, cells)
        for r, c in cells:
            output[r][c] = color
    return output


def transform(grid: list[list[int]], settings: dict) -> list[list[int]]:
    scope = _scope(settings)
    groups = _components(_validate_grid(grid))
    selected = groups if scope == "all_objects" else relay_intermediate(grid)["selected_components"]
    return _paint_selected(grid, selected)


def counterfactual_transform(grid: list[list[int]]) -> list[list[int]]:
    groups = _components(_validate_grid(grid))
    largest = _largest(groups)
    selected = tuple(cells for cells in groups if len(cells) == len(largest))
    return _paint_selected(grid, selected)


def program(settings: dict) -> str:
    scope = _scope(settings)
    filename = "canonical.rkt" if scope == "all_objects" else "largest-key-size.rkt"
    return Path(__file__).with_name(filename).read_bytes().decode("utf-8")


def counterfactual_program() -> str:
    return Path(__file__).with_name("counterfactual-largest-size.rkt").read_bytes().decode("utf-8")


def _gap_shape(size: int) -> tuple[tuple[int, int], ...]:
    path = ((0, 1), (1, 1), (1, 0), (2, 0), (2, 1), (2, 2),
            (1, 2), (0, 2), (0, 3), (1, 3), (2, 3))
    _integer(size, 3, 9, "shape size")
    return path[:size]


def _solid_shape(size: int) -> tuple[tuple[int, int], ...]:
    path = ((0, 0), (0, 1), (1, 1), (1, 0), (2, 0), (2, 1),
            (2, 2), (1, 2), (0, 2), (0, 3), (1, 3))
    _integer(size, 3, 9, "shape size")
    return path[:size]


def _shape_dims(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    shape = tuple(shape)
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _place(grid: list[list[int]], shape: Iterable[tuple[int, int]], top: int, left: int,
           key_color: int) -> tuple[tuple[int, int], ...]:
    cells = tuple(sorted((top + r, left + c) for r, c in shape))
    key = (top - 1, left)
    footprint = cells + (key,)
    if any(not (0 <= r < len(grid) and 0 <= c < len(grid[0])) for r, c in footprint):
        raise RuntimeError("constructed object escaped grid")
    if any(grid[r][c] != 0 for r, c in footprint):
        raise RuntimeError("constructed objects or keys overlapped")
    for r, c in cells:
        grid[r][c] = 3
    grid[key[0]][key[1]] = key_color
    return cells


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = f"{TASK_ID}:{VERSION}:{seed}:{split}:{index}".encode("ascii")
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _slot_positions(h: int, w: int, shapes: list[tuple[tuple[int, int], ...]]) -> list[tuple[int, int]]:
    n = len(shapes)
    top_count = (n + 1) // 2
    bottom_count = n - top_count

    def columns(count: int, shape_subset: list[tuple[tuple[int, int], ...]]) -> list[int]:
        if count == 1:
            sw = _shape_dims(shape_subset[0])[1]
            return [(w - sw) // 2]
        result = []
        for i, shape in enumerate(shape_subset):
            sw = _shape_dims(shape)[1]
            if i == 0:
                result.append(0)
            elif i == count - 1:
                result.append(w - sw)
            else:
                result.append((w - sw) // 2)
        return result

    positions = []
    top_shapes = shapes[:top_count]
    for shape, left in zip(top_shapes, columns(top_count, top_shapes)):
        positions.append((1, left))
    bottom_shapes = shapes[top_count:]
    for shape, left in zip(bottom_shapes, columns(bottom_count, bottom_shapes)):
        sh, _ = _shape_dims(shape)
        positions.append((h - sh, left))
    return positions


def _assign_nonlargest_keys(sizes: list[int], target_size: int, rng: random.Random) -> list[int]:
    palette = [color for color in _KEY_COLORS if color != target_size]
    rng.shuffle(palette)
    assigned = []
    used = set()
    for size in sizes:
        color = next(color for color in palette if color not in used and color != size)
        assigned.append(color)
        used.add(color)
    return assigned


def _input(seed: int, split: str, index: int) -> list[list[int]]:
    dims = DEMO_DIMS if split == "train" else QUERY_DIMS
    counts = DEMO_GROUPS if split == "train" else QUERY_GROUPS
    h, w = dims[index]
    n = counts[index]
    rng = _rng(seed, split, index)
    target_size = rng.choice((4, 5, 6, 7))
    others = [size for size in (3, 4, 5, 6, 7, 8) if size != target_size]
    shift = rng.randrange(len(others))
    others = others[shift:] + others[:shift]

    sizes = [None] * n
    sizes[1] = target_size
    sizes[-1] = 9
    for slot, size in zip((i for i in range(n) if i not in {1, n - 1}), others):
        sizes[slot] = size
    size_values = [int(value) for value in sizes]

    shapes = [_gap_shape(size) if slot in {0, 1, n - 1} else _solid_shape(size)
              for slot, size in enumerate(size_values)]
    keys = _assign_nonlargest_keys(size_values[:-1], target_size, rng) + [target_size]
    positions = _slot_positions(h, w, shapes)

    grid = [[0] * w for _ in range(h)]
    for shape, key_color, (top, left) in zip(shapes, keys, positions):
        _place(grid, shape, top, left, key_color)

    if (h, w) == (30, 30):
        # Irrelevant but visible workload, kept away from all bbox keys/objects.
        for c in range(9, 21):
            if grid[14][c] == 0:
                grid[14][c] = 9
    return grid


def analyze(grid: list[list[int]]) -> dict:
    errors = []
    try:
        groups = _components(_validate_grid(grid))
        largest = _largest(groups)
        keys = [_key(grid, cells) for cells in groups]
        target = _key(grid, largest)
        selected = [cells for cells in groups if len(cells) == target]
        if len(selected) != 1:
            errors.append("largest key must select one object size")
        if len(set(keys)) != len(keys):
            errors.append("bbox keys must be distinct")
        if target >= len(largest):
            errors.append("largest key must be smaller than largest object")
        if groups and groups[0] == largest:
            errors.append("largest object must not be first in scan order")
        for cells, color in zip(groups, keys):
            if color == len(cells):
                errors.append("object key must not equal its own size")
    except (ValueError, RuntimeError) as exc:
        errors.append(str(exc))
        groups, largest, keys, target = [], (), [], 0
    h, w = (len(grid), len(grid[0])) if isinstance(grid, list) and grid and isinstance(grid[0], list) else (0, 0)
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value] if h and w else []
    sides = set()
    if any(r == 0 for r, _ in points): sides.add("top")
    if any(r == h - 1 for r, _ in points): sides.add("bottom")
    if any(c == 0 for _, c in points): sides.add("left")
    if any(c == w - 1 for _, c in points): sides.add("right")
    return {
        "errors": errors,
        "component_sizes": [len(cells) for cells in groups],
        "largest_size": len(largest),
        "largest_key": target,
        "keys": keys,
        "empty_bbox_corner_count": sum((_bbox(cells)[0], _bbox(cells)[1]) not in cells for cells in groups),
        "largest_is_first": bool(groups and groups[0] == largest),
        "nonzero_count": len(points),
        "boundary_sides": sorted(sides),
    }


def _topmost_key(grid: list[list[int]], cells: tuple[tuple[int, int], ...]) -> int:
    top = min(r for r, _ in cells)
    column = min(c for r, c in cells if r == top)
    return grid[top - 1][column]


def _selected_for_scope(grid: list[list[int]], settings: dict) -> tuple[tuple[tuple[int, int], ...], ...]:
    groups = _components(grid)
    return tuple(groups) if _scope(settings) == "all_objects" else relay_intermediate(grid)["selected_components"]


def _wrong_above_topmost(grid: list[list[int]], settings: dict) -> list[list[int]]:
    groups = _components(grid)
    if _scope(settings) == "all_objects":
        selected = tuple(groups)
    else:
        wrong_target = _topmost_key(grid, _largest(groups))
        selected = tuple(cells for cells in groups if len(cells) == wrong_target)
    return _paint_selected(grid, selected, key_reader=_topmost_key)


def _wrong_one_key(grid: list[list[int]], settings: dict) -> list[list[int]]:
    selected = _selected_for_scope(grid, settings)
    first_color = _key(grid, _components(grid)[0])
    return _paint_selected(grid, selected, key_reader=lambda _g, _c: first_color)


def _wrong_first_key_size(grid: list[list[int]], _settings: dict) -> list[list[int]]:
    groups = _components(grid)
    target = _key(grid, groups[0])
    return _paint_selected(grid, tuple(cells for cells in groups if len(cells) == target))


def _wrong_largest_size(grid: list[list[int]], _settings: dict) -> list[list[int]]:
    return counterfactual_transform(grid)


def _wrong_largest_only(grid: list[list[int]], _settings: dict) -> list[list[int]]:
    groups = _components(grid)
    return _paint_selected(grid, (_largest(groups),))


def _wrong_key_equals_size(grid: list[list[int]], _settings: dict) -> list[list[int]]:
    groups = _components(grid)
    return _paint_selected(grid, tuple(cells for cells in groups if _key(grid, cells) == len(cells)))


SHORTCUTS = {
    "above_topmost_occupied": _wrong_above_topmost,
    "one_key_for_all": _wrong_one_key,
    "first_object_key_as_target_size": _wrong_first_key_size,
    "largest_size_instead_of_largest_key": _wrong_largest_size,
    "recolor_largest_only": _wrong_largest_only,
    "key_color_equals_object_size": _wrong_key_equals_size,
}


def lesson_certificate(demos: list[dict], settings: dict) -> dict:
    scope = _scope(settings)
    expected = [pair["output"] for pair in demos]
    survivors = []
    for candidate in SCOPES:
        if all(transform(pair["input"], {"scope": candidate}) == output
               for pair, output in zip(demos, expected)):
            survivors.append({"scope": candidate})
    surviving_shortcuts = [name for name, rival in SHORTCUTS.items()
                           if all(rival(pair["input"], {"scope": scope}) == output
                                  for pair, output in zip(demos, expected))]
    return {
        "selected": {"scope": scope},
        "surviving_settings": survivors,
        "surviving_shortcuts": surviving_shortcuts,
        "query_outputs_consulted": False,
    }


def generate(seed: int, settings: dict, demos: int = 3, queries: int = 4) -> dict:
    _integer(seed, 0, 2**63 - 1, "seed")
    scope = _scope(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    chosen = {"scope": scope}
    train_inputs = [_input(seed, "train", index) for index in range(demos)]
    test_inputs = [_input(seed, "test", index) for index in range(queries)]
    return {
        "train": [{"input": grid, "output": transform(grid, chosen)} for grid in train_inputs],
        "test": [{"input": grid, "output": transform(grid, chosen)} for grid in test_inputs],
        "program_solution": program(chosen),
    }
