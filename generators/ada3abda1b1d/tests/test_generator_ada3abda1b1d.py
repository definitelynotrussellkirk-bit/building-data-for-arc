from __future__ import annotations

import copy
import importlib
import random

import pytest


MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.ada3abda1b1d.generator"
)

CANONICAL = [
    (
        [
            [1, 0, 0, 2, 3, 0, 0],
            [0, 0, 0, 2, 0, 0, 3],
            [0, 4, 0, 0, 5, 0, 0],
            [0, 0, 0, 0, 5, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ],
        [
            [0, 0, 0, 2, 3, 0, 0],
            [0, 0, 0, 2, 0, 0, 3],
            [0, 0, 0, 0, 5, 0, 0],
            [0, 0, 0, 0, 5, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ],
    ),
    (
        [
            [1, 1, 2, 2, 3, 3, 0],
            [1, 0, 0, 2, 0, 0, 0],
            [0, 0, 4, 4, 4, 4, 0],
            [0, 0, 0, 5, 0, 0, 5],
            [0, 0, 0, 0, 0, 0, 0],
        ],
        [
            [0, 0, 0, 0, 3, 3, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 5, 0, 0, 5],
            [0, 0, 0, 0, 0, 0, 0],
        ],
    ),
    (
        [
            [7, 0, 0, 0, 8, 0, 0],
            [0, 7, 0, 0, 8, 0, 0],
            [0, 0, 9, 9, 9, 0, 0],
            [0, 0, 0, 6, 0, 0, 6],
            [0, 0, 0, 0, 0, 0, 0],
        ],
        [
            [7, 0, 0, 0, 8, 0, 0],
            [0, 7, 0, 0, 8, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 6, 0, 0, 6],
            [0, 0, 0, 0, 0, 0, 0],
        ],
    ),
]


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": MODULE.rule_mirror(grid)}


def test_rule_hash_and_canonical_pairs():
    assert MODULE.RULE_HASH == "761b29fec54a"
    for input_grid, output_grid in CANONICAL:
        assert MODULE.self_check(input_grid) == []
        assert MODULE.strict_canonical_like(input_grid) == []
        assert MODULE.rule_mirror(input_grid) == output_grid


def test_declared_override_boundaries_are_exact_and_observable():
    cases = [
        {
            "grid_h": 4,
            "grid_w": 5,
            "n_colors": 4,
            "pair_colors": 1,
            "count_profile": "singletons",
        },
        {
            "grid_h": 12,
            "grid_w": 16,
            "n_colors": 6,
            "pair_colors": 3,
            "count_profile": "canonical_mixed",
        },
        {
            "grid_h": 5,
            "grid_w": 7,
            "n_colors": 4,
            "pair_colors": 3,
            "count_profile": "triples",
        },
    ]
    for difficulty in ("easy", "medium", "hard"):
        for index, overrides in enumerate(cases):
            grid = MODULE.generate(91 + index, 17 + index, difficulty=difficulty, **overrides)
            assert MODULE.observe_overrides(grid) == overrides
            assert MODULE.self_check(grid) == []


def test_unknown_and_invalid_overrides_fail_loudly():
    with pytest.raises(TypeError, match="unknown override"):
        MODULE.generate(0, 0, mystery_axis=1)
    with pytest.raises(ValueError, match="grid_h"):
        MODULE.generate(0, 0, grid_h=3)
    with pytest.raises(ValueError, match="count_profile"):
        MODULE.generate(0, 0, count_profile="all_pairs")


def test_replay_freshness_and_global_rng_purity():
    random.seed(12345)
    before = random.getstate()
    first = MODULE.generate(17, 29, difficulty="hard")
    after = random.getstate()
    second = MODULE.generate(17, 29, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    first[0][0] = 99
    assert second[0][0] != 99


def test_three_consecutive_slots_cover_all_decisive_profiles():
    for start in range(36):
        profiles = {
            MODULE.observe_overrides(MODULE.generate(7, start + offset))["count_profile"]
            for offset in range(3)
        }
        assert profiles == set(MODULE.COUNT_PROFILES)


def test_lesson_identifiable_rejects_named_rivals():
    demos = [_pair(MODULE.generate(33, index, difficulty="medium")) for index in range(3)]
    query = _pair(MODULE.generate(33, 3, difficulty="medium"))
    assert MODULE.lesson_identifiable(demos, query) == []


def test_self_check_rejects_targeted_impostors():
    lawful = MODULE.generate(
        4,
        5,
        grid_h=5,
        grid_w=7,
        n_colors=4,
        pair_colors=2,
        count_profile="triples",
    )

    ragged = copy.deepcopy(lawful)
    ragged[0].pop()
    assert MODULE.self_check(ragged)

    no_pair = [[0] * 7 for _ in range(5)]
    for col, color in enumerate((1, 2, 3, 4)):
        no_pair[0][col] = color
    assert any("exactly-twice" in reason for reason in MODULE.self_check(no_pair))

    all_pairs = [[0] * 7 for _ in range(5)]
    for color, cells in enumerate((((0, 0), (1, 0)), ((0, 2), (1, 2)), ((0, 4), (1, 4)), ((0, 6), (1, 6))), 1):
        for row, col in cells:
            all_pairs[row][col] = color
    assert any("distractor" in reason for reason in MODULE.self_check(all_pairs))

    illegal_count = copy.deepcopy(lawful)
    counts = MODULE._grid_counts(illegal_count)
    distractor = next(color for color, count in counts.items() if count == 3)
    zeros = [
        (row, col)
        for row, values in enumerate(illegal_count)
        for col, value in enumerate(values)
        if value == 0
    ]
    for row, col in zeros[:3]:
        illegal_count[row][col] = distractor
    assert any("distractor counts" in reason for reason in MODULE.self_check(illegal_count))

    invalid_color = copy.deepcopy(lawful)
    invalid_color[0][0] = 10
    assert any("ARC colors" in reason for reason in MODULE.self_check(invalid_color))


def test_singleton_profile_accepts_a_count_five_boundary_distractor():
    grid = [
        [1, 1, 0, 0, 0, 0, 0],
        [2, 2, 0, 0, 0, 0, 0],
        [3, 0, 0, 0, 0, 0, 0],
        [4, 4, 4, 4, 4, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]
    assert MODULE.self_check(grid) == []
    assert MODULE.observe_overrides(grid) == {
        "grid_h": 5,
        "grid_w": 7,
        "n_colors": 4,
        "pair_colors": 2,
        "count_profile": "singletons",
    }
    assert MODULE.rule_mirror(grid) == [
        [1, 1, 0, 0, 0, 0, 0],
        [2, 2, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_three_consecutive_default_samples_cover_count_five_boundary(difficulty):
    for seed in (0, 17):
        samples = [
            MODULE.generate(seed, sample_index, difficulty=difficulty)
            for sample_index in range(26)
        ]
        for start in range(24):
            window = samples[start : start + 3]
            assert any(
                5 in MODULE._grid_counts(grid).values()
                for grid in window
            ), (difficulty, seed, start)


def test_count_five_permissive_rival_is_declared_and_rejected():
    rival = MODULE.SEMANTIC_RIVALS["keep_two_or_five_plus"]
    for start in range(24):
        demos = [
            _pair(MODULE.generate(33, start + offset, difficulty="medium"))
            for offset in range(3)
        ]
        query = _pair(MODULE.generate(33, start + 3, difficulty="medium"))
        assert any(rival(pair["input"]) != pair["output"] for pair in demos)
        assert MODULE.lesson_identifiable(demos, query) == []


def test_exact_canonical_anchor_slots_are_preserved():
    expected = {
        0: (1, 1, 2, 2, 2),
        4: (2, 2, 2, 3),
        8: (2, 2, 3, 3, 4),
    }
    for difficulty in (None, "easy", "medium", "hard"):
        for sample_index, signature in expected.items():
            grid = MODULE.generate(71, sample_index, difficulty=difficulty)
            assert MODULE.strict_canonical_like(grid) == []
            assert tuple(sorted(MODULE._grid_counts(grid).values())) == signature

@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_every_rotation_of_four_default_pairs_rejects_all_named_rivals(difficulty):
    for seed in (0, 17):
        samples = [
            _pair(MODULE.generate(seed, sample_index, difficulty=difficulty))
            for sample_index in range(27)
        ]
        for start in range(24):
            lesson = samples[start : start + 4]
            for query_offset in range(4):
                demos = [
                    pair
                    for offset, pair in enumerate(lesson)
                    if offset != query_offset
                ]
                query = lesson[query_offset]
                for name, rival in MODULE.LESSON_COMPETITORS.items():
                    assert any(
                        rival(pair["input"]) != pair["output"]
                        for pair in demos
                    ), (difficulty, seed, start, query_offset, name)
                assert MODULE.lesson_identifiable(demos, query) == []
