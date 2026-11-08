"""Native canonical and leftmost-ranked framed-band family.

The canonical setting is the byte-exact selected rule: row-sorted singleton
markers define adjacent horizontal bands, and every band receives full-height
left/right sides plus its marker row and the outer top/bottom closures.

The alternative keeps every marker row and the canonical outer closures, but
first finds the leftmost marker, converts that marker to its row-order rank, and
uses the rank to select the only band that receives vertical side borders.
Inputs are independent of the private setting.
"""
from __future__ import annotations

import copy
import hashlib
import random
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
POLICIES = ("all_bands", "leftmost_ranked")
SETTINGS = tuple({"frame_policy": policy} for policy in POLICIES)

_TRAIN_PROFILES = (
    ((12, 16), 4, 2, 0),
    ((15, 19), 5, 4, 3),
    ((18, 21), 6, 1, 5),
    ((21, 24), 6, 5, 1),
    ((24, 27), 7, 3, 6),
    ((27, 29), 8, 6, 2),
)
_QUERY_PROFILES = (
    ((15, 17), 5, 3, 2),
    ((20, 22), 6, 1, 5),
    ((25, 27), 7, 5, 1),
    ((30, 30), 8, 8, 4),
)
_PROFILE_RANK_BY_SIZE = {
    size: rank for size, _marker_count, rank, _offset in _TRAIN_PROFILES + _QUERY_PROFILES
}


def _policy(settings: Any) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"frame_policy"}
        or type(settings["frame_policy"]) is not str
        or settings["frame_policy"] not in POLICIES
    ):
        raise ValueError(
            "settings must contain only frame_policy='all_bands' or 'leftmost_ranked'"
        )
    return settings["frame_policy"]


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program(settings: Any) -> str:
    policy = _policy(settings)
    name = "canonical.rkt" if policy == "all_bands" else "leftmost_ranked.rkt"
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


def _markers(grid: Any) -> list[dict[str, int]]:
    source = _grid(grid)
    markers = [
        {"row": r, "column": c, "color": value}
        for r, row in enumerate(source)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not 2 <= len(markers) <= 9:
        raise ValueError("input must contain 2..9 nonzero singleton markers")
    if len({item["row"] for item in markers}) != len(markers):
        raise ValueError("marker rows must be distinct")
    if len({item["color"] for item in markers}) != len(markers):
        raise ValueError("marker colors must be unique")
    markers.sort(key=lambda item: item["row"])
    return markers


def _band_bounds(markers: list[dict[str, int]], height: int, index: int) -> tuple[int, int]:
    start = 0 if index == 0 else (markers[index - 1]["row"] + markers[index]["row"]) // 2 + 1
    end = height - 1 if index == len(markers) - 1 else (markers[index]["row"] + markers[index + 1]["row"]) // 2
    return start, end


def _paint(grid: Any, selected_rank: int | None) -> list[list[int]]:
    source = _grid(grid)
    markers = _markers(source)
    height, width = len(source), len(source[0])
    out = [[0] * width for _ in range(height)]
    for index, marker in enumerate(markers):
        start, end = _band_bounds(markers, height, index)
        color = marker["color"]
        for column in range(width):
            out[marker["row"]][column] = color
        if index == 0:
            for column in range(width):
                out[0][column] = color
        if index == len(markers) - 1:
            for column in range(width):
                out[height - 1][column] = color
        if selected_rank is None or selected_rank == index + 1:
            for row in range(start, end + 1):
                out[row][0] = color
                out[row][width - 1] = color
    return out


def apply_all_bands(grid: Any) -> list[list[int]]:
    return _paint(grid, None)


def apply_ranked(grid: Any, rank: Any) -> list[list[int]]:
    markers = _markers(grid)
    rank = _exact_int(rank, "rank", 1, len(markers))
    return _paint(grid, rank)


def leftmost_intermediate(grid: Any) -> dict[str, Any]:
    markers = _markers(grid)
    selected_index = min(
        range(len(markers)),
        key=lambda index: (markers[index]["column"], markers[index]["row"]),
    )
    marker = markers[selected_index]
    start, end = _band_bounds(markers, len(_grid(grid)), selected_index)
    return {
        "rank": selected_index + 1,
        "marker": [marker["row"], marker["column"], marker["color"]],
        "band_rows": [start, end],
        "marker_count": len(markers),
    }


def transform(grid: Any, settings: Any) -> list[list[int]]:
    policy = _policy(settings)
    if policy == "all_bands":
        return apply_all_bands(grid)
    return apply_ranked(grid, leftmost_intermediate(grid)["rank"])


def _rng(seed: int, split: str, index: int, salt: str) -> random.Random:
    raw = f"f5e7cf8dc78d-native-v1:{seed}:{split}:{index}:{salt}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _spread_rows(height: int, count: int) -> list[int]:
    return [2 + (index * (height - 5)) // (count - 1) for index in range(count)]


def _scene(
    seed: int,
    split: str,
    index: int,
    size: tuple[int, int],
    marker_count: int,
    leftmost_rank: int,
    offset: int,
) -> list[list[int]]:
    height, width = size
    if not 2 <= marker_count <= 9 or not 1 <= leftmost_rank <= marker_count:
        raise ValueError("invalid marker profile")
    rows = _spread_rows(height, marker_count)
    rng = _rng(seed, split, index, "scene")

    colors = list(range(1, 10))
    rng.shuffle(colors)
    colors = colors[:marker_count]
    selected = leftmost_rank - 1
    if colors[selected] in (min(colors), max(colors)):
        swap = next(
            position
            for position, color in enumerate(colors)
            if position != selected and color not in (min(colors), max(colors))
        )
        colors[selected], colors[swap] = colors[swap], colors[selected]

    columns: list[int | None] = [None] * marker_count
    leftmost_column = 1 + ((seed + index + offset + (0 if split == "train" else 1)) % 3)
    columns[selected] = leftmost_column
    rightmost = 0 if selected != 0 else marker_count - 1
    columns[rightmost] = width - 2
    available = list(range(leftmost_column + 2, width - 2))
    rng.shuffle(available)
    for position in range(marker_count):
        if columns[position] is None:
            columns[position] = available.pop()
    typed_columns = [int(value) for value in columns]

    # Rotate all non-causal features across profiles and seeds while preserving
    # the unique leftmost-marker rank.
    rotation = (seed + offset) % marker_count
    if rotation:
        other_positions = [p for p in range(marker_count) if p not in (selected, rightmost)]
        other_values = [typed_columns[p] for p in other_positions]
        if other_values:
            rotation %= len(other_values)
            other_values = other_values[rotation:] + other_values[:rotation]
            for position, value in zip(other_positions, other_values, strict=True):
                typed_columns[position] = value

    grid = [[0] * width for _ in range(height)]
    for row, column, color in zip(rows, typed_columns, colors, strict=True):
        grid[row][column] = color

    intermediate = leftmost_intermediate(grid)
    if intermediate["rank"] != leftmost_rank:
        raise ValueError("constructed leftmost rank drifted")
    rightmost_rank = max(range(marker_count), key=lambda i: typed_columns[i]) + 1
    if rightmost_rank == leftmost_rank:
        raise ValueError("leftmost and rightmost markers must differ")
    return grid


def _profile_rank(seed: int, split: str, index: int, marker_count: int, base_rank: int) -> int:
    """Vary the causal rank independently of the visible canvas profile."""
    if split == "train" and index == 0:
        return 2 + seed % 2
    if split == "train" and index == 1:
        return 3 + seed % 2
    return 1 + ((base_rank - 1 + seed + index) % marker_count)


def _profile_pairs(
    seed: int,
    split: str,
    profiles: tuple[tuple[tuple[int, int], int, int, int], ...],
    count: int,
    settings: dict[str, str],
) -> list[dict[str, list[list[int]]]]:
    result = []
    for index, (size, marker_count, base_rank, offset) in enumerate(profiles[:count]):
        rank = _profile_rank(seed, split, index, marker_count, base_rank)
        grid = _scene(seed, split, index, size, marker_count, rank, offset)
        result.append({"input": grid, "output": transform(grid, settings)})
    return result


def _rank_for_selector(grid: Any, selector: str) -> int:
    markers = _markers(grid)
    n = len(markers)
    if selector.startswith("fixed_"):
        number = int(selector.removeprefix("fixed_"))
        return min(number, n)
    if selector == "last":
        return n
    if selector == "rightmost":
        return max(range(n), key=lambda i: (markers[i]["column"], -markers[i]["row"])) + 1
    if selector == "lowest_color":
        return min(range(n), key=lambda i: markers[i]["color"]) + 1
    if selector == "highest_color":
        return max(range(n), key=lambda i: markers[i]["color"]) + 1
    if selector == "absolute_column_1":
        return next((i + 1 for i, marker in enumerate(markers) if marker["column"] == 1), 1)
    if selector == "profile_rank":
        height, width = len(_grid(grid)), len(_grid(grid)[0])
        return min(_PROFILE_RANK_BY_SIZE.get((height, width), 1), n)
    rank = leftmost_intermediate(grid)["rank"]
    if selector == "reverse_leftmost":
        return n - rank + 1
    if selector == "leftmost_plus_one":
        return rank % n + 1
    raise ValueError(f"unknown selector {selector!r}")


RIVALS = (
    "canonical_all_bands",
    "fixed_1",
    "fixed_2",
    "fixed_3",
    "fixed_4",
    "last",
    "rightmost",
    "lowest_color",
    "highest_color",
    "absolute_column_1",
    "profile_rank",
    "reverse_leftmost",
    "leftmost_plus_one",
)


def _rival_output(grid: Any, name: str) -> list[list[int]]:
    if name == "canonical_all_bands":
        return apply_all_bands(grid)
    return apply_ranked(grid, _rank_for_selector(grid, name))


def teaching_check(episode: Any, settings: Any) -> dict[str, Any]:
    policy = _policy(settings)
    if type(episode) is not dict or type(episode.get("train")) is not list:
        raise ValueError("episode must contain a demonstration list")
    demos = episode["train"]
    survivors = [
        {"frame_policy": candidate}
        for candidate in POLICIES
        if all(
            transform(pair["input"], {"frame_policy": candidate}) == pair["output"]
            for pair in demos
        )
    ]
    rivals = [
        name
        for name in RIVALS
        if not (policy == "all_bands" and name == "canonical_all_bands")
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
        "scope": "two declared settings and thirteen named shortcut families",
    }


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    _exact_int(demos, "demos", 2, 6)
    _exact_int(queries, "queries", 1, 4)
    policy = _policy(settings)
    normalized = {"frame_policy": policy}
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
