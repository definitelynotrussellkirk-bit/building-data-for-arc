"""Constructive lookup-and-assembly family for task 35368341e72e.

The input grammar is shared across settings.  The canonical setting galleries
queried prototypes in query order.  The alternative first decodes the queried
prototypes, measures their nonzero cells, then stably galleries occurrences from
fewest cells to most.  Repeated query keys remain repeated.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable


HERE = Path(__file__).resolve().parent
TASK_ID = "35368341e72e"
ASSEMBLIES = ("query_order", "fewest_cells_first")
PROGRAM_PATHS = {
    "query_order": HERE / "canonical.rkt",
    "fewest_cells_first": HERE / "fewest_cells_first.rkt",
}
PROGRAMS = {name: path.read_text(encoding="utf-8") for name, path in PROGRAM_PATHS.items()}

DEMO_SPECS = (
    (6, 15, 3, 4),
    (8, 18, 3, 5),
    (10, 21, 4, 5),
    (12, 24, 4, 6),
    (16, 27, 5, 6),
    (20, 30, 5, 7),
)
QUERY_SPECS = (
    (9, 17, 3, 4),
    (14, 23, 4, 5),
    (22, 28, 5, 6),
    (30, 30, 5, 7),
)

# Counts are 2,3,4,5,6.  Bounding-box areas are 9,3,4,9,6, so
# "fewest cells" is constructively distinguishable from "smallest box".
MASKS = (
    ((0, 0), (2, 2)),
    ((0, 1), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
)
QUERY_RANK_PATTERNS = {
    3: (2, 0, 2, 1, 0),
    4: (3, 1, 0, 3, 2, 1),
    5: (4, 1, 3, 0, 4, 2, 1),
}


def _setting(settings: Any) -> str:
    if type(settings) is not dict:
        raise TypeError("settings must be a dictionary")
    if set(settings) != {"assembly"}:
        raise ValueError("settings must contain exactly assembly")
    value = settings["assembly"]
    if type(value) is not str:
        raise TypeError("assembly must be a string")
    if value not in ASSEMBLIES:
        raise ValueError(f"assembly must be one of {list(ASSEMBLIES)}")
    return value


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer (bool is forbidden)")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return value


def program_for(settings: Any) -> str:
    return PROGRAMS[_setting(settings)]


def _seed(*parts: Any) -> int:
    raw = json.dumps(parts, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def _spread_positions(count: int, low: int, high: int) -> list[int]:
    if count == 1:
        return [(low + high) // 2]
    result = [round(low + i * (high - low) / (count - 1)) for i in range(count)]
    if len(set(result)) != count:
        raise ValueError("cannot spread distinct positions")
    return result


def _bbox_area(cells: tuple[tuple[int, int], ...]) -> int:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def _prototype_lookup(grid: list[list[int]]) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for column, key in enumerate(grid[0]):
        if key == 0:
            continue
        prototype = [row[column - 1 : column + 2] for row in grid[1:4]]
        active = sum(cell != 0 for row in prototype for cell in row)
        cells = tuple((r, c) for r, row in enumerate(prototype) for c, value in enumerate(row) if value != 0)
        result[key] = {
            "key": key,
            "column": column,
            "prototype": prototype,
            "active_cells": active,
            "bbox_area": _bbox_area(cells),
        }
    return result


def intermediate(grid: list[list[int]]) -> dict[str, Any]:
    errors = validate_input(grid)
    if errors:
        raise ValueError("invalid input: " + "; ".join(errors[:3]))
    lookup = _prototype_lookup(grid)
    query = [value for value in grid[-1] if value != 0]
    occurrences = []
    for index, key in enumerate(query):
        row = deepcopy(lookup[key])
        row["occurrence_index"] = index
        occurrences.append(row)
    ranked = sorted(occurrences, key=lambda row: row["active_cells"])
    return {
        "query_keys": query,
        "query_occurrences": occurrences,
        "fewest_first_keys": [row["key"] for row in ranked],
        "fewest_first_occurrences": ranked,
    }


def gallery(parts: list[list[list[int]]]) -> list[list[int]]:
    if not parts:
        return [[0]]
    width = 4 * len(parts) - 1
    output = [[0 for _ in range(width)] for _ in range(3)]
    for index, part in enumerate(parts):
        left = 4 * index
        for row in range(3):
            for col in range(3):
                if part[row][col] != 0:
                    output[row][left + col] = part[row][col]
    return output


def _ordered_occurrences(grid: list[list[int]], order: str) -> list[dict[str, Any]]:
    info = intermediate(grid)
    rows = info["query_occurrences"]
    if order == "query_order":
        return rows
    if order == "fewest_cells_first":
        return sorted(rows, key=lambda row: row["active_cells"])
    if order == "largest_cells_first":
        return sorted(rows, key=lambda row: -row["active_cells"])
    if order == "smallest_bbox_first":
        return sorted(rows, key=lambda row: row["bbox_area"])
    if order == "key_color_first":
        return sorted(rows, key=lambda row: row["key"])
    if order == "key_column_first":
        return sorted(rows, key=lambda row: row["column"])
    if order == "reverse_query":
        return list(reversed(rows))
    if order == "deduplicate_query":
        seen: set[int] = set()
        result = []
        for row in rows:
            if row["key"] not in seen:
                seen.add(row["key"])
                result.append(row)
        return result
    raise ValueError(order)


CANDIDATES = (
    "query_order",
    "fewest_cells_first",
    "largest_cells_first",
    "smallest_bbox_first",
    "key_color_first",
    "key_column_first",
    "reverse_query",
    "deduplicate_query",
)


def candidate_output(grid: list[list[int]], name: str) -> list[list[int]]:
    return gallery([row["prototype"] for row in _ordered_occurrences(grid, name)])


def mirror(grid: list[list[int]], settings: Any) -> list[list[int]]:
    return candidate_output(grid, _setting(settings))


def _grid_errors(grid: Any) -> tuple[list[str], int, int]:
    if type(grid) is not list or not grid:
        return ["grid must be a nonempty list"], 0, 0
    if type(grid[0]) is not list or not grid[0]:
        return ["rows must be nonempty lists"], 0, 0
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["grid must be rectangular"], len(grid), width
    if not 5 <= len(grid) <= 30 or not 1 <= width <= 30:
        return ["grid dimensions must be within 5..30 by 1..30"], len(grid), width
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                return [f"cell ({r},{c}) must be an exact integer color 0..9"], len(grid), width
    return [], len(grid), width


def validate_input(grid: Any) -> list[str]:
    errors, height, width = _grid_errors(grid)
    if errors:
        return errors
    keys = [(column, value) for column, value in enumerate(grid[0]) if value != 0]
    if not 3 <= len(keys) <= 5:
        errors.append(f"row 0 needs 3..5 keys, found {len(keys)}")
        return errors
    columns = [column for column, _ in keys]
    values = [value for _, value in keys]
    if len(set(values)) != len(values):
        errors.append("key colors must be distinct")
    if any(column in {0, width - 1} for column in columns):
        errors.append("each key needs a full 3-column prototype band")
    if any(right - left < 3 for left, right in zip(columns, columns[1:])):
        errors.append("prototype bands overlap")
    legal = {column + delta for column in columns for delta in (-1, 0, 1)}
    for row in range(1, 4):
        if any(value != 0 and column not in legal for column, value in enumerate(grid[row])):
            errors.append("prototype content lies outside a declared key band")
            break
    if any(any(value != 0 for value in grid[row]) for row in range(4, height - 1)):
        errors.append("rows between prototypes and query must be background")
    query = [value for value in grid[-1] if value != 0]
    if not 4 <= len(query) <= 7:
        errors.append(f"query must contain 4..7 entries, found {len(query)}")
    if set(query) - set(values):
        errors.append("query contains an undeclared key")
    if len(query) == len(set(query)):
        errors.append("query must repeat at least one key")
    lookup = _prototype_lookup(grid) if not errors else {}
    counts = [lookup[value]["active_cells"] for value in values] if lookup else []
    if counts and (any(count == 0 for count in counts) or len(set(counts)) != len(counts)):
        errors.append("prototype active-cell counts must be nonzero and distinct")
    return errors


def input_metrics(grid: list[list[int]]) -> dict[str, Any]:
    errors = validate_input(grid)
    if errors:
        raise ValueError("invalid input: " + "; ".join(errors[:3]))
    lookup = _prototype_lookup(grid)
    query = [value for value in grid[-1] if value != 0]
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
    return {
        "input_shape": [len(grid), len(grid[0])],
        "key_count": len(lookup),
        "query_length": len(query),
        "prototype_active_cells": sorted(row["active_cells"] for row in lookup.values()),
        "nonzero_cells": len(cells),
        "content_row_span": max(r for r, _ in cells) - min(r for r, _ in cells) + 1,
        "content_col_span": max(c for _, c in cells) - min(c for _, c in cells) + 1,
        "repeated_query": len(query) > len(set(query)),
    }


def _build_input(seed: int, role: str, index: int, spec: tuple[int, int, int, int]) -> list[list[int]]:
    height, width, n_keys, query_length = spec
    for nonce in range(128):
        rng = random.Random(_seed(TASK_ID, seed, role, index, nonce))
        key_columns = _spread_positions(n_keys, 1, width - 2)
        key_colors = rng.sample(range(1, 10), n_keys)
        rotation = 1 + ((_seed(seed, role, index, nonce, "rotation") % (n_keys - 1)))
        masks = [MASKS[(column_index + rotation) % n_keys] for column_index in range(n_keys)]
        remaining = [color for color in range(1, 10) if color not in key_colors]
        rng.shuffle(remaining)
        content_palette = remaining[: max(2, min(4, len(remaining)))]
        grid = [[0 for _ in range(width)] for _ in range(height)]
        rows_by_count: dict[int, int] = {}
        for column_index, (column, key, mask) in enumerate(zip(key_columns, key_colors, masks, strict=True)):
            grid[0][column] = key
            rows_by_count[len(mask)] = key
            for local_index, (r, c) in enumerate(mask):
                color = content_palette[(local_index + column_index + index) % len(content_palette)]
                grid[1 + r][column - 1 + c] = color
        ranked_keys = [rows_by_count[count] for count in sorted(rows_by_count)]
        pattern = QUERY_RANK_PATTERNS[n_keys]
        query = [ranked_keys[rank] for rank in pattern[:query_length]]
        query_columns = _spread_positions(query_length, 0, width - 1)
        for column, key in zip(query_columns, query, strict=True):
            grid[-1][column] = key
        if validate_input(grid):
            continue
        outputs = {name: candidate_output(grid, name) for name in CANDIDATES}
        if all(outputs[name] != outputs["query_order"] for name in CANDIDATES if name != "query_order") and all(
            outputs[name] != outputs["fewest_cells_first"]
            for name in CANDIDATES
            if name != "fewest_cells_first"
        ):
            return grid
    raise RuntimeError(f"failed to construct a distinguishing {role} input {index}")


def generate_episode(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 4, 4, "queries")
    assembly = _setting(settings)
    demo_inputs = [_build_input(seed, "demo", index, spec) for index, spec in enumerate(DEMO_SPECS[:demos])]
    query_inputs = [_build_input(seed, "query", index, spec) for index, spec in enumerate(QUERY_SPECS[:queries])]
    train = [{"input": grid, "output": candidate_output(grid, assembly)} for grid in demo_inputs]
    test = [{"input": grid, "output": candidate_output(grid, assembly)} for grid in query_inputs]
    return {"train": train, "test": test, "program_solution": PROGRAMS[assembly]}


def teaching_check(episode: dict[str, Any], settings: Any) -> dict[str, Any]:
    target = _setting(settings)
    if type(episode) is not dict:
        raise TypeError("episode must be a dictionary")
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or not train or type(test) is not list or not test:
        raise ValueError("episode needs demonstrations and queries")
    for pair in train:
        if pair.get("output") != candidate_output(pair.get("input"), target):
            raise ValueError("demonstration label disagrees with selected setting")
    eliminated: dict[str, list[int]] = {}
    survivors = []
    for name in CANDIDATES:
        witnesses = [
            index
            for index, pair in enumerate(train)
            if candidate_output(pair["input"], name) != pair["output"]
        ]
        if witnesses:
            eliminated[name] = witnesses
        else:
            survivors.append(name)
    harmful = [
        name
        for name in survivors
        if any(candidate_output(pair["input"], name) != candidate_output(pair["input"], target) for pair in test)
    ]
    return {
        "target": target,
        "survivors": survivors,
        "harmful_survivors": harmful,
        "eliminated": eliminated,
        "rivals_tested": len(CANDIDATES) - 1,
        "fit_uses": "demonstrations_only",
    }


def public_turn(episode: dict[str, Any], index: Any = 0) -> dict[str, Any]:
    if type(index) is not int:
        raise TypeError("query index must be an integer (bool is forbidden)")
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    if not 0 <= index < len(episode["test"]):
        raise ValueError("query index outside episode")
    train = [
        {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
        for pair in episode["train"]
    ]
    query = {"input": deepcopy(episode["test"][index]["input"])}
    return {"train": train, "test": [query]}
