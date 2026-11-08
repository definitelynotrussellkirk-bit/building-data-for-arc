"""Deterministic room-graph lessons for seeded versus neighboring targets."""
from __future__ import annotations

from collections import deque
import hashlib
from pathlib import Path

TASK_ID = "e5ec1ac39df5"
ALLOWED_MODES = ("seeded", "neighbors")
HOME = Path(__file__).resolve().parent
WALLS = {1, 7, 9}
BOUNDARY_WALLS = {1, 7}


def _validate_mode(value) -> str:
    if type(value) is not str or value not in ALLOWED_MODES:
        raise ValueError(f"target_rooms must be one of {ALLOWED_MODES}")
    return value


def _validate_counts(demos, queries) -> None:
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be exactly 4")


def program_for(target_rooms: str) -> str:
    mode = _validate_mode(target_rooms)
    return (HOME / ("canonical.rkt" if mode == "seeded" else "neighbors.rkt")).read_text(
        encoding="utf-8"
    )


def _partition(total: int, count: int, salt: bytes) -> list[int]:
    if total < 3 * count:
        raise ValueError("scene dimension cannot fit room lattice")
    sizes = [3] * count
    for index in range(total - 3 * count):
        sizes[(salt[index % len(salt)] + index) % count] += 1
    if count > 1 and len(set(sizes)) == 1 and sizes[0] > 3:
        sizes[0] -= 1
        sizes[-1] += 1
    shift = salt[0] % count
    return sizes[shift:] + sizes[:shift]


def _room_boxes(row_sizes: list[int], col_sizes: list[int]):
    boxes = []
    r0 = 1
    for rh in row_sizes:
        row = []
        c0 = 1
        for cw in col_sizes:
            row.append((r0, c0, rh, cw))
            c0 += cw + 1
        boxes.append(row)
        r0 += rh + 1
    return boxes


def _dimensions(sample_index: int, total: int):
    if sample_index == total - 1:
        return 30, 30, 4, 4
    return 12 + sample_index, 20 + ((3 * sample_index) % 10), (2 if sample_index % 2 == 0 else 3), (3 if sample_index % 2 == 0 else 2)


def build_input(seed: int, sample_index: int, total: int) -> list[list[int]]:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")
    if type(sample_index) is not int or type(total) is not int or not 0 <= sample_index < total:
        raise ValueError("sample_index outside episode")
    h, w, nr, nc = _dimensions(sample_index, total)
    salt = hashlib.sha256(f"{TASK_ID}:{seed}:{sample_index}:{total}".encode()).digest()
    row_sizes = _partition(h - nr - 1, nr, salt[:16])
    col_sizes = _partition(w - nc - 1, nc, salt[16:])
    boxes = _room_boxes(row_sizes, col_sizes)
    grid = [[1 for _ in range(w)] for _ in range(h)]
    for row in boxes:
        for r0, c0, rh, cw in row:
            for r in range(r0, r0 + rh):
                for c in range(c0, c0 + cw):
                    grid[r][c] = 0

    room_ids = [(ri, ci) for ri in range(nr) for ci in range(nc)]
    seed_room = room_ids[(salt[2] + sample_index) % len(room_ids)]

    # Materialize every possible lattice edge, but deliberately omit at least
    # one geometrically adjacent edge incident to the seeded room.  Thus the
    # visible color-7 graph, rather than plain room proximity, determines the
    # neighbor target set.
    edges = []
    for ri in range(nr):
        for ci in range(nc - 1):
            r0, c0, rh, cw = boxes[ri][ci]
            offset = salt[(5 + ri * nc + ci) % len(salt)] % rh
            edges.append(((ri, ci), (ri, ci + 1), (r0 + offset, c0 + cw)))
    for ri in range(nr - 1):
        for ci in range(nc):
            r0, c0, rh, cw = boxes[ri][ci]
            offset = salt[(19 + ri * nc + ci) % len(salt)] % cw
            edges.append(((ri, ci), (ri + 1, ci), (r0 + rh, c0 + offset)))

    incident = [index for index, (left, right, _cell) in enumerate(edges) if seed_room in (left, right)]
    if len(incident) < 2:
        raise ValueError("seeded room must have at least two geometric neighbors")
    rotation = salt[4] % len(incident)
    incident = incident[rotation:] + incident[:rotation]
    keep_count = 1 + salt[3] % (len(incident) - 1)
    kept_incident = set(incident[:keep_count])
    for index, (left, right, (r, c)) in enumerate(edges):
        if seed_room not in (left, right) or index in kept_incident:
            grid[r][c] = 7

    ri, ci = seed_room
    r0, c0, rh, cw = boxes[ri][ci]
    center = (r0 + rh // 2, c0 + cw // 2)
    if sample_index % 2:
        candidates = [
            (r, c)
            for r in range(r0, r0 + rh)
            for c in range(c0, c0 + cw)
            if (r, c) != center
        ]
        sr, sc = candidates[salt[3] % len(candidates)]
    else:
        sr, sc = center
    grid[sr][sc] = 2
    return grid


def _room_data(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    rooms = []
    cell_to_room = {}
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] in WALLS or (sr, sc) in seen:
                continue
            room_id = len(rooms)
            todo = deque([(sr, sc)])
            seen.add((sr, sc))
            cells = set()
            while todo:
                r, c = todo.popleft()
                cells.add((r, c))
                cell_to_room[(r, c)] = room_id
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] not in WALLS
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
            c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
            rooms.append({"id": room_id, "cells": cells, "bbox": (r0, r1, c0, c1)})
    adjacency = {room["id"]: set() for room in rooms}
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 7:
                continue
            ids = {
                cell_to_room[(nr, nc)]
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
                if (nr, nc) in cell_to_room
            }
            for first in ids:
                adjacency[first].update(ids - {first})
    return rooms, adjacency


def _boundary_cells(room, grid):
    h, w = len(grid), len(grid[0])
    result = set()
    for r, c in room["cells"]:
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] in BOUNDARY_WALLS:
                result.add((nr, nc))
    return result


def _geometric_adjacency(rooms):
    adjacency = {room["id"]: set() for room in rooms}
    for index, left in enumerate(rooms):
        lr0, lr1, lc0, lc1 = left["bbox"]
        for right in rooms[index + 1 :]:
            rr0, rr1, rc0, rc1 = right["bbox"]
            rows_overlap = max(lr0, rr0) <= min(lr1, rr1)
            cols_overlap = max(lc0, rc0) <= min(lc1, rc1)
            separated_by_vertical_wall = rows_overlap and (lc1 + 2 == rc0 or rc1 + 2 == lc0)
            separated_by_horizontal_wall = cols_overlap and (lr1 + 2 == rr0 or rr1 + 2 == lr0)
            if separated_by_vertical_wall or separated_by_horizontal_wall:
                adjacency[left["id"]].add(right["id"])
                adjacency[right["id"]].add(left["id"])
    return adjacency


def scene_features(grid):
    rooms, adjacency = _room_data(grid)
    geometric = _geometric_adjacency(rooms)
    seeded = {
        room["id"]
        for room in rooms
        if any(grid[r][c] == 2 for r, c in room["cells"])
    }
    graph_neighbors = set().union(*(adjacency[room_id] for room_id in seeded))
    geometric_neighbors = set().union(*(geometric[room_id] for room_id in seeded))
    off_center = False
    heights, widths = [], []
    for room in rooms:
        r0, r1, c0, c1 = room["bbox"]
        heights.append(r1 - r0 + 1)
        widths.append(c1 - c0 + 1)
        seeds = [p for p in room["cells"] if grid[p[0]][p[1]] == 2]
        center = (r0 + (r1 - r0 + 1) // 2, c0 + (c1 - c0 + 1) // 2)
        off_center = off_center or bool(seeds and seeds != [center])
    return {
        "room_count": len(rooms),
        "room_heights": heights,
        "room_widths": widths,
        "door_count": sum(value == 7 for row in grid for value in row),
        "edge_count": sum(len(v) for v in adjacency.values()) // 2,
        "off_center_seed": off_center,
        "seeded_graph_neighbor_count": len(graph_neighbors),
        "seeded_geometric_neighbor_count": len(geometric_neighbors),
    }


def python_mirror(grid, *, target_rooms: str):
    mode = _validate_mode(target_rooms)
    rooms, adjacency = _room_data(grid)
    seeded = {
        room["id"]
        for room in rooms
        if any(grid[r][c] == 2 for r, c in room["cells"])
    }
    targets = seeded if mode == "seeded" else set().union(*(adjacency[rid] for rid in seeded))
    cells = set()
    for room in rooms:
        if room["id"] in targets:
            cells.update(_boundary_cells(room, grid))
    return [
        [8 if (r, c) in cells else 0 for c in range(len(grid[0]))]
        for r in range(len(grid))
    ]


def generate_claims(seed: int, target_rooms: str, *, demos=3, queries=4):
    mode = _validate_mode(target_rooms)
    _validate_counts(demos, queries)
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")
    total = demos + queries
    pairs = []
    for index in range(total):
        grid = build_input(seed, index, total)
        pairs.append({"input": grid, "output": python_mirror(grid, target_rooms=mode)})
    return {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program_for(mode),
    }
