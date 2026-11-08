"""Causal parametric family for barrier-aware distance bands.

``original_seeds`` is the byte-exact canonical rule. ``farthest_relay`` first
runs the canonical multi-source, wall-aware BFS, chooses the row-major first cell
at maximum reachable distance, and then runs a second wall-aware BFS from that
input-dependent relay.  Inputs are sampled independently of the hidden setting.
"""
from __future__ import annotations

from collections import deque
import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any


TASK_ID = "9199b47fab1e"
HERE = Path(__file__).resolve().parent
SOURCE_MODES = ("original_seeds", "farthest_relay")
WALL_COLORS = (6, 7, 8, 9)
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
COLORS = (3, 4, 5)


def normalize_settings(settings: dict[str, Any]) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"source_mode"}:
        raise ValueError("settings must contain exactly source_mode")
    mode = settings["source_mode"]
    if type(mode) is not str or mode not in SOURCE_MODES:
        raise ValueError(f"source_mode must be one of {SOURCE_MODES}")
    return {"source_mode": mode}


def program(settings: dict[str, Any]) -> str:
    mode = normalize_settings(settings)["source_mode"]
    name = "canonical.rkt" if mode == "original_seeds" else "farthest_relay.rkt"
    return (HERE / name).read_text()


def _validate_grid(grid: Any) -> tuple[int, int, int]:
    if (
        type(grid) is not list
        or not 5 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 5 <= len(grid[0]) <= 30
    ):
        raise ValueError("input must be a rectangular 5..30 grid")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("input cells must be exact integer ARC colors")
    seeds = sum(value == 2 for row in grid for value in row)
    if not 1 <= seeds <= 3:
        raise ValueError("input requires 1..3 color-2 sources")
    wall_colors = {value for row in grid for value in row if value not in (0, 2)}
    if len(wall_colors) != 1 or next(iter(wall_colors)) not in WALL_COLORS:
        raise ValueError("input requires exactly one wall color from 6,7,8,9")
    return len(grid), width, next(iter(wall_colors))


def _distances(grid: list[list[int]], sources: list[tuple[int, int]]) -> dict[tuple[int, int], int]:
    height, width = len(grid), len(grid[0])
    distance = {point: 0 for point in sources}
    queue = deque(sources)
    while queue:
        row, column = queue.popleft()
        for dr, dc in CARDINAL:
            nr, nc = row + dr, column + dc
            if (
                0 <= nr < height
                and 0 <= nc < width
                and (nr, nc) not in distance
                and grid[nr][nc] in (0, 2)
            ):
                distance[(nr, nc)] = distance[(row, column)] + 1
                queue.append((nr, nc))
    return distance


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    _validate_grid(grid)
    sources = [
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value == 2
    ]
    primary = _distances(grid, sources)
    maximum = max(primary.values())
    relay = min(point for point, distance in primary.items() if distance == maximum)
    return {
        "sources": tuple(sources),
        "primary_distances": primary,
        "maximum_primary_distance": maximum,
        "relay": relay,
    }


def _paint(grid: list[list[int]], distances: dict[tuple[int, int], int]) -> list[list[int]]:
    output = copy.deepcopy(grid)
    for (row, column), distance in distances.items():
        output[row][column] = COLORS[distance % 3]
    return output


def solve_from_relay(grid: list[list[int]], relay: tuple[int, int]) -> list[list[int]]:
    facts = analyze(grid)
    if (
        type(relay) is not tuple
        or len(relay) != 2
        or any(type(value) is not int for value in relay)
        or relay not in facts["primary_distances"]
    ):
        raise ValueError("relay must be an exact primary-reachable coordinate")
    return _paint(grid, _distances(grid, [relay]))


def solve_python(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    mode = normalize_settings(settings)["source_mode"]
    facts = analyze(grid)
    if mode == "original_seeds":
        return _paint(grid, facts["primary_distances"])
    return solve_from_relay(grid, facts["relay"])


def _paint_frame(grid: list[list[int]], top: int, left: int, bottom: int, right: int, color: int) -> None:
    for column in range(left, right + 1):
        grid[top][column] = color
        grid[bottom][column] = color
    for row in range(top + 1, bottom):
        grid[row][left] = color
        grid[row][right] = color


def _open_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(height):
        for column in range(width):
            if grid[row][column] != 0 or (row, column) in seen:
                continue
            component: list[tuple[int, int]] = []
            queue = deque([(row, column)])
            seen.add((row, column))
            while queue:
                current = queue.popleft()
                component.append(current)
                for dr, dc in CARDINAL:
                    neighbor = current[0] + dr, current[1] + dc
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and grid[neighbor[0]][neighbor[1]] == 0
                        and neighbor not in seen
                    ):
                        seen.add(neighbor)
                        queue.append(neighbor)
            result.append(component)
    return result


def _rng(seed: int, split: str, index: int, attempt: int) -> random.Random:
    raw = f"{TASK_ID}:farthest-relay-v1:{seed}:{split}:{index}:{attempt}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _profile(split: str, index: int) -> tuple[str, int, int, int]:
    train = (
        ("vertical_split", 11, 13, 2),
        ("gated", 12, 14, 1),
        ("horizontal_split", 13, 11, 2),
        ("cross", 15, 15, 3),
        ("inner_box", 16, 18, 2),
        ("double_split", 18, 20, 3),
    )
    test = (
        ("staggered", 13, 17, 2),
        ("cross_gates", 19, 17, 2),
        ("rooms", 23, 27, 3),
        ("labyrinth30", 30, 30, 3),
    )
    table = train if split == "train" else test
    return table[index]


def _draw_walls(profile: str, height: int, width: int, color: int, rng: random.Random) -> list[list[int]]:
    grid = [[0] * width for _ in range(height)]
    margin = 0 if profile == "labyrinth30" else 1
    _paint_frame(grid, margin, margin, height - 1 - margin, width - 1 - margin, color)
    top, left, bottom, right = margin, margin, height - 1 - margin, width - 1 - margin

    if profile == "vertical_split":
        column = width // 2 + rng.choice((-1, 0, 1))
        for row in range(top, bottom + 1):
            grid[row][column] = color
    elif profile == "gated":
        column = width // 2 + rng.choice((-1, 0, 1))
        gap = rng.randint(top + 2, bottom - 2)
        for row in range(top, bottom + 1):
            if row != gap:
                grid[row][column] = color
    elif profile == "horizontal_split":
        row = height // 2 + rng.choice((-1, 0, 1))
        for column in range(left, right + 1):
            grid[row][column] = color
    elif profile == "cross":
        row = height // 2 + rng.choice((-1, 0, 1))
        column = width // 2 + rng.choice((-1, 0, 1))
        for c in range(left, right + 1):
            grid[row][c] = color
        for r in range(top, bottom + 1):
            grid[r][column] = color
    elif profile == "inner_box":
        inset_r = rng.randint(3, 4)
        inset_c = rng.randint(3, 5)
        _paint_frame(grid, inset_r, inset_c, height - 1 - inset_r, width - 1 - inset_c, color)
    elif profile == "double_split":
        for column in (width // 3, (2 * width) // 3):
            for row in range(top, bottom + 1):
                grid[row][column] = color
    elif profile == "staggered":
        first, second = width // 3, (2 * width) // 3
        for row in range(top, height // 2 + 1):
            grid[row][first] = color
        for row in range(height // 2 - 1, bottom + 1):
            grid[row][second] = color
        # One boundary-touching spur makes border handling visible after transforms.
        for column in range(0, first + 1):
            grid[height // 2][column] = color
    elif profile == "cross_gates":
        row, column = height // 2, width // 2
        row_gap = rng.choice((left + 2, right - 2))
        col_gap = rng.choice((top + 2, bottom - 2))
        for c in range(left, right + 1):
            if c != row_gap:
                grid[row][c] = color
        for r in range(top, bottom + 1):
            if r != col_gap:
                grid[r][column] = color
    elif profile == "rooms":
        for column in (width // 3, (2 * width) // 3):
            gaps = {rng.randint(2, height // 2 - 1), rng.randint(height // 2 + 1, height - 3)}
            for row in range(top, bottom + 1):
                if row not in gaps:
                    grid[row][column] = color
        for row in (height // 3, (2 * height) // 3):
            gaps = {rng.randint(2, width // 2 - 1), rng.randint(width // 2 + 1, width - 3)}
            for column in range(left, right + 1):
                if column not in gaps:
                    grid[row][column] = color
    elif profile == "labyrinth30":
        # Full boundary plus alternating barrier gates and crossbars provide
        # substantive 30x30 content across all four edges and the interior.
        for index, column in enumerate(range(4, width - 3, 4)):
            gaps = {2 + (index * 7) % (height - 4), 2 + (index * 11 + 5) % (height - 4)}
            for row in range(1, height - 1):
                if row not in gaps:
                    grid[row][column] = color
        for index, row in enumerate(range(5, height - 3, 5)):
            gaps = {2 + (index * 9) % (width - 4), 2 + (index * 13 + 3) % (width - 4)}
            for column in range(1, width - 1):
                if column not in gaps:
                    grid[row][column] = color
    else:
        raise ValueError(f"unknown profile {profile!r}")
    return grid


def _seed_components(grid: list[list[int]], count: int, rng: random.Random) -> None:
    height, width = len(grid), len(grid[0])
    interior = [
        component
        for component in _open_components(grid)
        if not any(row in (0, height - 1) or column in (0, width - 1) for row, column in component)
    ]
    interior.sort(key=lambda component: (-len(component), min(component)))
    if not interior:
        raise ValueError("profile has no enclosed traversable component")
    selected = interior[: min(count, len(interior))]
    while len(selected) < count:
        selected.append(interior[len(selected) % len(interior)])
    used: set[tuple[int, int]] = set()
    for component in selected:
        preferred = [
            point
            for point in component
            if point not in used
            and all(
                0 <= point[0] + dr < height
                and 0 <= point[1] + dc < width
                and grid[point[0] + dr][point[1] + dc] == 0
                for dr, dc in CARDINAL
            )
        ]
        candidates = preferred or [point for point in component if point not in used]
        if not candidates:
            raise ValueError("profile cannot place distinct sources")
        point = rng.choice(candidates)
        used.add(point)
        grid[point[0]][point[1]] = 2


def _transform(grid: list[list[int]], rotation: int, reflect: bool) -> list[list[int]]:
    result = [row[:] for row in grid]
    if reflect:
        result = [row[::-1] for row in result]
    for _ in range(rotation):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def _input(seed: int, split: str, index: int, attempt: int) -> list[list[int]]:
    profile, height, width, sources = _profile(split, index)
    rng = _rng(seed, split, index, attempt)
    wall_color = WALL_COLORS[(seed + index + (0 if split == "train" else 2)) % len(WALL_COLORS)]
    grid = _draw_walls(profile, height, width, wall_color, rng)
    _seed_components(grid, sources, rng)
    # Rectangular scenes may rotate only by 0/180 so profile dimensions remain
    # role-stable; square stress scenes use all orientations.
    rotation = rng.randrange(4) if height == width else 2 * rng.randrange(2)
    return _transform(grid, rotation, bool(rng.randrange(2)))


def _integer(value: int, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def teaching_check(episode: dict[str, Any]) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list:
        return {"ok": False, "reason": "episode needs a training list"}
    selected_program = episode.get("program_solution")
    survivors = []
    for mode in SOURCE_MODES:
        settings = {"source_mode": mode}
        try:
            if all(
                solve_python(pair["input"], settings) == pair["output"]
                for pair in episode["train"]
            ):
                survivors.append(mode)
        except (KeyError, TypeError, ValueError):
            return {"ok": False, "reason": "malformed demonstration"}
    expected = [mode for mode in SOURCE_MODES if program({"source_mode": mode}) == selected_program]
    return {
        "ok": survivors == expected and len(survivors) == 1,
        "survivors": survivors,
        "expected": expected,
        "finite_family": list(SOURCE_MODES),
    }


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    normalized = normalize_settings(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    used: set[str] = set()
    result: dict[str, list[dict[str, list[list[int]]]]] = {}
    for split, count in (("train", demos), ("test", queries)):
        pairs = []
        for index in range(count):
            for attempt in range(32):
                grid = _input(seed, split, index, attempt)
                key = json.dumps(grid, separators=(",", ":"))
                if key in used:
                    continue
                canonical = solve_python(grid, {"source_mode": "original_seeds"})
                relay = solve_python(grid, {"source_mode": "farthest_relay"})
                if canonical == relay:
                    continue
                used.add(key)
                break
            else:
                raise RuntimeError(f"distinct informative input budget exhausted at {split}[{index}]")
            pairs.append({"input": grid, "output": solve_python(grid, normalized)})
        result[split] = pairs
    episode = {
        "train": result["train"],
        "test": result["test"],
        "program_solution": program(normalized),
        "seed": seed,
        "settings": copy.deepcopy(normalized),
    }
    certificate = teaching_check(episode)
    if not certificate["ok"]:
        raise RuntimeError(f"constructive demonstrations failed finite identification: {certificate}")
    return episode


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }
