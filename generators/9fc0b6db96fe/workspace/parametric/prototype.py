"""Native gallery family with an input-derived transform alternative.

The canonical setting reads the explicit key at (0,0).  The alternate first
identifies the component named by the first legend entry, measures its occupied
cell count, maps 3/4/5 cells to clockwise/half-turn/left-right, and then applies
that derived transform to every legend-ordered crop.  Thus the transform stage
consumes an input-dependent component measurement rather than a cosmetic flag.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "9fc0b6db96fe"
HERE = Path(__file__).resolve().parent
MODES = ("explicit_key", "first_component_size")
DEFAULT_MODE = "explicit_key"
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)
_SIZE_TO_KEY = {3: 2, 4: 3, 5: 4}
_DIMS = (
    (12, 16), (14, 18), (16, 20), (18, 22), (20, 24), (22, 26),
    (13, 19), (17, 23), (24, 28), (30, 30),
)
_EXPLICIT_KEYS = (1, 3, 4, 1, 2, 4, 3, 1, 2, 3)
_FIRST_SIZES = (3, 5, 4, 3, 5, 4, 5, 3, 4, 5)
_BASE_SHAPES = {
    3: ((0, 0), (1, 0), (1, 1)),
    4: ((0, 0), (1, 0), (2, 0), (2, 1)),
    5: ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
}
_RIVAL_NAMES = (
    "other_setting",
    "last_component_size",
    "smallest_component_size",
    "largest_component_size",
    "constant_key_1",
    "constant_key_2",
    "constant_key_3",
    "constant_key_4",
    "body_scan_order",
)


def _text(name: str) -> str:
    return (HERE / name).read_text(encoding="utf-8")


def _mode(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {"transform_source"}:
        raise ValueError("settings must contain exactly transform_source")
    value = settings["transform_source"]
    if type(value) is not str or value not in MODES:
        raise ValueError(f"transform_source must be one of {MODES}")
    return value


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program(settings: object) -> str:
    return _text("canonical.rkt" if _mode(settings) == DEFAULT_MODE else "first-component-size.rkt")


def _neighbors4(row: int, col: int) -> Iterable[tuple[int, int]]:
    yield row - 1, col
    yield row + 1, col
    yield row, col - 1
    yield row, col + 1


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    values = tuple(cells)
    r0 = min(r for r, _ in values)
    c0 = min(c for _, c in values)
    return tuple(sorted((r - r0, c - c0) for r, c in values))


def _orient(cells: Iterable[tuple[int, int]], code: int) -> tuple[tuple[int, int], ...]:
    def xf(r: int, c: int) -> tuple[int, int]:
        if code == 0: return r, c
        if code == 1: return c, -r
        if code == 2: return -r, -c
        if code == 3: return -c, r
        if code == 4: return r, -c
        if code == 5: return -r, c
        if code == 6: return c, r
        return -c, -r
    return _normalize(xf(r, c) for r, c in cells)


def _components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    result: list[list[tuple[int, int]]] = []
    while remaining:
        seed = min(remaining)
        remaining.remove(seed)
        stack = [seed]
        cells: list[tuple[int, int]] = []
        while stack:
            cell = stack.pop()
            cells.append(cell)
            for nb in _neighbors4(*cell):
                if nb in remaining:
                    remaining.remove(nb)
                    stack.append(nb)
        result.append(sorted(cells))
    return result


def _facts(grid: list[list[int]]) -> dict[str, Any]:
    height, width = validate_grid(grid)
    legend = [value for value in grid[0][1:] if value != 0]
    body = [row[:] for row in grid[2:]]
    by_color: dict[int, list[tuple[int, int]]] = {}
    for color in legend:
        by_color[color] = [(r, c) for r, row in enumerate(body) for c, value in enumerate(row) if value == color]
    return {
        "height": height,
        "width": width,
        "explicit_key": grid[0][0],
        "legend": legend,
        "body": body,
        "cells": by_color,
        "sizes": [len(by_color[color]) for color in legend],
    }


def validate_grid(grid: object) -> tuple[int, int]:
    if type(grid) is not list or not 10 <= len(grid) <= 30:
        raise ValueError("grid height must be 10..30")
    if not grid or type(grid[0]) is not list or not 12 <= len(grid[0]) <= 30:
        raise ValueError("grid width must be 12..30")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    if grid[0][0] not in (1, 2, 3, 4):
        raise ValueError("(0,0) must be a transform key 1..4")
    if any(grid[1]):
        raise ValueError("row 1 must be blank")
    legend = [value for value in grid[0][1:] if value]
    if len(legend) not in (3, 4) or len(set(legend)) != len(legend):
        raise ValueError("legend must contain three or four distinct colors")
    if grid[0][0] in legend:
        raise ValueError("key color must be separate from legend colors")
    body = grid[2:]
    body_palette = {value for row in body for value in row if value}
    if body_palette != set(legend):
        raise ValueError("body colors must match the legend exactly")
    comps = _components(body)
    if len(comps) != len(legend):
        raise ValueError("body must have one separated nonzero component per legend color")
    for comp in comps:
        colors = {body[r][c] for r, c in comp}
        if len(colors) != 1:
            raise ValueError("different colors may not touch orthogonally")
        if not 3 <= len(comp) <= 5:
            raise ValueError("each component must contain 3..5 cells")
    for color in legend:
        owned = [comp for comp in comps if body[comp[0][0]][comp[0][1]] == color]
        if len(owned) != 1:
            raise ValueError("each legend color must own exactly one component")
    return len(grid), width


def _crop(body: list[list[int]], cells: list[tuple[int, int]]) -> list[list[int]]:
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    cell_set = set(cells)
    return [
        [body[r][c] if (r, c) in cell_set else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]


def _transform(grid: list[list[int]], key: int) -> list[list[int]]:
    if key == 1:
        return [row[:] for row in grid]
    if key == 2:
        return [list(row) for row in zip(*grid[::-1])]
    if key == 3:
        return [list(reversed(row)) for row in reversed(grid)]
    if key == 4:
        return [list(reversed(row)) for row in grid]
    raise ValueError("transform key must be 1..4")


def _pack(parts: list[list[list[int]]]) -> list[list[int]]:
    height = max(len(part) for part in parts)
    width = sum(len(part[0]) for part in parts) + len(parts) - 1
    out = [[0 for _ in range(width)] for _ in range(height)]
    left = 0
    for part in parts:
        for r, row in enumerate(part):
            for c, value in enumerate(row):
                if value:
                    out[r][left + c] = value
        left += len(part[0]) + 1
    return out


def _key_from_sizes(sizes: list[int], policy: str) -> int:
    if policy == "first": return _SIZE_TO_KEY[sizes[0]]
    if policy == "last": return _SIZE_TO_KEY[sizes[-1]]
    if policy == "smallest": return _SIZE_TO_KEY[min(sizes)]
    if policy == "largest": return _SIZE_TO_KEY[max(sizes)]
    raise ValueError(policy)


def _apply_with_key_and_order(grid: list[list[int]], key: int, order: str = "legend") -> list[list[int]]:
    facts = _facts(grid)
    legend = facts["legend"]
    if order == "scan":
        legend = [
            facts["body"][comp[0][0]][comp[0][1]]
            for comp in _components(facts["body"])
        ]
    parts = [_transform(_crop(facts["body"], facts["cells"][color]), key) for color in legend]
    return _pack(parts)


def apply_python(grid: list[list[int]], mode: str) -> list[list[int]]:
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}")
    facts = _facts(grid)
    key = facts["explicit_key"] if mode == "explicit_key" else _key_from_sizes(facts["sizes"], "first")
    return _apply_with_key_and_order(grid, key)


def _rng(seed: int, index: int, label: str) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|{seed}|{index}|{label}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _size_pattern(index: int, count: int) -> list[int]:
    first = _FIRST_SIZES[index]
    rest = {
        3: [5, 4, 5],
        4: [5, 3, 5],
        5: [3, 4, 3],
    }[first]
    values = [first] + rest[: count - 1]
    if index == 9:
        values = [5, 4, 5, 5]
    return values


def _origins(height: int, width: int, shapes: list[tuple[tuple[int, int], ...]]) -> list[tuple[int, int]]:
    # Legend order is deliberately not row-major: the first color is top-right,
    # the second top-left, and the remaining colors occupy the lower corners.
    corners = ("tr", "tl", "br", "bl") if len(shapes) == 4 else ("tr", "bl", "tl")
    result: list[tuple[int, int]] = []
    for shape, corner in zip(shapes, corners, strict=True):
        box_h = max(r for r, _ in shape) + 1
        box_w = max(c for _, c in shape) + 1
        row = 2 if corner[0] == "t" else height - box_h
        col = 0 if corner[1] == "l" else width - box_w
        result.append((row, col))
    return result


def make_input(seed: int, index: int) -> list[list[int]]:
    height, width = _DIMS[index]
    count = 4 if index not in (2, 6) else 3
    key = _EXPLICIT_KEYS[index]
    rng = _rng(seed, index, "scene")
    colors = rng.sample([value for value in range(1, 10) if value != key], count)
    sizes = _size_pattern(index, count)
    shapes = [_orient(_BASE_SHAPES[size], rng.randrange(8)) for size in sizes]
    origins = _origins(height, width, shapes)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    grid[0][0] = key
    layouts = ((1, 2, 3, 4), (1, 3, 5, 7), (1, 2, 4, 6))
    positions = layouts[index % len(layouts)]
    for color, col in zip(colors, positions, strict=False):
        grid[0][col] = color
    for legend_index, (row0, col0) in enumerate(origins):
        for dr, dc in shapes[legend_index]:
            grid[row0 + dr][col0 + dc] = colors[legend_index]
    validate_grid(grid)
    return grid


def _pair(seed: int, index: int, mode: str) -> dict[str, list[list[int]]]:
    grid = make_input(seed, index)
    return {"input": grid, "output": apply_python(grid, mode)}


def generate(seed: object, settings: object, demos: object = 3, queries: object = 4) -> dict[str, Any]:
    seed_i = _integer(seed, 0, 2**63 - 1, "seed")
    demos_i = _integer(demos, *DEMO_LIMITS, "demos")
    queries_i = _integer(queries, *QUERY_LIMITS, "queries")
    mode = _mode(settings)
    train = [_pair(seed_i, index, mode) for index in range(demos_i)]
    test = [_pair(seed_i, 6 + index, mode) for index in range(queries_i)]
    episode = {
        "train": train,
        "test": test,
        "program_solution": program({"transform_source": mode}),
        "meta": {"transform_source": mode, "seed": seed_i},
    }
    return deepcopy(episode)


def rival_output(grid: list[list[int]], name: str, chosen_mode: str) -> list[list[int]]:
    facts = _facts(grid)
    if name == "other_setting":
        other = next(mode for mode in MODES if mode != chosen_mode)
        return apply_python(grid, other)
    if name == "last_component_size":
        return _apply_with_key_and_order(grid, _key_from_sizes(facts["sizes"], "last"))
    if name == "smallest_component_size":
        return _apply_with_key_and_order(grid, _key_from_sizes(facts["sizes"], "smallest"))
    if name == "largest_component_size":
        return _apply_with_key_and_order(grid, _key_from_sizes(facts["sizes"], "largest"))
    if name.startswith("constant_key_"):
        return _apply_with_key_and_order(grid, int(name.rsplit("_", 1)[1]))
    if name == "body_scan_order":
        key = facts["explicit_key"] if chosen_mode == "explicit_key" else _key_from_sizes(facts["sizes"], "first")
        return _apply_with_key_and_order(grid, key, "scan")
    raise ValueError(name)


def teaching_report(episode: dict[str, Any], chosen_mode: str) -> dict[str, Any]:
    if chosen_mode not in MODES:
        raise ValueError(chosen_mode)
    survivors = []
    rows = []
    for name in _RIVAL_NAMES:
        mismatches = [
            index
            for index, pair in enumerate(episode["train"])
            if rival_output(pair["input"], name, chosen_mode) != pair["output"]
        ]
        query_disagrees = any(
            rival_output(pair["input"], name, chosen_mode) != pair["output"]
            for pair in episode["test"]
        )
        if not mismatches and query_disagrees:
            survivors.append(name)
        rows.append({"name": name, "demonstration_mismatches": mismatches, "query_disagrees": query_disagrees})
    return {"mode": chosen_mode, "rivals": rows, "surviving_harmful_rivals": survivors}


def public_turn(episode: dict[str, Any], query_index: object) -> dict[str, Any]:
    index = _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][index]["input"])}],
    }


def public_bytes(episode: dict[str, Any], query_index: int) -> bytes:
    return json.dumps(public_turn(episode, query_index), sort_keys=True, separators=(",", ":")).encode()


def public_filename(episode: dict[str, Any], query_index: int) -> str:
    return "challenge-" + hashlib.sha256(public_bytes(episode, query_index)).hexdigest() + ".json"


def causal_state(grid: list[list[int]]) -> dict[str, Any]:
    facts = _facts(grid)
    return {
        "first_legend_color": facts["legend"][0],
        "first_component_size": facts["sizes"][0],
        "derived_key": _key_from_sizes(facts["sizes"], "first"),
        "last_component_size": facts["sizes"][-1],
        "wrong_key": _key_from_sizes(facts["sizes"], "last"),
    }
