"""Native parametric adapter for 616a5c01a7ea.

The default is the exact canonical three-panel rule.  The alternate first
constructs the clockwise middle panel, reads the row of its unique color-8
marker, then chooses the right-panel rotation from that intermediate: upper
half gives the canonical half-turn, lower half gives a counter-clockwise turn.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any

_HOME = Path(__file__).resolve().parent
_PROGRAMS = {
    "fixed_half_turn": _HOME / "canonical.rkt",
    "marker_row_control": _HOME / "marker_row_control.rkt",
}
_COLORS = (1, 2, 3, 4, 6, 7, 9)

# (n, marker branch in the clockwise middle panel, density profile)
_DEMO_SPECS = (
    (4, "lower", "dense"),
    (5, "upper", "sparse"),
    (6, "lower", "sparse"),
    (3, "upper", "dense"),
    (7, "lower", "dense"),
    (8, "upper", "sparse"),
)
_QUERY_SPECS = (
    (4, "upper", "sparse"),
    (6, "lower", "dense"),
    (8, "upper", "dense"),
    (9, "lower", "stress"),
)


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def _policy(settings: Any) -> str:
    if not isinstance(settings, dict) or set(settings) != {"right_policy"}:
        raise ValueError("settings must contain exactly right_policy")
    policy = settings["right_policy"]
    if type(policy) is not str or policy not in _PROGRAMS:
        raise ValueError("right_policy must be fixed_half_turn or marker_row_control")
    return policy


def program(settings: Any) -> str:
    return _PROGRAMS[_policy(settings)].read_text(encoding="utf-8")


def _mix_seed(seed: int, role: str, index: int) -> int:
    payload = f"616a5c01a7ea|{seed}|{role}|{index}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _rotate90(panel: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*panel[::-1])]


def _rotations(panel: list[list[int]]) -> tuple[list[list[int]], ...]:
    result = [deepcopy(panel)]
    for _ in range(3):
        result.append(_rotate90(result[-1]))
    return tuple(result)


def _d4_count(panel: list[list[int]]) -> int:
    signatures = set()
    current = deepcopy(panel)
    for _ in range(4):
        signatures.add(tuple(tuple(row) for row in current))
        signatures.add(tuple(tuple(reversed(row)) for row in current))
        current = _rotate90(current)
    return len(signatures)


def _marker_col(n: int, branch: str, rng: random.Random) -> int:
    upper = [c for c in range(n) if 2 * c < n]
    lower = [c for c in range(n) if 2 * c >= n]
    return rng.choice(upper if branch == "upper" else lower)


def _panel(seed: int, role: str, index: int, n: int, branch: str, profile: str) -> list[list[int]]:
    rng = random.Random(_mix_seed(seed, role, index))
    marker_col = _marker_col(n, branch, rng)
    marker_row = rng.randrange(n)
    marker = (marker_row, marker_col)
    palette_size = min(len(_COLORS), 3 + ((seed + index + (0 if role == "demo" else 2)) % 4))
    palette = rng.sample(list(_COLORS), palette_size)
    cell_count = n * n

    for _ in range(512):
        panel = [[0 for _ in range(n)] for _ in range(n)]
        if profile in {"dense", "stress"}:
            occupied = [(r, c) for r in range(n) for c in range(n)]
        else:
            target = max(palette_size + 2, (2 * cell_count + 2) // 3)
            candidates = [(r, c) for r in range(n) for c in range(n) if (r, c) != marker]
            occupied = [marker, *rng.sample(candidates, min(target - 1, len(candidates)))]
        for r, c in occupied:
            panel[r][c] = rng.choice(palette)
        panel[marker_row][marker_col] = 8
        # Ensure every chosen ordinary color is observable without introducing
        # another marker or separator color.
        free = [(r, c) for r, c in occupied if (r, c) != marker]
        rng.shuffle(free)
        for color, (r, c) in zip(palette, free):
            panel[r][c] = color
        if _d4_count(panel) == 8:
            middle = _rotate90(panel)
            observed_row = next(r for r, row in enumerate(middle) if 8 in row)
            if (2 * observed_row >= n) == (branch == "lower"):
                return panel
    raise RuntimeError("failed to construct a D4-discriminative marker panel")


def _build_input(seed: int, role: str, index: int, spec: tuple[int, str, str]) -> list[list[int]]:
    n, branch, profile = spec
    source = _panel(seed, role, index, n, branch, profile)
    grid = [[0 for _ in range(3 * n + 2)] for _ in range(n)]
    for r in range(n):
        grid[r][:n] = source[r]
        grid[r][n] = 5
        grid[r][2 * n + 1] = 5
    return grid


def _solve(grid: list[list[int]], policy: str) -> list[list[int]]:
    n = len(grid)
    if any(len(row) != 3 * n + 2 for row in grid):
        raise ValueError("input must be n by 3*n+2")
    source = [list(row[:n]) for row in grid]
    turns = _rotations(source)
    middle = turns[1]
    marker_rows = [r for r, row in enumerate(middle) if 8 in row]
    if len(marker_rows) != 1 or sum(value == 8 for row in middle for value in row) != 1:
        raise ValueError("source must contain exactly one color-8 marker")
    marker_row = marker_rows[0]
    right = turns[2]
    if policy == "marker_row_control" and 2 * marker_row >= n:
        right = turns[3]

    output = [[0 for _ in range(3 * n + 2)] for _ in range(n)]
    for r in range(n):
        output[r][:n] = source[r]
        output[r][n] = 5
        output[r][n + 1 : 2 * n + 1] = middle[r]
        output[r][2 * n + 1] = 5
        output[r][2 * n + 2 :] = right[r]
    return output


def _pair(grid: list[list[int]], policy: str) -> dict[str, list[list[int]]]:
    return {"input": deepcopy(grid), "output": _solve(grid, policy)}


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 2, 6)
    queries = _integer("queries", queries, 1, 4)
    policy = _policy(settings)

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
        "train": [_pair(grid, policy) for grid in demo_inputs],
        "test": [_pair(grid, policy) for grid in selected_queries],
        "program_solution": program(settings),
    }
