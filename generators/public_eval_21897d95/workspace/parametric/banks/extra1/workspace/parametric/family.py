"""Arrow-transfer room family for public parent 21897d95."""
from __future__ import annotations

import copy
import hashlib
import json
import random
from collections import Counter

SETTINGS = ("center_override", "host_only")
RIVALS = ("opposite_payload", "no_rotation", "retain_rooms")
DIRECTIONS = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}
PERPENDICULAR = {
    "U": ((0, -1), (0, 1)),
    "D": ((0, -1), (0, 1)),
    "L": ((-1, 0), (1, 0)),
    "R": ((-1, 0), (1, 0)),
}
D4 = tuple(DIRECTIONS.values())
ROOM_COLORS = (0, 2, 3, 4, 5, 6, 7, 8)


def integer(value: object, lo: int, hi: int, name: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")
    return value


def _grid(grid: object) -> list[list[int]]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a non-empty rectangular list")
    width = len(grid[0])
    out: list[list[int]] = []
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        clean: list[int] = []
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                raise ValueError("grid colors must be exact integers in [0, 9]")
            clean.append(value)
        out.append(clean)
    return out


def _components(grid: list[list[int]]) -> list[tuple[int, set[tuple[int, int]]]]:
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w)}
    out: list[tuple[int, set[tuple[int, int]]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        value = grid[start[0]][start[1]]
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in D4:
                point = (r + dr, c + dc)
                if point in remaining and grid[point[0]][point[1]] == value:
                    remaining.remove(point)
                    component.add(point)
                    stack.append(point)
        out.append((value, component))
    return out


def _t_candidates(grid: list[list[int]]) -> list[dict[str, object]]:
    h, w = len(grid), len(grid[0])
    candidates: list[dict[str, object]] = []
    for r in range(h):
        for c in range(w):
            for direction, (dr, dc) in DIRECTIONS.items():
                arms = [(r + dr, c + dc)] + [(r + a, c + b) for a, b in PERPENDICULAR[direction]]
                if all(0 <= rr < h and 0 <= cc < w and grid[rr][cc] == 1 for rr, cc in arms):
                    cells = {(r, c), *arms}
                    candidates.append(
                        {
                            "center": (r, c),
                            "direction": direction,
                            "cells": cells,
                            "ones": {point for point in cells if grid[point[0]][point[1]] == 1},
                        }
                    )
    return candidates


def _select_markers(grid: list[list[int]]) -> list[dict[str, object]]:
    candidates = _t_candidates(grid)
    all_ones = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1}
    solutions: set[tuple[int, ...]] = set()

    def search(used_ones: set[tuple[int, int]], occupied: set[tuple[int, int]], chosen: list[int]) -> None:
        if used_ones == all_ones:
            solutions.add(tuple(sorted(chosen)))
            return
        point = min(all_ones - used_ones)
        for index, candidate in enumerate(candidates):
            if point not in candidate["ones"] or candidate["cells"] & occupied:
                continue
            search(used_ones | candidate["ones"], occupied | candidate["cells"], chosen + [index])
            if len(solutions) > 1:
                return

    search(set(), set(), [])
    if len(solutions) != 1:
        raise ValueError("color-1 cells do not have one unique disjoint T-marker cover")
    return [copy.deepcopy(candidates[index]) for index in next(iter(solutions))]


def _l_marker(grid: list[list[int]]) -> dict[str, object] | None:
    direction_pairs = (
        ((1, 0), (0, 1)),
        ((1, 0), (0, -1)),
        ((-1, 0), (0, 1)),
        ((-1, 0), (0, -1)),
    )
    found: list[dict[str, object]] = []
    for value, component in _components(grid):
        if value == 1 or len(component) != 5:
            continue
        for corner in component:
            for first, second in direction_pairs:
                shape = {
                    corner,
                    (corner[0] + first[0], corner[1] + first[1]),
                    (corner[0] + 2 * first[0], corner[1] + 2 * first[1]),
                    (corner[0] + second[0], corner[1] + second[1]),
                    (corner[0] + 2 * second[0], corner[1] + 2 * second[1]),
                }
                if shape == component:
                    found.append(
                        {
                            "value": value,
                            "cells": set(component),
                            "corner": corner,
                            "directions": frozenset((first, second)),
                        }
                    )
    if len(found) > 1:
        raise ValueError("more than one isolated corner marker")
    return found[0] if found else None


def _host_color(grid: list[list[int]], cells: set[tuple[int, int]], blocked: set[tuple[int, int]]) -> int:
    h, w = len(grid), len(grid[0])
    counts: Counter[int] = Counter()
    for r, c in cells:
        for dr, dc in D4:
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w and (rr, cc) not in blocked:
                counts[grid[rr][cc]] += 1
    if not counts:
        raise ValueError("marker has no surrounding host color")
    best = max(counts.values())
    winners = [value for value, count in counts.items() if count == best]
    if len(winners) != 1:
        raise ValueError("marker host color is ambiguous")
    return winners[0]


def _rotate_clockwise(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_counterclockwise(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)][::-1]


def _analyze(grid: object, setting: str) -> dict[str, object]:
    if setting not in SETTINGS:
        raise ValueError("unknown payload setting")
    g = _grid(grid)
    h, w = len(g), len(g[0])
    markers = _select_markers(g)
    corner = _l_marker(g)
    blocked: set[tuple[int, int]] = set()
    for marker in markers:
        blocked |= marker["cells"]
    if corner is not None:
        blocked |= corner["cells"]

    filled = copy.deepcopy(g)
    all_markers: list[dict[str, object]] = markers + ([corner] if corner is not None else [])
    for marker in all_markers:
        host_color = _host_color(g, marker["cells"], blocked)
        marker["host_color"] = host_color
        for r, c in marker["cells"]:
            filled[r][c] = host_color

    room_components = _components(filled)
    room_of: dict[tuple[int, int], int] = {}
    room_base: dict[int, int] = {}
    room_cells: dict[int, set[tuple[int, int]]] = {}
    for room_id, (value, cells) in enumerate(room_components):
        room_base[room_id] = value
        room_cells[room_id] = cells
        for point in cells:
            room_of[point] = room_id

    incoming: dict[int, int] = {}
    transfers: list[dict[str, object]] = []
    for marker in markers:
        center = marker["center"]
        host = room_of[center]
        dr, dc = DIRECTIONS[marker["direction"]]
        r, c = center[0] + dr, center[1] + dc
        destination = None
        while 0 <= r < h and 0 <= c < w:
            if room_of[(r, c)] != host:
                destination = room_of[(r, c)]
                break
            r += dr
            c += dc
        if destination is None:
            raise ValueError("T-marker ray never reaches another room")
        center_value = g[center[0]][center[1]]
        payload = center_value if setting == "center_override" and center_value != 1 else room_base[host]
        if destination in incoming and incoming[destination] != payload:
            raise ValueError("destination receives conflicting payloads")
        incoming[destination] = payload
        transfers.append(
            {
                "center": [center[0], center[1]],
                "direction": marker["direction"],
                "host_room": host,
                "host_color": room_base[host],
                "destination_room": destination,
                "destination_color": room_base[destination],
                "payload": payload,
                "cells": sorted(marker["cells"]),
            }
        )

    rotation = "none"
    if corner is not None:
        dirs = corner["directions"]
        if dirs == frozenset(((1, 0), (0, -1))):
            rotation = "counterclockwise"
        elif dirs == frozenset(((1, 0), (0, 1))):
            rotation = "clockwise"
        else:
            raise ValueError("unsupported corner orientation")

    return {
        "grid": g,
        "filled": filled,
        "height": h,
        "width": w,
        "markers": transfers,
        "corner": None
        if corner is None
        else {
            "value": corner["value"],
            "corner": list(corner["corner"]),
            "cells": sorted(corner["cells"]),
            "host_color": corner["host_color"],
        },
        "rotation": rotation,
        "room_of": room_of,
        "room_base": room_base,
        "room_cells": room_cells,
        "incoming": incoming,
    }


def analyze(grid: object, setting: str = "center_override") -> dict[str, object]:
    info = _analyze(grid, setting)
    return {
        "height": info["height"],
        "width": info["width"],
        "rotation": info["rotation"],
        "markers": copy.deepcopy(info["markers"]),
        "corner": copy.deepcopy(info["corner"]),
        "rooms": [
            {
                "id": room_id,
                "base_color": info["room_base"][room_id],
                "incoming": info["incoming"].get(room_id),
                "cells": sorted(info["room_cells"][room_id]),
            }
            for room_id in sorted(info["room_base"])
        ],
    }


def _render(info: dict[str, object], *, transfers: bool = True, rotation: bool = True) -> list[list[int]]:
    h, w = info["height"], info["width"]
    out = [
        [
            (info["incoming"].get(info["room_of"][(r, c)], info["room_base"][info["room_of"][(r, c)]]))
            if transfers
            else info["room_base"][info["room_of"][(r, c)]]
            for c in range(w)
        ]
        for r in range(h)
    ]
    if rotation:
        if info["rotation"] == "clockwise":
            out = _rotate_clockwise(out)
        elif info["rotation"] == "counterclockwise":
            out = _rotate_counterclockwise(out)
    return out


def solve(grid: object, setting: str = "center_override") -> list[list[int]]:
    return _render(_analyze(grid, setting))


def solve_rival(grid: object, setting: str, rival: str) -> list[list[int]]:
    if rival not in RIVALS:
        raise ValueError("unknown rival")
    if rival == "opposite_payload":
        other = "host_only" if setting == "center_override" else "center_override"
        return solve(grid, other)
    info = _analyze(grid, setting)
    if rival == "no_rotation":
        return _render(info, rotation=False)
    return _render(info, transfers=False)


def intermediate(grid: object, settings: dict[str, str] | None = None) -> dict[str, object]:
    setting = "center_override" if settings is None else settings.get("payload")
    info = analyze(grid, setting)
    return {
        "rotation": info["rotation"],
        "room_partition": [
            {
                "id": room["id"],
                "base_color": room["base_color"],
                "incoming": room["incoming"],
                "cells": room["cells"],
            }
            for room in info["rooms"]
        ],
        "transfers": info["markers"],
    }


def dependency() -> dict[str, str]:
    return {
        "step_a": "Find the unique disjoint cover of color-1 cells by T-markers, inpaint each marker into its host, recover the room partition, trace every stem ray to its first different room, and bind the incoming payload map plus corner rotation.",
        "intermediate": "An input-derived room ID for every cell, each room's incoming payload, the traced transfer records, and the optional quarter-turn.",
        "step_b": "Recolor every recovered room from its incoming payload (retaining rooms with no incoming arrow), erase all markers through that fill, and apply the inferred corner rotation.",
        "why": "The destination color and even the cells belonging to that destination are unknown until marker cover, host inpainting and ray tracing finish; changing the transfer intermediate changes the final region map.",
    }


def _rng(seed: int, tag: object) -> random.Random:
    material = json.dumps([seed, tag], sort_keys=True, separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest()[:16], "big"))


def _paint_t(grid: list[list[int]], center: tuple[int, int], direction: str, center_value: int) -> set[tuple[int, int]]:
    r, c = center
    dr, dc = DIRECTIONS[direction]
    cells = {(r, c), (r + dr, c + dc)} | {(r + a, c + b) for a, b in PERPENDICULAR[direction]}
    grid[r][c] = center_value
    for rr, cc in cells - {(r, c)}:
        grid[rr][cc] = 1
    return cells


def _marker_center(bounds: tuple[int, int, int, int], direction: str, offset: int = 0) -> tuple[int, int]:
    r0, r1, c0, c1 = bounds
    mid_r = max(r0 + 2, min(r1 - 2, (r0 + r1) // 2 + offset))
    mid_c = max(c0 + 2, min(c1 - 2, (c0 + c1) // 2 + offset))
    if direction == "R":
        return mid_r, c1 - 1
    if direction == "L":
        return mid_r, c0 + 1
    if direction == "D":
        return r1 - 1, mid_c
    return r0 + 1, mid_c


def _place_corner(grid: list[list[int]], bounds: tuple[int, int, int, int], orientation: str, occupied: set[tuple[int, int]]) -> set[tuple[int, int]]:
    r0, r1, c0, c1 = bounds
    if orientation == "top_right":
        candidates = [(r, c) for r in range(r0 + 1, r1 - 1) for c in range(c0 + 3, c1)]
        directions = ((1, 0), (0, -1))
    else:
        candidates = [(r, c) for r in range(r0 + 1, r1 - 1) for c in range(c0 + 1, c1 - 2)]
        directions = ((1, 0), (0, 1))
    for corner in candidates:
        d1, d2 = directions
        shape = {
            corner,
            (corner[0] + d1[0], corner[1] + d1[1]),
            (corner[0] + 2 * d1[0], corner[1] + 2 * d1[1]),
            (corner[0] + d2[0], corner[1] + d2[1]),
            (corner[0] + 2 * d2[0], corner[1] + 2 * d2[1]),
        }
        if shape.isdisjoint(occupied):
            for r, c in shape:
                grid[r][c] = 9
            return shape
    raise ValueError("room is too small for a corner marker")


def _layout(h: int, w: int, rooms: int, rng: random.Random) -> tuple[list[tuple[int, int, int, int]], list[str]]:
    if rooms == 4:
        split_r = max(8, min(h - 8, h // 2 + rng.choice((-1, 0, 1))))
        split_c = max(8, min(w - 8, w // 2 + rng.choice((-1, 0, 1))))
        bounds = [
            (0, split_r - 1, 0, split_c - 1),
            (0, split_r - 1, split_c, w - 1),
            (split_r, h - 1, split_c, w - 1),
            (split_r, h - 1, 0, split_c - 1),
        ]
        return bounds, ["R", "D", "L", "U"]
    split_r = max(8, min(h - 8, h // 2 + rng.choice((-1, 0, 1))))
    c1 = max(8, min(w - 16, w // 3 + rng.choice((-1, 0, 1))))
    c2 = max(c1 + 8, min(w - 8, 2 * w // 3 + rng.choice((-1, 0, 1))))
    bounds = [
        (0, split_r - 1, 0, c1 - 1),
        (0, split_r - 1, c1, c2 - 1),
        (0, split_r - 1, c2, w - 1),
        (split_r, h - 1, c2, w - 1),
        (split_r, h - 1, c1, c2 - 1),
        (split_r, h - 1, 0, c1 - 1),
    ]
    return bounds, ["R", "R", "D", "L", "L", "U"]


def make_scene(seed: int, tag: object, h: int, w: int, *, rooms: int = 4, stress: bool = False) -> list[list[int]]:
    integer(seed, 0, 2**63 - 1, "seed")
    integer(h, 16, 30, "height")
    integer(w, 16, 30, "width")
    if rooms not in (4, 6):
        raise ValueError("rooms must be 4 or 6")
    rng = _rng(seed, [tag, h, w, rooms, stress])
    for attempt in range(80):
        colors = rng.sample(ROOM_COLORS, rooms)
        bounds, directions = _layout(h, w, rooms, rng)
        grid = [[0] * w for _ in range(h)]
        for color, (r0, r1, c0, c1) in zip(colors, bounds):
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    grid[r][c] = color
        occupied: set[tuple[int, int]] = set()
        for index, (room_bounds, direction, host_color) in enumerate(zip(bounds, directions, colors)):
            center = _marker_center(room_bounds, direction, offset=(index % 3) - 1)
            center_value = host_color
            if index in (0, rooms // 2):
                center_value = next(value for value in ROOM_COLORS if value not in (host_color, colors[(index + 1) % rooms]))
            else:
                center_value = 1
            occupied |= _paint_t(grid, center, direction, center_value)
        orientation = "top_right" if (seed + len(str(tag)) + attempt) % 2 == 0 else "top_left"
        occupied |= _place_corner(grid, bounds[-1 if rooms == 4 else 4], orientation, occupied)
        try:
            canonical = solve(grid, "center_override")
            alternate = solve(grid, "host_only")
            if canonical == alternate:
                continue
            if any(solve_rival(grid, setting, rival) == solve(grid, setting) for setting in SETTINGS for rival in RIVALS):
                continue
            return grid
        except ValueError:
            continue
    raise RuntimeError("could not sample an identifiable arrow-transfer scene")


def _shapes() -> tuple[list[tuple[int, int, int]], list[tuple[int, int, int]]]:
    demos = [(16, 18, 4), (18, 20, 4), (20, 22, 4), (22, 24, 6), (24, 27, 6), (26, 29, 6)]
    queries = [(18, 22, 4), (22, 26, 4), (27, 30, 6), (30, 30, 6)]
    return demos, queries


def generate(seed: int, settings: dict[str, str], demos: int, queries: int) -> dict[str, object]:
    integer(seed, 0, 2**63 - 1, "seed")
    integer(demos, 2, 6, "demos")
    integer(queries, 1, 4, "queries")
    if type(settings) is not dict or set(settings) != {"payload"} or settings["payload"] not in SETTINGS:
        raise ValueError("settings must be exactly payload=center_override|host_only")
    setting = settings["payload"]
    demo_shapes, query_shapes = _shapes()

    def pair(index: int, shape: tuple[int, int, int], query: bool) -> dict[str, object]:
        h, w, rooms = shape
        grid = make_scene(seed, ["query" if query else "demo", index], h, w, rooms=rooms, stress=query and index == 3)
        return {"input": grid, "output": solve(grid, setting)}

    train = [pair(i, demo_shapes[i], False) for i in range(demos)]
    bank = [pair(i, shape, True) for i, shape in enumerate(query_shapes)]
    return {"train": train, "test": copy.deepcopy(bank[:queries]), "private_query_bank": bank}


def self_check(grid: object) -> list[str]:
    issues: list[str] = []
    try:
        g = _grid(grid)
        info = analyze(g, "center_override")
        if not info["markers"]:
            issues.append("no T-markers")
        if info["corner"] is None:
            issues.append("no corner marker")
        if solve(g, "center_override") == solve(g, "host_only"):
            issues.append("payload settings do not differ")
    except Exception as exc:
        issues.append(str(exc))
    return issues
