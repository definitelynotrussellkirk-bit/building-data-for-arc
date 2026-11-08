from __future__ import annotations

import copy
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash
from puzzle_generators.per_puzzle.bb435f29015f import generator as gen


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs_are_exact():
    assert gen.RULE_HASH == canonical_rule_hash(gen.TASK_ID) == "7ced211440aa"
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_generation_is_deterministic_fresh_and_global_rng_pure(difficulty):
    random.seed(99173)
    before = random.getstate()
    first = gen.generate(271828, 314, difficulty=difficulty)
    middle = random.getstate()
    second = gen.generate(271828, 314, difficulty=difficulty)
    after = random.getstate()

    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == middle == after
    assert gen.self_check(first, difficulty=difficulty) == []
    assert gen.rule_mirror(first) != first


def test_unknown_and_invalid_overrides_are_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, misspelled_axis=7)
    with pytest.raises(ValueError):
        gen.generate(1, 2, grid_h=6)
    with pytest.raises(ValueError):
        gen.generate(1, 2, grid_w=15)
    with pytest.raises(ValueError):
        gen.generate(1, 2, n_objs=4)
    with pytest.raises(ValueError):
        gen.generate(1, 2, color_family="mixed")
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 2, difficulty="extreme")


@pytest.mark.parametrize(
    ("axis", "values"),
    [
        ("grid_h", (7, 14)),
        ("grid_w", (7, 14)),
        ("n_objs", (2, 3)),
        ("color_family", ("low", "mid", "high")),
    ],
)
def test_every_axis_boundary_is_exact_and_observable(axis, values):
    for difficulty in ("easy", "medium", "hard"):
        for value in values:
            for seed in range(6):
                grid = gen.generate(
                    8000 + seed,
                    29 * seed + 3,
                    difficulty=difficulty,
                    **{axis: value},
                )
                assert gen.observe_overrides(grid)[axis] == value
                assert gen.self_check(
                    grid,
                    difficulty=difficulty,
                    meta={"overrides": {axis: value}},
                ) == []


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_four_profile_schedule_contains_the_required_counterexamples(difficulty):
    samples = {
        gen.schedule_profile(71, index, difficulty): gen.generate(
            71, index, difficulty=difficulty
        )
        for index in range(4)
    }
    assert gen.strict_canonical_like(samples["canonical_anchor"]) == []
    assert gen.SEMANTIC_WITNESSES["first_scan_decoy"](
        samples["bbox_and_position_decoy"]
    )
    assert gen.SEMANTIC_WITNESSES["larger_bbox_decoy"](
        samples["bbox_and_position_decoy"]
    )
    assert gen.SEMANTIC_WITNESSES["modal_colour_decoy"](
        samples["modal_colour_decoy"]
    )
    assert gen.SEMANTIC_WITNESSES["close_size_gap"](
        samples["close_gap_decoy"]
    )
    assert gen.strict_canonical_like(samples["close_gap_decoy"]) == []


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_sliding_four_demo_window_identifies_the_rule(difficulty):
    for start in range(12):
        seed = 41000 + start
        demos = [
            _pair(gen.generate(seed, start + offset, difficulty=difficulty))
            for offset in range(gen.EXAMPLES_NEEDED)
        ]
        query = _pair(
            gen.generate(
                seed,
                start + gen.EXAMPLES_NEEDED,
                difficulty=difficulty,
            )
        )
        assert gen.lesson_identifiable(demos, query) == []
        for competitor in gen.LESSON_COMPETITORS.values():
            assert not all(
                competitor(pair["input"]) == pair["output"] for pair in demos
            )


def test_self_check_rejects_targeted_impostors():
    all_background = [[0] * 7 for _ in range(7)]

    single_object = [[0] * 7 for _ in range(7)]
    for r, c in ((1, 1), (1, 2), (1, 3), (2, 2), (3, 2)):
        single_object[r][c] = 4

    tied_largest = [[0] * 7 for _ in range(7)]
    for r, c in ((0, 0), (0, 1), (1, 0), (1, 1)):
        tied_largest[r][c] = 2
    for r, c in ((5, 5), (5, 6), (6, 5), (6, 6)):
        tied_largest[r][c] = 7

    touching_objects = [[0] * 7 for _ in range(7)]
    for r, c in ((1, 1), (1, 2), (2, 1), (2, 2), (3, 1)):
        touching_objects[r][c] = 3
    for r, c in ((3, 2), (3, 3), (4, 3), (4, 4)):
        touching_objects[r][c] = 8

    one_cell_noise = [[0] * 7 for _ in range(7)]
    for r, c in ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)):
        one_cell_noise[r][c] = 5
    for r, c in ((4, 0), (4, 1), (5, 0), (5, 1)):
        one_cell_noise[r][c] = 2
    one_cell_noise[6][6] = 9

    fixtures = {
        "all_background": all_background,
        "single_object": single_object,
        "tied_largest": tied_largest,
        "touching_objects": touching_objects,
        "one_cell_noise": one_cell_noise,
    }
    for name, grid in fixtures.items():
        assert gen.self_check(grid), name
