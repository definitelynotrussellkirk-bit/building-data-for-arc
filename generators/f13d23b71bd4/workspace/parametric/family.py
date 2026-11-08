"""Native family for canonical and signal-ranked object falling.

The canonical setting is the byte-exact selected rule: every monochrome
4-connected object of size at least four falls to the canvas bottom.  The
alternative first measures the unique color-1 signal object's size, uses that
size as a one-based rank among large non-signal objects in row-major order, and
then drops only the selected object.  Inputs are independent of the private
setting.
"""
from __future__ import annotations

import copy
import hashlib
import random
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
POLICIES = ("all_large", "signal_ranked")
SETTINGS = tuple({"fall_policy": policy} for policy in POLICIES)
BACKGROUND = 7

# The first two demonstrations are a constructive teaching core: ranks two and
# three select different positions, sizes, and colors.  Later profiles expand
# geometry and stress without changing the first-two teaching contract.
_TRAIN_PROFILES = (
    ((11, 15), 2, 5, 0),
    ((13, 18), 3, 5, 3),
    ((16, 21), 1, 6, 5),
    ((19, 24), 3, 6, 1),
    ((23, 27), 2, 7, 4),
    ((27, 29), 1, 7, 6),
)
_QUERY_PROFILES = (
    ((15, 17), 1, 5, 2),
    ((20, 22), 3, 6, 6),
    ((25, 27), 2, 7, 1),
    ((30, 30), 3, 8, 0),
)

# Connected shapes of sizes four through eleven, each at most two columns wide.
_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (1, 0), (2, 0), (3, 0)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (3, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1), (3, 0), (3, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1), (3, 0), (3, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1), (3, 0), (3, 1), (4, 0), (4, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1), (3, 0), (3, 1), (4, 0), (4, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1), (3, 0), (3, 1), (4, 0), (4, 1), (5, 0), (5, 1)),
)
_CARGO_COLORS = (2, 3, 4, 5, 6, 8, 9)
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _policy(settings: Any) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"fall_policy"}
        or type(settings["fall_policy"]) is not str
        or settings["fall_policy"] not in POLICIES
    ):
        raise ValueError(
            "settings must contain only fall_policy='all_large' or 'signal_ranked'"
        )
    return settings["fall_policy"]


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program(settings: Any) -> str:
    policy = _policy(settings)
    name = "canonical.rkt" if policy == "all_large" else "signal_ranked.rkt"
    return (HERE / name).read_text()


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must be a rectangular 1..30 ARC grid")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must use exact integer colors 0..9")
    return value


def _components(grid: Any) -> list[dict[str, Any]]:
    source = _grid(grid)
    height, width = len(source), len(source[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for column in range(width):
            color = source[row][column]
            if color == BACKGROUND or (row, column) in seen:
                continue
            stack = [(row, column)]
            seen.add((row, column))
            cells: list[tuple[int, int]] = []
            while stack:
                cell = stack.pop()
                cells.append(cell)
                rr, cc = cell
                for dr, dc in _NEIGHBORS:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and source[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            cells.sort()
            result.append(
                {
                    "color": color,
                    "cells": tuple(cells),
                    "size": len(cells),
                    "r1": min(r for r, _ in cells),
                    "c1": min(c for _, c in cells),
                    "r2": max(r for r, _ in cells),
                    "c2": max(c for _, c in cells),
                }
            )
    return result


def _paint_with_target(grid: Any, target_cells: tuple[tuple[int, int], ...] | None) -> list[list[int]]:
    source = _grid(grid)
    height, width = len(source), len(source[0])
    out = [[BACKGROUND] * width for _ in range(height)]
    for obj in _components(source):
        falling = target_cells is not None and obj["cells"] == target_cells
        drop = height - 1 - obj["r2"] if falling else 0
        for row, column in obj["cells"]:
            out[row + drop][column] = obj["color"]
    return out


def apply_all_large(grid: Any) -> list[list[int]]:
    source = _grid(grid)
    height, width = len(source), len(source[0])
    out = [[BACKGROUND] * width for _ in range(height)]
    for obj in _components(source):
        drop = height - 1 - obj["r2"] if obj["size"] >= 4 else 0
        for row, column in obj["cells"]:
            out[row + drop][column] = obj["color"]
    return out


def _signal_and_candidates(grid: Any) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    objects = _components(grid)
    signals = [obj for obj in objects if obj["color"] == 1]
    if len(signals) != 1 or not 1 <= signals[0]["size"] <= 3:
        raise ValueError("input must contain exactly one color-1 signal of size 1..3")
    candidates = [
        obj for obj in objects if obj["color"] != 1 and obj["size"] >= 4
    ]
    if len(candidates) < 3:
        raise ValueError("input must contain at least three large non-signal objects")
    return signals[0], candidates


def signal_intermediate(grid: Any) -> dict[str, Any]:
    signal, candidates = _signal_and_candidates(grid)
    rank = signal["size"]
    if rank > len(candidates):
        raise ValueError("signal rank exceeds the candidate count")
    target = candidates[rank - 1]
    return {
        "rank": rank,
        "candidate_count": len(candidates),
        "target_bbox": [target["r1"], target["c1"], target["r2"], target["c2"]],
        "target_color": target["color"],
        "target_size": target["size"],
        "target_cells": [list(cell) for cell in target["cells"]],
    }


def apply_ranked(grid: Any, rank: Any) -> list[list[int]]:
    rank = _exact_int(rank, "rank", 1, 64)
    _, candidates = _signal_and_candidates(grid)
    if rank > len(candidates):
        raise ValueError("rank exceeds the candidate count")
    return _paint_with_target(grid, candidates[rank - 1]["cells"])


def transform(grid: Any, settings: Any) -> list[list[int]]:
    policy = _policy(settings)
    if policy == "all_large":
        return apply_all_large(grid)
    return apply_ranked(grid, signal_intermediate(grid)["rank"])


def _rng(seed: int, split: str, index: int, salt: str) -> random.Random:
    raw = f"f13d23b71bd4-native-v1:{seed}:{split}:{index}:{salt}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _rotate(values: tuple[Any, ...], offset: int) -> tuple[Any, ...]:
    offset %= len(values)
    return values[offset:] + values[:offset]


def _shape_size(shape: Iterable[tuple[int, int]]) -> int:
    return sum(1 for _ in shape)


def _place(
    grid: list[list[int]],
    shape: tuple[tuple[int, int], ...],
    top: int,
    left: int,
    color: int,
) -> None:
    height, width = len(grid), len(grid[0])
    for dr, dc in shape:
        row, column = top + dr, left + dc
        if not (0 <= row < height and 0 <= column < width):
            raise ValueError("constructed object leaves the canvas")
        if grid[row][column] != BACKGROUND:
            raise ValueError("constructed objects overlap")
        grid[row][column] = color


def _signal_shape(rank: int) -> tuple[tuple[int, int], ...]:
    return {
        1: ((0, 0),),
        2: ((0, 0), (0, 1)),
        3: ((0, 0), (1, 0), (1, 1)),
    }[rank]


def _scene(
    seed: int,
    split: str,
    index: int,
    size: tuple[int, int],
    rank: int,
    cargo_count: int,
    offset: int,
) -> list[list[int]]:
    height, width = size
    grid = [[BACKGROUND] * width for _ in range(height)]
    rng = _rng(seed, split, index, "scene")

    shapes = _rotate(_SHAPES, offset + seed % len(_SHAPES))
    colors = _rotate(_CARGO_COLORS, offset + (seed // 3) % len(_CARGO_COLORS))
    step = max(2, (width - 4) // cargo_count)
    top = 1 + rng.randrange(2)
    for cargo_index in range(cargo_count):
        shape = shapes[cargo_index]
        if rng.randrange(2):
            max_col = max(dc for _, dc in shape)
            shape = tuple((dr, max_col - dc) for dr, dc in shape)
        left = 2 + cargo_index * step
        color = colors[cargo_index % len(colors)]
        _place(grid, shape, top, left, color)

    signal = _signal_shape(rank)
    signal_height = 1 + max(dr for dr, _ in signal)
    _place(grid, signal, height - signal_height, 0, 1)

    # Small boundary distractors remain stationary under both settings and keep
    # the large 30x30 scene substantive.  Gaps prevent accidental merging.
    _place(grid, ((0, 0), (1, 0)), 0, 0, 6)
    _place(grid, ((0, 1), (1, 0), (1, 1)), 0, width - 2, 8)
    for ordinal, row in enumerate(range(3, height - 1, 3)):
        color = (2, 4, 5, 9)[(ordinal + offset) % 4]
        if grid[row][width - 1] == BACKGROUND:
            grid[row][width - 1] = color
    for ordinal, row in enumerate(range(4, max(4, height - 3), 4)):
        color = (3, 5, 8, 9)[(ordinal + offset + 1) % 4]
        if grid[row][0] == BACKGROUND:
            grid[row][0] = color
    if grid[height - 1][width - 1] == BACKGROUND:
        grid[height - 1][width - 1] = 5

    signal_obj, candidates = _signal_and_candidates(grid)
    if signal_obj["size"] != rank or len(candidates) != cargo_count:
        raise ValueError("constructed signal/candidate grammar drifted")
    if any(obj["r2"] == height - 1 for obj in candidates):
        raise ValueError("cargo must have positive falling distance")
    # Every cargo object occupies its own column band, so both transformations
    # preserve all cargo cells without accidental overwrite.
    return grid


def _profile_pairs(
    seed: int,
    split: str,
    profiles: tuple[tuple[tuple[int, int], int, int, int], ...],
    count: int,
    settings: dict[str, str],
) -> list[dict[str, list[list[int]]]]:
    result = []
    for index, (size, rank, cargo_count, offset) in enumerate(profiles[:count]):
        grid = _scene(seed, split, index, size, rank, cargo_count, offset)
        result.append({"input": grid, "output": transform(grid, settings)})
    return result


def _target_output(grid: Any, selector: str) -> list[list[int]]:
    _, candidates = _signal_and_candidates(grid)
    if selector == "first":
        target = candidates[0]
    elif selector == "second":
        target = candidates[1]
    elif selector == "third":
        target = candidates[2]
    elif selector == "last":
        target = candidates[-1]
    elif selector == "largest":
        target = max(candidates, key=lambda obj: (obj["size"], -obj["r1"], -obj["c1"]))
    elif selector == "smallest":
        target = min(candidates, key=lambda obj: (obj["size"], obj["r1"], obj["c1"]))
    else:
        raise ValueError(f"unknown selector {selector!r}")
    return _paint_with_target(grid, target["cells"])


RIVALS = (
    "canonical_all_large",
    "fixed_first",
    "fixed_second",
    "fixed_third",
    "fixed_last",
    "largest_large",
    "smallest_large",
    "reverse_signal_rank",
    "signal_rank_plus_one",
)


def _rival_output(grid: Any, name: str) -> list[list[int]]:
    if name == "canonical_all_large":
        return apply_all_large(grid)
    if name.startswith("fixed_"):
        return _target_output(grid, name.removeprefix("fixed_"))
    if name == "largest_large":
        return _target_output(grid, "largest")
    if name == "smallest_large":
        return _target_output(grid, "smallest")
    rank = signal_intermediate(grid)["rank"]
    _, candidates = _signal_and_candidates(grid)
    if name == "reverse_signal_rank":
        return _paint_with_target(grid, candidates[-rank]["cells"])
    if name == "signal_rank_plus_one":
        return _paint_with_target(grid, candidates[rank % len(candidates)]["cells"])
    raise ValueError(f"undeclared rival {name!r}")


def teaching_check(episode: Any, settings: Any) -> dict[str, Any]:
    policy = _policy(settings)
    if type(episode) is not dict or type(episode.get("train")) is not list:
        raise ValueError("episode must contain a demonstration list")
    demos = episode["train"]
    survivors = [
        {"fall_policy": candidate}
        for candidate in POLICIES
        if all(
            transform(pair["input"], {"fall_policy": candidate}) == pair["output"]
            for pair in demos
        )
    ]
    rivals = [
        name
        for name in RIVALS
        if not (policy == "all_large" and name == "canonical_all_large")
    ]
    surviving_rivals = [
        name
        for name in rivals
        if all(_rival_output(pair["input"], name) == pair["output"] for pair in demos)
    ]
    return {
        "survivors": survivors,
        "surviving_rivals": surviving_rivals,
        "rivals_tested": rivals,
        "basis": "demonstrations_only",
        "scope": "two declared settings and nine named shortcut families",
    }


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    _exact_int(demos, "demos", 2, 6)
    _exact_int(queries, "queries", 1, 4)
    policy = _policy(settings)
    normalized = {"fall_policy": policy}
    episode = {
        "train": _profile_pairs(seed, "train", _TRAIN_PROFILES, demos, normalized),
        "test": _profile_pairs(seed, "test", _QUERY_PROFILES, queries, normalized),
        "program_solution": program(normalized),
        "seed": seed,
        "settings": copy.deepcopy(normalized),
    }
    inputs = [repr(pair["input"]) for split in ("train", "test") for pair in episode[split]]
    if len(inputs) != len(set(inputs)):
        raise ValueError("all demonstration and query inputs must be distinct")
    check = teaching_check(episode, normalized)
    if check["survivors"] != [normalized] or check["surviving_rivals"]:
        raise ValueError(f"constructive demonstrations failed teaching contrasts: {check}")
    return episode


def public_turn(episode: Any, query_index: Any) -> dict[str, Any]:
    if (
        type(episode) is not dict
        or type(episode.get("train")) is not list
        or type(episode.get("test")) is not list
    ):
        raise ValueError("episode must contain train and test lists")
    _exact_int(query_index, "query_index", 0, len(episode["test"]) - 1)
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }
