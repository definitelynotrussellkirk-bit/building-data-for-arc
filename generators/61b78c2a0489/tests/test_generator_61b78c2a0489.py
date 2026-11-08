from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "61b78c2a0489"
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical task row missing")


def stable_gravity(grid):
    height, width = len(grid), len(grid[0])
    out = [[0 for _ in range(width)] for _ in range(height)]
    for column in range(width):
        values = [grid[row][column] for row in range(height) if grid[row][column] != 0]
        for offset, value in enumerate(values, start=height - len(values)):
            out[offset][column] = value
    return out


def test_rule_hash_matches_normalized_canonical_source():
    source = canonical_row()["program_solution"]
    expected = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert MODULE.RULE_HASH == expected == "aee24df7c267"


def test_self_check_accepts_every_canonical_input():
    row = canonical_row()
    pairs = list(row["train"]) + list(row["test"])
    assert len(pairs) == 5
    assert [MODULE.self_check(pair["input"]) for pair in pairs] == [[]] * 5


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_normal_draws_are_valid_nonidentity_and_match_python_semantic_mirror(difficulty):
    for seed in range(30):
        grid = MODULE.generate(seed, seed * 7 + 2, difficulty=difficulty)
        assert MODULE.self_check(grid, difficulty=difficulty) == []
        assert stable_gravity(grid) != grid
        assert len({value for row in grid for value in row if value}) >= 2


def test_exact_overrides_are_observable_at_full_boundaries():
    for height, width, colors in [(4, 5, 2), (4, 5, 9), (12, 12, 2), (12, 12, 9)]:
        grid = MODULE.generate(
            123,
            4,
            difficulty="easy",
            grid_h=height,
            grid_w=width,
            n_distinct_colors=colors,
            layout="bottom_mixed",
        )
        assert MODULE.observe_overrides(grid) == {
            "grid_h": height,
            "grid_w": width,
            "n_distinct_colors": colors,
        }
        assert MODULE.self_check(grid) == []


def test_layout_modes_are_lawful_and_behaviorally_distinct():
    outputs = {
        layout: MODULE.generate(77, 5, difficulty="medium", layout=layout)
        for layout in MODULE.LAYOUTS
    }
    assert len({json.dumps(grid) for grid in outputs.values()}) == len(MODULE.LAYOUTS)
    assert all(MODULE.self_check(grid) == [] for grid in outputs.values())
    assert all(value == 0 for value in outputs["top_heavy"][-1])
    assert any(value != 0 for value in outputs["bottom_mixed"][-1])


def test_three_step_schedule_covers_all_position_profiles_and_order_branch():
    grids = [MODULE.generate(91, index, difficulty="medium") for index in range(3)]
    assert all(value == 0 for value in grids[0][-1])
    assert any(value != 0 for value in grids[2][-1])
    assert any(
        len({grids[1][row][column] for row in range(len(grids[1])) if grids[1][row][column]}) >= 2
        for column in range(len(grids[1][0]))
    )


def test_determinism_fresh_returns_and_global_random_state():
    random.seed(90210)
    state = random.getstate()
    first = MODULE.generate(19, 23, difficulty="hard")
    assert random.getstate() == state
    second = MODULE.generate(19, 23, difficulty="hard")
    assert first == second
    assert first is not second and all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert MODULE.generate(19, 23, difficulty="hard") == second


def test_self_check_rejects_four_targeted_impostors():
    valid = MODULE.generate(321, 1, difficulty="medium")
    impostors = {}

    settled = stable_gravity(valid)
    impostors["already_settled"] = settled

    horizontal = copy.deepcopy(valid)
    row = next(r for r in range(len(horizontal)) if horizontal[r].count(0) >= 2)
    horizontal[row][0] = 1
    horizontal[row][1] = 2
    impostors["horizontal_line"] = horizontal

    block = copy.deepcopy(valid)
    block[0][0] = block[0][1] = block[1][0] = block[1][1] = 3
    impostors["solid_2x2"] = block

    one_column = [[0 for _ in row] for row in valid]
    for row, color in [(0, 1), (2, 2), (4, 1)]:
        one_column[row][0] = color
    impostors["single_active_column"] = one_column

    for name, grid in impostors.items():
        assert MODULE.self_check(grid), name



def test_self_check_rejects_non_grid_string_rows():
    assert MODULE.self_check(["00000", "01000", "02000", "01000"] )

def test_unknown_and_impossible_overrides_fail_loudly():
    with pytest.raises(ValueError, match="unsupported override"):
        MODULE.generate(1, 1, unknown_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        MODULE.generate(1, 1, difficulty="nightmare")
