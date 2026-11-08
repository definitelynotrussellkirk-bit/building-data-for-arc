"""Native family for global-color completion versus two local completion passes.

``global_color`` is the exact canonical rule.  ``two_pass_local`` first finds
all local monochrome 2x2 L-trominoes and fills their missing corners
simultaneously.  It then recomputes eligibility on that intermediate grid and
performs one more simultaneous pass.  The generated two-row chains require the
second pass and retain a third-pass opportunity, distinguishing one pass, two
passes and closure.
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
TWO_PASS_PROGRAM = (HOME / "two_pass_local.rkt").read_text(encoding="utf-8")
PROGRAMS = {
    "global_color": CANONICAL_PROGRAM,
    "two_pass_local": TWO_PASS_PROGRAM,
}

# height, width, number of isolated 5x6 slots to populate
DEMO_SPECS = (
    (10, 14, 4),
    (12, 18, 6),
    (15, 18, 8),
    (18, 24, 10),
    (20, 24, 12),
    (25, 30, 20),
)
QUERY_SPECS = (
    (11, 15, 4),
    (16, 20, 8),
    (23, 27, 16),
    (30, 30, 25),
)


def _validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"completion_mode"}:
        raise ValueError("settings must contain exactly completion_mode")
    mode = settings["completion_mode"]
    if type(mode) is not str or mode not in PROGRAMS:
        raise ValueError("completion_mode must be global_color or two_pass_local")
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


def global_color_output(grid: list[list[int]]) -> list[list[int]]:
    _validate_grid(grid)
    output = [row[:] for row in grid]
    colors = sorted({value for row in grid for value in row if value != 0})
    for color in colors:
        cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        rows = sorted({r for r, _ in cells})
        cols = sorted({c for _, c in cells})
        if (len(cells) == 3 and len(rows) == 2 and len(cols) == 2
                and rows[1] - rows[0] == 1 and cols[1] - cols[0] == 1):
            for row in rows:
                for col in cols:
                    output[row][col] = color
    return output


def completion_writes(grid: list[list[int]]) -> dict[tuple[int, int], int]:
    _validate_grid(grid)
    height, width = len(grid), len(grid[0])
    writes: dict[tuple[int, int], int] = {}
    for row0 in range(height - 1):
        for col0 in range(width - 1):
            cells = [
                (row, col, grid[row][col])
                for row in (row0, row0 + 1)
                for col in (col0, col0 + 1)
            ]
            colored = [value for _, _, value in cells if value != 0]
            zeros = [(row, col) for row, col, value in cells if value == 0]
            if len(colored) != 3 or len(zeros) != 1 or len(set(colored)) != 1:
                continue
            cell, color = zeros[0], colored[0]
            if cell in writes and writes[cell] != color:
                raise ValueError("ambiguous local completion writes different colors to one cell")
            writes[cell] = color
    return writes


def local_pass(grid: list[list[int]]) -> list[list[int]]:
    output = [row[:] for row in grid]
    for (row, col), color in sorted(completion_writes(grid).items()):
        output[row][col] = color
    return output


def two_pass_output(grid: list[list[int]]) -> list[list[int]]:
    intermediate = local_pass(grid)
    return local_pass(intermediate)


def label(grid: list[list[int]], mode: str) -> list[list[int]]:
    if mode == "global_color":
        return global_color_output(grid)
    if mode == "two_pass_local":
        return two_pass_output(grid)
    raise ValueError("unknown completion mode")


def _rng(seed: int, domain: str, index: int) -> random.Random:
    raw = f"eca9af4f6c53:{domain}:{seed}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _normalize(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    low_r = min(r for r, _ in cells)
    low_c = min(c for _, c in cells)
    return {(r - low_r, c - low_c) for r, c in cells}


def _orient(cells: set[tuple[int, int]], turns: int, reflect: bool) -> set[tuple[int, int]]:
    result = set(cells)
    for _ in range(turns % 4):
        result = {(-c, r) for r, c in result}
    if reflect:
        result = {(r, -c) for r, c in result}
    return _normalize(result)


def _chain() -> set[tuple[int, int]]:
    # Pass 1 fills (1,1), pass 2 fills (0,2), pass 3 would fill (1,3).
    return {(0, 0), (1, 0), (0, 1), (1, 2), (0, 3)}


def _canonical_l(missing: int) -> set[tuple[int, int]]:
    cells = ((0, 0), (0, 1), (1, 0), (1, 1))
    return {cell for index, cell in enumerate(cells) if index != missing}


def _paint_pattern(
    grid: list[list[int]], slot: tuple[int, int], cells: set[tuple[int, int]],
    color: int, rng: random.Random, *, fixed_corner: bool = False
) -> None:
    row0, col0 = slot
    height = max(r for r, _ in cells) + 1
    width = max(c for _, c in cells) + 1
    if fixed_corner:
        dr = dc = 0
    else:
        dr = rng.randrange(0, 5 - height)
        dc = rng.randrange(0, 6 - width)
    for row, col in cells:
        grid[row0 + dr + row][col0 + dc + col] = color


def build_input(seed: int, pair_index: int, spec: tuple[int, int, int]) -> list[list[int]]:
    height, width, count = spec
    rng = _rng(seed, "scene", pair_index)
    slots = [
        (r, c)
        for r in range(0, height - 4, 5)
        for c in range(0, width - 5, 6)
    ]
    if len(slots) < count:
        raise ValueError("scene spec does not provide enough isolated slots")
    grid = [[0 for _ in range(width)] for _ in range(height)]
    selected = slots[:count]

    # Unique canonical colors are used nowhere else, so the global-color default
    # has genuine positive examples in every scene.
    _paint_pattern(grid, selected[0], _canonical_l(3), 9, rng, fixed_corner=True)
    cursor = 1
    if count >= 6:
        cells = _orient(_canonical_l(rng.randrange(4)), rng.randrange(4), bool(rng.randrange(2)))
        _paint_pattern(grid, selected[cursor], cells, 8, rng)
        cursor += 1

    # The final slot is an unchanged full square control.
    last = count - 1
    decoy = _orient({(0, 0), (0, 1), (1, 0), (1, 1)}, rng.randrange(4), False)
    _paint_pattern(grid, selected[last], decoy, 7, rng)

    chain_index = 0
    while cursor < last:
        color = 1 + (chain_index % 6)
        cells = _orient(_chain(), rng.randrange(4), bool(rng.randrange(2)))
        _paint_pattern(grid, selected[cursor], cells, color, rng)
        cursor += 1
        chain_index += 1

    first = local_pass(grid)
    second = local_pass(first)
    third = local_pass(second)
    if first == second or second == third:
        raise RuntimeError("constructed scene does not expose exactly-two-pass reasoning")
    if global_color_output(grid) == second:
        raise RuntimeError("constructed scene does not distinguish the settings")
    return grid


def closure_output(grid: list[list[int]]) -> list[list[int]]:
    current = [row[:] for row in grid]
    for _ in range(32):
        updated = local_pass(current)
        if updated == current:
            return updated
        current = updated
    raise RuntimeError("local completion did not stabilize within 32 passes")


def rival_output(grid: list[list[int]], name: str) -> list[list[int]]:
    if name == "one_pass_local":
        return local_pass(grid)
    if name == "closure":
        return closure_output(grid)
    if name == "global_then_local":
        return local_pass(global_color_output(grid))
    if name == "fill_every_color_bbox":
        output = [row[:] for row in grid]
        for color in sorted({value for row in grid for value in row if value != 0}):
            cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            for row in range(min(rows), max(rows) + 1):
                for col in range(min(cols), max(cols) + 1):
                    output[row][col] = color
        return output
    raise ValueError("unknown rival")


def teaching_report(episode: dict[str, Any], mode: str) -> dict[str, Any]:
    demos = episode["train"]
    settings = [
        candidate
        for candidate in PROGRAMS
        if all(label(pair["input"], candidate) == pair["output"] for pair in demos)
    ]
    rivals = [
        name
        for name in ("one_pass_local", "closure", "global_then_local", "fill_every_color_bbox")
        if all(rival_output(pair["input"], name) == pair["output"] for pair in demos)
    ]
    return {"setting_survivors": settings, "surviving_rivals": rivals, "mode": mode}


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
