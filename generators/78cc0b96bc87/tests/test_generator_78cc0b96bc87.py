from __future__ import annotations

import copy
import importlib
import random

import pytest

from reviewer_support import canonical_pairs, find_root


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.78cc0b96bc87.generator"
)


def _first_absent_color(grid: list[list[int]]) -> int:
    present = {value for row in grid for value in row}
    return next(color for color in range(1, 10) if color not in present)


def _first_zero_outside_frame(grid: list[list[int]]) -> tuple[int, int]:
    facts, errors = gen._analyze(grid)
    assert errors == []
    frame = facts["frame"]
    return next(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 0
        and not (
            frame["top"] <= row <= frame["bottom"]
            and frame["left"] <= col <= frame["right"]
        )
    )


def test_rule_hash_and_all_canonical_pairs() -> None:
    pairs = canonical_pairs(gen.TASK_ID, root=find_root(__file__))
    assert gen.RULE_HASH == "5ed55d63a700"
    assert len(pairs) == 5
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original, "analysis and mirror must preserve input"


def test_every_declared_override_boundary_is_exact_and_observable() -> None:
    cases = [
        {"grid_h": 8},
        {"grid_h": 10},
        {"grid_w": 10},
        {"grid_w": 12},
        {"frame_h": 6},
        {"frame_h": 7},
        {"frame_w": 6},
        {"frame_w": 9},
        *({"seed_layout": layout} for layout in gen.SEED_LAYOUTS),
        {
            "grid_h": 8,
            "grid_w": 10,
            "frame_h": 7,
            "frame_w": 9,
            "seed_layout": "spaced_pair",
        },
        {
            "grid_h": 10,
            "grid_w": 12,
            "frame_h": 6,
            "frame_w": 6,
            "seed_layout": "shifted_pair",
        },
    ]
    for difficulty in ("easy", "medium", "hard"):
        for case_index, overrides in enumerate(cases):
            grid = gen.generate(
                71000 + case_index,
                37,
                difficulty=difficulty,
                **overrides,
            )
            assert gen.self_check(grid) == []
            observed = gen.observe_overrides(grid)
            for name, expected in overrides.items():
                assert observed[name] == expected

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, texture="helpful")
    with pytest.raises(ValueError, match="must be an integer"):
        gen.generate(1, 0, grid_h=True)
    with pytest.raises(ValueError, match=r"8\.\.10"):
        gen.generate(1, 0, grid_h=7)
    with pytest.raises(ValueError, match="seed_layout"):
        gen.generate(1, 0, seed_layout="vertical_pair")
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="expert")


def test_canonical_frame_height_eight_is_exact_and_observable() -> None:
    """The generator should cover the tallest frame in the canonical task."""
    for difficulty in ("easy", "medium", "hard"):
        for sample_index, layout in enumerate(gen.SEED_LAYOUTS):
            grid = gen.generate(
                78000 + sample_index,
                sample_index,
                difficulty=difficulty,
                grid_h=10,
                frame_h=8,
                seed_layout=layout,
            )
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            assert gen.observe_overrides(grid)["frame_h"] == 8


def test_self_check_rejects_targeted_negative_recombinations() -> None:
    base = gen.generate(81000, 2, difficulty="hard")
    facts, errors = gen._analyze(base)
    assert errors == []
    frame = facts["frame"]
    absent = _first_absent_color(base)

    broken_frame = copy.deepcopy(base)
    broken_frame[frame["top"]][frame["left"]] = 0
    assert gen.self_check(broken_frame)

    third_seed = copy.deepcopy(base)
    extra = next(
        (row, col)
        for row in range(frame["top"] + 1, frame["bottom"])
        for col in range(frame["left"] + 1, frame["right"])
        if third_seed[row][col] == 0
    )
    third_seed[extra[0]][extra[1]] = absent
    assert any("exactly two seed" in error for error in gen.self_check(third_seed))

    vertical_pair = copy.deepcopy(base)
    left_row, left_col, _left_color = facts["left_seed"]
    right_row, right_col, right_color = facts["right_seed"]
    vertical_pair[right_row][right_col] = 0
    destination = next(
        (row, left_col)
        for row in range(frame["top"] + 1, frame["bottom"])
        if row != left_row and vertical_pair[row][left_col] == 0
    )
    vertical_pair[destination[0]][destination[1]] = right_color
    assert any("share one row" in error for error in gen.self_check(vertical_pair))

    outside_distractor = copy.deepcopy(base)
    outside = _first_zero_outside_frame(outside_distractor)
    outside_distractor[outside[0]][outside[1]] = absent
    assert any("outside the frame" in error for error in gen.self_check(outside_distractor))

    wrong_parity = copy.deepcopy(base)
    wrong_parity[left_row][left_col] = 0
    parity_destination = next(
        (left_row, col)
        for col in range(frame["left"] + 1, frame["right"])
        if wrong_parity[left_row][col] == 0
        and ((left_row - frame["top"] - 1) + (col - frame["left"] - 1)) % 2 == 1
        and col < right_col
    )
    wrong_parity[parity_destination[0]][parity_destination[1]] = facts["left_color"]
    assert any("left seed must lie on even parity" in error for error in gen.self_check(wrong_parity))


def test_deterministic_replay_is_fresh_and_preserves_global_rng() -> None:
    random.seed(123456789)
    state = random.getstate()
    first = gen.generate(91000, 11, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(91000, 11, difficulty="medium")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert second[0][0] != 9


def test_every_three_slot_sliding_window_identifies_the_query() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for start in range(6):
            episode = []
            for sample_index in range(start, start + 4):
                grid = gen.generate(1234567, sample_index, difficulty=difficulty)
                episode.append({"input": grid, "output": gen.rule_mirror(grid)})
            layouts = {
                gen.observe_overrides(pair["input"])["seed_layout"]
                for pair in episode[:3]
            }
            assert layouts == set(gen.SEED_LAYOUTS)
            assert gen.lesson_identifiable(episode[:3], episode[3]) == []


def test_generated_seed_cells_are_never_relabelled() -> None:
    checked = 0
    for difficulty in ("easy", "medium", "hard"):
        for offset in range(60):
            grid = gen.generate(220000 + offset, offset, difficulty=difficulty)
            output = gen.rule_mirror(grid)
            facts, errors = gen._analyze(grid)
            assert errors == []
            for row, col, color in facts["seeds"]:
                assert output[row][col] == color
            checked += 1
    assert checked == 180
