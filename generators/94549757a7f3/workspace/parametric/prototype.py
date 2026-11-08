"""Native cap-only / cap-then-vertical-bridge family for 94549757a7f3.

The default is the exact selected Racket program.  The alternate first creates
the canonical red cap cells, treats their input-derived coordinates as an
intermediate, then fills zero cells vertically between the first and last new
cap in every column containing at least two new caps.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from reviewer_support import find_root, load_selected_generator

TASK_ID = "94549757a7f3"
HOME = Path(__file__).resolve().parent
PARAMETER = "finish_rule"
RULES = ("cap_only", "cap_then_vertical_bridge")
SETTINGS = tuple({PARAMETER: value} for value in RULES)
GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(
    TASK_ID, root=find_root(__file__)
)

_DEMO_SHAPES = ((10, 12), (12, 14), (14, 16), (16, 18), (18, 20), (20, 22))
_QUERY_SHAPES = ((11, 15), (18, 20), (24, 26), (30, 30))


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool and coercions are forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _setting(settings: dict[str, str]) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {PARAMETER}
        or type(settings[PARAMETER]) is not str
        or settings[PARAMETER] not in RULES
    ):
        raise ValueError(
            "settings must be exactly {'finish_rule': 'cap_only'|'cap_then_vertical_bridge'}"
        )
    return settings[PARAMETER]


def program(settings: dict[str, str]) -> str:
    rule = _setting(settings)
    name = "canonical.rkt" if rule == "cap_only" else "vertical_bridge.rkt"
    return (HOME / name).read_text(encoding="utf-8")


def _rng(seed: int, split: str, index: int) -> random.Random:
    payload = json.dumps(
        [TASK_ID, "cap-vertical-bridge-v1", seed, split, index],
        separators=(",", ":"),
    ).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _shape(split: str, index: int) -> tuple[int, int]:
    shapes = _DEMO_SHAPES if split == "train" else _QUERY_SHAPES
    _integer("index", index, 0, len(shapes) - 1)
    return shapes[index]


def _grid(grid: list[list[int]]) -> list[list[int]]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer ARC colors 0..9")
    return grid


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            todo = [(r, c)]
            seen.add((r, c))
            cells = []
            while todo:
                rr, cc = todo.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            result.append({
                "color": color,
                "cells": tuple(sorted(cells)),
                "r1": min(rr for rr, _ in cells),
                "r2": max(rr for rr, _ in cells),
                "c1": min(cc for _, cc in cells),
                "c2": max(cc for _, cc in cells),
            })
    return result


def cap_stage(grid: list[list[int]]) -> list[list[int]]:
    grid = _grid(grid)
    out = deepcopy(grid)
    width = len(grid[0])
    for component in _components(grid):
        if component["color"] != 3 or component["r1"] != component["r2"]:
            continue
        row = component["r1"]
        column = component["c2"] + 1
        if column < width and grid[row][column] == 0:
            out[row][column] = 2
    return out


def new_caps(grid: list[list[int]], capped: list[list[int]]) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] == 0 and capped[r][c] == 2
    ]


def vertical_bridge(grid: list[list[int]], capped: list[list[int]]) -> list[list[int]]:
    out = deepcopy(capped)
    caps = new_caps(grid, capped)
    for column in sorted({c for _, c in caps}):
        rows = [r for r, c in caps if c == column]
        if len(rows) < 2:
            continue
        for row in range(rows[0] + 1, rows[-1]):
            if capped[row][column] == 0:
                out[row][column] = 2
    return out


def horizontal_bridge(grid: list[list[int]], capped: list[list[int]]) -> list[list[int]]:
    out = deepcopy(capped)
    caps = new_caps(grid, capped)
    for row in sorted({r for r, _ in caps}):
        columns = [c for r, c in caps if r == row]
        if len(columns) < 2:
            continue
        for column in range(columns[0] + 1, columns[-1]):
            if capped[row][column] == 0:
                out[row][column] = 2
    return out


def first_column_bridge(grid: list[list[int]], capped: list[list[int]]) -> list[list[int]]:
    out = deepcopy(capped)
    caps = new_caps(grid, capped)
    if not caps:
        return out
    column = caps[0][1]
    rows = [r for r, c in caps if c == column]
    if len(rows) >= 2:
        for row in range(rows[0] + 1, rows[-1]):
            if capped[row][column] == 0:
                out[row][column] = 2
    return out


def solve_without_cap(grid: list[list[int]]) -> list[list[int]]:
    # The counterfactual feeds Stage B the raw input.  The admitted input grammar
    # contains no color-2 cells, so there are no derived cap coordinates.
    return vertical_bridge(grid, deepcopy(grid))


def claimed_output(grid: list[list[int]], settings: dict[str, str]) -> list[list[int]]:
    rule = _setting(settings)
    capped = cap_stage(grid)
    return capped if rule == "cap_only" else vertical_bridge(grid, capped)


def _cap_columns(width: int) -> list[int]:
    columns = []
    current = width - 2
    while current >= 4 and len(columns) < 4:
        columns.append(current)
        # Six-column spacing leaves at least one background cell between a
        # preceding cap and the next 2..4-cell green run.  That makes the
        # horizontal-bridge rival observably wrong in every admitted scene.
        current -= 6
    if len(columns) < 2:
        raise RuntimeError("canvas cannot hold two separated cap columns")
    return sorted(columns)


def _anchor_rows(height: int, border: bool) -> list[int]:
    margin = 2 if border else 1
    rows = [margin, height // 2, height - margin - 1]
    if len(set(rows)) != 3 or min(b - a for a, b in zip(rows, rows[1:])) < 2:
        raise RuntimeError("canvas cannot hold three separated teaching rows")
    return rows


def _build_input(seed: int, split: str, index: int) -> list[list[int]]:
    height, width = _shape(split, index)
    rng = _rng(seed, split, index)
    border = split == "test" and index == 3
    grid = [[0 for _ in range(width)] for _ in range(height)]

    if border:
        for column in range(width):
            grid[0][column] = 8
            grid[-1][column] = 8
        for row in range(height):
            grid[row][0] = 8
            grid[row][-1] = 8
    else:
        # Wrong-color horizontal controls touch top and bottom without affecting
        # the canonical green-object filter.
        for column in range(min(5, width - 2)):
            grid[0][column] = 8
        for column in range(max(1, width - 5), width):
            grid[-1][column] = 8

    rows = _anchor_rows(height, border)
    columns = _cap_columns(width)
    for row_index, row in enumerate(rows):
        for column_index, cap_column in enumerate(columns):
            raw_length = 2 + ((seed + index + row_index + column_index + rng.randrange(3)) % 3)
            length = min(raw_length, cap_column - 1)
            start = cap_column - length
            if start < 1:
                raise RuntimeError("target run escaped left teaching margin")
            if any(grid[row][column] for column in range(start, cap_column + 1)):
                raise RuntimeError("target placement collided")
            for column in range(start, cap_column):
                grid[row][column] = 3
            # cap_column intentionally remains zero for Stage A.

    # A small isolated color-8 control makes color-blind capping visibly wrong.
    control_row = next(r for r in range(1, height - 1) if r not in rows)
    if all(grid[control_row][c] == 0 for c in range(1, 4)):
        grid[control_row][1] = 8
        grid[control_row][2] = 8

    capped = cap_stage(grid)
    facts = analyze_input(grid)
    if len(facts["bridge_columns"]) < 2 or not facts["vertical_bridge_cells"]:
        raise RuntimeError("constructed scene failed to expose vertical bridge")
    if not facts["horizontal_bridge_cells"]:
        raise RuntimeError("constructed scene failed to expose orientation rival")
    if claimed_output(grid, {PARAMETER: RULES[0]}) == claimed_output(grid, {PARAMETER: RULES[1]}):
        raise RuntimeError("constructed scene failed to separate settings")
    return grid


def _changed(before: list[list[int]], after: list[list[int]]) -> list[list[int]]:
    return [
        [r, c]
        for r in range(len(before))
        for c in range(len(before[0]))
        if before[r][c] != after[r][c]
    ]


def analyze_input(grid: list[list[int]]) -> dict[str, Any]:
    grid = _grid(grid)
    capped = cap_stage(grid)
    caps = new_caps(grid, capped)
    bridged = vertical_bridge(grid, capped)
    horizontal = horizontal_bridge(grid, capped)
    columns = sorted(column for column in {c for _, c in caps}
                     if sum(1 for _, cc in caps if cc == column) >= 2)
    return {
        "shape": [len(grid), len(grid[0])],
        "new_cap_count": len(caps),
        "new_caps": [list(cell) for cell in caps],
        "bridge_columns": columns,
        "vertical_bridge_cells": _changed(capped, bridged),
        "horizontal_bridge_cells": _changed(capped, horizontal),
        "skip_a_changed_cells": _changed(solve_without_cap(grid), bridged),
    }


def causal_case(grid: list[list[int]]) -> dict[str, Any]:
    grid = _grid(grid)
    settings = {PARAMETER: "cap_then_vertical_bridge"}
    output = claimed_output(grid, settings)
    counterfactual = solve_without_cap(grid)
    facts = analyze_input(grid)
    return {
        "input": deepcopy(grid),
        "settings": settings,
        "program": program(settings),
        "output": output,
        "counterfactual_program": (HOME / "skip_cap.rkt").read_text(encoding="utf-8"),
        "counterfactual_output": counterfactual,
        "ablation": "skip_a",
        "intermediate_value": {
            "new_cap_coordinates": facts["new_caps"],
            "bridge_columns": facts["bridge_columns"],
            "changed_final_cells": len(facts["skip_a_changed_cells"]),
        },
    }


def generate(seed: int, settings: dict[str, str], demos: int, queries: int) -> dict:
    _integer("seed", seed, 0, 2**63 - 1)
    rule = _setting(settings)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    chosen = {PARAMETER: rule}
    train = []
    test = []
    for split, count in (("train", demos), ("test", queries)):
        destination = train if split == "train" else test
        for index in range(count):
            grid = _build_input(seed, split, index)
            destination.append({"input": grid, "output": claimed_output(grid, chosen)})
    return {
        "train": train,
        "test": test,
        "program_solution": program(chosen),
        "settings": chosen,
        "seed": seed,
    }


def public_turn(episode: dict, query_index: int) -> dict:
    if type(query_index) is not int:
        raise TypeError("query_index must be an exact integer")
    train = episode.get("train") if isinstance(episode, dict) else None
    test = episode.get("test") if isinstance(episode, dict) else None
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode must contain nonempty train/test lists")
    if not 0 <= query_index < len(test):
        raise ValueError("query_index is outside the stored query prefix")
    return {
        "train": deepcopy(train),
        "test": [{"input": deepcopy(test[query_index]["input"])}],
    }


def public_turn_bytes(episode: dict, query_index: int) -> bytes:
    public = public_turn(episode, query_index)
    return (
        json.dumps(public, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def public_turn_id(episode: dict, query_index: int) -> str:
    return hashlib.sha256(public_turn_bytes(episode, query_index)).hexdigest()
