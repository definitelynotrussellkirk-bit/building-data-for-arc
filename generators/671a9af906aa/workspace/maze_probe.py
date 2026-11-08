"""Independent semantic probe for task 671a9af906aa.

This file deliberately does not import the production generator.  It mirrors the
canonical stateful BFS from the public rule description and implements plausible
rivals used by task-local tests and review evidence.
"""
from __future__ import annotations

from collections import deque
import json
from pathlib import Path
from typing import Iterable

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def positions(grid, color: int) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]


def _single(grid, color: int) -> tuple[int, int]:
    found = positions(grid, color)
    if len(found) != 1:
        raise ValueError(f"expected one color-{color} cell, found {len(found)}")
    return found[0]


def stateful_path(
    grid,
    *,
    doors_open_from_start: bool = False,
    doors_never_open: bool = False,
) -> list[tuple[int, int, bool]] | None:
    """Return the canonical BFS state path, or None when the goal is unreachable."""
    start = _single(grid, 2)
    goal = _single(grid, 3)
    h, w = len(grid), len(grid[0])
    initial = (start[0], start[1], False)
    queue = deque([initial])
    parent: dict[tuple[int, int, bool], tuple[int, int, bool] | None] = {initial: None}
    end = None

    while queue:
        state = queue.popleft()
        r, c, has_key = state
        if (r, c) == goal:
            end = state
            break
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w):
                continue
            value = grid[nr][nc]
            if value == 8:
                continue
            new_key = has_key or value == 4
            if value == 5:
                if doors_never_open:
                    continue
                if not doors_open_from_start and not new_key:
                    continue
            next_state = (nr, nc, new_key)
            if next_state in parent:
                continue
            parent[next_state] = state
            queue.append(next_state)

    if end is None:
        return None
    path = []
    cur = end
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    return list(reversed(path))


def paint_path(grid, path: Iterable[tuple[int, int, bool]] | None):
    out = [list(row) for row in grid]
    if path is None:
        return out
    for r, c, _ in path:
        if grid[r][c] == 0:
            out[r][c] = 7
    return out


def rule_output(grid):
    return paint_path(grid, stateful_path(grid))


def global_key_unlock_rival(grid):
    """Wrong rival: a key anywhere makes every door open from the first step."""
    return paint_path(grid, stateful_path(grid, doors_open_from_start=bool(positions(grid, 4))))


def door_is_wall_rival(grid):
    """Wrong rival: color 5 is always impassable, even after collecting the key."""
    return paint_path(grid, stateful_path(grid, doors_never_open=True))


def _coordinate_path(grid, start, goal, *, door_open: bool):
    h, w = len(grid), len(grid[0])
    queue = deque([start])
    parent = {start: None}
    while queue:
        point = queue.popleft()
        if point == goal:
            break
        for dr, dc in DIRS:
            nxt = (point[0] + dr, point[1] + dc)
            if not (0 <= nxt[0] < h and 0 <= nxt[1] < w) or nxt in parent:
                continue
            value = grid[nxt[0]][nxt[1]]
            if value == 8 or (value == 5 and not door_open):
                continue
            parent[nxt] = point
            queue.append(nxt)
    if goal not in parent:
        return None
    out = []
    cur = goal
    while cur is not None:
        out.append(cur)
        cur = parent[cur]
    return list(reversed(out))


def always_visit_key_rival(grid):
    """Canonical-compatible shortcut: force start->key, then key->goal.

    This fits all three public demonstrations but fails the public query, where
    the shortest valid route correctly bypasses the irrelevant key and door.
    """
    start, key, goal = _single(grid, 2), _single(grid, 4), _single(grid, 3)
    first = _coordinate_path(grid, start, key, door_open=False)
    if first is None:
        return [list(row) for row in grid]
    second = _coordinate_path(grid, key, goal, door_open=True)
    if second is None:
        return [list(row) for row in grid]
    out = [list(row) for row in grid]
    for r, c in first + second[1:]:
        if grid[r][c] == 0:
            out[r][c] = 7
    return out


def classify(grid) -> str:
    path = stateful_path(grid)
    if path is None:
        return "unreachable"
    values = [grid[r][c] for r, c, _ in path]
    used_key, used_door = 4 in values, 5 in values
    if used_key and used_door:
        return "key_detour"
    if not used_key and not used_door:
        return "key_bypass"
    return "partial"


def canonical_record(repo_root: Path):
    ledger = repo_root / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in ledger.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == "671a9af906aa":
            return row
    raise LookupError("canonical task 671a9af906aa not found")
