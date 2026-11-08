"""Frozen original-data oracle; standard library only, no repository imports."""
from collections import deque

BACKGROUND = 8


def inspect(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("Expected a rectangular grid")
    h, w = len(grid), len(grid[0])
    choices = []
    for side, col in (("left", 0), ("right", w - 1)):
        if grid[0][col] != 0:
            continue
        horizontal = grid[0][1 if col == 0 else 0]
        vertical = grid[1][col]
        if {horizontal, vertical} != {1, 2}:
            continue
        if any(grid[0][x] != horizontal for x in range(w) if x != col):
            continue
        if any(grid[y][col] != vertical for y in range(1, h)):
            continue
        choices.append((side, horizontal == 1, col))
    if len(choices) != 1:
        raise ValueError("Expected exactly one supported top corner with borders 0,1,2")
    side, horizontal_tracks, edge = choices[0]
    xs = range(1, w) if edge == 0 else range(w - 1)
    foreground = {(y, x) for y in range(1, h) for x in xs if grid[y][x] != BACKGROUND}
    remaining = set(foreground)
    objects = []
    while remaining:
        seed = min(remaining)
        remaining.remove(seed)
        found, todo = {seed}, deque([seed])
        while todo:
            y, x = todo.popleft()
            for nxt in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if nxt in remaining:
                    remaining.remove(nxt)
                    found.add(nxt)
                    todo.append(nxt)
        min_y = min(y for y, x in found)
        max_y = max(y for y, x in found)
        min_x = min(x for y, x in found)
        max_x = max(x for y, x in found)
        patch = [list(row[min_x:max_x + 1]) for row in grid[min_y:max_y + 1]]
        if len(found) != len(patch) * len(patch[0]):
            raise ValueError("Original-domain objects are filled non-8 rectangles")
        if horizontal_tracks:
            if len(patch) != 2 or len(patch[0]) % 2:
                raise ValueError("Expected an even-length horizontal two-row bar")
        elif len(patch[0]) != 2 or len(patch) % 2:
            raise ValueError("Expected an even-length vertical two-column bar")
        objects.append({"bounds": (min_y, min_x, max_y, max_x), "patch": patch})
    if not objects:
        raise ValueError("Expected at least one object")
    return {"side": side, "horizontal": horizontal_tracks, "objects": objects}


def ccw(patch):
    return [list(col) for col in zip(*patch)][::-1]


def object_key(obj, horizontal, side):
    top, left, bottom, right = obj["bounds"]
    across = left if side == "left" else -right
    return (top, across) if horizontal else (across, top)


def stack(patches, alignment="center"):
    width = max(len(patch[0]) for patch in patches)
    result = []
    for patch in patches:
        difference = width - len(patch[0])
        left = 0 if alignment == "left" else difference if alignment == "right" else difference // 2
        for row in patch:
            result.append([BACKGROUND] * left + list(row) + [BACKGROUND] * (difference - left))
    return result


def solve(grid):
    parts = inspect(grid)
    ordered = sorted(parts["objects"], key=lambda obj: object_key(obj, parts["horizontal"], parts["side"]))
    patches = [obj["patch"] if parts["horizontal"] else ccw(obj["patch"]) for obj in ordered]
    return stack(patches)


def reverse_output_order(grid):
    """Optional authored setting: reverse the sequence of two-row result bars."""
    output = solve(grid)
    return [row for offset in reversed(range(0, len(output), 2)) for row in output[offset:offset + 2]]


# The oracle above was frozen from the original public examples and gold before
# candidate inspection. It is copied here to keep these checks task-portable.
import importlib.util
import json
from pathlib import Path

import pytest

TASK_HOME = Path(__file__).resolve().parents[1]


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def candidate():
    return _load(TASK_HOME / "generator.py", "independent291_candidate")


@pytest.fixture(scope="module")
def episode_adapter():
    return _load(TASK_HOME / "workspace/parametric/adapter.py", "independent291_adapter")


def _frame(height, width, horizontal, right, placements):
    grid = [[8] * width for _ in range(height)]
    edge = width - 1 if right else 0
    grid[0] = [1 if horizontal else 2] * width
    for row in grid:
        row[edge] = 2 if horizontal else 1
    grid[0][edge] = 0
    for top, left, tile in placements:
        for dy, row in enumerate(tile):
            grid[top + dy][left:left + len(row)] = row
    return grid


def _expected(grid, order):
    return solve(grid) if order == "forward" else reverse_output_order(grid)


def test_frozen_oracle_matches_every_original_label(candidate):
    raw = TASK_HOME.parents[1] / "shared/data/raw"
    task = json.loads((raw / "arc-agi_evaluation_challenges.json").read_text())["291dc1e1"]
    gold = json.loads((raw / "arc-agi_evaluation_solutions.json").read_text())["291dc1e1"]
    pairs = task["train"] + [{"input": pair["input"], "output": output} for pair, output in zip(task["test"], gold)]
    assert len(pairs) == 5
    for pair in pairs:
        assert solve(pair["input"]) == candidate.solve(pair["input"]) == pair["output"]


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
@pytest.mark.parametrize("order", ["forward", "reverse"])
def test_all_lesson_profiles_match_frozen_oracle(episode_adapter, seed, order):
    episode = episode_adapter.generate(seed, {"stack_order": order}, 6, 4)
    for pair in episode["train"] + episode["test"]:
        assert pair["output"] == _expected(pair["input"], order)


@pytest.mark.parametrize("horizontal,right", [(True, False), (False, True)])
@pytest.mark.parametrize("order", ["forward", "reverse"])
def test_fifteen_bars_and_length28_reach_output_boundary(candidate, horizontal, right, order):
    long_tile = [[3, 4, 5, 6, 7, 9, 0] * 4, [1, 2, 3, 4, 5, 6, 7] * 4]
    placements = [(1, 1, long_tile)]
    placements += [(r, c, [[3, 4], [5, 6]]) for r in range(5, 24, 3) for c in (1, 5)]
    assert len(placements) == 15
    if not horizontal:
        placements = [(c, r, [list(col) for col in zip(*tile)]) for r, c, tile in placements]
    grid = _frame(30, 30, horizontal, right, placements)
    expected = _expected(grid, order)
    assert len(expected) == 30 and len(expected[0]) == 28
    assert candidate.solve(grid, order) == expected


def test_sixteen_bars_exceed_declared_admission_boundary(candidate):
    grid = _frame(15, 15, True, False, [(r, c, [[3, 4], [5, 6]]) for r in (1, 4, 7, 10) for c in (1, 4, 7, 10)])
    with pytest.raises(ValueError):
        candidate.solve(grid)


@pytest.mark.parametrize("horizontal,right", [(True, False), (False, True)])
@pytest.mark.parametrize("order", ["forward", "reverse"])
def test_diagonal_contact_preserves_two_independent_objects(candidate, horizontal, right, order):
    grid = _frame(6, 6, horizontal, right, [(1, 1, [[3, 4], [5, 6]]), (3, 3, [[7, 9], [1, 2]])])
    assert len(inspect(grid)["objects"]) == 2
    expected = _expected(grid, order)
    assert len(expected) == 4 and len(expected[0]) == 2
    assert candidate.solve(grid, order) == expected
