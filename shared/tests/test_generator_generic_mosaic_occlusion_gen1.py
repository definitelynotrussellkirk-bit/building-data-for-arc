from __future__ import annotations

import copy
import random

from puzzle_generators.generic.concepts.mosaic_occlusion import gen1


def _messages(task):
    return "\n".join(gen1.self_check_task(task))


def _mutate_non_hole(value):
    for candidate in range(10):
        if candidate not in (value, gen1.HOLE):
            return candidate
    raise AssertionError("no alternate ARC color")


def test_generated_lessons_are_structural_and_identifiable():
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(30):
            task = gen1.generate_task(seed, difficulty=difficulty)
            assert gen1.self_check_task(task) == []
            assert gen1.lesson_identifiable(task["train"], task["test"][0]) == []

            al_offsets = {
                gen1._detect_axis(pair["input"], True)
                - (len(pair["input"][0]) - 1)
                for pair in task["train"]
            }
            au_offsets = {
                gen1._detect_axis(pair["input"], False)
                - (len(pair["input"]) - 1)
                for pair in task["train"]
            }
            assert len(al_offsets) >= 2
            assert len(au_offsets) >= 2
            assert al_offsets <= {1, 2, 3}
            assert au_offsets <= {1, 2, 3}


def test_self_check_rejects_four_targeted_impostors():
    task = gen1.generate_task(314159, difficulty="medium")

    wrong_answer = copy.deepcopy(task)
    wrong_answer["train"][0]["output"][0][0] = _mutate_non_hole(
        wrong_answer["train"][0]["output"][0][0]
    )
    assert "output does not match the mirror-recovery rule" in _messages(wrong_answer)

    broken_rectangle = copy.deepcopy(task)
    pair = broken_rectangle["train"][0]
    bbox = gen1._hole_bbox(pair["input"])
    assert bbox is not None
    r1, c1, _, _ = bbox
    pair["input"][r1][c1] = pair["output"][0][0]
    assert "color 8 cells are not one solid rectangle" in _messages(broken_rectangle)

    one_axis_lesson = copy.deepcopy(task)
    one_axis_lesson["train"][1] = copy.deepcopy(one_axis_lesson["train"][0])
    one_axis_errors = _messages(one_axis_lesson)
    assert "duplicates an earlier input" in one_axis_errors
    assert (
        "lacks a horizontal-only recovery witness" in one_axis_errors
        or "lacks a vertical-only recovery witness" in one_axis_errors
    )

    broken_symmetry = copy.deepcopy(task)
    grid = broken_symmetry["test"][0]["input"]
    al = gen1._detect_axis(grid, True)
    au = gen1._detect_axis(grid, False)
    changed = False
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == gen1.HOLE:
                continue
            for rr, cc in ((r, al - c), (au - r, c)):
                if (
                    0 <= rr < len(grid)
                    and 0 <= cc < len(grid[0])
                    and (rr, cc) != (r, c)
                    and grid[rr][cc] != gen1.HOLE
                ):
                    grid[r][c] = _mutate_non_hole(value)
                    changed = True
                    break
            if changed:
                break
        if changed:
            break
    assert changed
    symmetry_errors = _messages(broken_symmetry)
    assert (
        "does not have unique best reflection axes" in symmetry_errors
        or "output does not match the mirror-recovery rule" in symmetry_errors
        or "reconstruction breaks declared mirror symmetry" in symmetry_errors
    )


def test_replay_is_fresh_and_does_not_touch_global_rng():
    before = random.getstate()
    expected = gen1.generate_task(271828, difficulty="hard")
    assert random.getstate() == before

    mutated = gen1.generate_task(271828, difficulty="hard")
    mutated["train"][0]["input"][0][0] = _mutate_non_hole(
        mutated["train"][0]["input"][0][0]
    )
    replay = gen1.generate_task(271828, difficulty="hard")
    assert replay == expected
    assert replay is not expected
    assert replay["train"][0]["input"] is not expected["train"][0]["input"]
    assert random.getstate() == before


def test_rule_axes_are_unique_and_reconstruction_is_exact():
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(20, 40):
            task = gen1.generate_task(seed, difficulty=difficulty)
            for pair in task["train"] + task["test"]:
                grid = pair["input"]
                assert gen1._unique_best_axis(grid, True) == gen1._detect_axis(grid, True)
                assert gen1._unique_best_axis(grid, False) == gen1._detect_axis(grid, False)
                assert gen1._apply(grid) == pair["output"]
