"""Native parametric family for control-selected normalized mask operations.

The canonical setting is byte-exact with the selected ARC rule.  The alternate
first compares occupied areas of the normalized color-1 and color-2 operands,
binds the larger operand as an input-derived intermediate (ties choose color 1),
rotates only that operand clockwise, and only then applies the visible control
cell's union/XOR/intersection operation.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
import hashlib
import json
import random
from pathlib import Path
from typing import Any, Callable

TASK_ID = "3020cc038f3f"
PARAMETER = "preprocess"
SETTINGS = ("identity", "rotate_larger_cw")
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4
MAX_SEED = 2**63 - 1

_HOME = Path(__file__).resolve().parent
_PROGRAM_FILES = {
    "identity": _HOME / "canonical.rkt",
    "rotate_larger_cw": _HOME / "rotate_larger_cw.rkt",
}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


@dataclass(frozen=True)
class Profile:
    height: int
    width: int
    ctrl: int
    first: frozenset[tuple[int, int]]
    second: frozenset[tuple[int, int]]
    orientation: str
    spread: bool = False


def _strict_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return value


def _settings(value: Any) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER!r}")
    selected = value[PARAMETER]
    if type(selected) is not str or selected not in SETTINGS:
        raise ValueError(f"{PARAMETER} must be one of {SETTINGS!r}")
    return {PARAMETER: selected}


def program(settings: dict[str, str]) -> str:
    selected = _settings(settings)[PARAMETER]
    return _PROGRAM_FILES[selected].read_text(encoding="utf-8")


def _normalize(cells: Any) -> frozenset[tuple[int, int]]:
    frozen = frozenset(cells)
    if not frozen:
        return frozenset()
    top = min(row for row, _col in frozen)
    left = min(col for _row, col in frozen)
    return frozenset((row - top, col - left) for row, col in frozen)


def _extent(cells: frozenset[tuple[int, int]]) -> tuple[int, int]:
    if not cells:
        return 0, 0
    return max(row for row, _col in cells) + 1, max(col for _row, col in cells) + 1


def _bbox(cells: frozenset[tuple[int, int]]) -> tuple[int, int, int, int]:
    return (
        min(row for row, _col in cells),
        min(col for _row, col in cells),
        max(row for row, _col in cells),
        max(col for _row, col in cells),
    )


def _connected(cells: frozenset[tuple[int, int]]) -> bool:
    if not cells:
        return False
    todo = [next(iter(cells))]
    seen = {todo[0]}
    while todo:
        row, col = todo.pop()
        for drow, dcol in _CARDINAL:
            point = (row + drow, col + dcol)
            if point in cells and point not in seen:
                seen.add(point)
                todo.append(point)
    return len(seen) == len(cells)


def _grid(value: Any) -> tuple[int, int]:
    if type(value) is not list or not value or type(value[0]) is not list or not value[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    height, width = len(value), len(value[0])
    if not 1 <= height <= 30 or not 1 <= width <= 30:
        raise ValueError("grid dimensions must be in 1..30")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact ARC integer colors")
    return height, width


def analyze_input(grid: list[list[int]]) -> dict[str, Any]:
    height, width = _grid(grid)
    ctrl = grid[0][0]
    if ctrl not in (3, 4, 5):
        raise ValueError("(0,0) must be control 3, 4, or 5")
    controls = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] in (3, 4, 5)
    ]
    if controls != [(0, 0)]:
        raise ValueError("the only control-colored cell must be (0,0)")
    palette = {cell for row in grid for cell in row}
    if palette != {0, 1, 2, ctrl}:
        raise ValueError(f"palette must be exactly {{0,1,2,{ctrl}}}")

    physical: dict[int, frozenset[tuple[int, int]]] = {}
    normalized: dict[int, frozenset[tuple[int, int]]] = {}
    for color in (1, 2):
        cells = frozenset(
            (row, col)
            for row in range(height)
            for col in range(width)
            if grid[row][col] == color
        )
        if not _connected(cells):
            raise ValueError(f"color {color} must form one nonempty 4-connected component")
        physical[color] = cells
        normalized[color] = _normalize(cells)

    first_box = _bbox(physical[1])
    second_box = _bbox(physical[2])
    separated = (
        first_box[2] + 1 < second_box[0]
        or second_box[2] + 1 < first_box[0]
        or first_box[3] + 1 < second_box[1]
        or second_box[3] + 1 < first_box[1]
    )
    if not separated:
        raise ValueError("operand bounding boxes require a blank separator row or column")

    sizes = {color: len(normalized[color]) for color in (1, 2)}
    larger_color = 1 if sizes[1] >= sizes[2] else 2
    return {
        "height": height,
        "width": width,
        "ctrl": ctrl,
        "physical": physical,
        "normalized": normalized,
        "sizes": sizes,
        "bbox_areas": {
            color: _extent(normalized[color])[0] * _extent(normalized[color])[1]
            for color in (1, 2)
        },
        "larger_color": larger_color,
        "smaller_color": 2 if larger_color == 1 else 1,
    }


def _rotate_cw(cells: frozenset[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    height, _width = _extent(cells)
    return _normalize((col, height - 1 - row) for row, col in cells)


def _rotate_ccw(cells: frozenset[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    result = cells
    for _ in range(3):
        result = _rotate_cw(result)
    return result


def _rotate_180(cells: frozenset[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    return _rotate_cw(_rotate_cw(cells))


def _combine(
    first: frozenset[tuple[int, int]],
    second: frozenset[tuple[int, int]],
    ctrl: int,
) -> frozenset[tuple[int, int]]:
    if ctrl == 3:
        return first | second
    if ctrl == 4:
        return first ^ second
    if ctrl == 5:
        return first & second
    return frozenset()


def _render(
    result: frozenset[tuple[int, int]],
    first: frozenset[tuple[int, int]],
    second: frozenset[tuple[int, int]],
) -> list[list[int]]:
    if not result:
        return [[0]]
    height = max(_extent(first)[0], _extent(second)[0])
    width = max(_extent(first)[1], _extent(second)[1])
    return [
        [8 if (row, col) in result else 0 for col in range(width)]
        for row in range(height)
    ]


def _transform_policy(
    grid: list[list[int]],
    *,
    selected_color: int | None = None,
    rotation: str = "cw",
    forced_ctrl: int | None = None,
) -> list[list[int]]:
    analysis = analyze_input(grid)
    first = analysis["normalized"][1]
    second = analysis["normalized"][2]
    rotate: Callable[[frozenset[tuple[int, int]]], frozenset[tuple[int, int]]]
    if rotation == "cw":
        rotate = _rotate_cw
    elif rotation == "ccw":
        rotate = _rotate_ccw
    elif rotation == "180":
        rotate = _rotate_180
    else:
        raise ValueError(f"unknown rotation {rotation!r}")
    if selected_color == 1:
        first = rotate(first)
    elif selected_color == 2:
        second = rotate(second)
    elif selected_color is not None:
        raise ValueError("selected_color must be 1, 2, or None")
    ctrl = analysis["ctrl"] if forced_ctrl is None else forced_ctrl
    return _render(_combine(first, second, ctrl), first, second)


def transform_with_selected_color(
    grid: list[list[int]], selected_color: int
) -> list[list[int]]:
    return _transform_policy(grid, selected_color=selected_color)


def transform(grid: list[list[int]], settings: Any) -> list[list[int]]:
    selected = _settings(settings)[PARAMETER]
    analysis = analyze_input(grid)
    selected_color = None if selected == "identity" else analysis["larger_color"]
    return _transform_policy(grid, selected_color=selected_color)


def _rect(height: int, width: int) -> frozenset[tuple[int, int]]:
    return frozenset((row, col) for row in range(height) for col in range(width))


def _l_shape(height: int, width: int) -> frozenset[tuple[int, int]]:
    return frozenset(
        {(row, 0) for row in range(height)}
        | {(height - 1, col) for col in range(width)}
    )


def _t_shape(height: int, width: int) -> frozenset[tuple[int, int]]:
    middle = width // 2
    return frozenset(
        {(0, col) for col in range(width)}
        | {(row, middle) for row in range(1, height)}
    )


def _snake(size: int, width: int) -> frozenset[tuple[int, int]]:
    cells = []
    for index in range(size):
        row, offset = divmod(index, width)
        col = offset if row % 2 == 0 else width - 1 - offset
        cells.append((row, col))
    shape = _normalize(cells)
    if not _connected(shape):
        raise RuntimeError("snake constructor lost connectivity")
    return shape


_TRAIN_PROFILES = (
    Profile(9, 12, 3, _rect(2, 3), _l_shape(3, 3), "horizontal"),
    Profile(10, 13, 4, _l_shape(3, 3), _snake(7, 3), "vertical"),
    Profile(12, 14, 5, _snake(8, 3), _l_shape(3, 3), "horizontal"),
    Profile(14, 16, 3, _t_shape(4, 3), _snake(9, 4), "vertical"),
    Profile(18, 20, 4, _snake(11, 4), _l_shape(4, 3), "horizontal"),
    Profile(22, 24, 5, _t_shape(5, 5), _snake(13, 5), "vertical"),
)
_QUERY_PROFILES = (
    Profile(9, 11, 5, _l_shape(3, 3), _snake(7, 3), "horizontal"),
    Profile(16, 19, 3, _snake(13, 5), _t_shape(4, 3), "vertical"),
    Profile(24, 27, 4, _snake(37, 7), _l_shape(8, 6), "horizontal", True),
    Profile(30, 30, 5, _snake(83, 8), _snake(67, 9), "vertical", True),
)


def _rng(seed: int, split: str, index: int) -> random.Random:
    payload = f"{TASK_ID}|larger-rotate-inputs-v1|{seed}|{split}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def _translated(
    shape: frozenset[tuple[int, int]], row: int, col: int
) -> frozenset[tuple[int, int]]:
    return frozenset((row + drow, col + dcol) for drow, dcol in shape)


def _place_pair(profile: Profile, rng: random.Random) -> tuple[frozenset[tuple[int, int]], frozenset[tuple[int, int]]]:
    shapes = [(1, profile.first), (2, profile.second)]
    if rng.randrange(2):
        shapes.reverse()

    if profile.orientation == "horizontal":
        (left_color, left), (right_color, right) = shapes
        lh, lw = _extent(left)
        rh, rw = _extent(right)
        if lw + rw + 1 > profile.width:
            raise RuntimeError("horizontal profile does not fit")
        free = profile.width - lw - rw - 1
        if profile.spread:
            left_col = 0
            right_col = profile.width - rw
        else:
            left_col = rng.randint(0, free)
            right_col = left_col + lw + 1 + rng.randint(0, free - left_col)
            if right_col + rw > profile.width:
                right_col = profile.width - rw
        left_row = rng.randint(1, profile.height - lh)
        right_row = rng.randint(1, profile.height - rh)
        placed = {
            left_color: _translated(left, left_row, left_col),
            right_color: _translated(right, right_row, right_col),
        }
    elif profile.orientation == "vertical":
        (top_color, top), (bottom_color, bottom) = shapes
        th, tw = _extent(top)
        bh, bw = _extent(bottom)
        usable_height = profile.height - 1
        if th + bh + 1 > usable_height:
            raise RuntimeError("vertical profile does not fit")
        free = usable_height - th - bh - 1
        if profile.spread:
            top_row = 1
            bottom_row = profile.height - bh
            top_col = 0
            bottom_col = profile.width - bw
        else:
            top_row = 1 + rng.randint(0, free)
            bottom_row = top_row + th + 1 + rng.randint(0, free - (top_row - 1))
            if bottom_row + bh > profile.height:
                bottom_row = profile.height - bh
            top_col = rng.randint(0, profile.width - tw)
            bottom_col = rng.randint(0, profile.width - bw)
        placed = {
            top_color: _translated(top, top_row, top_col),
            bottom_color: _translated(bottom, bottom_row, bottom_col),
        }
    else:
        raise ValueError(f"unknown orientation {profile.orientation!r}")

    if (0, 0) in placed[1] or (0, 0) in placed[2] or not placed[1].isdisjoint(placed[2]):
        raise RuntimeError("physical placement overlaps control or the other operand")
    return placed[1], placed[2]


def _sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _TRAIN_PROFILES if split == "train" else _QUERY_PROFILES
    profile = profiles[index]
    rng = _rng(seed, split, index)
    first, second = _place_pair(profile, rng)
    grid = [[0 for _ in range(profile.width)] for _ in range(profile.height)]
    grid[0][0] = profile.ctrl
    for row, col in first:
        grid[row][col] = 1
    for row, col in second:
        grid[row][col] = 2
    analysis = analyze_input(grid)
    if analysis["sizes"][1] == analysis["sizes"][2]:
        raise RuntimeError("teaching grammar requires unequal occupied areas")
    if transform(grid, {PARAMETER: "identity"}) == transform(
        grid, {PARAMETER: "rotate_larger_cw"}
    ):
        raise RuntimeError(f"profile {split}[{index}] does not distinguish settings")
    return grid


def _policy_solver(name: str) -> Callable[[list[list[int]]], list[list[int]]]:
    def solve(grid: list[list[int]]) -> list[list[int]]:
        analysis = analyze_input(grid)
        if name == "rotate_smaller_cw":
            return _transform_policy(grid, selected_color=analysis["smaller_color"])
        if name == "rotate_color1_cw":
            return _transform_policy(grid, selected_color=1)
        if name == "rotate_color2_cw":
            return _transform_policy(grid, selected_color=2)
        if name == "rotate_larger_ccw":
            return _transform_policy(
                grid, selected_color=analysis["larger_color"], rotation="ccw"
            )
        if name == "rotate_larger_180":
            return _transform_policy(
                grid, selected_color=analysis["larger_color"], rotation="180"
            )
        if name == "rotate_bbox_larger_cw":
            selected = 1 if analysis["bbox_areas"][1] >= analysis["bbox_areas"][2] else 2
            return _transform_policy(grid, selected_color=selected)
        preprocess, op = name.split("_always_", 1)
        selected_color = None if preprocess == "identity" else analysis["larger_color"]
        forced = {"union": 3, "xor": 4, "intersection": 5}[op]
        return _transform_policy(grid, selected_color=selected_color, forced_ctrl=forced)

    return solve


_RIVAL_NAMES = (
    "rotate_smaller_cw",
    "rotate_color1_cw",
    "rotate_color2_cw",
    "rotate_larger_ccw",
    "rotate_larger_180",
    "rotate_bbox_larger_cw",
    "identity_always_union",
    "identity_always_xor",
    "identity_always_intersection",
    "rotate_larger_always_union",
    "rotate_larger_always_xor",
    "rotate_larger_always_intersection",
)
RIVAL_SOLVERS = {name: _policy_solver(name) for name in _RIVAL_NAMES}


def audit_episode(episode: dict[str, Any], selected_setting: str) -> dict[str, Any]:
    if selected_setting not in SETTINGS:
        raise ValueError(f"unknown selected setting {selected_setting!r}")
    train = episode.get("train")
    if type(train) is not list or not MIN_DEMOS <= len(train) <= MAX_DEMOS:
        raise ValueError("episode has an invalid demonstration list")

    declared = []
    for setting in SETTINGS:
        disagreements = [
            index
            for index, pair in enumerate(train)
            if transform(pair["input"], {PARAMETER: setting}) != pair["output"]
        ]
        declared.append(
            {"settings": {PARAMETER: setting}, "disagreeing_demo_indices": disagreements}
        )
    survivors = [record["settings"] for record in declared if not record["disagreeing_demo_indices"]]
    expected = [{PARAMETER: selected_setting}]
    if survivors != expected:
        raise ValueError(f"demonstrations do not identify selected setting: {survivors}")

    rival_refutations: dict[str, list[int]] = {}
    for name, rival in RIVAL_SOLVERS.items():
        disagreements = [
            index
            for index, pair in enumerate(train)
            if rival(pair["input"]) != pair["output"]
        ]
        if not disagreements:
            raise ValueError(f"finite rival {name!r} survives every demonstration")
        rival_refutations[name] = disagreements
    return {
        "scope": "two declared settings plus twelve authored preprocessing/control shortcuts",
        "survivors": survivors,
        "declared_refutations": declared,
        "rival_refutations": rival_refutations,
        "limits": "Finite authored rival set only; this is not a uniqueness proof.",
    }


def generate(
    seed: int,
    settings: dict[str, str],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    seed = _strict_int("seed", seed, 0, MAX_SEED)
    demos = _strict_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = _strict_int("queries", queries, MIN_QUERIES, MAX_QUERIES)
    chosen = _settings(settings)

    train = []
    for index in range(demos):
        grid = _sample_input(seed, "train", index)
        train.append({"input": grid, "output": transform(grid, chosen)})
    test = []
    for index in range(queries):
        grid = _sample_input(seed, "query", index)
        test.append({"input": grid, "output": transform(grid, chosen)})

    serialized = [
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in train + test
    ]
    if len(serialized) != len(set(serialized)):
        raise RuntimeError("all demonstration and query inputs must be distinct")
    episode = {
        "schema": "3020cc038f3f-larger-rotate-parametric-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": chosen,
        "train": train,
        "test": test,
        "program_solution": program(chosen),
        "program_sha256": hashlib.sha256(program(chosen).encode()).hexdigest(),
    }
    episode["certificate"] = audit_episode(episode, chosen[PARAMETER])
    return episode


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    test = episode.get("test")
    train = episode.get("train")
    if type(test) is not list or type(train) is not list:
        raise ValueError("episode must contain train/test lists")
    _strict_int("query_index", query_index, 0, len(test) - 1)
    return {
        "train": copy.deepcopy(train),
        "test": [{"input": copy.deepcopy(test[query_index]["input"])}],
    }


def source_hashes() -> dict[str, str]:
    files = (
        "prototype.py",
        "adapter.py",
        "canonical.rkt",
        "rotate_larger_cw.rkt",
        "rotate_smaller_counterfactual.rkt",
        "promotion.json",
    )
    return {
        name: hashlib.sha256((_HOME / name).read_bytes()).hexdigest()
        for name in files
        if (_HOME / name).exists()
    }
