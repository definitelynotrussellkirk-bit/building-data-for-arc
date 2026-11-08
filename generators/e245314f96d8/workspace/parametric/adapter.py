"""Native contact-neighborhood family for e245314f96d8.

A segments same-color four-connected objects and constructs either the cardinal
or king-move contact graph.  Its input-dependent degree vector is consumed by B,
which recolors every complete object by degree (0->3, 1->4, 2->6, 3+->8).
Inputs are matched across settings and the first two demonstrations contain
both diagonal-only and mixed cardinal/diagonal contacts.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from typing import Any, Iterable

_HOME = Path(__file__).resolve().parent
_TASK_HOME = _HOME.parents[1]
_SOURCE = _TASK_HOME / "generator.py"
_NAME = "_arc_e245314f96d8_production_" + hashlib.sha256(str(_SOURCE).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _SOURCE)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load production generator: {_SOURCE}")
_PRODUCTION = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _PRODUCTION
_SPEC.loader.exec_module(_PRODUCTION)

SETTINGS = (
    {"contact_neighborhood": "cardinal"},
    {"contact_neighborhood": "king"},
)
DEFAULT = SETTINGS[0]
_PROGRAMS = {
    "cardinal": (_HOME / "canonical.rkt").read_text(encoding="utf-8"),
    "king": (_HOME / "king.rkt").read_text(encoding="utf-8"),
}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIAGONAL = ((-1, -1), (-1, 1), (1, -1), (1, 1))
_KING = _CARDINAL + _DIAGONAL
_DIMS = (12, 14, 16, 18, 20, 22, 24, 26, 28, 30)
_COLORS = tuple(range(1, 10))
Cell = tuple[int, int]
Group = tuple[Cell, ...]
Grid = list[list[int]]


def _setting(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"contact_neighborhood"}:
        raise ValueError("settings must contain exactly contact_neighborhood")
    value = settings["contact_neighborhood"]
    if type(value) is not str or value not in _PROGRAMS:
        raise ValueError("contact_neighborhood must be cardinal or king")
    return {"contact_neighborhood": value}


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")
    return value


def _mix(seed: int, stream: str, index: int) -> int:
    payload = f"e245314f96d8:{seed}:{stream}:{index}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & ((1 << 63) - 1)


def _validate_grid(grid: Any) -> Grid:
    if type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list:
        raise ValueError("grid must be a nonempty list of rows")
    width = len(grid[0])
    if not 1 <= width <= 30 or any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular and at most 30x30")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid values must be exact ARC integers 0..9")
    return deepcopy(grid)


def program(settings: dict[str, Any]) -> str:
    return _PROGRAMS[_setting(settings)["contact_neighborhood"]]


def _offsets(mode: str) -> tuple[Cell, ...]:
    return _CARDINAL if mode == "cardinal" else _KING


def _normalized_objects(grid: Grid) -> list[dict[str, Any]]:
    return [
        {
            "color": int(obj["color"]),
            "cells": [list(cell) for cell in obj["cells"]],
            "size": int(obj["size"]),
        }
        for obj in _PRODUCTION._components(grid)
    ]


def _contact_graph(objects: list[dict[str, Any]], offsets: Iterable[Cell]) -> list[list[int]]:
    offset_tuple = tuple(offsets)
    cell_sets = [{tuple(cell) for cell in obj["cells"]} for obj in objects]
    graph = [set() for _ in objects]
    for first_index, first in enumerate(objects):
        for second_index in range(first_index + 1, len(objects)):
            second = cell_sets[second_index]
            if any(
                (row + delta_row, col + delta_col) in second
                for row, col in (tuple(cell) for cell in first["cells"])
                for delta_row, delta_col in offset_tuple
            ):
                graph[first_index].add(second_index)
                graph[second_index].add(first_index)
    return [sorted(neighbors) for neighbors in graph]


def dependency_intermediate(grid: Any, settings: dict[str, Any]) -> dict[str, Any]:
    normalized = _validate_grid(grid)
    mode = _setting(settings)["contact_neighborhood"]
    objects = _normalized_objects(normalized)
    if not objects:
        raise ValueError("grid must contain at least one nonzero object")
    graph = _contact_graph(objects, _offsets(mode))
    return {
        "contact_neighborhood": mode,
        "objects": objects,
        "graph": graph,
        "degrees": [len(neighbors) for neighbors in graph],
    }


def _degree_color(degree: int) -> int:
    return {0: 3, 1: 4, 2: 6}.get(degree, 8)


def solve_from_intermediate(grid: Any, intermediate: dict[str, Any]) -> Grid:
    normalized = _validate_grid(grid)
    if type(intermediate) is not dict:
        raise ValueError("intermediate must be a dictionary")
    objects = intermediate.get("objects")
    if objects != _normalized_objects(normalized):
        raise ValueError("intermediate objects do not belong to this grid")
    degrees = intermediate.get("degrees")
    if (
        type(degrees) is not list
        or len(degrees) != len(objects)
        or any(type(value) is not int or not 0 <= value < len(objects) for value in degrees)
    ):
        raise ValueError("intermediate degrees are invalid")
    output = [[0] * len(normalized[0]) for _ in normalized]
    for obj, degree in zip(objects, degrees, strict=True):
        color = _degree_color(degree)
        for row, col in obj["cells"]:
            output[row][col] = color
    return output


def solve(grid: Any, settings: dict[str, Any]) -> Grid:
    return solve_from_intermediate(grid, dependency_intermediate(grid, settings))


def _rect(top: int, left: int, height: int, width: int) -> Group:
    return tuple((top + row, left + col) for row in range(height) for col in range(width))


def _checker(top: int, left: int, size: int) -> list[Group]:
    return [
        _rect(top, left, size, size),
        _rect(top, left + size, size, size),
        _rect(top + size, left, size, size),
        _rect(top + size, left + size, size, size),
    ]


def _cross(top: int, left: int, size: int) -> list[Group]:
    return [
        _rect(top + size, left + size, size, size),
        _rect(top, left + size, size, size),
        _rect(top + size, left, size, size),
        _rect(top + size, left + 2 * size, size, size),
        _rect(top + 2 * size, left + size, size, size),
    ]


def _diagonal_chain(top: int, left: int, length: int, size: int) -> list[Group]:
    return [_rect(top + index * size, left + index * size, size, size) for index in range(length)]


def _cardinal_chain(top: int, left: int, length: int, size: int) -> list[Group]:
    return [_rect(top, left + index * size, size, size) for index in range(length)]


def _profile_groups(index: int) -> list[Group]:
    groups: list[Group] = []
    if index == 0:
        groups += _diagonal_chain(1, 1, 5, 1)
        groups += _cardinal_chain(9, 1, 3, 1)
        groups += _checker(8, 8, 1)
    elif index == 1:
        groups += _cross(2, 2, 1)
        groups += _checker(9, 9, 1)
        groups += _diagonal_chain(1, 10, 3, 1)
        groups += _cardinal_chain(12, 1, 3, 1)
    elif index == 2:
        groups += _checker(1, 1, 2)
        groups += _diagonal_chain(7, 1, 4, 2)
        groups += _cross(10, 11, 1)
    elif index == 3:
        groups += _cross(1, 1, 2)
        groups += _checker(11, 11, 2)
        groups += _diagonal_chain(2, 12, 4, 1)
        groups += _cardinal_chain(15, 2, 4, 1)
    elif index == 4:
        groups += _checker(1, 1, 3)
        groups += _cross(10, 1, 2)
        groups += _diagonal_chain(9, 12, 5, 1)
        groups += _cardinal_chain(17, 11, 5, 1)
    elif index == 5:
        groups += _cross(1, 1, 3)
        groups += _checker(13, 1, 2)
        groups += _checker(13, 13, 2)
        groups += _diagonal_chain(2, 15, 5, 1)
    elif index == 6:
        groups += _checker(1, 1, 3)
        groups += _cross(11, 2, 2)
        groups += _diagonal_chain(1, 12, 5, 2)
        groups += _cardinal_chain(20, 10, 4, 2)
    elif index == 7:
        groups += _cross(1, 1, 3)
        groups += _checker(16, 1, 3)
        groups += _checker(17, 17, 2)
        groups += _diagonal_chain(3, 18, 6, 1)
        groups += _cardinal_chain(23, 15, 5, 1)
    elif index == 8:
        groups += _checker(1, 1, 4)
        groups += _cross(12, 1, 3)
        groups += _checker(19, 19, 3)
        groups += _diagonal_chain(2, 19, 6, 1)
        groups += _cardinal_chain(25, 10, 7, 1)
    else:
        offsets = (0, 6, 12, 18, 26)
        for top in offsets:
            for left in offsets:
                groups += _checker(top, left, 2)
    return groups


def _normalize_groups(groups: Iterable[Iterable[Cell]]) -> list[Group]:
    materialized = [tuple(group) for group in groups]
    min_row = min(row for group in materialized for row, _ in group)
    min_col = min(col for group in materialized for _, col in group)
    return [
        tuple(sorted((row - min_row, col - min_col) for row, col in group))
        for group in materialized
    ]


def _transform_groups(groups: list[Group], transform_index: int) -> list[Group]:
    turns = transform_index % 4
    reflect = transform_index >= 4
    transformed = []
    for group in groups:
        cells = []
        for row, col in group:
            if reflect:
                col = -col
            for _ in range(turns):
                row, col = col, -row
            cells.append((row, col))
        transformed.append(tuple(cells))
    return _normalize_groups(transformed)


def _groups_graph(groups: list[Group], offsets: Iterable[Cell]) -> list[list[int]]:
    objects = [
        {"color": 1, "cells": [list(cell) for cell in group], "size": len(group)}
        for group in groups
    ]
    return _contact_graph(objects, offsets)


def _proper_colors(rng: random.Random, groups: list[Group], *, require_conflict: bool) -> list[int]:
    cardinal = _groups_graph(groups, _CARDINAL)
    king = _groups_graph(groups, _KING)
    for _ in range(400):
        order = list(range(len(groups)))
        rng.shuffle(order)
        order.sort(key=lambda index: len(cardinal[index]), reverse=True)
        slots: dict[int, int] = {}
        for index in order:
            available = [
                slot for slot in range(5)
                if all(slots.get(neighbor) != slot for neighbor in cardinal[index])
            ]
            if not available:
                break
            slots[index] = rng.choice(available)
        if len(slots) != len(groups):
            continue
        if require_conflict:
            cardinal_degrees = [len(neighbors) for neighbors in cardinal]
            king_degrees = [len(neighbors) for neighbors in king]
            conflicted = []
            for degrees in (cardinal_degrees, king_degrees):
                by_slot: dict[int, set[int]] = {}
                for index, slot in slots.items():
                    by_slot.setdefault(slot, set()).add(_degree_color(degrees[index]))
                conflicted.append(any(len(outputs) >= 2 for outputs in by_slot.values()))
            if not all(conflicted):
                continue
        palette = rng.sample(_COLORS, 5)
        return [palette[slots[index]] for index in range(len(groups))]
    raise RuntimeError("failed to assign separated, shortcut-conflicting object colors")


def _scene(seed: int, index: int) -> Grid:
    dimension = _DIMS[index]
    rng = random.Random(_mix(seed, "scene", index))
    groups = _profile_groups(index)
    groups = _transform_groups(groups, rng.randrange(8))
    occupied: set[Cell] = set()
    for group in groups:
        if not group or any(cell in occupied for cell in group):
            raise AssertionError(f"profile {index} contains overlapping or empty objects")
        occupied.update(group)
    extent_height = max(row for row, _ in occupied) + 1
    extent_width = max(col for _, col in occupied) + 1
    if extent_height > dimension or extent_width > dimension:
        raise AssertionError(f"profile {index} does not fit {dimension}x{dimension}")
    if index == 9:
        top = left = 0
    else:
        top = rng.randint(0, dimension - extent_height)
        left = rng.randint(0, dimension - extent_width)
    colors = _proper_colors(rng, groups, require_conflict=index < 2)
    grid = [[0] * dimension for _ in range(dimension)]
    for group, color in zip(groups, colors, strict=True):
        for row, col in group:
            target = (top + row, left + col)
            if grid[target[0]][target[1]] != 0:
                raise AssertionError(f"profile {index} overlaps at {target}")
            grid[target[0]][target[1]] = color
    # The color assignment must preserve the authored object partition.
    if len(_normalized_objects(grid)) != len(groups):
        raise AssertionError(f"profile {index} merged same-color objects")
    if dependency_intermediate(grid, DEFAULT)["degrees"] == dependency_intermediate(grid, SETTINGS[1])["degrees"]:
        raise AssertionError(f"profile {index} does not distinguish contact neighborhoods")
    return grid


@lru_cache(maxsize=128)
def _input_banks(seed: int) -> tuple[list[Grid], list[Grid]]:
    scenes = [_scene(seed, index) for index in range(10)]
    return scenes[:6], scenes[6:]


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 2, 6)
    queries = _integer("queries", queries, 1, 4)
    selected = _setting(settings)
    demo_inputs, query_inputs = _input_banks(seed)

    def pairs(inputs: list[Grid]) -> list[dict[str, Grid]]:
        return [{"input": deepcopy(grid), "output": solve(grid, selected)} for grid in inputs]

    episode = {
        "settings": deepcopy(selected),
        "train": pairs(demo_inputs[:demos]),
        "test": pairs(query_inputs[:queries]),
        "program_solution": program(selected),
    }
    fingerprints = [
        json.dumps(pair["input"], separators=(",", ":"))
        for split in ("train", "test")
        for pair in episode[split]
    ]
    if len(fingerprints) != len(set(fingerprints)):
        raise AssertionError("generated inputs must be distinct")
    return episode


def first_turn_bytes(episode: dict[str, Any]) -> bytes:
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode must contain nonempty train and test lists")
    public = {
        "train": [
            {"input": _validate_grid(pair["input"]), "output": _validate_grid(pair["output"])}
            for pair in train
        ],
        "test": [{"input": _validate_grid(test[0]["input"])}],
    }
    return (json.dumps(public, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _solve_with_offsets(grid: Grid, offsets: Iterable[Cell]) -> Grid:
    objects = _normalized_objects(grid)
    graph = _contact_graph(objects, offsets)
    return solve_from_intermediate(grid, {"objects": objects, "degrees": [len(row) for row in graph]})


def _feature_rows(episode: dict[str, Any]) -> list[dict[str, int]]:
    rows = []
    for pair in episode["train"]:
        objects = _normalized_objects(pair["input"])
        for rank, obj in enumerate(objects):
            outputs = {pair["output"][row][col] for row, col in obj["cells"]}
            if len(outputs) != 1:
                raise AssertionError("demonstration object is not uniformly recolored")
            rows.append({
                "input_color": obj["color"],
                "size": obj["size"],
                "reading_rank": rank,
                "output_color": next(iter(outputs)),
            })
    return rows


def _feature_lookup_survives(rows: list[dict[str, int]], feature: str) -> bool:
    mapping: dict[int, set[int]] = {}
    for row in rows:
        mapping.setdefault(row[feature], set()).add(row["output_color"])
    return all(len(outputs) == 1 for outputs in mapping.values())


def audit_episode(episode: dict[str, Any], mode: str) -> list[str]:
    selected = _setting({"contact_neighborhood": mode})
    demos = episode.get("train")
    if type(demos) is not list or len(demos) < 2:
        return ["at least two demonstrations are required"]
    failures: list[str] = []
    rivals = {
        "cardinal": _CARDINAL,
        "king": _KING,
        "diagonal_only": _DIAGONAL,
        "cardinal_plus_main_diagonal": _CARDINAL + ((-1, -1), (1, 1)),
        "cardinal_plus_anti_diagonal": _CARDINAL + ((-1, 1), (1, -1)),
    }
    for name, offsets in rivals.items():
        if name == selected["contact_neighborhood"]:
            continue
        if all(_solve_with_offsets(pair["input"], offsets) == pair["output"] for pair in demos):
            failures.append(f"rival neighborhood {name} fits every visible demonstration")
    if all(
        [[3 if value else 0 for value in row] for row in pair["input"]] == pair["output"]
        for pair in demos
    ):
        failures.append("all-objects-isolated rival fits every visible demonstration")
    if all(pair["input"] == pair["output"] for pair in demos):
        failures.append("identity rival fits every visible demonstration")
    rows = _feature_rows(episode)
    for feature in ("input_color", "size", "reading_rank"):
        if _feature_lookup_survives(rows, feature):
            failures.append(f"{feature} lookup fits every visible demonstration")
    return failures
