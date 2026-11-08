"""Task-local authoring implementation for the 547c45a21db1 rule family.

Inputs are simple induced cardinal paths with endpoint seeds 2 and 3.  The
canonical setting colors each internal cell by nearest endpoint.  The alternate
setting first observes the path from seed 2, records the distance to its first
turn, then uses that input-dependent radius to grow endpoint colors inward.
Python labels are authoring claims; native qualification re-executes the exact
Racket programs through the protected runtime.
"""
from __future__ import annotations

import copy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from reviewer_support import (
    canonical_path,
    find_root,
    public_challenge_id,
)


TASK_ID = "547c45a21db1"
COLORING_MODES = ("nearest_seed", "first_turn_growth")
DEFAULT_COLORING_MODE = "nearest_seed"
HERE = Path(__file__).resolve().parent
DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

# (route height, route width, exact path length, first-turn distance from seed 2)
# The first two demonstrations already distinguish the settings and fixed-radius
# shortcuts.  Later demonstrations broaden size, orientation and turn depth.
DEMO_PROFILES = (
    (5, 7, 13, 2),
    (7, 8, 18, 3),
    (9, 10, 24, 4),
    (11, 12, 30, 5),
    (13, 14, 36, 3),
    (15, 16, 42, 6),
)
QUERY_PROFILES = (
    (7, 9, 17, 3),
    (11, 13, 28, 4),
    (19, 21, 44, 5),
    (29, 30, 121, 6),
)


def _load_canonical_program() -> str:
    matches: list[str] = []
    ledger = canonical_path(find_root(__file__))
    for line in ledger.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("content_hash") == TASK_ID:
            value = row.get("program_solution")
            if type(value) is not str or not value:
                raise RuntimeError("canonical row has no program_solution")
            matches.append(value)
    if len(matches) != 1:
        raise RuntimeError(f"expected one canonical row for {TASK_ID}, found {len(matches)}")
    return matches[0]


CANONICAL_PROGRAM = _load_canonical_program()


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2^63-1")
    return seed


def _validate_mode(value: Any) -> str:
    if type(value) is not str or value not in COLORING_MODES:
        raise ValueError(f"coloring_mode must be one of {COLORING_MODES}")
    return value


def validate_settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"coloring_mode"}:
        raise ValueError("settings must contain exactly coloring_mode")
    return {"coloring_mode": _validate_mode(settings["coloring_mode"])}


def _validate_count(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program_for(coloring_mode: str) -> str:
    mode = _validate_mode(coloring_mode)
    if mode == DEFAULT_COLORING_MODE:
        return CANONICAL_PROGRAM
    path = HERE / "rules" / "first_turn_growth.rkt"
    if not path.is_file():
        raise RuntimeError("first-turn growth Racket program is missing")
    return path.read_text(encoding="utf-8")


def program(settings: Any) -> str:
    normalized = validate_settings(settings)
    return program_for(normalized["coloring_mode"])


def _validate_grid(grid: Any) -> tuple[int, int]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or cell not in (0, 1, 2, 3) for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact colors 0,1,2,3")
    return len(grid), width


def _active_cells(grid: list[list[int]]) -> set[tuple[int, int]]:
    return {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value in (1, 2, 3)
    }


def _neighbors(cell: tuple[int, int], cells: set[tuple[int, int]]) -> list[tuple[int, int]]:
    row, col = cell
    return [
        (row + dr, col + dc)
        for dr, dc in DIRS4
        if (row + dr, col + dc) in cells
    ]


def path_order(grid: Any) -> list[tuple[int, int]]:
    """Return the validated active path ordered from seed 2 to seed 3."""
    _validate_grid(grid)
    cells = _active_cells(grid)
    if len(cells) < 4:
        raise ValueError("path needs at least four active cells")
    seed2 = [cell for cell in cells if grid[cell[0]][cell[1]] == 2]
    seed3 = [cell for cell in cells if grid[cell[0]][cell[1]] == 3]
    if len(seed2) != 1 or len(seed3) != 1:
        raise ValueError("path needs exactly one seed 2 and one seed 3")
    degrees = {cell: len(_neighbors(cell, cells)) for cell in cells}
    endpoints = {cell for cell, degree in degrees.items() if degree == 1}
    if endpoints != {seed2[0], seed3[0]} or any(
        degree not in (1, 2) for degree in degrees.values()
    ):
        raise ValueError("active cells must form an induced path with seeded endpoints")

    ordered: list[tuple[int, int]] = []
    previous: tuple[int, int] | None = None
    current: tuple[int, int] | None = seed2[0]
    while current is not None:
        ordered.append(current)
        onward = [cell for cell in _neighbors(current, cells) if cell != previous]
        if len(onward) > 1:
            raise ValueError("active cells branch")
        previous, current = current, onward[0] if onward else None
        if len(ordered) > len(cells):
            raise ValueError("active cells contain a cycle")
    if len(ordered) != len(cells) or ordered[-1] != seed3[0]:
        raise ValueError("active cells must be one connected path from 2 to 3")
    return ordered


def _direction(first: tuple[int, int], second: tuple[int, int]) -> list[int]:
    return [second[0] - first[0], second[1] - first[1]]


def first_turn_intermediate(grid: Any) -> dict[str, Any]:
    """Observe A: first turn distance and orientation while walking from seed 2."""
    path = path_order(grid)
    for index in range(1, len(path) - 1):
        incoming = _direction(path[index - 1], path[index])
        outgoing = _direction(path[index], path[index + 1])
        if incoming != outgoing:
            return {
                "radius": index,
                "first_turn_cell": list(path[index]),
                "incoming": incoming,
                "outgoing": outgoing,
                "turn_found": True,
                "path_length": len(path),
            }
    # The admitted sampler always bends, but a straight lawful path remains
    # explicit and total: its endpoint distance becomes the growth radius.
    return {
        "radius": len(path) - 1,
        "first_turn_cell": list(path[-1]),
        "incoming": _direction(path[-2], path[-1]),
        "outgoing": [0, 0],
        "turn_found": False,
        "path_length": len(path),
    }


def _growth_output(
    grid: list[list[int]], path: list[tuple[int, int]], radius: int
) -> list[list[int]]:
    if type(radius) is not int or radius < 0:
        raise ValueError("radius must be a nonnegative exact integer")
    output = copy.deepcopy(grid)
    final = len(path) - 1
    for index, (row, col) in enumerate(path[1:-1], start=1):
        near2 = index <= radius
        near3 = final - index <= radius
        output[row][col] = 4 if near2 and near3 else 2 if near2 else 3 if near3 else 1
    return output


def apply_python(
    grid: Any, coloring_mode: Any, *, radius_override: int | None = None
) -> list[list[int]]:
    """Diagnostic Python mirror used for fixtures, never qualification authority."""
    mode = _validate_mode(coloring_mode)
    path = path_order(grid)
    if mode == "nearest_seed":
        output = copy.deepcopy(grid)
        final = len(path) - 1
        for index, (row, col) in enumerate(path[1:-1], start=1):
            output[row][col] = 2 if index < final - index else 3 if final - index < index else 4
        return output
    radius = (
        first_turn_intermediate(grid)["radius"]
        if radius_override is None
        else radius_override
    )
    return _growth_output(grid, path, radius)


def _digest_int(seed: int, split: str, index: int, salt: str) -> int:
    payload = f"{TASK_ID}|v1|{seed}|{split}|{index}|{salt}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _spaced_snake(height: int, width: int) -> list[tuple[int, int]]:
    path: list[tuple[int, int]] = []
    for stripe, row in enumerate(range(0, height, 2)):
        if path:
            path.append((row - 1, path[-1][1]))
        columns: Iterable[int] = range(width) if stripe % 2 == 0 else range(width - 1, -1, -1)
        path.extend((row, col) for col in columns)
    return path


def _turn_indices(path: tuple[tuple[int, int], ...] | list[tuple[int, int]]) -> list[int]:
    return [
        index
        for index in range(1, len(path) - 1)
        if _direction(path[index - 1], path[index])
        != _direction(path[index], path[index + 1])
    ]


def _is_induced_path(path: tuple[tuple[int, int], ...] | list[tuple[int, int]]) -> bool:
    cells = set(path)
    if len(cells) != len(path):
        return False
    return all(
        len(_neighbors(cell, cells)) == (1 if index in (0, len(path) - 1) else 2)
        for index, cell in enumerate(path)
    )


@lru_cache(maxsize=None)
def _profile_candidates(profile: tuple[int, int, int, int]) -> tuple[tuple[tuple[int, int], ...], ...]:
    height, width, length, target_radius = profile
    route = _spaced_snake(height, width)
    candidates: list[tuple[tuple[int, int], ...]] = []
    for oriented in (route, list(reversed(route))):
        for start in range(len(oriented) - length + 1):
            candidate = tuple(oriented[start : start + length])
            turns = _turn_indices(candidate)
            if turns and turns[0] == target_radius and _is_induced_path(candidate):
                candidates.append(candidate)
    if not candidates:
        raise RuntimeError(f"no induced path candidate for profile {profile}")
    return tuple(candidates)


def _transform_path(
    path: tuple[tuple[int, int], ...],
    height: int,
    width: int,
    code: int,
) -> tuple[list[tuple[int, int]], int, int]:
    transforms = (
        (lambda r, c: (r, c), height, width),
        (lambda r, c: (c, height - 1 - r), width, height),
        (lambda r, c: (height - 1 - r, width - 1 - c), height, width),
        (lambda r, c: (width - 1 - c, r), width, height),
        (lambda r, c: (r, width - 1 - c), height, width),
        (lambda r, c: (height - 1 - r, c), height, width),
        (lambda r, c: (c, r), width, height),
        (lambda r, c: (width - 1 - c, height - 1 - r), width, height),
    )
    transform, transformed_h, transformed_w = transforms[code % len(transforms)]
    return [transform(row, col) for row, col in path], transformed_h, transformed_w


def make_input(seed: Any, *, split: str, index: int) -> list[list[int]]:
    seed = _validate_seed(seed)
    if split not in {"demo", "query"}:
        raise ValueError("split must be 'demo' or 'query'")
    if type(index) is not int or index < 0:
        raise ValueError("index must be a nonnegative exact integer")
    profiles = DEMO_PROFILES if split == "demo" else QUERY_PROFILES
    if index >= len(profiles):
        raise ValueError(f"{split} index {index} exceeds supported profiles")
    profile = profiles[index]
    route_h, route_w, _, expected_radius = profile
    candidates = _profile_candidates(profile)
    chosen = candidates[_digest_int(seed, split, index, "candidate") % len(candidates)]
    transform_code = (
        2 * (_digest_int(seed, split, index, "d4") % 2)
        if split == "query" and index == len(QUERY_PROFILES) - 1
        else _digest_int(seed, split, index, "d4") % 8
    )
    transformed, body_h, body_w = _transform_path(
        chosen,
        route_h,
        route_w,
        transform_code,
    )

    if split == "query" and index == len(QUERY_PROFILES) - 1:
        canvas_h = canvas_w = 30
    else:
        canvas_h = min(30, body_h + 2 + _digest_int(seed, split, index, "pad-r") % 3)
        canvas_w = min(30, body_w + 2 + _digest_int(seed, split, index, "pad-c") % 3)
    row_room = canvas_h - body_h
    col_room = canvas_w - body_w
    row0 = 0 if split == "query" and index == 3 else _digest_int(seed, split, index, "row0") % (row_room + 1)
    col0 = 0 if split == "query" and index == 3 else _digest_int(seed, split, index, "col0") % (col_room + 1)
    placed = [(row + row0, col + col0) for row, col in transformed]

    grid = [[0 for _ in range(canvas_w)] for _ in range(canvas_h)]
    for row, col in placed:
        grid[row][col] = 1
    grid[placed[0][0]][placed[0][1]] = 2
    grid[placed[-1][0]][placed[-1][1]] = 3

    facts = first_turn_intermediate(grid)
    if facts["radius"] != expected_radius or not facts["turn_found"]:
        raise AssertionError("D4 placement changed the selected first-turn depth")
    return grid



RIVAL_NAMES = (
    "other_setting",
    "fixed_radius_1",
    "fixed_radius_2",
    "first_turn_minus_one",
    "first_turn_plus_one",
    "last_turn_radius",
)


def _last_turn_radius(grid: Any) -> int:
    path = path_order(grid)
    turns = _turn_indices(path)
    return turns[-1] if turns else len(path) - 1


def _rival_output(grid: Any, selected_mode: str, rival: str) -> list[list[int]]:
    if rival == "other_setting":
        other = "first_turn_growth" if selected_mode == "nearest_seed" else "nearest_seed"
        return apply_python(grid, other)
    radius = first_turn_intermediate(grid)["radius"]
    overrides = {
        "fixed_radius_1": 1,
        "fixed_radius_2": 2,
        "first_turn_minus_one": max(0, radius - 1),
        "first_turn_plus_one": radius + 1,
        "last_turn_radius": _last_turn_radius(grid),
    }
    if rival not in overrides:
        raise ValueError(f"unknown rival {rival!r}")
    return apply_python(grid, "first_turn_growth", radius_override=overrides[rival])


def bounded_rival_audit(seed: Any, demos: Any = 2) -> dict[str, Any]:
    """Finite authoring audit; this is not a proof beyond the declared scope."""
    seed = _validate_seed(seed)
    demos = _validate_count(demos, 2, 6, "demos")
    grids = [make_input(seed, split="demo", index=index) for index in range(demos)]
    survivors: dict[str, list[str]] = {}
    refutations: dict[str, dict[str, int]] = {}
    for selected in COLORING_MODES:
        expected = [apply_python(grid, selected) for grid in grids]
        surviving: list[str] = []
        selected_refutations: dict[str, int] = {}
        for rival in RIVAL_NAMES:
            outputs = [_rival_output(grid, selected, rival) for grid in grids]
            mismatch = next(
                (index for index, (got, want) in enumerate(zip(outputs, expected, strict=True)) if got != want),
                None,
            )
            if mismatch is None:
                surviving.append(rival)
            else:
                selected_refutations[rival] = mismatch
        survivors[selected] = surviving
        refutations[selected] = selected_refutations
    return {
        "scope": {
            "seeds": [seed],
            "demonstrations_per_setting": demos,
            "settings": list(COLORING_MODES),
        },
        "rivals": list(RIVAL_NAMES),
        "survivors": survivors,
        "refutations": refutations,
        "all_refuted": not any(survivors.values()),
    }


def public_projection(episode: Any) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or not train or type(test) is not list or not test:
        raise ValueError("episode must contain nonempty train and test lists")
    try:
        return {
            "train": [
                {
                    "input": copy.deepcopy(pair["input"]),
                    "output": copy.deepcopy(pair["output"]),
                }
                for pair in train
            ],
            "test": [{"input": copy.deepcopy(pair["input"])} for pair in test],
        }
    except (KeyError, TypeError) as error:
        raise ValueError("episode pairs must contain private labels") from error


def public_id(episode: Any) -> str:
    return public_challenge_id(public_projection(episode))

def generate_episode(
    seed: Any,
    *,
    coloring_mode: Any,
    demos: Any = 3,
    queries: Any = 4,
) -> dict[str, Any]:
    seed = _validate_seed(seed)
    mode = _validate_mode(coloring_mode)
    demos = _validate_count(demos, 2, 6, "demos")
    queries = _validate_count(queries, 1, 4, "queries")

    all_demo_inputs = [make_input(seed, split="demo", index=index) for index in range(6)]
    all_query_inputs = [make_input(seed, split="query", index=index) for index in range(4)]

    def pairs(grids: list[list[list[int]]]) -> list[dict[str, list[list[int]]]]:
        return [
            {"input": copy.deepcopy(grid), "output": apply_python(grid, mode)}
            for grid in grids
        ]

    return {
        "train": pairs(all_demo_inputs[:demos]),
        "test": pairs(all_query_inputs[:queries]),
        "program_solution": program_for(mode),
    }
