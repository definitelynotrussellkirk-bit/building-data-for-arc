"""Matched-input native family for chamber-local versus next-room seed fill.

The canonical setting fills each color-8-walled room from its own unique seed.
The alternate first extracts room seeds in row-major room order, cyclically
shifts that input-derived sequence left, then fills each room from the shifted
seed.  Generated episodes use three or four rooms with distinct seed colors so
both the shift and its direction are identified from demonstrations.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "99f58784e7a0"
PARAMETER = "color_source"
MODES = ("own", "next")
_DIR = Path(__file__).resolve().parent
_PROGRAMS = {
    "own": (_DIR / "canonical.rkt").read_text(encoding="utf-8"),
    "next": (_DIR / "next_seed.rkt").read_text(encoding="utf-8"),
}
_DEMO_DIMS = ((10, 16), (12, 18), (14, 20), (18, 22), (20, 24), (24, 28))
_QUERY_DIMS = ((9, 17), (15, 19), (22, 25), (30, 30))
_DEMO_LAYOUTS = ((1, 3), (3, 1), (2, 2), (1, 4), (4, 1), (2, 2))
_QUERY_LAYOUTS = ((1, 3), (3, 1), (2, 2), (2, 2))
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_PALETTE = (1, 2, 3, 4, 5, 6, 7, 9)


def _mode(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError("settings must name exactly color_source")
    mode = settings[PARAMETER]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"color_source must be one of {MODES}")
    return mode


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def program(settings: dict[str, Any]) -> str:
    return _PROGRAMS[_mode(settings)]


def _validate_grid(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    height, width = len(grid), len(grid[0])
    if height > 30 or width > 30:
        raise ValueError("grid must fit within 30x30")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return grid


def _rooms(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Return non-wall four-connected rooms in row-major discovery order."""
    _validate_grid(grid)
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 8 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _DIRS4:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] != 8
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            cells.sort()
            seeds = [(rr, cc, grid[rr][cc]) for rr, cc in cells if grid[rr][cc] not in (0, 8)]
            if len(seeds) != 1:
                raise ValueError("each room must contain exactly one nonzero non-wall seed")
            rows = [cell[0] for cell in cells]
            cols = [cell[1] for cell in cells]
            result.append({
                "cells": cells,
                "seed": seeds[0],
                "color": seeds[0][2],
                "bbox": (min(rows), min(cols), max(rows), max(cols)),
                "size": len(cells),
            })
    return result


def observables(grid: list[list[int]]) -> dict[str, Any]:
    rooms = _rooms(grid)
    colors = [room["color"] for room in rooms]
    return {
        "rooms": copy.deepcopy(rooms),
        "room_count": len(rooms),
        "seed_colors": colors,
        "next_seed_colors": colors[1:] + colors[:1],
        "previous_seed_colors": colors[-1:] + colors[:-1],
        "room_sizes": [room["size"] for room in rooms],
    }


def _fill_with_colors(grid: list[list[int]], colors: list[int]) -> list[list[int]]:
    rooms = _rooms(grid)
    if len(colors) != len(rooms):
        raise ValueError("one fill color is required per room")
    output = copy.deepcopy(grid)
    for room, color in zip(rooms, colors, strict=True):
        for row, col in room["cells"]:
            output[row][col] = color
    return output


def solve(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    mode = _mode(settings)
    facts = observables(grid)
    colors = facts["seed_colors"] if mode == "own" else facts["next_seed_colors"]
    return _fill_with_colors(grid, colors)


def validate_input(grid: Any) -> list[str]:
    try:
        _validate_grid(grid)
    except ValueError as exc:
        return [str(exc)]
    height, width = len(grid), len(grid[0])
    errors: list[str] = []
    if any(grid[0][col] != 8 or grid[-1][col] != 8 for col in range(width)):
        errors.append("top and bottom borders must be complete color-8 walls")
    if any(grid[row][0] != 8 or grid[row][-1] != 8 for row in range(height)):
        errors.append("left and right borders must be complete color-8 walls")
    full_rows = {row for row in range(height) if all(value == 8 for value in grid[row])}
    full_cols = {col for col in range(width) if all(grid[row][col] == 8 for row in range(height))}
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 8 and row not in full_rows and col not in full_cols:
                errors.append("every wall cell must belong to a complete wall row or column")
                break
        if errors and errors[-1].startswith("every wall"):
            break
    try:
        facts = observables(grid)
    except ValueError as exc:
        errors.append(str(exc))
        return errors
    if facts["room_count"] not in (3, 4):
        errors.append("generated scenes require three or four rooms")
    if len(set(facts["seed_colors"])) != facts["room_count"]:
        errors.append("generated room seeds must be distinct")
    if any(size < 4 for size in facts["room_sizes"]):
        errors.append("every room must contain at least four cells")
    if solve(grid, {PARAMETER: "own"}) == solve(grid, {PARAMETER: "next"}):
        errors.append("own and next labels must differ")
    return errors


def _axis_walls(length: int, parts: int) -> list[int]:
    if parts < 1:
        raise ValueError("parts must be positive")
    usable = length - (parts + 1)
    base, remainder = divmod(usable, parts)
    spans = [base + (1 if index < remainder else 0) for index in range(parts)]
    if min(spans) < 2:
        raise ValueError("layout leaves a room narrower than two cells")
    walls = [0]
    cursor = 0
    for span in spans:
        cursor += span + 1
        walls.append(cursor)
    if walls[-1] != length - 1:
        raise AssertionError("wall partition does not close at the outer border")
    return walls


def _chamber_cells(row_walls: list[int], col_walls: list[int]) -> list[list[tuple[int, int]]]:
    chambers = []
    for row_a, row_b in zip(row_walls, row_walls[1:]):
        for col_a, col_b in zip(col_walls, col_walls[1:]):
            chambers.append([
                (row, col)
                for row in range(row_a + 1, row_b)
                for col in range(col_a + 1, col_b)
            ])
    return chambers


def _derived_rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|{seed}|{split}|{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    rng = _derived_rng(seed, split, index)
    if split == "train":
        height, width = _DEMO_DIMS[index]
        row_parts, col_parts = _DEMO_LAYOUTS[index]
    elif split == "test":
        height, width = _QUERY_DIMS[index]
        row_parts, col_parts = _QUERY_LAYOUTS[index]
    else:  # pragma: no cover - internal guard
        raise ValueError(split)
    row_walls = _axis_walls(height, row_parts)
    col_walls = _axis_walls(width, col_parts)
    grid = [[0] * width for _ in range(height)]
    for row in row_walls:
        grid[row] = [8] * width
    for col in col_walls:
        for row in range(height):
            grid[row][col] = 8
    chambers = _chamber_cells(row_walls, col_walls)
    colors = list(_PALETTE)
    rng.shuffle(colors)
    for chamber, color in zip(chambers, colors, strict=False):
        row, col = rng.choice(chamber)
        grid[row][col] = color
    errors = validate_input(grid)
    if errors:
        raise AssertionError(f"constructed chamber scene violates grammar: {errors}")
    return grid


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    mode = _mode(settings)
    train_inputs = [_scene(seed, "train", index) for index in range(demos)]
    test_inputs = [_scene(seed, "test", index) for index in range(queries)]
    chosen = {PARAMETER: mode}
    return {
        "train": [{"input": grid, "output": solve(grid, chosen)} for grid in train_inputs],
        "test": [{"input": grid, "output": solve(grid, chosen)} for grid in test_inputs],
        "program_solution": _PROGRAMS[mode],
    }


def public_view(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    if type(query_index) is not int or isinstance(query_index, bool):
        raise ValueError("query_index must be an exact integer")
    tests = episode.get("test")
    if type(tests) is not list or not 0 <= query_index < len(tests):
        raise ValueError("query_index is outside the episode")
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(tests[query_index]["input"])}],
    }


def _rival_output(grid: list[list[int]], rival: str) -> list[list[int]]:
    facts = observables(grid)
    colors = facts["seed_colors"]
    if rival in MODES:
        return solve(grid, {PARAMETER: rival})
    if rival == "previous":
        return _fill_with_colors(grid, facts["previous_seed_colors"])
    if rival == "reverse":
        return _fill_with_colors(grid, list(reversed(colors)))
    if rival == "first_seed":
        return _fill_with_colors(grid, [colors[0]] * len(colors))
    if rival == "smallest_seed":
        return _fill_with_colors(grid, [min(colors)] * len(colors))
    if rival == "identity":
        return copy.deepcopy(grid)
    raise ValueError(rival)


def audit_episode(seed: int, mode: str, demos: int = 2, queries: int = 4) -> dict[str, Any]:
    episode = generate(seed, {PARAMETER: mode}, demos, queries)
    rivals = [candidate for candidate in MODES if candidate != mode]
    rivals += ["previous", "reverse", "first_seed", "smallest_seed", "identity"]
    reports = []
    harmful_survivors = []
    for rival in rivals:
        fits = all(_rival_output(pair["input"], rival) == pair["output"] for pair in episode["train"])
        changes_query = any(_rival_output(pair["input"], rival) != pair["output"] for pair in episode["test"])
        record = {"rival": rival, "fits_demos": fits, "changes_query": changes_query}
        reports.append(record)
        if fits and changes_query:
            harmful_survivors.append(record)
    return {
        "seed": seed,
        "settings": {PARAMETER: mode},
        "fit_uses": "demonstrations_only",
        "candidate_results": reports,
        "harmful_survivors": harmful_survivors,
        "query_shapes": [[len(pair["input"]), len(pair["input"][0])] for pair in episode["test"]],
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--color-source", choices=MODES, default=MODES[0])
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    args = parser.parse_args()
    print(json.dumps(generate(args.seed, {PARAMETER: args.color_source}, args.demos, args.queries), indent=2))
