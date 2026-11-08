"""Native two-setting endpoint-segment family with a keyed signature.

``all_aligned`` is the exact canonical rule.  In ``key_match`` mode, step A
reads the orientation and inclusive length of the color-7 endpoint pair.  Step
B completes only pairs with that same two-part signature; all other colors are
preserved at their original cells.
"""
from __future__ import annotations

from copy import deepcopy
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import random
from typing import Any


HOME = Path(__file__).resolve().parent
CANONICAL_PROGRAM = (HOME / "canonical.rkt").read_text(encoding="utf-8")
KEY_MATCH_PROGRAM = (HOME / "key_match.rkt").read_text(encoding="utf-8")
PROGRAMS = {"all_aligned": CANONICAL_PROGRAM, "key_match": KEY_MATCH_PROGRAM}

# height, width, key orientation, inclusive key length, color-9 texture cells
DEMO_SPECS = (
    (12, 16, "horizontal", 5, 14),
    (13, 17, "vertical", 4, 16),
    (14, 18, "horizontal", 6, 18),
    (15, 19, "vertical", 5, 20),
    (16, 20, "horizontal", 4, 24),
    (18, 22, "vertical", 6, 28),
)
QUERY_SPECS = (
    (13, 18, "vertical", 3, 18),
    (17, 21, "horizontal", 7, 28),
    (22, 26, "vertical", 6, 48),
    (30, 30, "horizontal", 8, 104),
)


def _validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"connection_mode"}:
        raise ValueError("settings must contain exactly connection_mode")
    mode = settings["connection_mode"]
    if type(mode) is not str or mode not in PROGRAMS:
        raise ValueError("connection_mode must be all_aligned or key_match")
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


def cells_by_color(grid: list[list[int]]) -> dict[int, list[tuple[int, int]]]:
    _validate_grid(grid)
    result: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color:
                result[color].append((row, col))
    return dict(result)


def pair_signature(cells: list[tuple[int, int]]) -> tuple[str, int | None] | None:
    if len(cells) != 2:
        return None
    (r1, c1), (r2, c2) = cells
    if r1 == r2:
        return ("horizontal", abs(c2 - c1) + 1)
    if c1 == c2:
        return ("vertical", abs(r2 - r1) + 1)
    return ("diagonal", None)


def _paint_segment(output: list[list[int]], color: int, cells: list[tuple[int, int]]) -> None:
    (r1, c1), (r2, c2) = cells
    if r1 == r2:
        for col in range(min(c1, c2), max(c1, c2) + 1):
            output[r1][col] = color
    elif c1 == c2:
        for row in range(min(r1, r2), max(r1, r2) + 1):
            output[row][c1] = color
    else:
        for row, col in cells:
            output[row][col] = color


def all_aligned_output(grid: list[list[int]]) -> list[list[int]]:
    by_color = cells_by_color(grid)
    output = [[0 for _ in row] for row in grid]
    for color, cells in sorted(by_color.items()):
        if len(cells) == 2:
            _paint_segment(output, color, cells)
        else:
            for row, col in cells:
                output[row][col] = color
    return output


def key_signature(grid: list[list[int]]) -> tuple[str, int]:
    signature = pair_signature(cells_by_color(grid).get(7, []))
    if signature is None or signature[0] not in {"horizontal", "vertical"} or signature[1] is None:
        raise ValueError("scene must contain one aligned exactly-two-cell color-7 key")
    return signature[0], signature[1]


def key_match_output(grid: list[list[int]]) -> list[list[int]]:
    signature = key_signature(grid)
    output = [[0 for _ in row] for row in grid]
    for color, cells in sorted(cells_by_color(grid).items()):
        current = pair_signature(cells)
        if len(cells) != 2:
            for row, col in cells:
                output[row][col] = color
        elif current == signature:
            _paint_segment(output, color, cells)
        else:
            for row, col in cells:
                output[row][col] = color
    return output


def label(grid: list[list[int]], mode: str) -> list[list[int]]:
    if mode == "all_aligned":
        return all_aligned_output(grid)
    if mode == "key_match":
        return key_match_output(grid)
    raise ValueError("unknown connection mode")


def _rng(seed: int, domain: str, index: int) -> random.Random:
    raw = f"21eb0f467b5a:{domain}:{seed}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _segment_cells(orientation: str, row: int, col: int, length: int) -> set[tuple[int, int]]:
    if orientation == "horizontal":
        return {(row, col + offset) for offset in range(length)}
    return {(row + offset, col) for offset in range(length)}


def _candidate_segments(height: int, width: int, orientation: str, length: int):
    if orientation == "horizontal":
        for row in range(height):
            for col in range(width - length + 1):
                yield _segment_cells(orientation, row, col, length)
    else:
        for row in range(height - length + 1):
            for col in range(width):
                yield _segment_cells(orientation, row, col, length)


def _place_pair(
    grid: list[list[int]], color: int, orientation: str, length: int,
    reserved: set[tuple[int, int]], rng: random.Random, *, prefer_boundary: bool = False,
) -> set[tuple[int, int]]:
    height, width = len(grid), len(grid[0])
    candidates = list(_candidate_segments(height, width, orientation, length))
    rng.shuffle(candidates)
    if prefer_boundary:
        boundary = [cells for cells in candidates if any(
            row in {0, height - 1} or col in {0, width - 1} for row, col in cells)]
        interior = [cells for cells in candidates if cells not in boundary]
        candidates = boundary + interior
    for cells in candidates:
        if cells & reserved:
            continue
        endpoints = [min(cells), max(cells)]
        if orientation == "horizontal":
            row = next(iter(cells))[0]
            endpoints = [(row, min(col for _, col in cells)), (row, max(col for _, col in cells))]
        else:
            col = next(iter(cells))[1]
            endpoints = [(min(row for row, _ in cells), col), (max(row for row, _ in cells), col)]
        if any(grid[row][col] for row, col in endpoints):
            continue
        for row, col in endpoints:
            grid[row][col] = color
        reserved.update(cells)
        return cells
    raise RuntimeError(f"could not place {orientation} pair of length {length}")


def _different_length(length: int, limit: int) -> int:
    for candidate in (length + 2, length - 2, length + 1, length - 1):
        if 3 <= candidate <= limit and candidate != length:
            return candidate
    raise RuntimeError("no distinct lawful segment length")


def build_input(seed: int, pair_index: int, spec: tuple[int, int, str, int, int]) -> list[list[int]]:
    height, width, key_orientation, key_length, texture_count = spec
    rng = _rng(seed, "scene", pair_index)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    reserved: set[tuple[int, int]] = set()
    colors = [1, 2, 3, 4, 5, 6]
    rng.shuffle(colors)
    opposite = "vertical" if key_orientation == "horizontal" else "horizontal"
    same_limit = width if key_orientation == "horizontal" else height
    opposite_limit = height if key_orientation == "horizontal" else width
    roles = [
        (7, key_orientation, key_length, True),
        (colors[0], key_orientation, key_length, False),
        (colors[1], key_orientation, _different_length(key_length, same_limit), False),
        (colors[2], opposite, key_length, False),
        (colors[3], opposite, _different_length(key_length, opposite_limit), False),
    ]
    for color, orientation, length, boundary in roles:
        _place_pair(grid, color, orientation, length, reserved, rng, prefer_boundary=boundary)

    free = [(row, col) for row in range(height) for col in range(width)
            if (row, col) not in reserved and grid[row][col] == 0]
    rng.shuffle(free)
    diagonal = None
    for index, first in enumerate(free):
        for second in free[index + 1:]:
            if first[0] != second[0] and first[1] != second[1]:
                diagonal = (first, second)
                break
        if diagonal:
            break
    if diagonal is None:
        raise RuntimeError("could not place diagonal control pair")
    for row, col in diagonal:
        grid[row][col] = colors[4]
        reserved.add((row, col))

    free = [(row, col) for row in range(height) for col in range(width)
            if (row, col) not in reserved and grid[row][col] == 0]
    singleton = rng.choice(free)
    grid[singleton[0]][singleton[1]] = 8
    reserved.add(singleton)

    available = [(row, col) for row in range(height) for col in range(width)
                 if (row, col) not in reserved and grid[row][col] == 0]
    rng.shuffle(available)
    corners = [(0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)]
    chosen = [cell for cell in corners if cell in available]
    remaining = [cell for cell in available if cell not in chosen]
    chosen.extend(remaining[:max(0, texture_count - len(chosen))])
    if len(chosen) < texture_count:
        raise RuntimeError("not enough cells for texture control")
    for row, col in chosen[:texture_count]:
        grid[row][col] = 9

    signature = key_signature(grid)
    observed = {color: pair_signature(cells) for color, cells in cells_by_color(grid).items()}
    if sum(value == signature for color, value in observed.items() if color != 7) != 1:
        raise RuntimeError("scene must contain exactly one non-key signature match")
    if not any(value and value[0] == signature[0] and value[1] != signature[1]
               for color, value in observed.items() if color != 7):
        raise RuntimeError("scene lacks same-orientation different-length control")
    if not any(value and value[0] != signature[0] and value[1] == signature[1]
               for color, value in observed.items() if color != 7):
        raise RuntimeError("scene lacks opposite-orientation same-length control")
    if all_aligned_output(grid) == key_match_output(grid):
        raise RuntimeError("scene does not distinguish the settings")
    return grid


def _connect_if(grid, predicate) -> list[list[int]]:
    output = [[0 for _ in row] for row in grid]
    for color, cells in sorted(cells_by_color(grid).items()):
        signature = pair_signature(cells)
        if len(cells) == 2 and signature and signature[0] in {"horizontal", "vertical"} and predicate(color, signature):
            _paint_segment(output, color, cells)
        else:
            for row, col in cells:
                output[row][col] = color
    return output


def rival_output(grid: list[list[int]], name: str) -> list[list[int]]:
    key = key_signature(grid)
    if name == "key_only":
        return _connect_if(grid, lambda color, signature: color == 7)
    if name == "same_orientation":
        return _connect_if(grid, lambda color, signature: signature[0] == key[0])
    if name == "same_length":
        return _connect_if(grid, lambda color, signature: signature[1] == key[1])
    if name == "fixed_4":
        return _connect_if(grid, lambda color, signature: signature[1] == 4)
    if name == "fixed_5":
        return _connect_if(grid, lambda color, signature: signature[1] == 5)
    if name == "horizontal_only":
        return _connect_if(grid, lambda color, signature: signature[0] == "horizontal")
    if name == "vertical_only":
        return _connect_if(grid, lambda color, signature: signature[0] == "vertical")
    if name == "first_aligned":
        candidates = [color for color, cells in sorted(cells_by_color(grid).items())
                      if (pair_signature(cells) or (None,))[0] in {"horizontal", "vertical"}]
        chosen = candidates[0]
        return _connect_if(grid, lambda color, signature: color == chosen)
    raise ValueError("unknown rival")


RIVALS = ("key_only", "same_orientation", "same_length", "fixed_4", "fixed_5",
          "horizontal_only", "vertical_only", "first_aligned")


def teaching_report(episode: dict[str, Any], mode: str) -> dict[str, Any]:
    demos = episode["train"]
    survivors = [candidate for candidate in PROGRAMS
                 if all(label(pair["input"], candidate) == pair["output"] for pair in demos)]
    rivals = [name for name in RIVALS
              if all(rival_output(pair["input"], name) == pair["output"] for pair in demos)]
    return {"mode": mode, "setting_survivors": survivors, "surviving_rivals": rivals}


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
    episode = {"train": pairs[:demos], "test": pairs[demos:], "program_solution": program(settings)}
    report = teaching_report(episode, mode)
    if report["setting_survivors"] != [mode] or report["surviving_rivals"]:
        raise RuntimeError(f"demonstrations do not teach the declared rule: {report}")
    return episode
