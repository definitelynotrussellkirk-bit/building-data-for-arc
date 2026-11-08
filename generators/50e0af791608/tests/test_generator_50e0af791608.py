from __future__ import annotations

import copy
import importlib
import json
import random
from collections import deque
from pathlib import Path

import pytest


TASK = "50e0af791608"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def canonical_pairs():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row["train"] + row["test"]
    raise AssertionError("canonical row missing")


def distances(grid, origin):
    result = {origin: 0}
    queue = deque([origin])
    while queue:
        row, col = queue.popleft()
        for drow, dcol in DELTAS:
            cell = row + drow, col + dcol
            if 0 <= cell[0] < len(grid) and 0 <= cell[1] < len(grid[0]) and grid[cell[0]][cell[1]] != 5 and cell not in result:
                result[cell] = result[(row, col)] + 1
                queue.append(cell)
    return result


def independent_oracle(grid):
    start = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2)
    goal = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3)
    from_start, from_goal = distances(grid, start), distances(grid, goal)
    optimum = from_start[goal]
    union = {cell for cell, distance in from_start.items() if grid[cell[0]][cell[1]] == 0 and cell in from_goal and distance + from_goal[cell] == optimum}
    output = copy.deepcopy(grid)
    for row, col in union:
        output[row][col] = 8
    return output, union


@pytest.mark.parametrize("index,profile", list(enumerate(MODULE.PUBLIC_PROFILES)))
def test_exact_public_replay(index, profile):
    pair = canonical_pairs()[index]
    grid = MODULE.generate(100 + index, index, scene_profile=profile)
    assert grid == pair["input"]
    assert MODULE.rule_mirror(grid) == pair["output"]
    assert MODULE.canonical_profile_signature(grid) == profile
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", MODULE.GENERAL_PROFILES)
def test_every_general_profile_in_every_band(profile, band):
    grid = MODULE.generate(20_000 + len(profile), 11, difficulty=band, scene_profile=profile)
    analysis = MODULE._analysis(grid)
    expected, _ = independent_oracle(grid)
    assert not analysis["errors"]
    assert analysis["scene_profile"] == profile
    assert analysis["output"] == expected
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
    assert all(value == 5 for value in grid[0] + grid[-1])
    assert all(row[0] == row[-1] == 5 for row in grid)


@pytest.mark.parametrize("profile", ["horizontal_corridor_pocket", "vertical_corridor_pocket"])
def test_corridor_pocket_is_reachable_but_not_shortest(profile):
    grid = MODULE.generate(31, 4, difficulty="hard", scene_profile=profile)
    facts = MODULE._analysis(grid)["facts"]
    assert facts["off_shortest"]
    assert set(facts["union"]).isdisjoint(facts["off_shortest"])
    assert all(facts["output"][r][c] == 0 for r, c in facts["off_shortest"])


def test_open_room_marks_every_interior_zero():
    grid = MODULE.generate(37, 2, difficulty="medium", scene_profile="open_room")
    facts = MODULE._analysis(grid)["facts"]
    zeros = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 0}
    assert set(facts["union"]) == zeros


@pytest.mark.parametrize("profile", ["symmetric_block_horizontal", "symmetric_block_vertical"])
def test_symmetric_blocks_mark_both_equal_detours(profile):
    grid = MODULE.generate(41, 3, difficulty="hard", scene_profile=profile)
    facts = MODULE._analysis(grid)["facts"]
    walls = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5 and 0 < r < len(grid) - 1 and 0 < c < len(grid[0]) - 1}
    row0, row1 = min(r for r, _ in walls), max(r for r, _ in walls)
    col0, col1 = min(c for _, c in walls), max(c for _, c in walls)
    if profile.endswith("horizontal"):
        assert any(r < row0 for r, _ in facts["union"]) and any(r > row1 for r, _ in facts["union"])
    else:
        assert any(c < col0 for _, c in facts["union"]) and any(c > col1 for _, c in facts["union"])


@pytest.mark.parametrize("profile,side", [("top_shorter_block", "top"), ("bottom_shorter_block", "bottom"), ("left_shorter_block", "left"), ("right_shorter_block", "right")])
def test_asymmetric_blocks_mark_only_shorter_side(profile, side):
    grid = MODULE.generate(43, 5, difficulty="hard", scene_profile=profile)
    facts = MODULE._analysis(grid)["facts"]
    walls = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5 and 0 < r < len(grid) - 1 and 0 < c < len(grid[0]) - 1}
    row0, row1 = min(r for r, _ in walls), max(r for r, _ in walls)
    col0, col1 = min(c for _, c in walls), max(c for _, c in walls)
    union = set(facts["union"])
    if side == "top":
        assert any(r < row0 for r, _ in union) and not any(r > row1 for r, _ in union)
    elif side == "bottom":
        assert any(r > row1 for r, _ in union) and not any(r < row0 for r, _ in union)
    elif side == "left":
        assert any(c < col0 for _, c in union) and not any(c > col1 for _, c in union)
    else:
        assert any(c > col1 for _, c in union) and not any(c < col0 for _, c in union)


def test_twin_gates_both_belong_to_union():
    grid = MODULE.generate(47, 6, difficulty="hard", scene_profile="twin_gates")
    facts = MODULE._analysis(grid)["facts"]
    barrier = len(grid[0]) // 2
    gaps = {(r, barrier) for r in range(1, len(grid) - 1) if grid[r][barrier] == 0}
    assert len(gaps) == 2 and gaps <= set(facts["union"])


def test_only_union_zeros_change_and_markers_walls_stay_fixed():
    grid = MODULE.generate(51, 7, difficulty="hard", scene_profile="symmetric_block_horizontal")
    expected, union = independent_oracle(grid)
    actual = MODULE.rule_mirror(grid)
    changed = {(r, c) for r in range(len(grid)) for c in range(len(grid[0])) if grid[r][c] != actual[r][c]}
    assert actual == expected and changed == union
    assert all(actual[r][c] == grid[r][c] for r in range(len(grid)) for c in range(len(grid[0])) if grid[r][c] in (2, 3, 5))


def test_determinism_fresh_returns_and_global_rng_independence():
    random.seed(773)
    state = random.getstate()
    first = MODULE.generate(61, 8, difficulty="medium", scene_profile="twin_gates")
    assert random.getstate() == state
    second = MODULE.generate(61, 8, difficulty="medium", scene_profile="twin_gates")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 0
    assert MODULE.generate(61, 8, difficulty="medium", scene_profile="twin_gates") == second


@pytest.mark.parametrize("grid", [[], [[]], [[5] * 8 for _ in range(6)], [[5] * 7 for _ in range(31)], [[5] * 8 for _ in range(8)] + [[5] * 7], [[False] * 8 for _ in range(8)], [[9] * 8 for _ in range(8)]])
def test_malformed_grids_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_missing_markers_open_boundary_and_unreachable_fail_closed():
    missing = [[5] * 9 for _ in range(9)]
    assert MODULE.self_check(missing)
    open_boundary = MODULE.generate(71, 1, scene_profile="open_room")
    open_boundary[0][2] = 0
    assert MODULE.self_check(open_boundary)
    unreachable = MODULE.generate(73, 2, scene_profile="open_room")
    start = next((r, c) for r, row in enumerate(unreachable) for c, value in enumerate(row) if value == 2)
    for drow, dcol in DELTAS:
        unreachable[start[0] + drow][start[1] + dcol] = 5
    assert MODULE.self_check(unreachable)


@pytest.mark.parametrize("kwargs", [{"scene_profile": "unknown"}, {"texture": "maze"}, {"difficulty": "expert"}])
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, **kwargs)


def test_axis_contract_is_literal_and_minimal():
    assert set(MODULE.AXES) == {"scene_profile"}
    assert set(MODULE.SCENE_PROFILES) == set(MODULE.AXES["scene_profile"]["valid"].split("|"))
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()
