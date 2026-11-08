"""Episode-fixed red-band anchor family for ARC task 8c12816521a2.

The canonical rule packs each triggered lane's input-derived red count at the
far edge.  The alternate keeps every other step but packs that same count next
to the cyan separator.  Labels returned here are claims; native qualification
replays every program in protected Racket.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any

ANCHORS = ("far_edge", "separator_edge")
_HOME = Path(__file__).resolve().parent


def _anchor(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"red_anchor"}:
        raise ValueError("settings must contain exactly red_anchor")
    anchor = settings["red_anchor"]
    if anchor not in ANCHORS:
        raise ValueError("red_anchor must be far_edge or separator_edge")
    return anchor


def program(settings: dict[str, Any]) -> str:
    anchor = _anchor(settings)
    name = "canonical.rkt" if anchor == "far_edge" else "separator_edge.rkt"
    return (_HOME / name).read_text(encoding="utf-8")


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)]


def _grid(grid: Any) -> list[list[int]]:
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(value) is not int or not 0 <= value <= 9 for value in row)
                   for row in grid)):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return [row[:] for row in grid]


def _normalize(grid: list[list[int]]) -> tuple[list[list[int]], bool, int]:
    height, width = len(grid), len(grid[0])
    horizontal = any(all(grid[row][col] == 8 for col in range(width)) for row in range(height))
    normalized = _transpose(grid) if horizontal else [row[:] for row in grid]
    nheight, nwidth = len(normalized), len(normalized[0])
    separators = [col for col in range(nwidth)
                  if all(normalized[row][col] == 8 for row in range(nheight))]
    if not separators:
        raise ValueError("input requires a complete cyan separator row or column")
    return normalized, horizontal, separators[0]


def solve_python(grid: list[list[int]], red_anchor: str) -> list[list[int]]:
    """Python mirror of both exact Racket settings without mutating the input."""
    if red_anchor not in ANCHORS:
        raise ValueError("red_anchor must be far_edge or separator_edge")
    source = _grid(grid)
    normalized, horizontal, separator = _normalize(source)
    height, width = len(normalized), len(normalized[0])
    left_yellow = sum(normalized[row][col] == 4
                      for row in range(height) for col in range(separator))
    right_yellow = sum(normalized[row][col] == 4
                       for row in range(height) for col in range(separator + 1, width))
    yellow_left = left_yellow > right_yellow
    result: list[list[int]] = []
    for row in range(height):
        yellow_range = range(separator) if yellow_left else range(separator + 1, width)
        red_range = range(separator + 1, width) if yellow_left else range(separator)
        yellow_cells = [col for col in yellow_range if normalized[row][col] == 4]
        red_count = sum(normalized[row][col] == 2 for col in red_range)
        if not yellow_cells:
            result.append(normalized[row][:])
            continue
        values: list[int] = []
        for col, value in enumerate(normalized[row]):
            if value == 4:
                new_value = 3
            elif col == separator:
                new_value = 8
            elif yellow_left and col < separator and col > yellow_cells[-1]:
                new_value = 4
            elif not yellow_left and col > separator and col < yellow_cells[0]:
                new_value = 4
            elif red_anchor == "far_edge" and yellow_left and col > separator and col < width - red_count:
                new_value = 8
            elif red_anchor == "far_edge" and not yellow_left and col < separator and col >= red_count:
                new_value = 8
            elif red_anchor == "far_edge" and yellow_left and col >= width - red_count:
                new_value = 2
            elif red_anchor == "far_edge" and not yellow_left and col < red_count:
                new_value = 2
            elif red_anchor == "separator_edge" and yellow_left and separator < col < separator + red_count + 1:
                new_value = 2
            elif red_anchor == "separator_edge" and not yellow_left and col < separator and col >= separator - red_count:
                new_value = 2
            elif red_anchor == "separator_edge" and yellow_left and col > separator:
                new_value = 8
            elif red_anchor == "separator_edge" and not yellow_left and col < separator:
                new_value = 8
            else:
                new_value = value
            values.append(new_value)
        result.append(values)
    return _transpose(result) if horizontal else result


_DEMO_PROFILES = (
    (15, 17, "vertical", True, 2),
    (18, 16, "horizontal", False, 2),
    (20, 21, "vertical", False, 3),
    (23, 19, "horizontal", True, 3),
    (25, 24, "vertical", True, 2),
    (27, 26, "horizontal", False, 3),
)
_QUERY_PROFILES = (
    (30, 30, "vertical", True, 3),
    (21, 24, "horizontal", False, 2),
    (26, 22, "vertical", False, 3),
    (15, 30, "horizontal", True, 2),
)
_NEUTRAL_COLORS = (1, 3, 5, 6, 7, 9)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _rng(seed: int, stream: str, index: int) -> random.Random:
    digest = hashlib.sha256(
        f"8c12816521a2:red-anchor:v1:{seed}:{stream}:{index}".encode("utf-8")
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _trigger_rows(height: int, components: int, rng: random.Random) -> list[int]:
    rows: set[int] = set()
    for component in range(components):
        center = round((component + 1) * height / (components + 1))
        length = 2 + rng.randrange(2)
        start = max(1, min(height - length - 1, center - length // 2))
        rows.update(range(start, start + length))
    return sorted(rows)


def _scene(seed: int, stream: str, index: int, profile: tuple[int, int, str, bool, int]) -> list[list[int]]:
    height, width, orientation, yellow_left, components = profile
    rng = _rng(seed, stream, index)
    separator = rng.randint(5, width - 6)
    normalized = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        normalized[row][separator] = 8

    # The input red object is one connected shape.  Its common spine makes
    # per-lane red counts observable while allowing counts 1..4 to vary.
    phase = rng.randrange(4)
    if yellow_left:
        spine = separator + 2
        for row in range(height):
            count = 1 + ((row + phase) % 4)
            for col in range(spine, spine + count):
                normalized[row][col] = 2
    else:
        spine = separator - 2
        for row in range(height):
            count = 1 + ((row + phase) % 4)
            for col in range(spine - count + 1, spine + 1):
                normalized[row][col] = 2

    trigger_rows = _trigger_rows(height, components, rng)
    for offset, row in enumerate(trigger_rows):
        length = 1 + ((offset + rng.randrange(3)) % 3)
        if yellow_left:
            end = separator - 2
            for col in range(end - length + 1, end + 1):
                normalized[row][col] = 4
        else:
            start = separator + 2
            for col in range(start, start + length):
                normalized[row][col] = 4

    # A neutral marker makes adjacent seeds observably different without
    # participating in the rule.  Row zero is deliberately non-triggering.
    neutral = _NEUTRAL_COLORS[(seed + index) % len(_NEUTRAL_COLORS)]
    normalized[0][0 if yellow_left else width - 1] = neutral
    return _transpose(normalized) if orientation == "horizontal" else normalized


def _pair(grid: list[list[int]], anchor: str) -> dict[str, list[list[int]]]:
    return {"input": [row[:] for row in grid], "output": solve_python(grid, anchor)}


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict:
    anchor = _anchor(settings)
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")

    demo_inputs = [
        _scene(seed, "demo", index, _DEMO_PROFILES[index])
        for index in range(demos)
    ]
    query_inputs = [
        _scene(seed, "query", index, _QUERY_PROFILES[index])
        for index in range(queries)
    ]
    inputs = demo_inputs + query_inputs
    frozen = [tuple(tuple(row) for row in grid) for grid in inputs]
    if len(set(frozen)) != len(frozen):
        raise ValueError("all demonstration and query inputs must be distinct")
    if any(solve_python(grid, "far_edge") == solve_python(grid, "separator_edge")
           for grid in inputs):
        raise ValueError("every sampled input must distinguish both declared settings")

    return {
        "train": [_pair(grid, anchor) for grid in demo_inputs],
        "test": [_pair(grid, anchor) for grid in query_inputs],
        "program_solution": program(settings),
        "settings": {"red_anchor": anchor},
        "seed": seed,
        "teaching": {
            "used_query_answers": False,
            "minimum_demos_cover": ["vertical-left", "horizontal-right"],
        },
    }


def public_turn(episode: Any, query_index: Any = 0) -> dict[str, Any]:
    """Return visible demos plus one masked query for sequential reveal."""
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    if type(query_index) is not int:
        raise TypeError("query_index must be an exact integer")
    if not 0 <= query_index < len(episode["test"]):
        raise IndexError("query_index is outside the private episode")
    try:
        train = [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ]
        query = {"input": deepcopy(episode["test"][query_index]["input"])}
    except (KeyError, TypeError) as error:
        raise ValueError("episode pairs require input grids and demonstration outputs") from error
    return {"train": train, "test": [query]}
