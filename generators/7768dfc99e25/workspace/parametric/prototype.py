"""Episode-fixed target-color variants for 7768dfc99e25.

The canonical rule crops the unique border-touching color-2 component.  The
alternate setting applies the same object, border, and bounding-box reasoning
to color 3.  Inputs are setting-neutral: every scene has one border component
and at least one interior distractor of each candidate color.
"""
from __future__ import annotations

from copy import deepcopy
import random
from typing import Any, Iterable, Sequence

TASK_ID = "7768dfc99e25"
SETTINGS = ({"target_color": 2}, {"target_color": 3})
DEFAULT = {"target_color": 2}
DEMO_PROFILES = ((9, 10), (10, 12), (12, 10), (14, 15), (16, 18), (20, 16))
QUERY_PROFILES = ((12, 14), (18, 20), (24, 24), (30, 30), (20, 28), (28, 20), (26, 30), (30, 26))

CANONICAL_PROGRAM = "(rule! (let ((dummy 0)) (define (crop-bbox grid cells) (let* ((bb (bbox-of-cells cells)) (r0 (first bb)) (c0 (second bb)) (r1 (third bb)) (c1 (fourth bb))) (subgrid grid r0 c0 r1 c1))) (let* ((comps (filter (lambda (obj) (= (obj-color obj) 2)) (objects g 0))) (comp (first (filter (lambda (obj) (any? (lambda (p) (or (= (first p) 0) (= (first p) (- (rows g) 1)) (= (second p) 0) (= (second p) (- (cols g) 1)))) (obj-cells obj))) comps)))) (crop-bbox g (obj-cells comp)))))"
COLOR_THREE_PROGRAM = "(rule! (let ((dummy 0)) (define (crop-bbox grid cells) (let* ((bb (bbox-of-cells cells)) (r0 (first bb)) (c0 (second bb)) (r1 (third bb)) (c1 (fourth bb))) (subgrid grid r0 c0 r1 c1))) (let* ((comps (filter (lambda (obj) (= (obj-color obj) 3)) (objects g 0))) (comp (first (filter (lambda (obj) (any? (lambda (p) (or (= (first p) 0) (= (first p) (- (rows g) 1)) (= (second p) 0) (= (second p) (- (cols g) 1)))) (obj-cells obj))) comps)))) (crop-bbox g (obj-cells comp)))))"

_BORDER_TWO = ((0, 0), (1, 0), (1, 1), (2, 0))
_BORDER_THREE = ((0, 1), (1, 1), (2, 1), (2, 0))
_INTERIOR_TWO = ((0, 0), (0, 1), (1, 1))
_INTERIOR_THREE = ((0, 0), (1, 0), (1, 1))
_LEFT_MARKER = ((0, 0), (1, 0), (1, 1))
_RIGHT_MARKER = ((0, 0), (1, 0), (2, 0))


def _integer(value: Any, lo: int, hi: int, name: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")
    return value


def _settings(value: Any) -> dict[str, int]:
    if not isinstance(value, dict) or set(value) != {"target_color"}:
        raise ValueError("settings must contain exactly target_color")
    color = value["target_color"]
    if type(color) is not int:
        raise TypeError("target_color must be an integer (not bool)")
    if color not in (2, 3):
        raise ValueError("target_color must be 2 or 3")
    return {"target_color": color}


def program(settings: Any) -> str:
    chosen = _settings(settings)
    return CANONICAL_PROGRAM if chosen["target_color"] == 2 else COLOR_THREE_PROGRAM


def _rectangular(grid: Sequence[Sequence[int]]) -> tuple[int, int]:
    if not isinstance(grid, Sequence) or isinstance(grid, (str, bytes)) or not grid:
        raise ValueError("grid must be a non-empty rectangular sequence")
    if not isinstance(grid[0], Sequence) or isinstance(grid[0], (str, bytes)) or not grid[0]:
        raise ValueError("grid must be a non-empty rectangular sequence")
    width = len(grid[0])
    if any(
        not isinstance(row, Sequence)
        or isinstance(row, (str, bytes))
        or len(row) != width
        for row in grid
    ):
        raise ValueError("grid must be rectangular")
    return len(grid), width


def _components(grid: Sequence[Sequence[int]], color: int) -> list[set[tuple[int, int]]]:
    height, width = _rectangular(grid)
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == color}
    components: list[set[tuple[int, int]]] = []
    while unseen:
        seed = unseen.pop()
        component = {seed}
        stack = [seed]
        while stack:
            row, col = stack.pop()
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return components


def transform(grid: Sequence[Sequence[int]], settings: Any) -> list[list[int]]:
    color = _settings(settings)["target_color"]
    height, width = _rectangular(grid)
    components = _components(grid, color)
    border = [
        component
        for component in components
        if any(r == 0 or r == height - 1 or c == 0 or c == width - 1 for r, c in component)
    ]
    interior = [component for component in components if component not in border]
    if len(border) != 1 or not interior:
        raise ValueError(
            f"color {color} must have exactly one border-touching component and at least one interior component"
        )
    cells = border[0]
    row0, row1 = min(r for r, _ in cells), max(r for r, _ in cells)
    col0, col1 = min(c for _, c in cells), max(c for _, c in cells)
    return [[int(grid[r][c]) for c in range(col0, col1 + 1)] for r in range(row0, row1 + 1)]


def _translated(shape: Sequence[tuple[int, int]], row0: int, col0: int) -> set[tuple[int, int]]:
    return {(row0 + dr, col0 + dc) for dr, dc in shape}


def _place(
    grid: list[list[int]],
    shape: Sequence[tuple[int, int]],
    candidates: list[tuple[int, int]],
    color: int,
    rng: random.Random,
    *,
    separate_from_same_color: bool = False,
) -> set[tuple[int, int]]:
    height, width = len(grid), len(grid[0])
    order = list(candidates)
    rng.shuffle(order)
    for row0, col0 in order:
        cells = _translated(shape, row0, col0)
        if any(not (0 <= row < height and 0 <= col < width) for row, col in cells):
            continue
        if any(grid[row][col] != 0 for row, col in cells):
            continue
        if separate_from_same_color:
            neighbors = {
                (row + dr, col + dc)
                for row, col in cells
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            } - cells
            if any(0 <= row < height and 0 <= col < width and grid[row][col] == color for row, col in neighbors):
                continue
        for row, col in cells:
            grid[row][col] = color
        return cells
    raise RuntimeError(f"could not place color {color} shape in {height}x{width}")


def _scene(seed: int, role: str, index: int, shape: tuple[int, int]) -> list[list[int]]:
    height, width = shape
    if height < 9 or width < 10:
        raise ValueError("target-color scenes require dimensions at least 9x10")
    rng = random.Random(f"{TASK_ID}:{seed}:{role}:{index}")
    grid = [[0] * width for _ in range(height)]

    top_candidates = [(0, col) for col in range(1, max(2, width // 3))]
    bottom_candidates = [
        (height - 3, col)
        for col in range(max(width // 2, 1), width - 2)
    ]
    _place(grid, _BORDER_TWO, top_candidates, 2, rng)
    _place(grid, _BORDER_THREE, bottom_candidates, 3, rng)

    interior_two = [
        (row, col)
        for row in range(3, height - 2)
        for col in range(1, max(2, width // 2 - 1))
    ]
    interior_three = [
        (row, col)
        for row in range(1, height - 2)
        for col in range(max(width // 2, 2), width - 2)
    ]
    _place(grid, _INTERIOR_TWO, interior_two, 2, rng, separate_from_same_color=True)
    _place(grid, _INTERIOR_THREE, interior_three, 3, rng, separate_from_same_color=True)

    left_candidates = [(row, 0) for row in range(1, height - 2)]
    right_candidates = [(row, width - 1) for row in range(0, height - 2)]
    _place(grid, _LEFT_MARKER, left_candidates, 1, rng)
    _place(grid, _RIGHT_MARKER, right_candidates, 4, rng)

    for color in (2, 3):
        components = _components(grid, color)
        border_count = sum(
            any(r == 0 or r == height - 1 or c == 0 or c == width - 1 for r, c in component)
            for component in components
        )
        if len(components) < 2 or border_count != 1:
            raise RuntimeError(f"constructive scene violated color-{color} object grammar")
    return grid


def _pair(grid: list[list[int]], settings: dict[str, int]) -> dict[str, Any]:
    return {"input": deepcopy(grid), "output": transform(grid, settings)}


def fit_settings(demos: Iterable[dict[str, Any]]) -> list[dict[str, int]]:
    pairs = list(demos)
    survivors: list[dict[str, int]] = []
    for candidate in SETTINGS:
        try:
            if all(
                isinstance(pair, dict)
                and pair.get("output") == transform(pair.get("input"), candidate)
                for pair in pairs
            ):
                survivors.append(dict(candidate))
        except (TypeError, ValueError):
            continue
    return survivors


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 8, "queries")
    chosen = _settings(settings)
    train = [
        _pair(_scene(seed, "demo", index, DEMO_PROFILES[index]), chosen)
        for index in range(demos)
    ]
    test = [
        _pair(_scene(seed, "query", index, QUERY_PROFILES[index]), chosen)
        for index in range(queries)
    ]
    if fit_settings(train) != [chosen]:
        raise RuntimeError("demonstrations do not uniquely identify target_color")
    serial = [repr(pair["input"]) for pair in train + test]
    if len(serial) != len(set(serial)):
        raise RuntimeError("episode contains duplicate inputs")
    return {
        "train": train,
        "test": test,
        "settings": chosen,
        "seed": seed,
        "program_solution": program(chosen),
        "certificate": {
            "finite_rivals": [dict(setting) for setting in SETTINGS],
            "survivors": fit_settings(train),
            "racket_checked": False,
        },
    }
