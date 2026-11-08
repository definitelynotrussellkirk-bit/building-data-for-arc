"""Deterministic native family for keyed straight and clockwise-elbow rays."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Iterable

TASK_ID = "7d09ccad28c8"
ROUTE_MODES = ("straight", "clockwise_elbow")
_DIRECTIONS = {1: (-1, 0), 2: (0, 1), 3: (1, 0), 4: (0, -1)}
_HERE = Path(__file__).resolve().parent
_PROGRAM_FILES = {
    "straight": "canonical.rkt",
    "clockwise_elbow": "clockwise-elbow.rkt",
}


def validate_settings(settings: dict) -> str:
    if type(settings) is not dict or set(settings) != {"route_mode"}:
        raise ValueError("settings must contain exactly route_mode")
    mode = settings["route_mode"]
    if type(mode) is not str:
        raise TypeError("route_mode must be an exact string")
    if mode not in ROUTE_MODES:
        raise ValueError(f"route_mode must be one of {ROUTE_MODES}")
    return mode


def _integer(name: str, value: int, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def program(settings: dict) -> str:
    return (_HERE / _PROGRAM_FILES[validate_settings(settings)]).read_text(
        encoding="utf-8"
    )


def _rng(seed: int, split: str, index: int) -> random.Random:
    material = f"{TASK_ID}|route-v1|{seed}|{split}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest()[:16], "big"))


def _empty(height: int, width: int) -> list[list[int]]:
    return [[0 for _ in range(width)] for _ in range(height)]


def _border(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r1, c1, r2, c2 = box
    return {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }


def _inside(box: tuple[int, int, int, int]) -> list[tuple[int, int]]:
    r1, c1, r2, c2 = box
    return [
        (r, c)
        for r in range(r1 + 1, r2)
        for c in range(c1 + 1, c2)
    ]


def _ray(
    start: tuple[int, int],
    direction: tuple[int, int],
    box: tuple[int, int, int, int],
) -> list[tuple[int, int]]:
    r1, c1, r2, c2 = box
    r, c = start[0] + direction[0], start[1] + direction[1]
    cells: list[tuple[int, int]] = []
    while r1 < r < r2 and c1 < c < c2:
        cells.append((r, c))
        r += direction[0]
        c += direction[1]
    return cells


def _clockwise(direction: tuple[int, int]) -> tuple[int, int]:
    return direction[1], -direction[0]


def _layout_boxes(
    height: int, width: int, size: int, count: int, variant: int
) -> list[tuple[int, int, int, int]]:
    if count == 2:
        positions = (
            ((1, 1), (height - size - 1, width - size - 1)),
            ((1, width - size - 1), (height - size - 1, 1)),
        )[variant % 2]
    elif count == 3:
        positions = (
            (1, 1),
            (1, width - size - 1),
            (height - size - 1, (width - size) // 2),
        )
    elif count == 4:
        positions = (
            (1, 1),
            (1, width - size - 1),
            (height - size - 1, 1),
            (height - size - 1, width - size - 1),
        )
    else:
        raise ValueError("route family supports 2..4 frames")
    boxes = [(r, c, r + size - 1, c + size - 1) for r, c in positions]
    borders = [_border(box) for box in boxes]
    for index, first in enumerate(borders):
        for second in borders[index + 1 :]:
            if first & second:
                raise ValueError("planned frame borders overlap")
    return boxes


def _candidate_scene(
    box: tuple[int, int, int, int],
    key_value: int,
    blocker_mode: str,
    rng: random.Random,
):
    direction = _DIRECTIONS[key_value]
    cells = _inside(box)
    emitters = list(cells)
    rng.shuffle(emitters)
    for emitter in emitters:
        straight = _ray(emitter, direction, box)
        if len(straight) < 2:
            continue
        if blocker_mode == "first":
            blocker_index = max(1, min(len(straight) - 1, len(straight) // 2))
            blocker = straight[blocker_index]
            first_leg = straight[:blocker_index]
        else:
            blocker = None
            first_leg = straight
        endpoint = first_leg[-1] if first_leg else emitter
        turn_path = _ray(endpoint, _clockwise(direction), box)
        if len(turn_path) < 2:
            continue
        if blocker_mode == "turn":
            blocker_index = max(1, min(len(turn_path) - 1, len(turn_path) // 2))
            blocker = turn_path[blocker_index]
            second_leg = turn_path[:blocker_index]
        else:
            second_leg = turn_path
        forbidden = {emitter, *straight, *turn_path}
        safe = [cell for cell in cells if cell not in forbidden]
        rng.shuffle(safe)
        if blocker is None:
            if not safe:
                continue
            blocker = safe.pop()
        key_cells = [cell for cell in safe if cell != blocker]
        if not key_cells:
            continue
        key_cell = key_cells[0]
        if first_leg and second_leg:
            return {
                "emitter": emitter,
                "key": key_cell,
                "blocker": blocker,
                "first_leg": first_leg,
                "second_leg": second_leg,
            }
    raise ValueError(f"could not place a route scene in frame {box}")


def _profile(split: str, index: int) -> tuple[int, int, int, int]:
    train = (
        (15, 17, 7, 2),
        (16, 18, 7, 2),
        (18, 22, 8, 2),
        (19, 21, 8, 2),
        (21, 24, 7, 3),
        (24, 24, 8, 3),
    )
    test = (
        (15, 18, 7, 2),
        (18, 22, 8, 2),
        (24, 26, 9, 3),
        (30, 30, 11, 4),
    )
    profiles = train if split == "train" else test
    return profiles[index % len(profiles)]


def build_input(seed: int, split: str, index: int) -> list[list[int]]:
    _integer("seed", seed, 0, 2**63 - 1)
    if split not in ("train", "test"):
        raise ValueError("split must be train or test")
    _integer("index", index, 0, 10_000)
    height, width, size, count = _profile(split, index)
    rng = _rng(seed, split, index)
    boxes = _layout_boxes(height, width, size, count, index + seed)
    grid = _empty(height, width)
    for box in boxes:
        for r, c in _border(box):
            grid[r][c] = 8
    blocker_modes = ("first", "turn", "wall")
    direction_shift = (seed + index + (0 if split == "train" else 2)) % 4
    for scene_index, box in enumerate(boxes):
        key = ((direction_shift + scene_index) % 4) + 1
        mode = blocker_modes[(index + scene_index) % len(blocker_modes)]
        scene = _candidate_scene(box, key, mode, rng)
        kr, kc = scene["key"]
        er, ec = scene["emitter"]
        br, bc = scene["blocker"]
        grid[kr][kc] = key
        grid[er][ec] = 6
        grid[br][bc] = 7
    if not route_analysis(grid):
        raise ValueError("constructed route input has no frames")
    if transform(grid, "straight") == transform(grid, "clockwise_elbow"):
        raise ValueError("constructed route input does not distinguish settings")
    return grid


def _components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = r + dr, c + dc
                if nxt in remaining:
                    remaining.remove(nxt)
                    cells.add(nxt)
                    stack.append(nxt)
        result.append(cells)
    return result


def _frame_boxes(grid: list[list[int]]) -> list[tuple[int, int, int, int]]:
    boxes = []
    for cells in _components(grid, 8):
        r1 = min(r for r, _ in cells)
        c1 = min(c for _, c in cells)
        r2 = max(r for r, _ in cells)
        c2 = max(c for _, c in cells)
        box = r1, c1, r2, c2
        if cells != _border(box):
            raise ValueError("color-8 component is not a hollow rectangular frame")
        boxes.append(box)
    return sorted(boxes)


def _until_blocker(
    grid: list[list[int]],
    start: tuple[int, int],
    direction: tuple[int, int],
    box: tuple[int, int, int, int],
) -> list[tuple[int, int]]:
    result = []
    for cell in _ray(start, direction, box):
        if grid[cell[0]][cell[1]] == 7:
            break
        result.append(cell)
    return result


def route_analysis(grid: list[list[int]]) -> list[dict]:
    result = []
    for box in _frame_boxes(grid):
        cells = _inside(box)
        emitters = [cell for cell in cells if grid[cell[0]][cell[1]] == 6]
        keys = [
            (cell[0], cell[1], grid[cell[0]][cell[1]])
            for cell in cells
            if grid[cell[0]][cell[1]] in _DIRECTIONS
        ]
        blockers = [cell for cell in cells if grid[cell[0]][cell[1]] == 7]
        if len(emitters) != 1 or len(keys) != 1 or len(blockers) != 1:
            raise ValueError("each frame needs one emitter, key, and blocker")
        emitter = emitters[0]
        key = keys[0]
        direction = _DIRECTIONS[key[2]]
        first_leg = _until_blocker(grid, emitter, direction, box)
        endpoint = first_leg[-1] if first_leg else emitter
        second_leg = _until_blocker(grid, endpoint, _clockwise(direction), box)
        result.append(
            {
                "box": box,
                "emitter": emitter,
                "key": key,
                "blocker": blockers[0],
                "direction": direction,
                "first_leg": first_leg,
                "endpoint": endpoint,
                "second_leg": second_leg,
            }
        )
    return result


def _paint(grid: list[list[int]], cells: Iterable[tuple[int, int]]) -> None:
    for r, c in cells:
        if grid[r][c] == 0:
            grid[r][c] = 6


def transform(grid: list[list[int]], mode: str) -> list[list[int]]:
    if mode not in ROUTE_MODES:
        raise ValueError(f"unsupported route mode {mode!r}")
    out = deepcopy(grid)
    for scene in route_analysis(grid):
        _paint(out, scene["first_leg"])
        if mode == "clockwise_elbow":
            _paint(out, scene["second_leg"])
    return out


def transform_wrong_intermediate(grid: list[list[int]]) -> list[list[int]]:
    """Ablation: turn at the emitter instead of the computed first endpoint."""
    out = deepcopy(grid)
    for scene in route_analysis(grid):
        _paint(out, scene["first_leg"])
        wrong_leg = _until_blocker(
            grid,
            scene["emitter"],
            _clockwise(scene["direction"]),
            scene["box"],
        )
        _paint(out, wrong_leg)
    return out


def generate(seed: int, settings: dict, demos: int, queries: int) -> dict:
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    mode = validate_settings(settings)

    def pair(split: str, index: int) -> dict:
        grid = build_input(seed, split, index)
        return {"input": grid, "output": transform(grid, mode)}

    return {
        "train": [pair("train", index) for index in range(demos)],
        "test": [pair("test", index) for index in range(queries)],
        "program_solution": program(settings),
    }
