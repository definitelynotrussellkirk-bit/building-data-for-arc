from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest


TASK_ID = "10293dae26ed"
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _canonical_inputs():
    path = Path("data/canonical/puzzles.jsonl")
    with path.open() as handle:
        row = next(
            json.loads(line)
            for line in handle
            if f'"task_id": "{TASK_ID}"' in line
        )
    return [pair["input"] for split in ("train", "test") for pair in row[split]]


def test_all_scene_profile_overrides_are_exact_and_valid():
    for index, profile in enumerate(MODULE.SCENE_PROFILES):
        grid = MODULE.generate(917, index, difficulty="hard", scene_profile=profile)
        assert MODULE.self_check(grid) == []
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
        assert MODULE.rule_mirror(grid) != grid


def test_unknown_override_is_rejected_loudly():
    with pytest.raises(ValueError, match="unknown override axis"):
        MODULE.generate(0, 0, bogus_axis=3)


def test_sequential_schedule_covers_every_profile_and_anchors_every_lesson():
    for seed in range(17):
        observed = [
            MODULE.observe_overrides(MODULE.generate(seed, index))["scene_profile"]
            for index in range(len(MODULE._SCHEDULE_PATTERN))
        ]
        assert set(observed) == set(MODULE.SCENE_PROFILES)
        cyclic = observed + observed[:2]
        for start in range(len(observed)):
            assert "four_duplicate_color" in cyclic[start : start + 3]


def test_three_demo_lessons_refute_all_declared_competitors():
    for seed in range(17):
        for start in range(len(MODULE._SCHEDULE_PATTERN)):
            demos = []
            for index in range(start, start + 3):
                grid = MODULE.generate(seed, index, difficulty="medium")
                demos.append({"input": grid, "output": MODULE.rule_mirror(grid)})
            query_grid = MODULE.generate(seed, start + 3, difficulty="medium")
            query = {"input": query_grid, "output": MODULE.rule_mirror(query_grid)}
            assert MODULE.lesson_identifiable(demos, query) == []


def test_palette_shortcut_is_refuted_in_every_three_demo_lesson():
    for seed in range(257):
        for start in range(len(MODULE._SCHEDULE_PATTERN)):
            demos = []
            for index in range(start, start + 3):
                grid = MODULE.generate(seed, index, difficulty="medium")
                demos.append({"input": grid, "output": MODULE.rule_mirror(grid)})
            assert any(
                MODULE._canonical_palette_only(demo["input"]) != demo["output"]
                for demo in demos
            )


def test_palette_shortcut_regression_seed_64_window_0():
    demos = []
    for index in range(3):
        grid = MODULE.generate(64, index, difficulty="medium")
        demos.append({"input": grid, "output": MODULE.rule_mirror(grid)})
    query_grid = MODULE.generate(64, 3, difficulty="medium")
    query = {"input": query_grid, "output": MODULE.rule_mirror(query_grid)}

    assert any(
        MODULE._canonical_palette_only(demo["input"]) != demo["output"]
        for demo in demos
    )
    assert MODULE.lesson_identifiable(demos, query) == []


def test_four_component_duplicate_color_branch_is_present():
    grid = MODULE.generate(11, 5, scene_profile="four_duplicate_color")
    analysis = MODULE._analysis(grid)
    assert analysis["scene_profile"] == "four_duplicate_color"
    assert len(analysis["components"]) == 4
    colors = [component["color"] for component in analysis["components"]]
    assert len(set(colors)) == 3
    output = MODULE.rule_mirror(grid)
    for component in analysis["components"]:
        r1, c1, r2, c2 = component["bbox"]
        assert all(
            output[row][col] == 8
            for row in range(r1 + 1, r2)
            for col in range(c1 + 1, c2)
        )


def test_self_check_rejects_targeted_impostors():
    valid = MODULE.generate(3, 7, scene_profile="two_interior_mixed")

    prefilled = copy.deepcopy(valid)
    component = MODULE._analysis(prefilled)["components"][0]
    r1, c1, _r2, _c2 = component["bbox"]
    prefilled[r1 + 1][c1 + 1] = 8
    assert MODULE.self_check(prefilled)

    single = [[0] * 8 for _ in range(8)]
    for row in range(1, 5):
        for col in range(1, 5):
            single[row][col] = 2
    assert MODULE.self_check(single)

    tiny = copy.deepcopy(valid)
    component = MODULE._analysis(tiny)["components"][0]
    for row, col in component["cells"]:
        tiny[row][col] = 0
    for row in range(2):
        for col in range(2):
            tiny[row][col] = 4
    assert MODULE.self_check(tiny)

    hollow = copy.deepcopy(valid)
    component = MODULE._analysis(hollow)["components"][0]
    r1, c1, r2, c2 = component["bbox"]
    hollow[(r1 + r2) // 2][(c1 + c2) // 2] = 0
    assert MODULE.self_check(hollow)

    touching = copy.deepcopy(valid)
    components = MODULE._analysis(touching)["components"]
    first = components[0]
    second = components[1]
    r1, c1, r2, c2 = first["bbox"]
    sr1, sc1, _sr2, _sc2 = second["bbox"]
    # Add a same-colored bridge toward the other object; this either creates
    # a non-rectangle or a cardinal contact, both of which must be rejected.
    row = min(r2 + 1, len(touching) - 1)
    col = c2
    touching[row][col] = first["color"]
    if row < sr1:
        for rr in range(row + 1, sr1):
            touching[rr][col] = first["color"]
    elif col < sc1:
        for cc in range(col + 1, sc1):
            touching[row][cc] = first["color"]
    assert MODULE.self_check(touching)


def test_every_canonical_input_is_accepted_and_solved_by_mirror():
    for grid in _canonical_inputs():
        original = copy.deepcopy(grid)
        assert MODULE.self_check(grid) == []
        output = MODULE.rule_mirror(grid)
        assert grid == original
        assert output != grid


def test_determinism_fresh_returns_and_global_rng_state():
    state = random.getstate()
    first = MODULE.generate(12345, 9, difficulty="medium")
    second = MODULE.generate(12345, 9, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 0
    assert first != second
    assert random.getstate() == state
