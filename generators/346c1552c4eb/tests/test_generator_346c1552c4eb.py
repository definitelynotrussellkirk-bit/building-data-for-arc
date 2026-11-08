from __future__ import annotations

import importlib
import random

generator = importlib.import_module("puzzle_generators.per_puzzle.346c1552c4eb.generator")


CANONICAL_INPUTS = [
    [
        "00000000",
        "01000220",
        "00000000",
        "00000000",
        "03000440",
        "03300440",
        "00000000",
        "00000000",
    ],
    [
        "000000000",
        "000000050",
        "000000050",
        "000000000",
        "000060000",
        "000000000",
        "077000880",
        "070000888",
        "000000000",
    ],
    [
        "0000000000",
        "0990000030",
        "0990000000",
        "0000000000",
        "0000000000",
        "0020000000",
        "0020000400",
        "0000000440",
        "0000000000",
        "0000000000",
    ],
]


def test_canonical_inputs_and_outputs():
    expected = [[[1, 2, 3, 4]], [[6, 5, 7, 8]], [[3, 2, 4, 9]]]
    for grid, output in zip(CANONICAL_INPUTS, expected):
        assert generator.self_check(grid) == []
        assert generator.rule_mirror(grid) == output


def test_exact_override_boundaries_are_observable():
    for case in (
        {"grid_h": 7},
        {"grid_h": 14},
        {"grid_w": 7},
        {"grid_w": 14},
        {"n_blobs": 2},
        {"n_blobs": 6},
        {"grid_h": 7, "grid_w": 7, "n_blobs": 6},
        {"grid_h": 14, "grid_w": 14, "n_blobs": 2},
    ):
        grid = generator.generate(17, 3, difficulty="hard", **case)
        observed = generator.observe_overrides(grid)
        for key, value in case.items():
            assert observed[key] == value


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    state = random.getstate()
    first = generator.generate(1234, 9, difficulty="medium", n_blobs=5)
    assert random.getstate() == state
    second = generator.generate(1234, 9, difficulty="medium", n_blobs=5)
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_self_check_rejects_targeted_impostors():
    tied_sizes = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 0, 2, 2, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 3, 3, 3, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]
    repeated_color = [row[:] for row in tied_sizes]
    repeated_color[1][4] = 1
    repeated_color[1][5] = 1
    touching_colors = [row[:] for row in tied_sizes]
    touching_colors[1][3] = 4
    invalid_color = [row[:] for row in tied_sizes]
    invalid_color[5][5] = 10
    too_few = [[0] * 7 for _ in range(7)]
    too_few[2][2] = 1

    assert any("pairwise distinct" in error for error in generator.self_check(tied_sizes))
    assert any("exactly one object" in error for error in generator.self_check(repeated_color))
    assert any("must not touch" in error for error in generator.self_check(touching_colors))
    assert any("integer color" in error for error in generator.self_check(invalid_color))
    assert any("2..6 objects" in error for error in generator.self_check(too_few))


def test_generated_lessons_require_area_reasoning():
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(30):
            grid = generator.generate(seed, seed % 7, difficulty=difficulty)
            assert generator.self_check(grid) == []
            analysis = generator._analysis(grid)
            output = generator.rule_mirror(grid)[0]
            assert output != sorted(component["color"] for component in analysis["components"])
            assert output != [component["color"] for component in analysis["components"]]
