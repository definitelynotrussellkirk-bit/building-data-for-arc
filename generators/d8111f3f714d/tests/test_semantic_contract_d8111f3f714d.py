from __future__ import annotations

from copy import deepcopy

from reviewer_support import find_root, load_selected_generator


TASK_ID = "d8111f3f714d"
ROOT = find_root(__file__)
GEN, _SOURCE_PATH, _SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _vertical_scene(branch_row: int, branch_col: int) -> list[list[int]]:
    """Hand-authored lawful one-branch scene with a vertical trunk at column 5."""
    grid = [[0 for _ in range(12)] for _ in range(12)]
    for row, col in ((1, 5), (10, 5), (branch_row, branch_col)):
        grid[row][col] = 2
    assert GEN.self_check(grid) == []
    return grid


def _pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_normal_three_demo_schedules_refute_every_declared_competitor() -> None:
    assert GEN.EXAMPLES_NEEDED == 3
    assert set(GEN.LESSON_COMPETITORS) == {
        "trunk_only",
        "branches_only",
        "negative_side_only",
        "positive_side_only",
        "branches_away_to_edge",
    }

    for difficulty in ("easy", "medium", "hard"):
        demos = [
            _pair(GEN.generate(7301, sample_index, difficulty=difficulty))
            for sample_index in range(3)
        ]
        query = _pair(GEN.generate(7301, 3, difficulty=difficulty))

        assert GEN.lesson_identifiable(demos, query) == []
        for name, competitor in GEN.LESSON_COMPETITORS.items():
            assert any(
                competitor(deepcopy(pair["input"])) != pair["output"]
                for pair in demos
            ), (difficulty, name)


def test_one_sided_demonstrations_expose_surviving_negative_side_shortcut() -> None:
    demos = [
        _pair(_vertical_scene(branch_row, 2))
        for branch_row in (3, 5, 7)
    ]
    query = _pair(_vertical_scene(6, 8))

    competitor = GEN.LESSON_COMPETITORS["negative_side_only"]
    assert all(competitor(pair["input"]) == pair["output"] for pair in demos)
    assert competitor(query["input"]) != query["output"]

    reasons = GEN.lesson_identifiable(demos, query)
    assert any("negative_side_only" in reason for reason in reasons)


def test_contract_rejects_malformed_or_mislabeled_lesson_pairs() -> None:
    valid = _pair(_vertical_scene(4, 2))

    assert GEN.lesson_identifiable([], valid) == ["need at least 3 demonstrations"]
    assert GEN.lesson_identifiable([valid, valid, {}], valid) == [
        "demo 2 must contain input and output"
    ]

    wrong = deepcopy(valid)
    wrong["output"] = deepcopy(wrong["input"])
    assert GEN.lesson_identifiable([valid, valid, wrong], valid) == [
        "demo 2 output does not match the canonical rule"
    ]
