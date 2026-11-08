"""Native whole-pattern / largest-component family for 5c126cb64bf7.

Inputs are setting-neutral.  ``whole`` is the exact selected canonical rule.
``largest_component`` first extracts each panel's unique largest 4-connected
component (Step A), then compares those three normalized intermediates under
quarter turns to build the relation matrix (Step B).
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
SCOPES = ("whole", "largest_component")
PROGRAMS = {
    "whole": HERE / "canonical.rkt",
    "largest_component": HERE / "largest_component.rkt",
}
STARTS = (0, 6, 12)
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
PALETTE = (1, 2, 3, 4, 5, 6, 7, 8, 9)


def _norm(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    r0 = min(row for row, _ in cells)
    c0 = min(column for _, column in cells)
    return tuple(sorted((row - r0, column - c0) for row, column in cells))


def _rotate(cells: Iterable[tuple[int, int]], turns: int = 1) -> tuple[tuple[int, int], ...]:
    result = _norm(cells)
    for _ in range(turns % 4):
        result = _norm((column, -row) for row, column in result)
    return result


def _mirror(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _norm((row, -column) for row, column in cells)


def _orbit(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return min(_rotate(cells, turns) for turns in range(4))


def _components(cells: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    remaining = set(cells)
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        component = []
        while stack:
            row, column = stack.pop()
            component.append((row, column))
            for dr, dc in CARDINAL:
                neighbor = (row + dr, column + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        result.append(tuple(sorted(component)))
    return tuple(sorted(result, key=lambda part: (-len(part), part)))


def _panels(grid: list[list[int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    return tuple(
        tuple(
            (row, column)
            for row, line in enumerate(grid)
            for column, value in enumerate(line[start:start + 5])
            if value != 0
        )
        for start in STARTS
    )


def _relation(keys: list[Any]) -> list[list[int]]:
    return [
        [8 if i == j else 2 if keys[i] == keys[j] else 0 for j in range(3)]
        for i in range(3)
    ]


def whole_output(grid: list[list[int]]) -> list[list[int]]:
    return _relation([_orbit(panel) for panel in _panels(grid)])


def largest_intermediate(grid: list[list[int]]) -> list[list[list[int]]]:
    """Return normalized largest-component cell lists for causal evidence."""
    result = []
    for panel in _panels(grid):
        components = _components(panel)
        if not components:
            raise ValueError("every panel must contain foreground content")
        if len(components) > 1 and len(components[0]) == len(components[1]):
            raise ValueError("largest component must be unique")
        result.append([list(cell) for cell in _norm(components[0])])
    return result


def largest_output(grid: list[list[int]]) -> list[list[int]]:
    keys = [_orbit(tuple(tuple(cell) for cell in component))
            for component in largest_intermediate(grid)]
    return _relation(keys)


# Teaching shapes.  X0/X1 share a chiral L core but differ as whole patterns;
# X2 is X0's reflection.  Thus demo 2 yields whole=all-distinct,
# largest=pair(0,1), reflection-rival=pair(0,2), count-rival=pair(0,2).
A0 = ((0, 0), (0, 1), (0, 2), (0, 4), (1, 1))
A1 = ((0, 0), (0, 1), (0, 2), (1, 1), (1, 4))
SQUARE = ((0, 0), (0, 1), (0, 3), (1, 0), (1, 1))
LINE0 = ((0, 0), (0, 1), (0, 2), (1, 4))
LINE1 = ((0, 0), (0, 1), (0, 2), (2, 4))
PLUS = ((0, 0), (0, 3), (1, 2), (1, 3), (1, 4), (2, 3))
LCORE = ((0, 0), (1, 0), (2, 0), (2, 1))
X0 = LCORE + ((0, 4),)
X1 = LCORE + ((0, 4), (2, 4))
X2 = _mirror(X0)

STRESS_T = ((14, 0), (14, 1), (14, 2), (15, 1))
STRESS_SQUARE = ((14, 1), (14, 2), (15, 1), (15, 2))
STRESS_S0 = STRESS_T + ((0, 4), (5, 0), (10, 4), (20, 0), (29, 4))
STRESS_S1 = STRESS_T + ((0, 0), (6, 4), (11, 0), (22, 4), (29, 0))
STRESS_S2 = STRESS_SQUARE + ((0, 4), (5, 0), (10, 4), (20, 0), (29, 4))

# (height, shapes, color relation).  Dimensions are intentionally unique across
# the ten fixed slots, making accidental duplicate inputs impossible.
DEMO_PROFILES = (
    (5, (A0, _rotate(A0, 1), _rotate(A0, 2)), "distinct"),
    (6, (X0, X1, X2), "same"),
    (7, (A0, _rotate(A0, 1), A1), "pair01"),
    (8, (SQUARE, A0, A1), "pair12"),
    (9, (LINE0, SQUARE, _rotate(LINE0, 2)), "pair02"),
    (10, (PLUS, _rotate(PLUS, 1), _rotate(PLUS, 3)), "same"),
)
QUERY_PROFILES = (
    (11, (X0, X1, X2), "pair01"),
    (12, (A0, _rotate(A0, 1), A1), "distinct"),
    (13, (LINE0, LINE1, PLUS), "same"),
    (30, (STRESS_S0, STRESS_S1, STRESS_S2), "pair02"),
)


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def _scope(settings: Any) -> str:
    if (type(settings) is not dict or set(settings) != {"pattern_scope"}
            or type(settings["pattern_scope"]) is not str
            or settings["pattern_scope"] not in SCOPES):
        raise ValueError("settings must contain exactly one supported pattern_scope")
    return settings["pattern_scope"]


def program(settings: Any) -> str:
    return PROGRAMS[_scope(settings)].read_text(encoding="utf-8")


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(
        f"5c126cb64bf7-parametric-v1|{seed}|{split}|{index}".encode()
    ).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _color_tuple(rng: random.Random, relation: str) -> tuple[int, int, int]:
    values = list(PALETTE)
    rng.shuffle(values)
    a, b, c = values[:3]
    choices = {
        "same": (a, a, a),
        "distinct": (a, b, c),
        "pair01": (a, a, b),
        "pair02": (a, b, a),
        "pair12": (a, b, b),
    }
    return choices[relation]


def _fit_rotations(shape: tuple[tuple[int, int], ...], height: int):
    result = []
    for turns in range(4):
        rotated = _rotate(shape, turns)
        shape_h = max(row for row, _ in rotated) + 1
        shape_w = max(column for _, column in rotated) + 1
        if shape_h <= height and shape_w <= 5:
            result.append((rotated, shape_h, shape_w))
    return result


def _build_input(seed: int, split: str, index: int, profile) -> list[list[int]]:
    height, shapes, color_relation = profile
    rng = _rng(seed, split, index)
    grid = [[0] * 17 for _ in range(height)]
    colors = _color_tuple(rng, color_relation)
    for panel_index, (shape, color) in enumerate(zip(shapes, colors)):
        choices = _fit_rotations(shape, height)
        if not choices:
            raise RuntimeError("profile shape does not fit its panel")
        rotated, shape_h, shape_w = rng.choice(choices)
        row_offset = rng.randrange(height - shape_h + 1)
        column_offset = rng.randrange(5 - shape_w + 1)
        start = STARTS[panel_index]
        for row, column in rotated:
            target = (row + row_offset, start + column + column_offset)
            if grid[target[0]][target[1]] != 0:
                raise RuntimeError("profile contains overlapping cells")
            grid[target[0]][target[1]] = color

    panels = _panels(grid)
    for panel in panels:
        parts = _components(panel)
        if not parts or (len(parts) > 1 and len(parts[0]) == len(parts[1])):
            raise RuntimeError("constructed panel lacks a unique largest component")
    return grid


def _pair(grid: list[list[int]], scope: str) -> dict[str, Any]:
    output = whole_output(grid) if scope == "whole" else largest_output(grid)
    return {"input": deepcopy(grid), "output": output}


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 2, 6)
    queries = _integer("queries", queries, 1, 4)
    scope = _scope(settings)
    demo_inputs = [
        _build_input(seed, "train", index, profile)
        for index, profile in enumerate(DEMO_PROFILES[:demos])
    ]
    query_bank = [
        _build_input(seed, "test", index, profile)
        for index, profile in enumerate(QUERY_PROFILES)
    ]
    selected_queries = query_bank[:queries]
    all_inputs = demo_inputs + selected_queries
    if len({repr(grid) for grid in all_inputs}) != len(all_inputs):
        raise RuntimeError("episode inputs must be distinct")
    return {
        "train": [_pair(grid, scope) for grid in demo_inputs],
        "test": [_pair(grid, scope) for grid in selected_queries],
        "program_solution": program(settings),
        "seed": seed,
        "settings": deepcopy(settings),
    }


def public_turn(episode: Any, query_index: Any) -> dict[str, Any]:
    query_index = _integer("query_index", query_index, 0, 3)
    if (type(episode) is not dict or type(episode.get("train")) is not list
            or type(episode.get("test")) is not list
            or query_index >= len(episode["test"])):
        raise ValueError("episode does not contain the requested query")
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }
