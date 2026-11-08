"""Parametric episodes for 6ecd8be24495.

The default is the exact canonical "most total seeds" chamber rule.  The nearby
setting selects the chamber with the most distinct seed colors instead.  Both
then compute that selected chamber's local majority color and fill only its
blank cells.  Every teaching scene makes the two selectors disagree and also
contains a stronger single-color decoy, directly closing the retained shortcut.
"""
from __future__ import annotations

from collections import Counter, deque
from hashlib import sha256
from pathlib import Path
import random
from typing import Any


TASK_ID = "6ecd8be24495"
SETTINGS = (
    {"selection_metric": "total_seeds"},
    {"selection_metric": "distinct_colors"},
)
RIVALS = (
    "strongest_single_color",
    "largest_chamber",
    "first_chamber",
    "fewest_seeds",
)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

_ALTERNATE_PATH = Path(__file__).with_name("distinct_colors.rkt")


def _setting(settings: dict[str, Any]) -> str:
    if type(settings) is not dict or set(settings) != {"selection_metric"}:
        raise ValueError("settings must name exactly selection_metric")
    value = settings["selection_metric"]
    if value not in ("total_seeds", "distinct_colors"):
        raise ValueError("selection_metric must be total_seeds or distinct_colors")
    return value


def program(settings: dict[str, Any]) -> str:
    value = _setting(settings)
    if value == "total_seeds":
        return Path(__file__).with_name("canonical.rkt").read_text()
    return _ALTERNATE_PATH.read_text()


def _rng(seed: int, domain: str, index: int) -> random.Random:
    payload = f"{TASK_ID}:{domain}:{seed}:{index}".encode()
    return random.Random(int.from_bytes(sha256(payload).digest(), "big"))


def _validate_request(seed: int, demos: int, queries: int) -> None:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2^63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")


def _validate_grid(grid: list[list[int]]) -> None:
    if (
        type(grid) is not list
        or not 3 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 3 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must have 3..30 rows and columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")


def _chambers(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 5}
    result: list[list[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        cells = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARDINAL:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    cells.add(nxt)
                    queue.append(nxt)
        result.append(sorted(cells))
    return sorted(result, key=lambda cells: cells[0])


def _record(grid: list[list[int]], cells: list[tuple[int, int]]) -> dict[str, Any]:
    counts = Counter(grid[r][c] for r, c in cells if grid[r][c] != 0)
    if not counts:
        raise ValueError("every chamber must contain a seed")
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    if len(ordered) > 1 and ordered[0][1] == ordered[1][1]:
        raise ValueError("every chamber must have a unique local majority")
    return {
        "cells": cells,
        "area": len(cells),
        "seed_total": sum(counts.values()),
        "distinct_colors": len(counts),
        "counts": dict(counts),
        "majority_color": ordered[0][0],
        "majority_count": ordered[0][1],
        "blank_count": sum(grid[r][c] == 0 for r, c in cells),
    }


def _score(record: dict[str, Any], metric: str) -> tuple[int, ...]:
    base = (record["seed_total"], record["majority_count"], -record["majority_color"])
    if metric == "total_seeds":
        return base
    return (record["distinct_colors"],) + base


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    _validate_grid(grid)
    h, w = len(grid), len(grid[0])
    if not (
        all(grid[0][c] == 5 for c in range(w))
        and all(grid[h - 1][c] == 5 for c in range(w))
        and all(grid[r][0] == 5 for r in range(h))
        and all(grid[r][w - 1] == 5 for r in range(h))
    ):
        raise ValueError("outer border must be gray")
    records = [_record(grid, cells) for cells in _chambers(grid)]
    if not 2 <= len(records) <= 4:
        raise ValueError("expected 2..4 chambers")
    if any(record["blank_count"] == 0 for record in records):
        raise ValueError("every chamber must retain at least one blank")
    total_winner = max(range(len(records)), key=lambda index: _score(records[index], "total_seeds"))
    distinct_winner = max(range(len(records)), key=lambda index: _score(records[index], "distinct_colors"))
    return {
        "chambers": records,
        "total_winner": total_winner,
        "distinct_winner": distinct_winner,
    }


def _fill_rank(grid: list[list[int]], records: list[dict[str, Any]], rank: int) -> list[list[int]]:
    output = [row[:] for row in grid]
    selected = records[rank]
    for r, c in selected["cells"]:
        if output[r][c] == 0:
            output[r][c] = selected["majority_color"]
    return output


def transform(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    metric = _setting(settings)
    analysis = analyze(grid)
    rank = analysis["total_winner"] if metric == "total_seeds" else analysis["distinct_winner"]
    return _fill_rank(grid, analysis["chambers"], rank)


def _blank_board(h: int, w: int) -> list[list[int]]:
    grid = [[0 for _ in range(w)] for _ in range(h)]
    for r in range(h):
        grid[r][0] = grid[r][w - 1] = 5
    for c in range(w):
        grid[0][c] = grid[h - 1][c] = 5
    return grid


def _partition(h: int, w: int, layout: str, rng: random.Random) -> list[list[int]]:
    grid = _blank_board(h, w)
    if layout == "cross":
        wall_r = h // 2 + rng.choice((-1, 0, 1))
        wall_c = w // 2 + rng.choice((-1, 0, 1))
        for c in range(1, w - 1):
            grid[wall_r][c] = 5
        for r in range(1, h - 1):
            grid[r][wall_c] = 5
    elif layout == "t":
        wall_c = w // 2 + rng.choice((-1, 0, 1))
        wall_r = h // 2 + rng.choice((-1, 0, 1))
        for r in range(1, h - 1):
            grid[r][wall_c] = 5
        side = rng.choice(("left", "right"))
        columns = range(1, wall_c) if side == "left" else range(wall_c + 1, w - 1)
        for c in columns:
            grid[wall_r][c] = 5
    elif layout == "rows":
        walls = (h // 3, 2 * h // 3)
        for wall in walls:
            for c in range(1, w - 1):
                grid[wall][c] = 5
    elif layout == "columns":
        walls = (w // 3, 2 * w // 3)
        for wall in walls:
            for r in range(1, h - 1):
                grid[r][wall] = 5
    elif layout == "two":
        if rng.randrange(2):
            wall = h // 2
            for c in range(1, w - 1):
                grid[wall][c] = 5
        else:
            wall = w // 2
            for r in range(1, h - 1):
                grid[r][wall] = 5
    else:
        raise ValueError(layout)
    return grid


def _spread_positions(cells: list[tuple[int, int]], count: int, rng: random.Random) -> list[tuple[int, int]]:
    pool = list(cells)
    rng.shuffle(pool)
    chosen: list[tuple[int, int]] = []
    for cell in pool:
        if all(abs(cell[0] - r) + abs(cell[1] - c) > 1 for r, c in chosen):
            chosen.append(cell)
            if len(chosen) == count:
                return chosen
    for cell in pool:
        if cell not in chosen:
            chosen.append(cell)
            if len(chosen) == count:
                return chosen
    raise ValueError("not enough chamber cells for requested seeds")


def _paint_counts(
    grid: list[list[int]],
    cells: list[tuple[int, int]],
    counts: dict[int, int],
    rng: random.Random,
) -> None:
    positions = _spread_positions(cells, sum(counts.values()), rng)
    values = [color for color, count in counts.items() for _ in range(count)]
    rng.shuffle(values)
    for (r, c), color in zip(positions, values):
        grid[r][c] = color


def _role_schedule(layout: str, index: int, n: int) -> tuple[int, int, int | None]:
    schedules = {
        "cross": ((1, 3, 0), (2, 0, 3), (3, 1, 2)),
        "t": ((2, 0, 1), (0, 2, 1), (1, 0, 2)),
        "rows": ((0, 2, 1), (2, 1, 0), (1, 0, 2)),
        "columns": ((1, 2, 0), (2, 0, 1), (0, 1, 2)),
        "two": ((0, 1, None), (1, 0, None)),
    }
    total, distinct, peak = schedules[layout][index % len(schedules[layout])]
    if max(total, distinct, peak if peak is not None else 0) >= n:
        raise AssertionError("role schedule exceeds chamber count")
    return total, distinct, peak


def _scene(seed: int, domain: str, index: int, h: int, w: int) -> list[list[int]]:
    rng = _rng(seed, domain, index)
    layouts = ("cross", "t", "columns", "rows", "cross", "two")
    layout = layouts[index % len(layouts)]
    grid = _partition(h, w, layout, rng)
    chambers = _chambers(grid)
    # Assign the two intended winners to non-largest rooms whenever there are
    # at least three chambers.  The largest room becomes the strongest
    # single-color decoy.  This makes the two-demo lesson refute both the
    # largest-room and strongest-blob shortcuts by construction, independent
    # of the small wall jitter above.
    area_order = sorted(range(len(chambers)), key=lambda rank: (len(chambers[rank]), rank))
    if len(chambers) >= 3:
        non_largest = area_order[:-1]
        if domain == "demo" and index == 0:
            # The minimum lesson must reject "always take the first chamber"
            # for both settings regardless of wall jitter.  A four-room cross
            # always leaves at least two nonzero ranks outside the largest room.
            nonzero = [rank for rank in non_largest if rank != 0]
            if len(nonzero) < 2:
                raise AssertionError("first teaching scene lacks two nonzero non-largest rooms")
            total_rank, distinct_rank = nonzero[:2]
        else:
            total_rank = non_largest[index % len(non_largest)]
            distinct_rank = non_largest[(index + 1) % len(non_largest)]
        peak_rank = area_order[-1]
    else:
        total_rank = index % 2
        distinct_rank = 1 - total_rank
        peak_rank = None

    min_area = min(map(len, chambers))
    total_count = min(24, max(9, min_area // 4))
    if total_count >= min_area:
        total_count = min_area - 1
    if total_count < 8:
        raise ValueError("chambers are too small for the contrast grammar")

    colors = [1, 2, 3, 4]
    rng.shuffle(colors)
    total_counts = {
        colors[0]: total_count // 3 + 1,
        colors[1]: (total_count - (total_count // 3 + 1)) // 2 + 1,
    }
    used = sum(total_counts.values())
    total_counts[colors[2]] = total_count - used
    if len(set(total_counts.values())) != len(total_counts) or min(total_counts.values()) <= 0:
        # A literal, uniquely ordered three-color split for the small boundary.
        total_counts = {colors[0]: total_count - 7, colors[1]: 4, colors[2]: 3}
    if len(set(total_counts.values())) != len(total_counts) or min(total_counts.values()) <= 0:
        total_counts = {colors[0]: total_count - 5, colors[1]: 3, colors[2]: 2}

    distinct_count = total_count - 1
    distinct_counts = {colors[1]: distinct_count - 3, colors[0]: 1, colors[2]: 1, colors[3]: 1}
    peak_count = total_count - 2

    role_counts: dict[int, dict[int, int]] = {
        total_rank: total_counts,
        distinct_rank: distinct_counts,
    }
    if peak_rank is not None:
        role_counts[peak_rank] = {colors[3]: peak_count}

    for rank in range(len(chambers)):
        if rank not in role_counts:
            other_total = max(2, total_count - 3 - rank)
            role_counts[rank] = {colors[rank % 4]: other_total - 1, colors[(rank + 1) % 4]: 1}
        if sum(role_counts[rank].values()) >= len(chambers[rank]):
            raise ValueError("seed role leaves no blank cell")
        _paint_counts(
            grid,
            chambers[rank],
            role_counts[rank],
            _rng(seed, f"{domain}-chamber-{rank}", index),
        )

    analysis = analyze(grid)
    if analysis["total_winner"] != total_rank or analysis["distinct_winner"] != distinct_rank:
        raise AssertionError(
            f"role construction failed: expected {(total_rank, distinct_rank)}, "
            f"got {(analysis['total_winner'], analysis['distinct_winner'])}"
        )
    return grid


def rival_output(grid: list[list[int]], name: str) -> list[list[int]]:
    analysis = analyze(grid)
    records = analysis["chambers"]
    if name == "strongest_single_color":
        rank = max(range(len(records)), key=lambda i: (records[i]["majority_count"], -i))
    elif name == "largest_chamber":
        rank = max(range(len(records)), key=lambda i: (records[i]["area"], -i))
    elif name == "first_chamber":
        rank = 0
    elif name == "fewest_seeds":
        rank = min(range(len(records)), key=lambda i: (records[i]["seed_total"], i))
    else:
        raise ValueError(f"unknown rival {name}")
    return _fill_rank(grid, records, rank)


def teaching_check(episode: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    _setting(settings)
    demos = episode["train"]
    survivors = [
        candidate
        for candidate in SETTINGS
        if all(transform(pair["input"], candidate) == pair["output"] for pair in demos)
    ]
    surviving_rivals = [
        name
        for name in RIVALS
        if all(rival_output(pair["input"], name) == pair["output"] for pair in demos)
    ]
    return {
        "survivors": survivors,
        "surviving_rivals": surviving_rivals,
        "scope": "two declared selectors and four named shortcut selectors; demonstrations only",
    }


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 2,
    queries: int = 4,
) -> dict[str, Any]:
    _setting(settings)
    _validate_request(seed, demos, queries)
    demo_sizes = [(18, 18), (18, 20), (20, 18), (22, 22), (24, 26), (26, 24)]
    query_sizes = [(18, 22), (22, 18), (26, 28), (30, 30)]
    _rng(seed, "query-order", 0).shuffle(query_sizes)

    train = []
    for index, (h, w) in enumerate(demo_sizes[:demos]):
        grid = _scene(seed, "demo", index, h, w)
        train.append({"input": grid, "output": transform(grid, settings)})
    test = []
    for index, (h, w) in enumerate(query_sizes[:queries]):
        grid = _scene(seed, "query", index + 2, h, w)
        test.append({"input": grid, "output": transform(grid, settings)})

    episode = {"train": train, "test": test, "program_solution": program(settings)}
    check = teaching_check(episode, settings)
    if check["survivors"] != [settings] or check["surviving_rivals"]:
        raise ValueError(f"demonstrations do not identify the requested rule: {check}")
    return episode
