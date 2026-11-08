from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.per_puzzle.a5192bbc9e88 import generator as gen
from scripts.canonical_profile_gate import canonical_inputs


def test_canonical_inputs_are_accepted_regression() -> None:
    inputs = canonical_inputs(gen.TASK_ID)
    assert len(inputs) == 4
    assert [gen.self_check(grid) for grid in inputs] == [[], [], [], []]


def test_profile_schedule_and_exact_observation() -> None:
    seen = set()
    for difficulty in (None, "easy", "medium", "hard"):
        for sample_index in range(len(gen.SCENE_PROFILES)):
            grid = gen.generate(1234, sample_index, difficulty=difficulty)
            assert gen.self_check(grid) == []
            observed = gen.observe_overrides(grid)
            expected = gen.schedule_profile(1234, sample_index, difficulty)
            assert observed == {"scene_profile": expected}
            seen.add(observed["scene_profile"])
    assert seen == set(gen.SCENE_PROFILES)


def test_every_profile_override_is_exact_and_unknown_keys_reject() -> None:
    for profile in gen.SCENE_PROFILES:
        grid = gen.generate(77, 9, difficulty="easy", scene_profile=profile)
        assert gen.observe_overrides(grid) == {"scene_profile": profile}
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 0, typo_profile="x")


def test_four_consecutive_demos_refute_named_competitors() -> None:
    for start in range(24):
        demos = []
        for index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(900 + start, index, difficulty="medium")
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        query_grid = gen.generate(900 + start, start + gen.EXAMPLES_NEEDED, difficulty="medium")
        query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []
        for competitor in gen.LESSON_COMPETITORS.values():
            assert any(competitor(pair["input"]) != pair["output"] for pair in demos)


def test_self_check_rejects_targeted_impostors() -> None:
    base = gen.generate(42, 3, scene_profile="medium_8x10_asymmetric")
    assert gen.self_check(base) == []

    empty = [[0 for _ in row] for row in base]
    assert gen.self_check(empty)

    two_color = copy.deepcopy(base)
    cells = [(r, c) for r, row in enumerate(two_color) for c, value in enumerate(row) if value]
    two_color[cells[0][0]][cells[0][1]] = 9 if two_color[cells[0][0]][cells[0][1]] != 9 else 8
    assert any("one object color" in error for error in gen.self_check(two_color))

    disconnected = copy.deepcopy(base)
    r0, c0 = cells[0]
    disconnected[r0][c0] = 0
    disconnected[1][1] = next(value for row in base for value in row if value)
    assert any("4-connected" in error for error in gen.self_check(disconnected))

    edge_touching = copy.deepcopy(base)
    color = next(value for row in base for value in row if value)
    edge_touching[0][0] = color
    assert any("outer margin" in error for error in gen.self_check(edge_touching))

    symmetry_drift = [[0 for _ in row] for row in base]
    vertical_template = ((1, 0), (1, 1), (1, 0))
    for dr, row in enumerate(vertical_template):
        for dc, value in enumerate(row):
            if value:
                symmetry_drift[2 + dr][2 + dc] = color
    assert any("requires asymmetric" in error for error in gen.self_check(symmetry_drift))


def test_determinism_fresh_objects_and_global_rng() -> None:
    random.seed(12345)
    before = random.getstate()
    first = gen.generate(99, 17, difficulty="hard")
    middle = random.getstate()
    second = gen.generate(99, 17, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert before == middle == after
