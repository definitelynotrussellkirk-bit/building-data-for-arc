"""Native parametric adapter for 6b6e3acc8a0a.

The default setting is the exact canonical vector translation.  The alternate
first translates a unique color-8 pointer by the anchor vector, reads the color
at that input-dependent landing cell, then translates color-9 cargo by the same
vector and paints it with the selected color.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any

_HOME = Path(__file__).resolve().parent
_PROGRAMS = {
    "canonical_all": _HOME / "canonical.rkt",
    "pointer_select_color": _HOME / "pointer_select_color.rkt",
}
_SELECTOR_COLORS = (3, 4, 6, 7)

# (height, width, dr, dc, profile)
_DEMO_SPECS = (
    (9, 11, 2, 3, "compact"),
    (10, 12, -2, 3, "compact"),
    (12, 14, 3, -4, "boundary"),
    (14, 16, -4, -3, "dense"),
    (16, 18, 1, 5, "dense"),
    (18, 20, -5, 2, "boundary"),
)
_QUERY_SPECS = (
    (11, 13, 2, -3, "compact"),
    (15, 17, -3, 4, "boundary"),
    (22, 24, 4, 5, "dense"),
    (30, 30, -5, -6, "stress"),
)


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def _mode(settings: Any) -> str:
    if not isinstance(settings, dict) or set(settings) != {"translation_mode"}:
        raise ValueError("settings must contain exactly translation_mode")
    mode = settings["translation_mode"]
    if type(mode) is not str or mode not in _PROGRAMS:
        raise ValueError("translation_mode must be canonical_all or pointer_select_color")
    return mode


def program(settings: Any) -> str:
    return _PROGRAMS[_mode(settings)].read_text(encoding="utf-8")


def _mix_seed(seed: int, role: str, index: int) -> int:
    payload = f"6b6e3acc8a0a|{seed}|{role}|{index}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _positions(grid: list[list[int]], color: int) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]


def _anchor_pair(height: int, width: int, dr: int, dc: int, rng: random.Random) -> tuple[tuple[int, int], tuple[int, int]]:
    candidates = [
        (r, c)
        for r in range(1, height - 1)
        for c in range(1, width - 1)
        if 0 <= r + dr < height and 0 <= c + dc < width
    ]
    if not candidates:
        raise RuntimeError("no legal anchor pair")
    source = rng.choice(candidates)
    return source, (source[0] + dr, source[1] + dc)


def _selector_cluster(
    height: int,
    width: int,
    dr: int,
    dc: int,
    forbidden: set[tuple[int, int]],
    rng: random.Random,
) -> tuple[tuple[int, int], tuple[int, int], tuple[tuple[int, int], ...]]:
    candidates = []
    for r in range(1, height - 1):
        for c in range(1, width - 1):
            selector = (r, c)
            pointer = (r - dr, c - dc)
            cluster = ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1))
            if (
                0 <= pointer[0] < height
                and 0 <= pointer[1] < width
                and pointer not in cluster
                and not ({pointer, *cluster} & forbidden)
            ):
                candidates.append((pointer, selector, cluster))
    if not candidates:
        raise RuntimeError("no legal pointer-selector cluster")
    return rng.choice(candidates)


def _build_input(seed: int, role: str, index: int, spec: tuple[int, int, int, int, str]) -> list[list[int]]:
    height, width, dr, dc, profile = spec
    rng = random.Random(_mix_seed(seed, role, index))
    source, destination = _anchor_pair(height, width, dr, dc, rng)
    pointer, selector, cluster = _selector_cluster(
        height, width, dr, dc, {source, destination}, rng
    )

    ordinal = index if role == "demo" else len(_DEMO_SPECS) + index
    selected_color = _SELECTOR_COLORS[(seed + ordinal) % len(_SELECTOR_COLORS)]
    other_colors = [color for color in _SELECTOR_COLORS if color != selected_color]
    rng.shuffle(other_colors)

    grid = [[0 for _ in range(width)] for _ in range(height)]
    grid[source[0]][source[1]] = 1
    grid[destination[0]][destination[1]] = 2
    grid[pointer[0]][pointer[1]] = 8
    for cell, color in zip(cluster, (selected_color, *other_colors)):
        grid[cell[0]][cell[1]] = color

    reserved = {source, destination, pointer, *cluster}
    valid_cargo = [
        (r, c)
        for r in range(height)
        for c in range(width)
        if (r, c) not in reserved
        and 0 <= r + dr < height
        and 0 <= c + dc < width
        and (r + dr, c + dc) not in reserved
    ]
    rng.shuffle(valid_cargo)
    cargo_count = {
        "compact": 8,
        "boundary": 14,
        "dense": max(24, (height * width) // 8),
        "stress": 70,
    }[profile]
    if len(valid_cargo) < cargo_count:
        raise RuntimeError("insufficient legal cargo cells")
    cargo = valid_cargo[:cargo_count]
    for r, c in cargo:
        grid[r][c] = 9
    reserved.update(cargo)

    if profile in {"boundary", "stress"}:
        invalid = [
            (r, c)
            for r in range(height)
            for c in range(width)
            if (r, c) not in reserved
            and not (0 <= r + dr < height and 0 <= c + dc < width)
        ]
        rng.shuffle(invalid)
        for r, c in invalid[: min(4, len(invalid))]:
            grid[r][c] = 9
            reserved.add((r, c))

    spectator_target = {
        "compact": 4,
        "boundary": 10,
        "dense": max(18, (height * width) // 10),
        "stress": 36,
    }[profile]
    free = [
        (r, c)
        for r in range(height)
        for c in range(width)
        if (r, c) not in reserved
    ]
    rng.shuffle(free)
    for offset, (r, c) in enumerate(free[:spectator_target]):
        grid[r][c] = _SELECTOR_COLORS[(offset + ordinal + 1) % len(_SELECTOR_COLORS)]

    # Construction-time assertions keep the sequential role unambiguous.
    assert _positions(grid, 1) == [source]
    assert _positions(grid, 2) == [destination]
    assert _positions(grid, 8) == [pointer]
    assert grid[pointer[0] + dr][pointer[1] + dc] == selected_color
    assert len(_positions(grid, 9)) >= cargo_count
    return grid


def _canonical_output(grid: list[list[int]]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    source = _positions(grid, 1)[0]
    destination = _positions(grid, 2)[0]
    dr, dc = destination[0] - source[0], destination[1] - source[1]
    output = [[0 for _ in range(width)] for _ in range(height)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 1, 2):
                continue
            rr, cc = r + dr, c + dc
            if 0 <= rr < height and 0 <= cc < width:
                output[rr][cc] = value
    return output


def _pointer_select_output(grid: list[list[int]]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    source = _positions(grid, 1)[0]
    destination = _positions(grid, 2)[0]
    pointer = _positions(grid, 8)[0]
    dr, dc = destination[0] - source[0], destination[1] - source[1]
    selected_color = grid[pointer[0] + dr][pointer[1] + dc]
    if selected_color not in _SELECTOR_COLORS:
        raise ValueError("translated pointer must land on a selector color")
    output = [[0 for _ in range(width)] for _ in range(height)]
    for r, c in _positions(grid, 9):
        rr, cc = r + dr, c + dc
        if 0 <= rr < height and 0 <= cc < width:
            output[rr][cc] = selected_color
    return output


def _pair(grid: list[list[int]], mode: str) -> dict[str, list[list[int]]]:
    output = _canonical_output(grid) if mode == "canonical_all" else _pointer_select_output(grid)
    return {"input": deepcopy(grid), "output": output}


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 2, 6)
    queries = _integer("queries", queries, 1, 4)
    mode = _mode(settings)

    demo_inputs = [
        _build_input(seed, "demo", index, spec)
        for index, spec in enumerate(_DEMO_SPECS[:demos])
    ]
    query_bank = [
        _build_input(seed, "query", index, spec)
        for index, spec in enumerate(_QUERY_SPECS)
    ]
    selected_queries = query_bank[:queries]
    inputs = demo_inputs + selected_queries
    if len({repr(grid) for grid in inputs}) != len(inputs):
        raise RuntimeError("episode inputs are not distinct")

    return {
        "train": [_pair(grid, mode) for grid in demo_inputs],
        "test": [_pair(grid, mode) for grid in selected_queries],
        "program_solution": program(settings),
    }
