"""Deterministic matched-input authoring prototype for room gravity variants."""
from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Iterable

MODES = ("canonical", "bottom_color_relay")
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)

Cell = tuple[int, int]
Room = list[Cell]


def _integer(name: str, value: int, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def validate_request(seed: int, settings: dict, demos: int, queries: int) -> str:
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, *DEMO_LIMITS)
    _integer("queries", queries, *QUERY_LIMITS)
    if not isinstance(settings, dict) or set(settings) != {"mode"}:
        raise ValueError("settings must contain exactly mode")
    mode = settings["mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    return mode


def _partition(interior: int, minimums: list[int], rng: random.Random) -> tuple[list[tuple[int, int]], list[int]]:
    room_cells = interior - (len(minimums) - 1)
    if room_cells < sum(minimums):
        raise ValueError("canvas is too small for the room partition")
    sizes = list(minimums)
    for _ in range(room_cells - sum(sizes)):
        sizes[rng.randrange(len(sizes))] += 1
    segments: list[tuple[int, int]] = []
    dividers: list[int] = []
    cursor = 1
    for index, size in enumerate(sizes):
        segments.append((cursor, cursor + size - 1))
        cursor += size
        if index + 1 < len(sizes):
            dividers.append(cursor)
            cursor += 1
    return segments, dividers


def _rooms(row_segments: list[tuple[int, int]], col_segments: list[tuple[int, int]]) -> list[Room]:
    return [
        [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]
        for r0, r1 in row_segments
        for c0, c1 in col_segments
    ]


def _room_columns(room: Room) -> list[list[Cell]]:
    return [
        sorted((r, c) for r, c in room if c == column)
        for column in sorted({c for _r, c in room})
    ]


def _profile(index: int, *, query: bool) -> tuple[int, int]:
    if query:
        return ((9, 16), (13, 19), (18, 24), (30, 30))[index]
    return ((8, 14), (10, 17), (12, 20), (15, 23), (18, 26), (22, 28))[index]


def _target_intermediate(index: int, *, query: bool) -> int:
    return ((1, 3, 2, 2) if query else (2, 3, 1, 2, 3, 1))[index]


def _put_payload(grid: list[list[int]], room: Room, rng: random.Random, role: int) -> None:
    columns = _room_columns(room)
    colors = (1, 3, 4, 6, 7, 2, 8)
    target = min(len(room) - 1, 3 + role + rng.randrange(3))
    positions: list[Cell] = []
    # Make gravity visibly move a stable two-marker stack.
    first = columns[role % len(columns)]
    if len(first) >= 3:
        positions.extend(first[:2])
    candidates = [cell for col in columns for cell in col[:-1] if cell not in positions]
    rng.shuffle(candidates)
    positions.extend(candidates[: max(0, target - len(positions))])
    for offset, (r, c) in enumerate(positions):
        grid[r][c] = colors[(role + offset) % len(colors)]


def build_input(seed: int, index: int, *, query: bool) -> list[list[int]]:
    h, w = _profile(index, query=query)
    rng = random.Random((seed + 1) * 1_000_003 + (index + 1) * 97_409 + (10_000_019 if query else 0))
    row_segments, divider_rows = _partition(h - 2, [3, 2], rng)
    col_segments, divider_cols = _partition(w - 2, [3, 2, 2, 2], rng)
    rooms = _rooms(row_segments, col_segments)

    grid = [[0 for _ in range(w)] for _ in range(h)]
    for r in range(h):
        grid[r][0] = grid[r][w - 1] = 5
    for c in range(w):
        grid[0][c] = grid[h - 1][c] = 5
    for r in divider_rows:
        for c in range(w):
            grid[r][c] = 5
    for c in divider_cols:
        for r in range(h):
            grid[r][c] = 5

    k = _target_intermediate(index, query=query)
    controller_columns = _room_columns(rooms[0])
    if len(controller_columns) < 3 or any(len(column) < 3 for column in controller_columns[:3]):
        raise ValueError("controller room cannot carry three cue columns")
    for cue_index, column in enumerate(controller_columns[:3]):
        top, second = column[0], column[1]
        values = (2 + cue_index % 3, 9) if cue_index < k else (9, 2 + cue_index % 3)
        grid[top[0]][top[1]], grid[second[0]][second[1]] = values
    for extra_index, column in enumerate(controller_columns[3:]):
        if len(column) >= 2:
            r, c = column[0]
            grid[r][c] = (6, 7, 4)[extra_index % 3]

    for room_index, room in enumerate(rooms[1:], start=1):
        _put_payload(grid, room, rng, room_index)
    return grid


def _nonwall_rooms(grid: list[list[int]]) -> list[Room]:
    h, w = len(grid), len(grid[0])
    seen: set[Cell] = set()
    rooms: list[Room] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 5 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            room: Room = []
            while stack:
                rr, cc = stack.pop()
                room.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 5 and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rooms.append(sorted(room))
    return sorted(rooms, key=lambda room: (min(r for r, _ in room), min(c for _, c in room)))


def canonical_output(grid: list[list[int]]) -> list[list[int]]:
    out = [[5 if value == 5 else 0 for value in row] for row in grid]
    for room in _nonwall_rooms(grid):
        for column in _room_columns(room):
            values = [grid[r][c] for r, c in column if grid[r][c] != 0]
            for (r, c), value in zip(column[-len(values):] if values else (), values):
                out[r][c] = value
    return out


def controller_intermediate(grid: list[list[int]]) -> int:
    settled = canonical_output(grid)
    controller = _nonwall_rooms(grid)[0]
    bottom = max(r for r, _ in controller)
    columns = sorted({c for _r, c in controller})
    value = sum(settled[bottom][c] == 9 for c in columns)
    if value not in (1, 2, 3):
        raise ValueError(f"controller intermediate must be 1..3, found {value}")
    return value


def raw_bottom_intermediate(grid: list[list[int]]) -> int:
    controller = _nonwall_rooms(grid)[0]
    bottom = max(r for r, _ in controller)
    raw = sum(grid[bottom][c] == 9 for c in sorted({c for _r, c in controller}))
    return max(1, min(3, raw))


def _relay_with_intermediate(grid: list[list[int]], value: int) -> list[list[int]]:
    settled = canonical_output(grid)
    rooms = _nonwall_rooms(grid)
    selected = rooms[value]
    for r, c in selected:
        if settled[r][c] != 0:
            settled[r][c] = 8
    return settled


def relay_output(grid: list[list[int]]) -> list[list[int]]:
    return _relay_with_intermediate(grid, controller_intermediate(grid))


def raw_bottom_relay_output(grid: list[list[int]]) -> list[list[int]]:
    return _relay_with_intermediate(grid, raw_bottom_intermediate(grid))


def fixed_relay_output(grid: list[list[int]], value: int) -> list[list[int]]:
    return _relay_with_intermediate(grid, value)


def all_nines_relay_output(grid: list[list[int]]) -> list[list[int]]:
    controller = _nonwall_rooms(grid)[0]
    value = max(1, min(3, sum(grid[r][c] == 9 for r, c in controller)))
    return _relay_with_intermediate(grid, value)


def generate_pairs(seed: int, demos: int, queries: int, mode: str) -> list[dict]:
    output = canonical_output if mode == "canonical" else relay_output
    pairs: list[dict] = []
    for index in range(demos):
        grid = build_input(seed, index, query=False)
        pairs.append({"input": grid, "output": output(grid)})
    for index in range(queries):
        grid = build_input(seed, index, query=True)
        pairs.append({"input": grid, "output": output(grid)})
    return pairs
