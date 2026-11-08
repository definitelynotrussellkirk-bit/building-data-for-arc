"""Standalone crop-to-emblem completion generator for public task 269e22fb."""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
from functools import lru_cache
import hashlib
import random

GENERATOR_ID = TASK_ID = "public_eval_269e22fb"
RULE_TASK_ID = 'ee_269e22fb'
VERSION = "1.0.0"
SUMMARY = "Locate a two-color crop inside a dihedral emblem completion and reconstruct the full 20 by 20 canvas."
INVARIANTS = [
    "exactly two unequal-frequency colors",
    "minority color denotes the emblem",
    "input is a unique contiguous crop of one dihedral emblem pose",
    "output is 20 by 20",
]

# The canonical emblem is specified as horizontal geometric strokes, not as a
# table from supplied inputs to supplied outputs. Each pair is an inclusive run.
RUNS: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 1), (15, 16)),
    ((0, 5), (15, 16)),
    ((0, 6), (15, 17)),
    ((0, 1), (5, 7), (15, 17)),
    ((6, 8), (14, 18)),
    ((7, 9), (14, 14), (17, 18)),
    ((8, 9), (12, 14), (17, 18)),
    ((9, 9), (12, 12), (14, 14), (17, 18)),
    ((9, 12), (14, 14), (17, 18)),
    ((1, 9), (11, 12), (14, 14), (17, 18)),
    ((1, 1), (9, 12), (14, 14), (17, 18)),
    ((1, 9), (12, 12), (14, 14), (17, 18)),
    ((1, 1), (3, 3), (9, 9), (12, 14), (17, 18)),
    ((0, 2), (4, 9), (14, 14), (17, 18)),
    ((1, 1), (3, 4), (9, 9), (14, 18)),
    ((0, 2), (4, 4), (9, 9), (13, 14), (16, 17)),
    ((1, 1), (3, 4), (9, 9), (13, 13), (17, 18)),
    ((0, 2), (4, 4), (9, 9), (13, 14), (18, 19)),
    ((1, 1), (3, 4), (8, 8), (10, 10), (14, 14), (16, 18)),
    ((0, 2), (7, 7), (11, 11), (14, 16)),
)

PROFILE_DIMS: tuple[tuple[int, int], ...] = (
    (8, 10), (13, 12), (10, 10), (16, 8), (9, 14),
    (14, 9), (11, 10), (16, 10), (12, 18), (19, 19),
)


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _policy(value: object) -> str:
    if type(value) is not str or value not in ("preserve", "mark_enclosed"):
        raise ValueError("pocket_policy must be preserve or mark_enclosed")
    return value


def blueprint() -> list[list[int]]:
    return [
        [int(any(start <= column <= end for start, end in RUNS[row])) for column in range(20)]
        for row in range(20)
    ]


def rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1], strict=True)]


def rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid[::-1]]


def rotate_ccw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid, strict=True)][::-1]


def flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid]


def flip_ud(grid: list[list[int]]) -> list[list[int]]:
    return grid[::-1]


def transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid, strict=True)]


@lru_cache(maxsize=1)
def _pose_bank() -> tuple[tuple[tuple[int, ...], ...], ...]:
    source = blueprint()
    poses = [
        source,
        rotate_cw(source),
        rotate_180(source),
        rotate_ccw(source),
        flip_lr(source),
        flip_ud(source),
        transpose(source),
        rotate_180(transpose(source)),
    ]
    return tuple(tuple(tuple(row) for row in pose) for pose in poses)


def transforms(grid: list[list[int]] | None = None) -> list[list[list[int]]]:
    if grid is None:
        return [[list(row) for row in pose] for pose in _pose_bank()]
    source = deepcopy(grid)
    return [
        source,
        rotate_cw(source),
        rotate_180(source),
        rotate_ccw(source),
        flip_lr(source),
        flip_ud(source),
        transpose(source),
        rotate_180(transpose(source)),
    ]


def _parse(grid: object) -> tuple[list[list[int]], int, int, int, int]:
    if type(grid) is not list or not 2 <= len(grid) <= 20:
        raise ValueError("grid height must be an exact list in 2..20")
    if type(grid[0]) is not list or not 2 <= len(grid[0]) <= 20:
        raise ValueError("grid width must be an exact list in 2..20")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("rectangular exact list rows required")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("exact integer ARC colors 0..9 required")
    counts = Counter(value for row in grid for value in row)
    if len(counts) != 2 or len(set(counts.values())) != 2:
        raise ValueError("exactly two colors with unequal frequencies required")
    background = max(counts, key=counts.get)
    foreground = min(counts, key=counts.get)
    copied = [row[:] for row in grid]
    return copied, len(copied), width, foreground, background


def _binary(grid: list[list[int]], foreground: int) -> list[list[int]]:
    return [[int(value == foreground) for value in row] for row in grid]


def find_matches(binary_crop: list[list[int]]) -> list[tuple[int, int, int]]:
    height, width = len(binary_crop), len(binary_crop[0])
    matches: list[tuple[int, int, int]] = []
    for pose, full in enumerate(_pose_bank()):
        for row in range(21 - height):
            for column in range(21 - width):
                if [list(line[column : column + width]) for line in full[row : row + height]] == binary_crop:
                    matches.append((pose, row, column))
    return matches


def fill_enclosed(grid: list[list[int]], background: int, marker: int = 2) -> tuple[list[list[int]], list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    reachable: set[tuple[int, int]] = set()
    queue: deque[tuple[int, int]] = deque()
    for row in range(height):
        for column in (0, width - 1):
            if grid[row][column] == background and (row, column) not in reachable:
                reachable.add((row, column)); queue.append((row, column))
    for column in range(width):
        for row in (0, height - 1):
            if grid[row][column] == background and (row, column) not in reachable:
                reachable.add((row, column)); queue.append((row, column))
    while queue:
        row, column = queue.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = row + dr, column + dc
            if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] == background and (nr, nc) not in reachable:
                reachable.add((nr, nc)); queue.append((nr, nc))
    enclosed = [
        (row, column)
        for row in range(height)
        for column in range(width)
        if grid[row][column] == background and (row, column) not in reachable
    ]
    output = [row[:] for row in grid]
    for row, column in enclosed:
        output[row][column] = marker
    return output, enclosed


def analyze(grid: object, pocket_policy: str = "preserve") -> dict[str, object]:
    policy = _policy(pocket_policy)
    parsed, _height, _width, foreground, background = _parse(grid)
    binary_crop = _binary(parsed, foreground)
    matches = find_matches(binary_crop)
    if len(matches) != 1:
        raise ValueError(f"crop must identify exactly one pose and offset, found {len(matches)}")
    pose, row, column = matches[0]
    binary_completion = [list(line) for line in _pose_bank()[pose]]
    completion = [[foreground if value else background for value in line] for line in binary_completion]
    marked, enclosed = fill_enclosed(completion, background)
    output = completion if policy == "preserve" else marked
    return {
        "foreground": foreground,
        "background": background,
        "binary_crop": binary_crop,
        "matches": matches,
        "pose": pose,
        "crop_row": row,
        "crop_column": column,
        "binary_completion": binary_completion,
        "completion": completion,
        "enclosed_cells": enclosed,
        "output": output,
    }


def solve(grid: object, pocket_policy: str = "preserve") -> list[list[int]]:
    return deepcopy(analyze(grid, pocket_policy)["output"])


def self_check(grid: object, **_: object) -> list[str]:
    try:
        analyze(grid, "preserve")
    except (TypeError, ValueError) as error:
        return [str(error)]
    return []


def _rng(seed: int, label: str) -> random.Random:
    raw = hashlib.sha256(f"269e22fb/{seed}/{label}".encode()).digest()
    return random.Random(int.from_bytes(raw, "big"))


@lru_cache(maxsize=None)
def _eligible_crops(height: int, width: int, allowed_poses: tuple[int, ...]) -> tuple[tuple[int, int, int], ...]:
    eligible: list[tuple[int, int, int]] = []
    all_poses = _pose_bank()
    for pose in allowed_poses:
        full = all_poses[pose]
        for row in range(21 - height):
            for column in range(21 - width):
                crop = [list(line[column : column + width]) for line in full[row : row + height]]
                ones = sum(sum(line) for line in crop)
                if ones * 2 >= height * width:
                    continue
                if find_matches(crop) == [(pose, row, column)]:
                    eligible.append((pose, row, column))
    return tuple(eligible)


@lru_cache(maxsize=512)
def _sample_scene_cached(seed: int, index: int) -> dict[str, object]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(index, 0, len(PROFILE_DIMS) - 1, "index")
    height, width = PROFILE_DIMS[index]
    allowed = tuple(range(4)) if index == 0 else tuple(range(4, 8)) if index == 1 else tuple(range(8))
    candidates = _eligible_crops(height, width, allowed)
    if not candidates:
        candidates = _eligible_crops(height, width, tuple(range(8)))
    if not candidates:
        raise ValueError(f"no unique crop for profile {index}")
    rng = _rng(seed, f"scene-{index}")
    pose, row, column = rng.choice(candidates)
    palette = [0, 1, 3, 4, 5, 6, 7, 8, 9]
    background, foreground = rng.sample(palette, 2)
    full_binary = _pose_bank()[pose]
    binary_crop = [list(line[column : column + width]) for line in full_binary[row : row + height]]
    input_grid = [[foreground if value else background for value in line] for line in binary_crop]
    canonical = [[foreground if value else background for value in line] for line in full_binary]
    marked, enclosed = fill_enclosed(canonical, background)
    # Exercise the same inference path used by external callers.
    inferred = analyze(input_grid, "preserve")
    if inferred["matches"] != [(pose, row, column)]:
        raise AssertionError("sampled crop inference drift")
    return {
        "input": input_grid,
        "preserve": canonical,
        "mark_enclosed": marked,
        "certificate": {
            "profile": index,
            "pose": pose,
            "crop": [row, column, height, width],
            "foreground": foreground,
            "background": background,
            "enclosed_count": len(enclosed),
        },
    }


def sample_scene(seed: int, index: int) -> dict[str, object]:
    return deepcopy(_sample_scene_cached(seed, index))


def lesson_scenes(seed: int) -> tuple[list[dict[str, object]], list[dict[str, object]], list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    scenes = [sample_scene(seed, index) for index in range(10)]
    order = list(range(4))
    _rng(seed, "query-presentation").shuffle(order)
    if order == [0, 1, 2, 3]:
        order = [1, 2, 3, 0]
    return scenes[:6], [scenes[6 + index] for index in order], order


def generate(seed: int = 0, sample_index: int = 0, *, difficulty: str | None = None, **overrides: object):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(sample_index, 0, 2**63 - 1, "sample_index")
    if difficulty not in (None, "easy", "medium", "hard") or overrides:
        raise ValueError("unsupported generation request")
    stream = int.from_bytes(hashlib.sha256(f"{TASK_ID}|{seed}|{sample_index // 10}".encode()).digest()[:8], "big") % (2**63)
    return deepcopy(sample_scene(stream, sample_index % 10)["input"])
