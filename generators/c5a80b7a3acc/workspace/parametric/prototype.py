"""Native authoring prototype for c5a80b7a3acc's largest-result relay.

``direct`` is the exact canonical rule. ``largest_component`` performs the
same marker-selected normalized set operation (Stage A), then selects and
re-crops the largest four-connected component created by that intermediate
(Stage B).  Component ties are resolved by row-major top-left position.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable


TASK_ID = "c5a80b7a3acc"
HERE = Path(__file__).resolve().parent
RESULT_POLICIES = ("direct", "largest_component")
HYPOTHESES = RESULT_POLICIES + (
    "smallest_component",
    "first_component",
    "largest_bbox",
    "always_intersection_largest",
    "always_xor_largest",
    "union_largest",
    "red_shape",
    "green_shape",
    "red_minus_green_largest",
    "green_minus_red_largest",
)


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(value: Any) -> str:
    if type(value) is not dict or set(value) != {"result_policy"}:
        raise ValueError("settings must contain only result_policy")
    policy = value["result_policy"]
    if type(policy) is not str or policy not in RESULT_POLICIES:
        raise ValueError("result_policy must be direct or largest_component")
    return policy


def program(settings: Any) -> str:
    policy = _settings(settings)
    name = "canonical.rkt" if policy == "direct" else "largest_component.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def _normalize(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = frozenset(cells)
    if not cells:
        return cells
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return frozenset((row - top, col - left) for row, col in cells)


def _components(cells: Iterable[tuple[int, int]]) -> list[frozenset[tuple[int, int]]]:
    remaining = set(cells)
    result: list[frozenset[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        pending = [start]
        component = {start}
        while pending:
            row, col = pending.pop()
            for point in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    pending.append(point)
        result.append(frozenset(component))
    return result


def _component_key(component: frozenset[tuple[int, int]]) -> tuple[int, tuple[int, int]]:
    return (-len(component), min(component))


def _bbox_area(component: frozenset[tuple[int, int]]) -> int:
    return (
        max(row for row, _ in component) - min(row for row, _ in component) + 1
    ) * (
        max(col for _, col in component) - min(col for _, col in component) + 1
    )


def _crop(cells: Iterable[tuple[int, int]]) -> list[list[int]]:
    cells = _normalize(cells)
    if not cells:
        return [[0]]
    height = max(row for row, _ in cells) + 1
    width = max(col for _, col in cells) + 1
    return [
        [8 if (row, col) in cells else 0 for col in range(width)]
        for row in range(height)
    ]


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or cell not in {0, 2, 3, 7, 9} for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with colors 0,2,3,7,9")
    return value


def _source_cells(value: list[list[int]], color: int) -> frozenset[tuple[int, int]]:
    cells = frozenset(
        (row, col)
        for row, line in enumerate(value)
        for col, cell in enumerate(line)
        if cell == color
    )
    parts = _components(cells)
    if len(parts) != 1:
        raise ValueError(f"expected exactly one four-connected color-{color} source")
    return _normalize(parts[0])


def _stage_a(value: list[list[int]], operation: str | None = None) -> frozenset[tuple[int, int]]:
    _grid(value)
    red = _source_cells(value, 2)
    green = _source_cells(value, 3)
    selected = operation or ("intersection" if any(7 in row for row in value) else "xor")
    if selected == "intersection":
        return red & green
    if selected == "xor":
        return red ^ green
    if selected == "union":
        return red | green
    if selected == "red_minus_green":
        return red - green
    if selected == "green_minus_red":
        return green - red
    raise ValueError(f"unknown set operation: {selected}")


def _select(cells: frozenset[tuple[int, int]], mode: str) -> frozenset[tuple[int, int]]:
    parts = _components(cells)
    if not parts:
        return frozenset()
    if mode == "largest":
        return min(parts, key=_component_key)
    if mode == "smallest":
        return min(parts, key=lambda part: (len(part), min(part)))
    if mode == "first":
        return min(parts, key=min)
    if mode == "bbox":
        return min(parts, key=lambda part: (-_bbox_area(part), min(part)))
    raise ValueError(f"unknown component selector: {mode}")


def observe(value: Any) -> dict[str, Any]:
    value = _grid(value)
    red = _source_cells(value, 2)
    green = _source_cells(value, 3)
    operation = "intersection" if any(7 in row for row in value) else "xor"
    result = red & green if operation == "intersection" else red ^ green
    parts = sorted(_components(result), key=_component_key)
    if not parts:
        raise ValueError("prototype grammar requires a nonempty Stage-A result")
    return {
        "height": len(value),
        "width": len(value[0]),
        "source_components": {"2": 1, "3": 1},
        "source_sizes": {"2": len(red), "3": len(green)},
        "operation": operation,
        "result_size": len(result),
        "result_component_sizes": [len(part) for part in parts],
        "largest_component_top_left": list(min(parts[0])),
        "largest_component_bbox_area": _bbox_area(parts[0]),
    }


def predict(value: Any, hypothesis: Any) -> list[list[int]]:
    if type(hypothesis) is not str or hypothesis not in HYPOTHESES:
        raise ValueError("unknown declared hypothesis")
    value = _grid(value)
    red = _source_cells(value, 2)
    green = _source_cells(value, 3)
    selected = _stage_a(value)
    if hypothesis == "direct":
        return _crop(selected)
    if hypothesis == "largest_component":
        return _crop(_select(selected, "largest"))
    if hypothesis == "smallest_component":
        return _crop(_select(selected, "smallest"))
    if hypothesis == "first_component":
        return _crop(_select(selected, "first"))
    if hypothesis == "largest_bbox":
        return _crop(_select(selected, "bbox"))
    if hypothesis == "always_intersection_largest":
        return _crop(_select(red & green, "largest"))
    if hypothesis == "always_xor_largest":
        return _crop(_select(red ^ green, "largest"))
    if hypothesis == "union_largest":
        return _crop(_select(red | green, "largest"))
    if hypothesis == "red_shape":
        return _crop(red)
    if hypothesis == "green_shape":
        return _crop(green)
    if hypothesis == "red_minus_green_largest":
        return _crop(_select(red - green, "largest"))
    return _crop(_select(green - red, "largest"))


def _grid_hash(value: list[list[int]]) -> str:
    raw = json.dumps(value, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def teaching_certificate(train: Any, query_inputs: Any) -> dict[str, Any]:
    if type(train) is not list or not 2 <= len(train) <= 6:
        raise ValueError("two through six demonstrations are required")
    if type(query_inputs) is not list or not 1 <= len(query_inputs) <= 4:
        raise ValueError("one through four query inputs are required")
    for pair in train:
        if type(pair) is not dict or set(pair) != {"input", "output"}:
            raise ValueError("each demonstration must contain input and output")
        observe(pair["input"])
    for value in query_inputs:
        observe(value)
    survivors = [
        name
        for name in HYPOTHESES
        if all(predict(pair["input"], name) == pair["output"] for pair in train)
    ]
    return {
        "declared_hypotheses": list(HYPOTHESES),
        "survivors": survivors,
        "demos": len(train),
        "queries": len(query_inputs),
        "operations": [observe(pair["input"])["operation"] for pair in train],
        "predicted_query_sha256": {
            name: [_grid_hash(predict(value, name)) for value in query_inputs]
            for name in survivors
        },
        "scope": "Finite declared rivals only; no universal uniqueness claim.",
    }


def _transform(cells: Iterable[tuple[int, int]], name: str) -> frozenset[tuple[int, int]]:
    cells = _normalize(cells)
    if name == "identity":
        return cells
    max_row = max(row for row, _ in cells)
    max_col = max(col for _, col in cells)
    if name == "rotate_cw":
        mapped = {(col, max_row - row) for row, col in cells}
    elif name == "rotate_180":
        mapped = {(max_row - row, max_col - col) for row, col in cells}
    elif name == "flip_lr":
        mapped = {(row, max_col - col) for row, col in cells}
    elif name == "flip_ud":
        mapped = {(max_row - row, col) for row, col in cells}
    else:
        raise ValueError(f"unknown transform: {name}")
    return _normalize(mapped)


_AND_SMALL = frozenset({(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)})
_AND_LARGE = frozenset({(4, 6), (4, 7), (4, 8), (5, 6), (5, 7), (5, 8)})
_AND_RED = _AND_SMALL | _AND_LARGE | frozenset({(3, 2), (3, 3), (3, 4), (3, 5), (4, 5)})
_AND_GREEN = _AND_SMALL | _AND_LARGE | frozenset({
    (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (1, 6), (2, 6), (3, 6)
})
_XOR_SHARED = frozenset({
    (0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (2, 2)
})
_XOR_RED_ONLY = frozenset({(1, 1), (2, 1), (3, 1), (3, 0), (4, 0), (4, 1)})
_XOR_GREEN_ONLY = frozenset({(1, 4), (2, 4), (3, 4), (4, 4)})
_XOR_RED = _XOR_SHARED | _XOR_RED_ONLY
_XOR_GREEN = _XOR_SHARED | _XOR_GREEN_ONLY


def _stress_shapes() -> tuple[frozenset[tuple[int, int]], frozenset[tuple[int, int]]]:
    shared = frozenset({(0, col) for col in range(12)} | {(row, 6) for row in range(1, 12)})
    red_only = frozenset({(row, col) for row in range(2, 11) for col in range(5)} | {(2, 5)})
    green_main = frozenset({(row, col) for row in range(4, 10) for col in range(7, 12)})
    green_small = frozenset({(1, 10), (1, 11), (2, 10), (2, 11)})
    return shared | red_only, shared | green_main | green_small


def _profile(red, green, marker, height, width, transform="identity", placement="opposite"):
    return {
        "red": _transform(red, transform),
        "green": _transform(green, transform),
        "marker": marker,
        "height": height,
        "width": width,
        "placement": placement,
    }


_STRESS_RED, _STRESS_GREEN = _stress_shapes()
_DEMO_PROFILES = (
    _profile(_AND_RED, _AND_GREEN, 1, 16, 22),
    _profile(_XOR_RED, _XOR_GREEN, 0, 14, 16),
    _profile(_AND_RED, _AND_GREEN, 1, 20, 18, "rotate_cw"),
    _profile(_XOR_RED, _XOR_GREEN, 0, 13, 18, "flip_lr"),
    _profile(_AND_RED, _AND_GREEN, 1, 17, 23, "rotate_180"),
    _profile(_XOR_RED, _XOR_GREEN, 0, 16, 19, "rotate_cw"),
)
_QUERY_PROFILES = (
    _profile(_AND_RED, _AND_GREEN, 1, 18, 24, "flip_ud"),
    _profile(_XOR_RED, _XOR_GREEN, 0, 13, 17, "rotate_180"),
    _profile(_AND_RED, _AND_GREEN, 1, 14, 20, "flip_lr", "edges"),
    _profile(_STRESS_RED, _STRESS_GREEN, 0, 30, 30, "identity", "edges"),
)


def _size(cells: frozenset[tuple[int, int]]) -> tuple[int, int]:
    return max(row for row, _ in cells) + 1, max(col for _, col in cells) + 1


def _anchors(profile: dict[str, Any], rng: random.Random) -> tuple[tuple[int, int], tuple[int, int]]:
    height, width = profile["height"], profile["width"]
    red_h, red_w = _size(profile["red"])
    green_h, green_w = _size(profile["green"])
    corners = (
        ((0, 0), (height - green_h, width - green_w)),
        ((0, width - red_w), (height - green_h, 0)),
        ((height - red_h, 0), (0, width - green_w)),
        ((height - red_h, width - red_w), (0, 0)),
    )
    if profile["placement"] == "edges":
        return corners[0]
    red_anchor, green_anchor = corners[rng.randrange(len(corners))]
    # Pull non-edge ordinary scenes inward by one cell where the canvas permits.
    def inset(anchor, shape_h, shape_w):
        row, col = anchor
        if row == 0 and height - shape_h >= 2:
            row = 1
        elif row > 0 and row >= 2:
            row -= 1
        if col == 0 and width - shape_w >= 2:
            col = 1
        elif col > 0 and col >= 2:
            col -= 1
        return row, col
    return inset(red_anchor, red_h, red_w), inset(green_anchor, green_h, green_w)


def _scene(seed: int, index: int, profile: dict[str, Any]) -> list[list[int]]:
    digest = hashlib.sha256(
        f"c5a80b7a3acc-largest-component-v1:{seed}:{index}".encode("ascii")
    ).digest()
    rng = random.Random(digest)
    height, width = profile["height"], profile["width"]
    grid = [[0] * width for _ in range(height)]
    red_anchor, green_anchor = _anchors(profile, rng)
    for cells, (top, left), color in (
        (profile["red"], red_anchor, 2),
        (profile["green"], green_anchor, 3),
    ):
        for row, col in cells:
            if grid[top + row][left + col] != 0:
                raise AssertionError("source placements overlap")
            grid[top + row][left + col] = color
    free = [(row, col) for row in range(height) for col in range(width) if grid[row][col] == 0]
    rng.shuffle(free)
    if profile["marker"]:
        row, col = free.pop()
        grid[row][col] = 7
    row, col = free.pop()
    grid[row][col] = 9
    state = observe(grid)
    if state["result_component_sizes"][0] <= state["result_component_sizes"][1]:
        raise AssertionError("profile must have a unique largest Stage-A component")
    return grid


@lru_cache(maxsize=128)
def _all_inputs(seed: int) -> tuple[tuple[list[list[int]], ...], tuple[list[list[int]], ...]]:
    demos = tuple(_scene(seed, index, profile) for index, profile in enumerate(_DEMO_PROFILES))
    queries = tuple(
        _scene(seed, 100 + index, profile) for index, profile in enumerate(_QUERY_PROFILES)
    )
    visible = [json.dumps(value, separators=(",", ":")) for value in demos + queries]
    if len(visible) != len(set(visible)):
        raise AssertionError("profile bank produced duplicate visible inputs")
    return demos, queries


def _pair(value: list[list[int]], policy: str) -> dict[str, list[list[int]]]:
    return {"input": [row[:] for row in value], "output": predict(value, policy)}


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _exact_int(seed, "seed", 0, 2**63 - 1)
    demos = _exact_int(demos, "demos", 2, 6)
    queries = _exact_int(queries, "queries", 1, 4)
    selected = _settings(settings)
    demo_bank, query_bank = _all_inputs(seed)
    train_inputs = list(demo_bank[:demos])
    all_query_inputs = list(query_bank)

    # Validate the same visible curriculum for both settings.  This makes input
    # generation setting-neutral and checks the two-demo prefix before any job
    # is exposed to the native worker.
    for policy in RESULT_POLICIES:
        train = [_pair(value, policy) for value in train_inputs]
        proof = teaching_certificate(train, all_query_inputs)
        if proof["survivors"] != [policy]:
            raise AssertionError(
                f"teaching prefix does not uniquely identify {policy}: {proof['survivors']}"
            )

    return {
        "train": [_pair(value, selected) for value in train_inputs],
        "test": [_pair(value, selected) for value in all_query_inputs[:queries]],
        "program_solution": program(settings),
    }
