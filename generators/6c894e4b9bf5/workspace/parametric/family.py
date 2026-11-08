"""Native two-setting family for endpoint marking with an input-derived ruler.

``all_vertical`` is the exact canonical rule.  In ``ruler_threshold`` mode,
step A finds the unique vertical color-7 ruler and measures its length.  Step B
uses that input-derived integer as the minimum length for eligible vertical
color-2 components before marking their endpoints.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any


HOME = Path(__file__).resolve().parent
CANONICAL_PROGRAM = (HOME / "canonical.rkt").read_text(encoding="utf-8")
RULER_THRESHOLD_PROGRAM = (HOME / "ruler_threshold.rkt").read_text(encoding="utf-8")
PROGRAMS = {
    "all_vertical": CANONICAL_PROGRAM,
    "ruler_threshold": RULER_THRESHOLD_PROGRAM,
}

# height, width, ruler length, number of qualifying vertical red components
DEMO_SPECS = (
    (10, 14, 3, 4),
    (12, 16, 5, 5),
    (14, 18, 4, 6),
    (16, 20, 3, 7),
    (18, 24, 5, 8),
    (20, 26, 4, 9),
)
QUERY_SPECS = (
    (11, 15, 4, 5),
    (15, 19, 3, 6),
    (22, 25, 4, 9),
    (30, 30, 5, 12),
)
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"selection_mode"}:
        raise ValueError("settings must contain exactly selection_mode")
    mode = settings["selection_mode"]
    if type(mode) is not str or mode not in PROGRAMS:
        raise ValueError("selection_mode must be all_vertical or ruler_threshold")
    return mode


def _plain_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be a plain integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _validate_grid(grid: Any) -> None:
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(value) is not int or not 0 <= value <= 9 for value in row)
                   for row in grid)):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")


def components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    _validate_grid(grid)
    height, width = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == color}
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            row, col = stack.pop()
            for dr, dc in CARDINAL:
                cell = (row + dr, col + dc)
                if cell in remaining:
                    remaining.remove(cell)
                    cells.add(cell)
                    stack.append(cell)
        result.append(cells)
    return result


def is_vertical(cells: set[tuple[int, int]]) -> bool:
    if len(cells) < 2:
        return False
    rows = {r for r, _ in cells}
    cols = {c for _, c in cells}
    return len(cols) == 1 and len(rows) == max(rows) - min(rows) + 1


def ruler_length(grid: list[list[int]]) -> int:
    rulers = [cells for cells in components(grid, 7) if is_vertical(cells)]
    if len(rulers) != 1:
        raise ValueError("scene must contain exactly one vertical color-7 ruler")
    return len(rulers[0])


def _mark(grid: list[list[int]], predicate) -> list[list[int]]:
    output = [row[:] for row in grid]
    for cells in components(grid, 2):
        if not is_vertical(cells) or not predicate(len(cells)):
            continue
        column = next(iter(c for _, c in cells))
        rows = sorted(r for r, _ in cells)
        output[rows[0]][column] = 1
        output[rows[-1]][column] = 1
    return output


def all_vertical_output(grid: list[list[int]]) -> list[list[int]]:
    return _mark(grid, lambda length: length >= 2)


def ruler_threshold_output(grid: list[list[int]]) -> list[list[int]]:
    threshold = ruler_length(grid)
    return _mark(grid, lambda length: length >= threshold)


def label(grid: list[list[int]], mode: str) -> list[list[int]]:
    if mode == "all_vertical":
        return all_vertical_output(grid)
    if mode == "ruler_threshold":
        return ruler_threshold_output(grid)
    raise ValueError("unknown selection mode")


def _rng(seed: int, domain: str, index: int) -> random.Random:
    raw = f"6c894e4b9bf5:{domain}:{seed}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _neighbors(row: int, col: int, height: int, width: int):
    for dr, dc in CARDINAL:
        rr, cc = row + dr, col + dc
        if 0 <= rr < height and 0 <= cc < width:
            yield rr, cc


def _can_place_red(grid: list[list[int]], cells: set[tuple[int, int]]) -> bool:
    height, width = len(grid), len(grid[0])
    if any(not (0 <= r < height and 0 <= c < width) or grid[r][c] != 0 for r, c in cells):
        return False
    return all(
        grid[rr][cc] != 2
        for row, col in cells
        for rr, cc in _neighbors(row, col, height, width)
        if (rr, cc) not in cells
    )


def _paint(grid: list[list[int]], cells: set[tuple[int, int]], color: int) -> None:
    for row, col in cells:
        grid[row][col] = color


def _place_red_decoys(grid: list[list[int]], rng: random.Random) -> None:
    height, width = len(grid), len(grid[0])
    candidates = []
    for row in (0, height - 1, max(1, height // 2 - 1)):
        for col in range(width - 1):
            candidates.append({(row, col), (row, col + 1)})
    rng.shuffle(candidates)
    for cells in candidates:
        if _can_place_red(grid, cells):
            _paint(grid, cells, 2)
            break
    else:
        raise RuntimeError("could not place horizontal red control")

    if height >= 12 and width >= 14:
        blocks = [
            {(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)}
            for r in range(height - 1)
            for c in range(width - 1)
        ]
        rng.shuffle(blocks)
        for cells in blocks:
            if _can_place_red(grid, cells):
                _paint(grid, cells, 2)
                return
        raise RuntimeError("could not place square red control")


def _place_ruler_and_decoys(grid: list[list[int]], threshold: int, rng: random.Random) -> None:
    height, width = len(grid), len(grid[0])
    ruler_col = 0 if rng.randrange(2) == 0 else width - 1
    for row in range(threshold):
        grid[row][ruler_col] = 7
    if ruler_col == 0:
        decoy = {(height - 1, width - 2), (height - 1, width - 1)}
    else:
        decoy = {(height - 1, 0), (height - 1, 1)}
    _paint(grid, decoy, 7)


def _line_lengths(threshold: int, count: int, rng: random.Random) -> list[int]:
    base = [threshold - 1, threshold, threshold + 1, 2, 7, 3, 6, 8, 4, 9, 5, 7]
    extras = [rng.randint(3, 9) for _ in range(max(0, count - len(base)))]
    return (base + extras)[:count]


def _place_vertical_lines(
    grid: list[list[int]], lengths: list[int], rng: random.Random
) -> None:
    height, width = len(grid), len(grid[0])
    for index, requested in enumerate(lengths):
        length = min(requested, height - 1)
        starts = list(range(height - length + 1))
        if index == 0:
            starts = [0] + [r for r in starts if r != 0]
        elif index == 1:
            bottom = height - length
            starts = [bottom] + [r for r in starts if r != bottom]
        else:
            rng.shuffle(starts)
        columns = list(range(width))
        rng.shuffle(columns)
        candidates = []
        for row0 in starts:
            for col in columns:
                cells = {(row0 + delta, col) for delta in range(length)}
                if _can_place_red(grid, cells):
                    candidates.append(cells)
            if candidates and index < 2:
                break
        if not candidates:
            raise RuntimeError(f"could not place vertical red line {index} of length {length}")
        cells = rng.choice(candidates)
        _paint(grid, cells, 2)


def build_input(
    seed: int, pair_index: int, spec: tuple[int, int, int, int]
) -> list[list[int]]:
    height, width, threshold, count = spec
    rng = _rng(seed, "scene", pair_index)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    _place_ruler_and_decoys(grid, threshold, rng)
    _place_red_decoys(grid, rng)
    _place_vertical_lines(grid, _line_lengths(threshold, count, rng), rng)

    vertical = [cells for cells in components(grid, 2) if is_vertical(cells)]
    lengths = sorted(len(cells) for cells in vertical)
    if len(vertical) != count:
        raise RuntimeError("constructed scene has the wrong vertical-line count")
    if not (any(length < threshold for length in lengths)
            and any(length == threshold for length in lengths)
            and any(length > threshold for length in lengths)):
        raise RuntimeError("constructed scene does not span the ruler threshold")
    if ruler_length(grid) != threshold:
        raise RuntimeError("constructed scene has an invalid ruler")
    if all_vertical_output(grid) == ruler_threshold_output(grid):
        raise RuntimeError("constructed scene does not distinguish the settings")
    return grid


def rival_output(grid: list[list[int]], name: str) -> list[list[int]]:
    threshold = ruler_length(grid)
    vertical_lengths = [len(cells) for cells in components(grid, 2) if is_vertical(cells)]
    if name == "fixed_3":
        return _mark(grid, lambda length: length >= 3)
    if name == "fixed_4":
        return _mark(grid, lambda length: length >= 4)
    if name == "fixed_5":
        return _mark(grid, lambda length: length >= 5)
    if name == "exact_ruler":
        return _mark(grid, lambda length: length == threshold)
    if name == "at_most_ruler":
        return _mark(grid, lambda length: length <= threshold)
    if name == "longest_only":
        maximum = max(vertical_lengths)
        return _mark(grid, lambda length: length == maximum)
    if name == "all_red_bboxes":
        output = [row[:] for row in grid]
        for cells in components(grid, 2):
            rows = sorted({r for r, _ in cells})
            for row, col in cells:
                if row in (rows[0], rows[-1]):
                    output[row][col] = 1
        return output
    raise ValueError("unknown rival")


def teaching_report(episode: dict[str, Any], mode: str) -> dict[str, Any]:
    demos = episode["train"]
    setting_survivors = [
        candidate
        for candidate in PROGRAMS
        if all(label(pair["input"], candidate) == pair["output"] for pair in demos)
    ]
    rivals = [
        name
        for name in ("fixed_3", "fixed_4", "fixed_5", "exact_ruler",
                     "at_most_ruler", "longest_only", "all_red_bboxes")
        if all(rival_output(pair["input"], name) == pair["output"] for pair in demos)
    ]
    return {"setting_survivors": setting_survivors, "surviving_rivals": rivals, "mode": mode}


def program(settings: dict[str, Any]) -> str:
    return PROGRAMS[_validate_settings(settings)]


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    _plain_int("seed", seed, 0, 2**63 - 1)
    _plain_int("demos", demos, 2, 6)
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be exactly 4")
    mode = _validate_settings(settings)
    specs = list(DEMO_SPECS[:demos]) + list(QUERY_SPECS)
    inputs = [build_input(seed, index, spec) for index, spec in enumerate(specs)]
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in inputs]
    if len(serialized) != len(set(serialized)):
        raise RuntimeError("episode inputs must be distinct")
    pairs = [{"input": deepcopy(grid), "output": label(grid, mode)} for grid in inputs]
    episode = {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program(settings),
    }
    report = teaching_report(episode, mode)
    if report["setting_survivors"] != [mode] or report["surviving_rivals"]:
        raise RuntimeError(f"demonstrations do not teach the declared rule: {report}")
    return episode
