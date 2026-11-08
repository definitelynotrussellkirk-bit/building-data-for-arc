#!/usr/bin/env python3
"""Episode-fixed header decoders for the contact-degree graph puzzle.

Every input keeps the original body semantics: same-colour 4-connected body
components are graph vertices and cardinal contact defines graph edges.  The
private episode setting chooses how the blue header is decoded into the target
degree:

* ``blue_cells`` counts all blue cells and is the exact canonical rule.
* ``blue_runs`` counts contiguous blue runs in reading order.

Inputs never consult the setting, so both rules receive matched demonstrations
and queries.  The body always exposes the degrees needed by both decoders.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import random
from typing import Any, Callable

from reviewer_support import find_root, load_selected_generator, public_challenge_id


TASK_ID = "1f9fef86a482"
PROTOTYPE_VERSION = "1.0.0"
HEADER_MEASURES = ("blue_cells", "blue_runs")
SETTINGS = tuple({"header_measure": value} for value in HEADER_MEASURES)
DEFAULT_SETTINGS = {"header_measure": "blue_cells"}
BODY_COLORS = (2, 3, 4, 5, 6, 7, 9)
OUTPUT_COLOR = 8
_HERE = Path(__file__).resolve().parent
_ROOT = find_root(__file__)
_PRODUCTION, _PRODUCTION_PATH, _PRODUCTION_SHA256 = load_selected_generator(
    TASK_ID, root=_ROOT
)

# (profile, height, width, blue cells, blue runs)
_DEMO_SPECS = (
    ("all_degrees", 10, 13, 2, 2),
    ("star", 9, 12, 3, 1),
    ("all_degrees", 10, 13, 4, 2),
    ("all_degrees", 12, 15, 2, 1),
    ("star", 11, 16, 3, 3),
    ("chain", 13, 17, 2, 1),
)
_QUERY_SPECS = (
    ("all_degrees", 12, 15, 3, 2),
    ("star", 13, 17, 3, 1),
    ("chain", 14, 16, 2, 1),
    ("stress", 30, 30, 4, 2),
)

Grid = list[list[int]]
Cell = tuple[int, int]


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(
            f"{name} must be an exact integer in {low}..{high}; bool is forbidden"
        )
    return value


def normalize_settings(value: Any) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"header_measure"}:
        raise ValueError("settings must contain exactly header_measure")
    measure = value["header_measure"]
    if type(measure) is not str or measure not in HEADER_MEASURES:
        raise ValueError(f"header_measure must be one of {HEADER_MEASURES}")
    return {"header_measure": measure}


def program_for(measure: Any) -> str:
    if type(measure) is dict:
        measure = normalize_settings(measure)["header_measure"]
    if type(measure) is not str or measure not in HEADER_MEASURES:
        raise ValueError(f"header_measure must be one of {HEADER_MEASURES}")
    name = "canonical.rkt" if measure == "blue_cells" else "blue_runs.rkt"
    source = (_HERE / name).read_text(encoding="utf-8")
    if not source.strip():
        raise ValueError(f"empty Racket source: {name}")
    return source


def _rng(seed: int, split: str, index: int, label: str = "") -> random.Random:
    payload = (
        f"{TASK_ID}|{PROTOTYPE_VERSION}|{seed}|{split}|{index}|{label}".encode()
    )
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _run_count_from_positions(positions: tuple[int, ...]) -> int:
    return sum(
        1
        for index, col in enumerate(positions)
        if index == 0 or col != positions[index - 1] + 1
    )


def _header_positions(
    width: int, count: int, runs: int, rng: random.Random
) -> tuple[int, ...]:
    candidates = [
        positions
        for positions in itertools.combinations(range(width), count)
        if _run_count_from_positions(positions) == runs
    ]
    if not candidates:
        raise ValueError(
            f"cannot place {count} blue cells in {runs} runs across width {width}"
        )
    # Prefer some boundary coverage without coupling all examples to the edge.
    boundary = [p for p in candidates if 0 in p or width - 1 in p]
    pool = boundary if rng.random() < 0.35 and boundary else candidates
    return rng.choice(pool)


def _rewrite_header(
    grid: Grid, *, count: int, runs: int, rng: random.Random
) -> Grid:
    result = deepcopy(grid)
    result[0] = [0] * len(result[0])
    for col in _header_positions(len(result[0]), count, runs, rng):
        result[0][col] = 1
    return result


def _small_input(
    seed: int,
    split: str,
    index: int,
    profile: str,
    height: int,
    width: int,
    blue_cells: int,
    blue_runs: int,
) -> Grid:
    local = _rng(seed, split, index, "production")
    production_seed = local.randrange(0, 2**63)
    sample_index = local.randrange(0, 2**31)
    source = _PRODUCTION.generate(
        production_seed,
        sample_index,
        difficulty="hard",
        scene_profile=profile,
        grid_h=height,
        grid_w=width,
        header_style="contiguous",
    )
    return _rewrite_header(
        source,
        count=blue_cells,
        runs=blue_runs,
        rng=_rng(seed, split, index, "header"),
    )


def _cross(center: Cell) -> set[Cell]:
    row, col = center
    return {
        (row, col),
        (row - 1, col),
        (row - 2, col),
        (row + 1, col),
        (row + 2, col),
        (row, col - 1),
        (row, col - 2),
        (row, col + 1),
        (row, col + 2),
    }


def _tee(center: Cell, orientation: int) -> set[Cell]:
    row, col = center
    leaves = (
        ((-1, 0), (0, -1), (0, 1)),
        ((1, 0), (0, -1), (0, 1)),
        ((-1, 0), (1, 0), (0, -1)),
        ((-1, 0), (1, 0), (0, 1)),
    )[orientation % 4]
    return {(row, col), *((row + dr, col + dc) for dr, dc in leaves)}


def _stress_input(seed: int, split: str, index: int) -> Grid:
    rng = _rng(seed, split, index, "stress")
    grid = [[0 for _ in range(30)] for _ in range(30)]
    for col in _header_positions(30, 4, 2, _rng(seed, split, index, "header")):
        grid[0][col] = 1

    occupied: set[Cell] = set()
    for center in ((4, 2), (4, 27), (27, 2), (27, 27), (15, 15)):
        occupied.update(_cross(center))
    for orientation, center in enumerate(
        ((10, 5), (10, 24), (21, 15), (15, 7), (15, 23))
    ):
        occupied.update(_tee(center, orientation))
    occupied.update(
        {
            (8, 0),
            (8, 29),
            (14, 0),
            (14, 29),
            (20, 0),
            (20, 29),
            (12, 11),
            (18, 19),
        }
    )
    palette = rng.sample(BODY_COLORS, 4)
    for row, col in sorted(occupied):
        # Cardinal neighbors always flip parity, so every occupied cell stays a
        # separate component while colors still repeat throughout the canvas.
        grid[row][col] = palette[(row + col) % 2]
    return grid


def _input(seed: int, split: str, index: int, spec: tuple[Any, ...]) -> Grid:
    profile, height, width, blue_cells, blue_runs = spec
    if profile == "stress":
        return _stress_input(seed, split, index)
    return _small_input(
        seed,
        split,
        index,
        profile,
        height,
        width,
        blue_cells,
        blue_runs,
    )


def _validated_grid(value: Any) -> Grid:
    if (
        type(value) is not list
        or not 3 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must be a rectangular 3..30 by 1..30 ARC grid")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    grid = deepcopy(value)
    if any(cell not in (0, 1) for cell in grid[0]):
        raise ValueError("header row may contain only blue 1 and background 0")
    if any(grid[1]):
        raise ValueError("row 1 must be an all-zero separator")
    if any(
        grid[row][col] in (1, 8)
        for row in range(2, len(grid))
        for col in range(width)
    ):
        raise ValueError("body cannot contain header/output colors 1 or 8")
    return grid


def header_values(grid: Any) -> dict[str, int]:
    source = _validated_grid(grid)
    header = source[0]
    cells = sum(value == 1 for value in header)
    runs = sum(
        value == 1 and (col == 0 or header[col - 1] != 1)
        for col, value in enumerate(header)
    )
    if not 1 <= runs <= cells <= 4:
        raise ValueError("header must encode 1..4 blue cells and runs")
    return {"blue_cells": cells, "blue_runs": runs}


def _components(grid: Grid) -> list[tuple[Cell, ...]]:
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    components: list[tuple[Cell, ...]] = []
    for row in range(2, height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[Cell] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = (current[0] + dr, current[1] + dc)
                    if (
                        2 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            components.append(tuple(sorted(cells)))
    components.sort(key=lambda cells: cells[0])
    return components


def analyze_input(grid: Any) -> dict[str, Any]:
    source = _validated_grid(grid)
    values = header_values(source)
    components = _components(source)
    if not components:
        raise ValueError("body must contain nonzero components")
    sets = [set(component) for component in components]
    graph = [set() for _ in components]
    for first, cells in enumerate(sets):
        for second in range(first + 1, len(sets)):
            other = sets[second]
            touching = any(
                (row + dr, col + dc) in other
                for row, col in cells
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            )
            if touching:
                graph[first].add(second)
                graph[second].add(first)
    degrees = tuple(len(neighbors) for neighbors in graph)
    histogram = Counter(degrees)
    return {
        **values,
        "components": components,
        "degrees": degrees,
        "degree_histogram": dict(sorted(histogram.items())),
    }


def apply_degree(grid: Any, target: Any) -> Grid:
    target = _integer(target, 0, 4, "target degree")
    source = _validated_grid(grid)
    facts = analyze_input(source)
    output = [[0 for _ in row] for row in source]
    for component, degree in zip(facts["components"], facts["degrees"]):
        if degree == target:
            for row, col in component:
                output[row][col] = OUTPUT_COLOR
    return output


def apply_python(grid: Any, settings: Any) -> Grid:
    chosen = normalize_settings(settings)
    facts = analyze_input(grid)
    target = facts[chosen["header_measure"]]
    return apply_degree(grid, target)


def generate_episode(
    seed: Any,
    settings: Any,
    *,
    demos: Any = 3,
    queries: Any = 4,
) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, len(_DEMO_SPECS), "demos")
    queries = _integer(queries, 1, len(_QUERY_SPECS), "queries")
    chosen = normalize_settings(settings)

    train = []
    for index, spec in enumerate(_DEMO_SPECS[:demos]):
        grid = _input(seed, "demo", index, spec)
        train.append({"input": grid, "output": apply_python(grid, chosen)})
    test = []
    for index, spec in enumerate(_QUERY_SPECS[:queries]):
        grid = _input(seed, "query", index, spec)
        test.append({"input": grid, "output": apply_python(grid, chosen)})

    episode = {
        "schema": "1f9fef86a482-header-measure-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "settings": deepcopy(chosen),
        "program_solution": program_for(chosen),
        "train": train,
        "test": test,
    }
    errors = episode_errors(episode)
    if errors:
        raise AssertionError("constructed invalid episode: " + "; ".join(errors))
    return episode


def teaching_survivors(episode: Any) -> list[dict[str, str]]:
    if type(episode) is not dict or type(episode.get("train")) is not list:
        raise ValueError("episode must contain a train list")
    survivors = []
    for setting in SETTINGS:
        if all(
            type(pair) is dict
            and apply_python(pair.get("input"), setting) == pair.get("output")
            for pair in episode["train"]
        ):
            survivors.append(deepcopy(setting))
    return survivors


def episode_errors(episode: Any) -> list[str]:
    if type(episode) is not dict:
        return ["episode must be a dictionary"]
    try:
        chosen = normalize_settings(episode.get("settings"))
    except ValueError as error:
        return [str(error)]
    errors: list[str] = []
    if episode.get("program_solution") != program_for(chosen):
        errors.append("program_solution does not match settings")
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or not 2 <= len(train) <= 6:
        errors.append("episode needs 2..6 demonstrations")
        train = []
    if type(test) is not list or not 1 <= len(test) <= 4:
        errors.append("episode needs 1..4 queries")
        test = []
    seen: set[str] = set()
    for split, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            label = f"{split}[{index}]"
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                errors.append(f"{label} needs input/output grids")
                continue
            try:
                expected = apply_python(pair["input"], chosen)
                facts = analyze_input(pair["input"])
            except ValueError as error:
                errors.append(f"{label} invalid input: {error}")
                continue
            key = json.dumps(pair["input"], separators=(",", ":"))
            if key in seen:
                errors.append(f"{label} duplicates an earlier input")
            seen.add(key)
            if pair["output"] != expected:
                errors.append(f"{label} output does not match settings")
            if not any(
                degree == facts[chosen["header_measure"]]
                for degree in facts["degrees"]
            ):
                errors.append(f"{label} has no component for the selected header value")
    if train and teaching_survivors({"train": train}) != [chosen]:
        errors.append("demonstrations do not identify the selected setting uniquely")
    return errors


def public_turn(episode: Any, query_index: Any = 0) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    query_index = _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def public_turn_id(episode: Any, query_index: Any = 0) -> str:
    return public_challenge_id(public_turn(episode, query_index))


def _target_fixed(value: int) -> Callable[[dict[str, Any]], int]:
    return lambda _facts: value


def _target_maximum(facts: dict[str, Any]) -> int:
    return max(facts["degrees"])


def _target_count_minus_one(facts: dict[str, Any]) -> int:
    return max(0, facts["blue_cells"] - 1)


def _target_count_plus_one(facts: dict[str, Any]) -> int:
    return min(4, facts["blue_cells"] + 1)


def _target_span_mod(facts: dict[str, Any]) -> int:
    # Plausible but wrong compact decoder: infer from the count/run contrast.
    return (facts["blue_cells"] + facts["blue_runs"]) % 5


_RIVALS: dict[str, Callable[[dict[str, Any]], int]] = {
    "fixed_degree_0": _target_fixed(0),
    "fixed_degree_1": _target_fixed(1),
    "fixed_degree_2": _target_fixed(2),
    "fixed_degree_3": _target_fixed(3),
    "fixed_degree_4": _target_fixed(4),
    "maximum_degree": _target_maximum,
    "blue_count_minus_one": _target_count_minus_one,
    "blue_count_plus_one": _target_count_plus_one,
    "count_run_mod_5": _target_span_mod,
}


def audit_episode(episode: Any) -> dict[str, Any]:
    if episode_errors(episode):
        raise ValueError("cannot audit an invalid episode")
    chosen = normalize_settings(episode["settings"])
    ambiguous = []
    for name, selector in _RIVALS.items():
        demo_fit = all(
            apply_degree(pair["input"], selector(analyze_input(pair["input"])))
            == pair["output"]
            for pair in episode["train"]
        )
        if not demo_fit:
            continue
        disagreements = [
            index
            for index, pair in enumerate(episode["test"])
            if apply_degree(pair["input"], selector(analyze_input(pair["input"])))
            != pair["output"]
        ]
        if disagreements:
            ambiguous.append({"rival": name, "query_indices": disagreements})
    return {
        "chosen_setting_survivors": teaching_survivors(episode),
        "tested_rivals": len(_RIVALS),
        "ambiguous_query_rivals": ambiguous,
        "production_generator_sha256": _PRODUCTION_SHA256,
    }
