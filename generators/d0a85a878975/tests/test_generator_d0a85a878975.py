from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.per_puzzle.d0a85a878975 import generator as gen
from scripts.canonical_profile_gate import canonical_inputs, canonical_pairs


def _generated(profile: int = 0, *, band: str = "medium"):
    return gen.generate(20260725, profile, difficulty=band)


def test_all_canonical_inputs_and_outputs_are_owned() -> None:
    inputs = canonical_inputs(gen.TASK_ID)
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(inputs) == 8
    assert len(pairs) == 8
    assert all(gen.self_check(grid) == [] for grid in inputs)
    assert all(gen.strict_canonical_like(grid) == [] for grid in inputs)
    assert all(gen.expected_output(pair["input"]) == pair["output"] for pair in pairs)


def test_six_profile_schedule_covers_every_semantic_branch_per_band() -> None:
    for band in ("easy", "medium", "hard"):
        grids = [_generated(index, band=band) for index in range(6)]
        assert [gen.schedule_profile(999, index, band) for index in range(6)] == list(range(6))
        assert all(gen.self_check(grid) == [] for grid in grids)
        for name, witness in gen.SEMANTIC_WITNESSES.items():
            assert any(witness(grid) for grid in grids), (band, name)
        assert sum(gen.strict_canonical_like(grid) == [] for grid in grids) == 4


def test_every_public_axis_is_exactly_observable_at_boundaries() -> None:
    cases = [
        {
            "grid_h": 20,
            "grid_w": 20,
            "n_sizes": 2,
            "size_start": 2,
            "smallest_drop": False,
            "noise_mode": "distinct",
        },
        {
            "grid_h": 30,
            "grid_w": 30,
            "n_sizes": 4,
            "size_start": 3,
            "smallest_drop": True,
            "noise_mode": "same_color",
        },
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(901 + index, index, difficulty="hard", **overrides)
        assert gen.observe_overrides(grid) == overrides
        assert gen.self_check(grid) == []
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, mystery_axis=3)


def test_same_color_noise_refutes_raw_area_counting() -> None:
    grid = _generated(4)
    analysis = gen._scene_analysis(grid)
    assert analysis["noise_mode"] == "same_color"
    assert analysis["shared_noise_colors"]
    assert gen.expected_output(grid) != gen.rival_raw_color_area_counts(grid)


def test_conditional_smallest_key_is_not_an_unconditional_decrement() -> None:
    drop_grid = _generated(0)
    keep_grid = _generated(2)
    assert gen._scene_analysis(drop_grid)["smallest_drop"] is True
    assert gen.expected_output(drop_grid) != gen.rival_never_drop_smallest(drop_grid)
    assert gen._scene_analysis(keep_grid)["smallest_drop"] is False
    assert gen.expected_output(keep_grid) != gen.rival_always_drop_smallest(keep_grid)


def test_six_sequential_demos_refute_all_named_competitors() -> None:
    demos = []
    for index in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(77, index, difficulty="medium")
        demos.append({"input": grid, "output": gen.expected_output(grid)})
    query_grid = gen.generate(77, gen.EXAMPLES_NEEDED, difficulty="medium")
    query = {"input": query_grid, "output": gen.expected_output(query_grid)}
    assert gen.lesson_identifiable(demos, query) == []
    for name, competitor in gen.LESSON_COMPETITORS.items():
        assert any(competitor(pair["input"]) != pair["output"] for pair in demos), name


def test_self_check_rejects_four_targeted_impostors() -> None:
    base = _generated(0)
    analysis = gen._scene_analysis(base)
    bg = analysis["background"]

    no_noise = copy.deepcopy(base)
    for item in analysis["noise"]:
        for r, c in item["cells"]:
            no_noise[r][c] = bg
    assert any("distractor" in reason for reason in gen.self_check(no_noise))

    two_colors_one_size = copy.deepcopy(base)
    first_square = next(item for item in analysis["squares"] if item["side"] == 2)
    unused = next(color for color in range(10) if color not in analysis["palette"])
    for r, c in first_square["cells"]:
        two_colors_one_size[r][c] = unused
    assert any("exactly one color" in reason for reason in gen.self_check(two_colors_one_size))

    one_color_two_sizes = copy.deepcopy(base)
    size2_color = analysis["color_by_size"][2]
    size3_square = next(item for item in analysis["squares"] if item["side"] == 3)
    for r, c in size3_square["cells"]:
        one_color_two_sizes[r][c] = size2_color
    assert any("exactly one size" in reason for reason in gen.self_check(one_color_two_sizes))

    one_size_only = copy.deepcopy(base)
    for item in analysis["squares"]:
        if item["side"] != 2:
            for r, c in item["cells"]:
                one_size_only[r][c] = bg
    assert any("at least two" in reason for reason in gen.self_check(one_size_only))


def test_generation_is_deterministic_fresh_and_global_rng_pure() -> None:
    before = random.getstate()
    first = gen.generate(987654, 5, difficulty="hard")
    after = random.getstate()
    second = gen.generate(987654, 5, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    original = second[0][0]
    first[0][0] = (first[0][0] + 1) % 10
    assert second[0][0] == original
