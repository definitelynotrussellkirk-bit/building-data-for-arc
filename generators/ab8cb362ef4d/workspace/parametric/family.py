"""Native matched-input parametric family for ``ab8cb362ef4d``.

``gravity_only`` is the byte-exact canonical rule.  ``mark_largest_landed_cluster``
first performs that gravity step, then recomputes the color-2 components created
by the landing and recolors the unique largest landed cluster color 9.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "ab8cb362ef4d"
PARAMETER = "finish"
SETTINGS = ("gravity_only", "mark_largest_landed_cluster")
DEFAULT = {PARAMETER: SETTINGS[0]}
MIN_DEMOS, MAX_DEMOS = 2, 6
MIN_QUERIES, MAX_QUERIES = 1, 4
MAX_SEED = 2**63 - 1
HOME = Path(__file__).resolve().parent
PROGRAM_FILES = {
    SETTINGS[0]: HOME / "canonical.rkt",
    SETTINGS[1]: HOME / "largest_landed_cluster.rkt",
}
CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))

TRAIN_PROFILES = (
    (12, 14, False),
    (13, 15, True),
    (14, 16, False),
    (15, 17, True),
    (16, 18, False),
    (17, 19, True),
)
QUERY_PROFILES = (
    (18, 20, True),
    (20, 22, False),
    (24, 26, True),
    (30, 30, False),
)


def _exact_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return value


def _finish(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER!r}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"{PARAMETER} must be one of {SETTINGS!r}")
    return value


def program(settings: Any) -> str:
    return PROGRAM_FILES[_finish(settings)].read_text(encoding="utf-8")


def _grid(value: Any) -> tuple[int, int]:
    if type(value) is not list or not value or type(value[0]) is not list or not value[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(value[0])
    if len(value) > 30 or width > 30:
        raise ValueError("grid dimensions must not exceed 30")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return len(value), width


def _components(value: list[list[int]], color: int) -> list[frozenset[tuple[int, int]]]:
    height, width = len(value), len(value[0])
    remaining = {(r, c) for r in range(height) for c in range(width) if value[r][c] == color}
    result: list[frozenset[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in CARDINALS:
                q = (r + dr, c + dc)
                if q in remaining:
                    remaining.remove(q)
                    cells.add(q)
                    stack.append(q)
        result.append(frozenset(cells))
    result.sort(key=min)
    return result


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    return (
        min(r for r, _ in cells), min(c for _, c in cells),
        max(r for r, _ in cells), max(c for _, c in cells),
    )


def _frame_boxes(value: list[list[int]]) -> list[tuple[int, int, int, int]]:
    boxes = [_bbox(cells) for cells in _components(value, 5)]
    boxes.sort()
    return boxes


def canonical_intermediate(value: Any) -> list[list[int]]:
    _grid(value)
    out = [[0 for _ in row] for row in value]
    boxes = _frame_boxes(value)
    if not boxes:
        raise ValueError("scene must contain a color-5 frame")
    for r0, c0, r1, c1 in boxes:
        for c in range(c0, c1 + 1):
            out[r0][c] = 5
            out[r1][c] = 5
        for r in range(r0, r1 + 1):
            out[r][c0] = 5
            out[r][c1] = 5
        for c in range(c0 + 1, c1):
            values = [value[r][c] for r in range(r0 + 1, r1) if value[r][c] != 0]
            for offset, cell in enumerate(reversed(values)):
                out[r1 - 1 - offset][c] = cell
    return out


def _unique_largest(components: list[frozenset[tuple[int, int]]]) -> frozenset[tuple[int, int]]:
    if not components:
        raise ValueError("no payload components")
    ordered = sorted(components, key=lambda cells: (-len(cells), min(cells)))
    if len(ordered) > 1 and len(ordered[0]) == len(ordered[1]):
        raise ValueError("largest payload component must be unique")
    return ordered[0]


def _mark_component(value: list[list[int]], cells: Iterable[tuple[int, int]], color: int = 9) -> list[list[int]]:
    out = deepcopy(value)
    for r, c in cells:
        out[r][c] = color
    return out


def solve(value: Any, settings: Any) -> list[list[int]]:
    finish = _finish(settings)
    intermediate = canonical_intermediate(value)
    if finish == SETTINGS[0]:
        return intermediate
    target = _unique_largest(_components(intermediate, 2))
    return _mark_component(intermediate, target)


def wrong_order_solve(value: Any) -> list[list[int]]:
    """Plausible wrong order: select the source's largest object before gravity."""
    _grid(value)
    target = _unique_largest(_components(value, 2))
    return canonical_intermediate(_mark_component(value, target))


def _mark_all_landed(value: Any) -> list[list[int]]:
    intermediate = canonical_intermediate(value)
    return [[9 if cell == 2 else cell for cell in row] for row in intermediate]


def _mark_first_landed(value: Any) -> list[list[int]]:
    intermediate = canonical_intermediate(value)
    return _mark_component(intermediate, _components(intermediate, 2)[0])


def rival_outputs(value: Any, settings: Any) -> dict[str, list[list[int]]]:
    chosen = _finish(settings)
    result = {"other_setting": solve(value, {PARAMETER: SETTINGS[1] if chosen == SETTINGS[0] else SETTINGS[0]})}
    if chosen == SETTINGS[1]:
        result.update(
            wrong_order=wrong_order_solve(value),
            mark_all_landed=_mark_all_landed(value),
            mark_first_landed=_mark_first_landed(value),
        )
    return result


def dependency_trace(value: Any) -> dict[str, Any]:
    _grid(value)
    source = _components(value, 2)
    landed = _components(canonical_intermediate(value), 2)
    source_largest = _unique_largest(source)
    landed_largest = _unique_largest(landed)
    ordered = sorted(landed, key=lambda cells: (-len(cells), min(cells)))
    return {
        "frame_count": len(_frame_boxes(value)),
        "source_largest_size": len(source_largest),
        "source_largest_cells": [list(cell) for cell in sorted(source_largest)],
        "landed_largest_size": len(landed_largest),
        "landed_largest_cells": [list(cell) for cell in sorted(landed_largest)],
        "landed_largest_unique": len(ordered) == 1 or len(ordered[0]) > len(ordered[1]),
        "landed_component_sizes": sorted((len(cells) for cells in landed), reverse=True),
    }


def _draw_frame(grid: list[list[int]], box: tuple[int, int, int, int]) -> None:
    r0, c0, r1, c1 = box
    for c in range(c0, c1 + 1):
        grid[r0][c] = grid[r1][c] = 5
    for r in range(r0, r1 + 1):
        grid[r][c0] = grid[r][c1] = 5


def _place_rank_inversion(
    grid: list[list[int]], box: tuple[int, int, int, int], *, mirror: bool, large: bool
) -> None:
    r0, c0, r1, c1 = box
    ih, iw = r1 - r0 - 1, c1 - c0 - 1
    if ih < 8 or iw < 10:
        raise ValueError("frame is too small for the rank-inversion lesson")
    if large:
        main = {
            (0, 0), (2, 0), (4, 0), (6, 0),
            (1, 1), (3, 1), (5, 1),
            (0, 2), (2, 2), (4, 2),
            (1, 3), (3, 3),
            (0, 4), (1, 5),
        }
    else:
        main = {(0, 0), (3, 0), (6, 0), (1, 1), (4, 1), (0, 2), (5, 2), (2, 3)}
    center = iw - 2
    decoy = {(1, center), (2, center - 1), (2, center), (2, center + 1), (3, center)}
    cells = main | decoy
    for rr, cc in cells:
        if mirror:
            cc = iw - 1 - cc
        grid[r0 + 1 + rr][c0 + 1 + cc] = 2


def _place_small_payload(grid: list[list[int]], box: tuple[int, int, int, int], *, mirror: bool) -> None:
    r0, c0, r1, c1 = box
    ih, iw = r1 - r0 - 1, c1 - c0 - 1
    cells = {(1, 1), (2, 0), (2, 1), (2, 2), (0, iw - 2), (4, iw - 1)}
    for rr, cc in cells:
        if mirror:
            cc = iw - 1 - cc
        if 0 <= rr < ih and 0 <= cc < iw:
            grid[r0 + 1 + rr][c0 + 1 + cc] = 2


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _exact_int("seed", seed, 0, MAX_SEED)
    if split not in ("train", "test"):
        raise ValueError("split must be 'train' or 'test'")
    profiles = TRAIN_PROFILES if split == "train" else QUERY_PROFILES
    _exact_int("index", index, 0, len(profiles) - 1)
    height, width, base_mirror = profiles[index]
    mirror = base_mirror ^ bool((seed >> (index % 11)) & 1)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    if split == "test" and index == 3:
        target = (1, 1, 13, 28)
        auxiliary = (15, 1, 28, 28)
        for box in (target, auxiliary):
            _draw_frame(grid, box)
        _place_rank_inversion(grid, target, mirror=mirror, large=True)
        _place_small_payload(grid, auxiliary, mirror=not mirror)
    else:
        target = (1, 1, height - 2, width - 2)
        _draw_frame(grid, target)
        _place_rank_inversion(grid, target, mirror=mirror, large=False)
    trace = dependency_trace(grid)
    if not (
        trace["source_largest_size"] < trace["landed_largest_size"]
        and trace["source_largest_cells"] != trace["landed_largest_cells"]
        and trace["landed_largest_unique"]
    ):
        raise RuntimeError(f"rank-inversion construction failed: {trace}")
    if solve(grid, {PARAMETER: SETTINGS[1]}) == wrong_order_solve(grid):
        raise RuntimeError("wrong-order construction did not change the final output")
    return grid


def teaching_check(episode: Any) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list:
        raise ValueError("episode must contain a training list")
    train = episode["train"]
    settings = episode.get("settings")
    survivors = []
    for name in sorted({key for pair in train for key in rival_outputs(pair["input"], settings)}):
        if all(rival_outputs(pair["input"], settings).get(name) == pair["output"] for pair in train):
            survivors.append(name)
    return {
        "status": "identified" if not survivors else "ambiguous",
        "surviving_rivals": survivors,
        "demonstrations": len(train),
    }


def generate(seed: int, settings: Any, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _exact_int("seed", seed, 0, MAX_SEED)
    _finish(settings)
    _exact_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    _exact_int("queries", queries, MIN_QUERIES, MAX_QUERIES)
    train = [
        {"input": (grid := sample_input(seed, "train", index)), "output": solve(grid, settings)}
        for index in range(demos)
    ]
    test = [
        {"input": (grid := sample_input(seed, "test", index)), "output": solve(grid, settings)}
        for index in range(queries)
    ]
    fingerprints = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(fingerprints) != len(set(fingerprints)):
        raise RuntimeError("constructed episode contains duplicate inputs")
    episode = {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": deepcopy(settings),
        "train": train,
        "test": test,
        "program_solution": program(settings),
        "sampling": {"draws": demos + queries, "duplicate_rejections": 0},
    }
    episode["teaching"] = teaching_check(episode)
    if episode["teaching"]["surviving_rivals"]:
        raise RuntimeError("declared teaching rivals survived: " + ", ".join(episode["teaching"]["surviving_rivals"]))
    return episode


def public_turn(episode: Any, query_index: Any = 0) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train/test lists")
    test = episode["test"]
    _exact_int("query_index", query_index, 0, len(test) - 1)
    query = {"input": deepcopy(test[query_index]["input"])}
    return {
        "train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])} for pair in episode["train"]],
        "test": [query],
    }


__all__ = [
    "DEFAULT", "SETTINGS", "canonical_intermediate", "dependency_trace", "generate",
    "program", "public_turn", "rival_outputs", "sample_input", "solve", "teaching_check",
    "wrong_order_solve",
]
