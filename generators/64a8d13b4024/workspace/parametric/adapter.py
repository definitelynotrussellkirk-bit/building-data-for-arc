"""Native adapter for the color-count bar column-order family.

The production generator and canonical ARC authority remain unchanged.  Both
settings share this adapter's richer input grammar and exact scene bytes:

* ``color_order`` is the byte-exact canonical rule.  It counts colors 1, 2,
  and 3 and renders their bars in fixed color order.
* ``count_descending`` first counts the same colors, then uses those totals to
  rank whole ``(color, height)`` bars by descending height, breaking ties by
  the lower color.  The ranked intermediate determines which colored bar is
  assigned to each output column.

Input sampling never depends on the private setting.  Distractor colors 4..9
make the larger scenes substantive while both Racket rules deliberately count
only colors 1..3.
"""
from __future__ import annotations

import copy
import hashlib
import random
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
POLICIES = ("color_order", "count_descending")
SETTINGS = tuple({"column_order": policy} for policy in POLICIES)

# The first two profiles are a constructive teaching core.  Demo 0 separates
# the two settings; demo 1 exposes the low-color tie break.  Later profiles add
# order and count diversity without changing the minimum teaching context.
_TRAIN_PROFILES = (
    ((10, 12), (2, 6, 4), (3, 1, 2)),
    ((12, 15), (5, 5, 1), (2, 3, 1)),
    ((15, 17), (6, 3, 5), (1, 3, 2)),
    ((18, 20), (1, 4, 6), (2, 1, 3)),
    ((22, 24), (4, 2, 4), (3, 2, 1)),
    ((27, 29), (3, 6, 2), (1, 2, 3)),
)
_QUERY_PROFILES = (
    ((14, 16), (6, 2, 5), (2, 1, 3)),
    ((19, 21), (3, 6, 1), (3, 1, 2)),
    ((24, 27), (2, 5, 5), (1, 3, 2)),
    ((30, 30), (4, 4, 6), (2, 3, 1)),
)


def _policy(settings: Any) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"column_order"}
        or type(settings["column_order"]) is not str
        or settings["column_order"] not in POLICIES
    ):
        raise ValueError(
            "settings must contain only column_order='color_order' or 'count_descending'"
        )
    return settings["column_order"]


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program(settings: Any) -> str:
    policy = _policy(settings)
    name = "canonical.rkt" if policy == "color_order" else "count_descending.rkt"
    return (HERE / name).read_text()


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("input must be a rectangular 1..30 grid")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("input must use exact integer colors 0..9")
    return value


def counts(grid: Any) -> tuple[int, int, int]:
    source = _grid(grid)
    result = tuple(
        sum(cell == color for row in source for cell in row) for color in (1, 2, 3)
    )
    if any(not 1 <= count <= 6 for count in result):
        raise ValueError("each target color must occur 1..6 times")
    return result  # type: ignore[return-value]


def ordered_bars(grid: Any, policy: str) -> tuple[tuple[int, int], ...]:
    if type(policy) is not str or policy not in POLICIES:
        raise ValueError("unknown column-order policy")
    bars = tuple(zip((1, 2, 3), counts(grid), strict=True))
    if policy == "count_descending":
        bars = tuple(sorted(bars, key=lambda item: (-item[1], item[0])))
    return bars


def render_bars(bars: Any) -> list[list[int]]:
    if (
        type(bars) not in (list, tuple)
        or len(bars) != 3
        or any(
            type(item) not in (list, tuple)
            or len(item) != 2
            or type(item[0]) is not int
            or item[0] not in (1, 2, 3)
            or type(item[1]) is not int
            or not 1 <= item[1] <= 6
            for item in bars
        )
        or {item[0] for item in bars} != {1, 2, 3}
    ):
        raise ValueError("bars must contain each target color once with height 1..6")
    return [
        [color if row >= 6 - height else 0 for color, height in bars]
        for row in range(6)
    ]


def transform(grid: Any, settings: Any) -> list[list[int]]:
    return render_bars(ordered_bars(grid, _policy(settings)))


def _rng(seed: int, split: str, index: int, salt: str) -> random.Random:
    raw = f"64a8d13b4024-parametric-v1:{seed}:{split}:{index}:{salt}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _first_free(candidates: list[tuple[int, int]], occupied: set[tuple[int, int]]) -> tuple[int, int]:
    for cell in candidates:
        if cell not in occupied:
            return cell
    raise ValueError("constructed scene exhausted target cells")


def _target_cells(
    seed: int,
    split: str,
    index: int,
    height: int,
    width: int,
    wanted: tuple[int, int, int],
    first_order: tuple[int, int, int],
) -> dict[int, list[tuple[int, int]]]:
    rng = _rng(seed, split, index, "targets")
    # These three top-edge anchors make the row-major first-occurrence order an
    # independently controlled nuisance variable rather than a label shortcut.
    anchor_columns = (1, width // 2, width - 2)
    result = {1: [], 2: [], 3: []}
    occupied: set[tuple[int, int]] = set()
    for column, color in zip(anchor_columns, first_order, strict=True):
        cell = (0, column)
        result[color].append(cell)
        occupied.add(cell)

    side_pools = {
        1: [(height - 1, c) for c in range(1, width - 1)],
        2: [(r, 0) for r in range(1, height)],
        3: [(r, width - 1) for r in range(1, height)],
    }
    for pool in side_pools.values():
        rng.shuffle(pool)

    interior = [(r, c) for r in range(1, height) for c in range(1, width - 1)]
    rng.shuffle(interior)
    for color, count in zip((1, 2, 3), wanted, strict=True):
        remaining = count - 1
        if remaining:
            edge = _first_free(side_pools[color], occupied)
            result[color].append(edge)
            occupied.add(edge)
            remaining -= 1
        while remaining:
            cell = _first_free(interior, occupied)
            result[color].append(cell)
            occupied.add(cell)
            remaining -= 1
    return result


def _distractor_candidates(height: int, width: int, index: int) -> list[tuple[int, int]]:
    candidates: list[tuple[int, int]] = []
    # All four boundaries and two long crossing traces remain visible even in
    # the 30x30 stress scene.  Duplicates are removed while preserving order.
    candidates.extend((0, c) for c in range(width))
    candidates.extend((height - 1, c) for c in range(width))
    candidates.extend((r, 0) for r in range(1, height - 1))
    candidates.extend((r, width - 1) for r in range(1, height - 1))
    candidates.extend((r, (2 * r + index) % width) for r in range(1, height - 1))
    candidates.extend((r, (width - 1 - 3 * r - index) % width) for r in range(1, height - 1))
    candidates.extend((height // 3, c) for c in range(1, width - 1))
    candidates.extend((2 * height // 3, c) for c in range(1, width - 1))
    seen: set[tuple[int, int]] = set()
    unique: list[tuple[int, int]] = []
    for cell in candidates:
        if cell not in seen:
            seen.add(cell)
            unique.append(cell)
    return unique


def _scene(
    seed: int,
    split: str,
    index: int,
    size: tuple[int, int],
    wanted: tuple[int, int, int],
    first_order: tuple[int, int, int],
) -> list[list[int]]:
    height, width = size
    grid = [[0] * width for _ in range(height)]
    target = _target_cells(seed, split, index, height, width, wanted, first_order)
    occupied: set[tuple[int, int]] = set()
    for color in (1, 2, 3):
        for row, column in target[color]:
            grid[row][column] = color
            occupied.add((row, column))

    rng = _rng(seed, split, index, "distractors")
    structured = [cell for cell in _distractor_candidates(height, width, index) if cell not in occupied]
    structured_set = set(structured)
    remaining = [
        (row, column)
        for row in range(height)
        for column in range(width)
        if (row, column) not in occupied and (row, column) not in structured_set
    ]
    rng.shuffle(remaining)
    desired = max(24, round(height * width * (0.10 + 0.01 * (index % 3))))
    cells = structured[: min(len(structured), desired)]
    if len(cells) < desired:
        cells.extend(remaining[: desired - len(cells)])
    if len(cells) < 6:
        raise ValueError("scene too small for distractor palette")
    for offset, (row, column) in enumerate(cells):
        # The first six guarantee complete distractor-palette coverage; later
        # colors use a seed-dependent but setting-independent assignment.
        color = 4 + offset if offset < 6 else 4 + rng.randrange(6)
        grid[row][column] = color

    if counts(grid) != wanted:
        raise ValueError("constructed target counts drifted")
    return grid


def _first_occurrence_order(grid: Any) -> tuple[int, int, int]:
    source = _grid(grid)
    positions = {}
    for color in (1, 2, 3):
        positions[color] = min(
            (row, column)
            for row, values in enumerate(source)
            for column, value in enumerate(values)
            if value == color
        )
    return tuple(sorted((1, 2, 3), key=positions.__getitem__))  # type: ignore[return-value]


def _bars_in_order(grid: Any, order: tuple[int, int, int]) -> tuple[tuple[int, int], ...]:
    values = counts(grid)
    by_color = dict(zip((1, 2, 3), values, strict=True))
    return tuple((color, by_color[color]) for color in order)


def _rival_output(grid: Any, selected_policy: str, name: str) -> list[list[int]]:
    values = counts(grid)
    if name == "count_ascending":
        bars = tuple(sorted(zip((1, 2, 3), values, strict=True), key=lambda item: (item[1], item[0])))
    elif name == "reverse_color_order":
        bars = _bars_in_order(grid, (3, 2, 1))
    elif name == "fixed_demo0_permutation":
        bars = _bars_in_order(grid, (2, 3, 1))
    elif name == "descending_height_recolored":
        heights = sorted(values, reverse=True)
        bars = tuple(zip((1, 2, 3), heights, strict=True))
    elif name == "descending_high_color_tie":
        bars = tuple(sorted(zip((1, 2, 3), values, strict=True), key=lambda item: (-item[1], -item[0])))
    elif name == "largest_then_color_order":
        largest = min((1, 2, 3), key=lambda color: (-values[color - 1], color))
        bars = _bars_in_order(grid, (largest, *(color for color in (1, 2, 3) if color != largest)))
    elif name == "first_occurrence_order":
        bars = _bars_in_order(grid, _first_occurrence_order(grid))
    elif name == "cap_heights_at_five":
        bars = tuple((color, min(5, height)) for color, height in ordered_bars(grid, selected_policy))
    elif name == "only_tallest_bar":
        ordered = ordered_bars(grid, selected_policy)
        tallest = max(height for _, height in ordered)
        bars = tuple((color, height if height == tallest else 1) for color, height in ordered)
    else:
        raise ValueError(f"undeclared rival: {name}")
    return render_bars(bars)


RIVALS = (
    "count_ascending",
    "reverse_color_order",
    "fixed_demo0_permutation",
    "descending_height_recolored",
    "descending_high_color_tie",
    "largest_then_color_order",
    "first_occurrence_order",
    "cap_heights_at_five",
    "only_tallest_bar",
)


def teaching_check(episode: Any, settings: Any) -> dict[str, Any]:
    policy = _policy(settings)
    if type(episode) is not dict or type(episode.get("train")) is not list:
        raise ValueError("episode must contain a demonstration list")
    demos = episode["train"]
    survivors = [
        {"column_order": candidate}
        for candidate in POLICIES
        if all(transform(pair["input"], {"column_order": candidate}) == pair["output"] for pair in demos)
    ]
    surviving_rivals = [
        name
        for name in RIVALS
        if all(_rival_output(pair["input"], policy, name) == pair["output"] for pair in demos)
    ]
    return {
        "survivors": survivors,
        "surviving_rivals": surviving_rivals,
        "rivals_tested": list(RIVALS),
        "basis": "demonstrations_only",
        "scope": "two declared settings and nine named shortcut families",
    }


def _pairs(
    seed: int,
    split: str,
    profiles: tuple[tuple[tuple[int, int], tuple[int, int, int], tuple[int, int, int]], ...],
    count: int,
    settings: dict[str, str],
) -> list[dict[str, list[list[int]]]]:
    return [
        {
            "input": grid,
            "output": transform(grid, settings),
        }
        for index, (size, wanted, first_order) in enumerate(profiles[:count])
        for grid in [_scene(seed, split, index, size, wanted, first_order)]
    ]


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    _exact_int(demos, "demos", 2, 6)
    _exact_int(queries, "queries", 1, 4)
    policy = _policy(settings)
    normalized = {"column_order": policy}
    episode = {
        "train": _pairs(seed, "train", _TRAIN_PROFILES, demos, normalized),
        "test": _pairs(seed, "test", _QUERY_PROFILES, queries, normalized),
        "program_solution": program(normalized),
        "seed": seed,
        "settings": copy.deepcopy(normalized),
    }
    identities = [repr(pair["input"]) for pair in episode["train"] + episode["test"]]
    if len(identities) != len(set(identities)):
        raise ValueError("all demonstration and query inputs must be distinct")
    check = teaching_check(episode, normalized)
    if check["survivors"] != [normalized] or check["surviving_rivals"]:
        raise ValueError("constructive demonstrations failed declared teaching contrasts")
    return episode


def public_turn(episode: Any, query_index: Any) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    _exact_int(query_index, "query_index", 0, len(episode["test"]) - 1)
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }
