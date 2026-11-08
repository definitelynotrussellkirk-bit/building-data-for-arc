"""Independent semantic probe for ARC task 90e1b47a15f9.

This module deliberately does not import the production generator.  It mirrors
only the pinned task rule and several plausible rivals so task-local tests and
future reviewers can inspect generated lessons without trusting generator code.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable, Sequence

Grid = Sequence[Sequence[int]]
_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


@dataclass(frozen=True)
class SearchResult:
    reachable: bool
    states: tuple[tuple[int, int, bool, bool], ...]

    @property
    def coordinates(self) -> tuple[tuple[int, int], ...]:
        return tuple((r, c) for r, c, _ka, _kb in self.states)


def positions(grid: Grid, color: int) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]


def search(
    grid: Grid,
    *,
    doors: str = "locked",
    require_both_keys_at_goal: bool = False,
) -> SearchResult:
    """Run a source-independent mirror of the canonical four-state BFS.

    ``doors`` is one of ``locked``, ``open``, ``wall``, or ``one_key_all``.
    The queue order matches the Racket prelude's cardinal deltas: up, down,
    left, right.
    """
    if doors not in {"locked", "open", "wall", "one_key_all"}:
        raise ValueError(f"unknown door mode: {doors}")
    starts = positions(grid, 2)
    goals = positions(grid, 3)
    if len(starts) != 1 or len(goals) != 1:
        return SearchResult(False, ())

    start = (starts[0][0], starts[0][1], False, False)
    goal = goals[0]
    queue = deque([start])
    parent: dict[
        tuple[int, int, bool, bool], tuple[int, int, bool, bool] | None
    ] = {start: None}
    end = None
    h, w = len(grid), len(grid[0])

    while queue:
        state = queue.popleft()
        r, c, key_a, key_b = state
        if (r, c) == goal and (
            not require_both_keys_at_goal or (key_a and key_b)
        ):
            end = state
            break

        # The authority updates possession from the current cell before testing
        # neighboring doors.  It also enqueues a same-cell state; that duplicate
        # does not change the first parent of any spatial neighbor.
        next_key_a = key_a or grid[r][c] == 4
        next_key_b = key_b or grid[r][c] == 5
        for dr, dc in _DIRS:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w):
                continue
            value = grid[nr][nc]
            if value == 8:
                continue
            if value in (6, 7):
                if doors == "wall":
                    continue
                if doors == "locked":
                    if value == 6 and not next_key_a:
                        continue
                    if value == 7 and not next_key_b:
                        continue
                elif doors == "one_key_all" and not (next_key_a or next_key_b):
                    continue
            nxt = (nr, nc, next_key_a, next_key_b)
            if nxt in parent:
                continue
            parent[nxt] = state
            queue.append(nxt)

    if end is None:
        return SearchResult(False, ())
    reverse_states = []
    current = end
    while current is not None:
        reverse_states.append(current)
        current = parent[current]
    return SearchResult(True, tuple(reversed(reverse_states)))


def paint(grid: Grid, result: SearchResult) -> list[list[int]]:
    out = [[0 for _ in row] for row in grid]
    if result.reachable:
        for r, c in result.coordinates:
            out[r][c] = 9
    return out


def rule_output(grid: Grid) -> list[list[int]]:
    return paint(grid, search(grid))


def erase_keys_and_doors_rival(grid: Grid) -> list[list[int]]:
    stripped = [
        [0 if value in (4, 5, 6, 7) else value for value in row]
        for row in grid
    ]
    return paint(stripped, search(stripped, doors="open"))


def doors_are_walls_rival(grid: Grid) -> list[list[int]]:
    return paint(grid, search(grid, doors="wall"))


def one_key_opens_both_rival(grid: Grid) -> list[list[int]]:
    return paint(grid, search(grid, doors="one_key_all"))


def always_collect_both_rival(grid: Grid) -> list[list[int]]:
    return paint(grid, search(grid, require_both_keys_at_goal=True))


def path_values(grid: Grid, result: SearchResult | None = None) -> set[int]:
    result = result or search(grid)
    return {grid[r][c] for r, c in result.coordinates}


def classify(grid: Grid) -> str:
    result = search(grid)
    if not result.reachable:
        return "unreachable"
    special = path_values(grid, result) & {4, 5, 6, 7}
    if special == {4, 5, 6, 7}:
        return "two_stage_detour"
    if not special:
        return "bypass"
    return "partial"
