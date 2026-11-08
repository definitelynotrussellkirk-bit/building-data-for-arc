"""Promotion-grade tie-marker family for the room-graph task.

Inputs are independent of the private setting.  The default marker 8 preserves
canonical behavior byte-for-byte; marker 6 changes only the color used when the
nearest *distinct colors* tie.  Labels returned here are deterministic claims;
native qualification re-executes every pair through protected Racket.
"""
from __future__ import annotations

from collections import deque
import hashlib
import random
from typing import Iterable

TASK_ID = "1b2b9283b4ab"
VERSION = "native-tie-marker-v1"
TIE_MARKERS = (8, 6)
SEED_COLORS = (2, 3, 4, 5)
WALLS = frozenset({1, 7, 9})

_DEMO_SPECS = (
    {"rows": 3, "cols": 3, "room": (2, 3), "graph": "same_color", "seeds": (0, 2, 6)},
    {"rows": 1, "cols": 5, "room": (4, 3), "graph": "island", "seeds": (0, 4)},
    {"rows": 1, "cols": 5, "room": (3, 3), "graph": "path", "seeds": (0, 4)},
    {"rows": 3, "cols": 3, "room": (3, 2), "graph": "grid", "seeds": (0, 8)},
    {"rows": 3, "cols": 3, "room": (3, 3), "graph": "serpentine", "seeds": (0, 8)},
    {"rows": 3, "cols": 5, "room": (3, 3), "graph": "grid", "seeds": (0, 14)},
)
_QUERY_SPECS = (
    {"rows": 1, "cols": 7, "room": (4, 3), "graph": "path", "seeds": (0, 6)},
    {"rows": 4, "cols": 4, "room": (3, 3), "graph": "grid", "seeds": (0, 15)},
    {"rows": 2, "cols": 5, "room": (3, 4), "graph": "disconnected", "seeds": (0, 9)},
    {"rows": 5, "cols": 5, "room": (4, 4), "graph": "grid", "seeds": (0, 24), "canvas": (30, 30)},
)


def _exact_int(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def validate_marker(value: object) -> int:
    if type(value) is not int or value not in TIE_MARKERS:
        raise ValueError(f"tie_marker must be one of {TIE_MARKERS}")
    return value


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = f"{TASK_ID}:{VERSION}:{seed}:{split}:{index}".encode("ascii")
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _serpentine(rows: int, cols: int) -> list[int]:
    return [r * cols + c for r in range(rows)
            for c in (range(cols) if r % 2 == 0 else range(cols - 1, -1, -1))]


def _grid_edges(rows: int, cols: int) -> list[tuple[int, int]]:
    return [(r * cols + c, rr * cols + cc)
            for r in range(rows) for c in range(cols)
            for rr, cc in ((r + 1, c), (r, c + 1)) if rr < rows and cc < cols]


def _edges(spec: dict) -> list[tuple[int, int]]:
    rows, cols, kind = spec["rows"], spec["cols"], spec["graph"]
    route = _serpentine(rows, cols)
    if kind in {"path", "serpentine", "same_color"}:
        return list(zip(route, route[1:]))
    if kind == "grid":
        return _grid_edges(rows, cols)
    if kind == "island":
        return [(0, 1), (3, 4)]
    if kind == "disconnected":
        return [(0, 1), (1, 2), (7, 8), (8, 9)]
    raise ValueError(f"unknown graph kind {kind!r}")


def _rotate(grid: list[list[int]], turns: int) -> list[list[int]]:
    out = [row[:] for row in grid]
    for _ in range(turns % 4):
        out = [list(row) for row in zip(*out[::-1])]
    return out


def _render(spec: dict, rng: random.Random) -> list[list[int]]:
    rows, cols = spec["rows"], spec["cols"]
    room_h, room_w = spec["room"]
    motif_h = 1 + rows * (room_h + 1)
    motif_w = 1 + cols * (room_w + 1)
    canvas_h, canvas_w = spec.get("canvas", (motif_h, motif_w))
    if canvas_h < motif_h or canvas_w < motif_w or canvas_h > 30 or canvas_w > 30:
        raise ValueError("invalid case canvas")
    wall = 9 if rng.randrange(4) == 0 else 1
    grid = [[wall for _ in range(canvas_w)] for _ in range(canvas_h)]
    top = (canvas_h - motif_h) // 2
    left = (canvas_w - motif_w) // 2

    def origin(room: int) -> tuple[int, int]:
        r, c = divmod(room, cols)
        return top + 1 + r * (room_h + 1), left + 1 + c * (room_w + 1)

    for room in range(rows * cols):
        r0, c0 = origin(room)
        for r in range(r0, r0 + room_h):
            for c in range(c0, c0 + room_w):
                grid[r][c] = 0

    for a, b in _edges(spec):
        a, b = sorted((a, b))
        r0, c0 = origin(a)
        if b == a + 1 and a // cols == b // cols:
            grid[r0 + rng.randrange(room_h)][c0 + room_w] = 7
        elif b == a + cols:
            grid[r0 + room_h][c0 + rng.randrange(room_w)] = 7
        else:
            raise ValueError("non-cardinal room edge")

    seed_rooms = tuple(spec["seeds"])
    if spec["graph"] == "same_color":
        low, extra, high = sorted(rng.sample(SEED_COLORS, 3))
        colors = (low, low, high)
        extras = ((seed_rooms[0], extra),)
    else:
        colors = tuple(rng.sample(SEED_COLORS, len(seed_rooms)))
        extras = ()

    def place(room: int, color: int) -> None:
        r0, c0 = origin(room)
        free = [(r, c) for r in range(r0, r0 + room_h)
                for c in range(c0, c0 + room_w) if grid[r][c] == 0]
        r, c = rng.choice(free)
        grid[r][c] = color

    for room, color in zip(seed_rooms, colors):
        place(room, color)
    for room, color in extras:
        place(room, color)
    return _rotate(grid, rng.randrange(4))


def _room_graph(grid: list[list[int]]):
    if (type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]
            or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)):
        raise ValueError("grid must be nonempty rectangular lists")
    h, w = len(grid), len(grid[0])
    owner: dict[tuple[int, int], int] = {}
    rooms: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] in WALLS or (r, c) in owner:
                continue
            rid = len(rooms)
            queue = deque([(r, c)])
            owner[r, c] = rid
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in owner
                            and grid[nr][nc] not in WALLS):
                        owner[nr, nc] = rid
                        queue.append((nr, nc))
            rooms.append(sorted(cells))
    adjacency = [set() for _ in rooms]
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 7:
                continue
            ids = {owner[p] for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)) if p in owner}
            for a in ids:
                for b in ids:
                    if a < b:
                        adjacency[a].add(b)
                        adjacency[b].add(a)
    return rooms, adjacency


def _distances(adjacency: list[set[int]], start: int) -> dict[int, int]:
    found = {start: 0}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for other in adjacency[node]:
            if other not in found:
                found[other] = found[node] + 1
                queue.append(other)
    return found


def nearest_color_intermediate(grid: list[list[int]]) -> dict:
    rooms, adjacency = _room_graph(grid)
    seeds = []
    for rid, cells in enumerate(rooms):
        colors = sorted({grid[r][c] for r, c in cells if grid[r][c] not in WALLS and grid[r][c] != 0})
        if colors:
            seeds.append((rid, colors[0]))
    if not seeds:
        raise ValueError("at least one seeded room is required")
    distance_maps = [(rid, color, _distances(adjacency, rid)) for rid, color in seeds]
    records = []
    for rid, cells in enumerate(rooms):
        scored = [(distances.get(rid, 999), color) for _, color, distances in distance_maps]
        best = min(distance for distance, _ in scored)
        nearest = tuple(sorted({color for distance, color in scored if distance == best}))
        records.append({"room_id": rid, "cells": cells, "best_distance": best,
                        "nearest_colors": nearest})
    return {"seeds": tuple((rid, color) for rid, color, _ in distance_maps),
            "adjacency": tuple(tuple(sorted(row)) for row in adjacency), "rooms": records}


def _paint_from_intermediate(grid: list[list[int]], marker: int, intermediate: dict,
                             *, all_colors: bool = False) -> list[list[int]]:
    marker = validate_marker(marker)
    output = [[value if value in WALLS else 0 for value in row] for row in grid]
    global_colors = tuple(sorted({color for _, color in intermediate["seeds"]}))
    for room in intermediate["rooms"]:
        colors = global_colors if all_colors else tuple(room["nearest_colors"])
        fill = colors[0] if len(colors) == 1 else marker
        for r, c in room["cells"]:
            output[r][c] = fill
    return output


def transform(grid: list[list[int]], tie_marker: int) -> list[list[int]]:
    return _paint_from_intermediate(grid, tie_marker, nearest_color_intermediate(grid))


def transform_all_colors_as_nearest(grid: list[list[int]], tie_marker: int) -> list[list[int]]:
    return _paint_from_intermediate(grid, tie_marker, nearest_color_intermediate(grid), all_colors=True)


def _input(seed: int, split: str, index: int) -> list[list[int]]:
    specs = _DEMO_SPECS if split == "train" else _QUERY_SPECS
    return _render(specs[index], _rng(seed, split, index))


def generate_episode(seed: int, *, tie_marker: int, demos: int, queries: int,
                     program_solution: str | None = None) -> dict:
    _exact_int(seed, 0, 2**63 - 1, "seed")
    marker = validate_marker(tie_marker)
    _exact_int(demos, 2, 6, "demos")
    _exact_int(queries, 1, 4, "queries")
    train_inputs = [_input(seed, "train", i) for i in range(demos)]
    test_inputs = [_input(seed, "test", i) for i in range(queries)]
    result = {
        "train": [{"input": grid, "output": transform(grid, marker)} for grid in train_inputs],
        "test": [{"input": grid, "output": transform(grid, marker)} for grid in test_inputs],
    }
    if program_solution is not None:
        result["program_solution"] = program_solution
    return result
