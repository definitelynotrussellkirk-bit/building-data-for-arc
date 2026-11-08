"""Behavioral regressions; expected labels use the independently validated oracle."""
from copy import deepcopy

import pytest


def lawful_fixture():
    grid = [[0] * 10 for _ in range(8)]
    grid[2][2] = grid[2][3] = grid[3][2] = 3
    grid[0][0], grid[1][1] = 2, 1
    return grid


def test_independent_oracle_reproduces_all_canonical_labels(oracle, pairs):
    assert len(pairs) == 5
    for pair in pairs:
        assert oracle.solve(pair["input"]) == pair["output"]


def test_validator_accepts_all_canonical_inputs_including_clipped_blank(generator, pairs):
    for pair in pairs:
        assert not generator.self_check(pair["input"])


@pytest.mark.parametrize("mutation", ["missing_one", "missing_two", "no_green", "singleton_green", "tied_green", "duplicate_one", "duplicate_two", "no_background"])
def test_validator_rejects_marker_green_and_tie_impostors(generator, mutation):
    grid = lawful_fixture()
    if mutation == "missing_one": grid[1][1] = 0
    elif mutation == "missing_two": grid[0][0] = 0
    elif mutation == "no_green":
        grid = [[0 if v == 3 else v for v in row] for row in grid]
    elif mutation == "singleton_green": grid[2][3] = grid[3][2] = 0
    elif mutation == "tied_green":
        grid[5][6] = grid[5][7] = grid[6][6] = 3
    elif mutation == "duplicate_one": grid[7][9] = 1
    elif mutation == "duplicate_two": grid[7][9] = 2
    elif mutation == "no_background":
        grid = [[4 if v == 0 else v for v in row] for row in grid]
    assert generator.self_check(grid), mutation


@pytest.mark.parametrize("grid", [None, [], [[]], [None], [[0, 0], [0]], [[True]], [[1.0]], [["3"]], [[-1]], [[10]]])
def test_validator_rejects_malformed_pixel_domain_even_with_metadata(generator, grid):
    assert generator.self_check(grid, meta={"texture": "missing_marker"})


def test_validator_allows_foreign_colors_marker_contact_and_smaller_green(generator):
    grid = lawful_fixture()
    grid[1][1] = 0
    grid[2][4] = 1  # marker touches the selected green component
    grid[7][9] = 3
    grid[6][0] = grid[6][1] = 6
    assert not generator.self_check(grid)


@pytest.mark.parametrize("kwargs", [
    {"grid_h": True}, {"grid_h": 8.0}, {"grid_h": "8"}, {"grid_h": 7}, {"grid_h": 17},
    {"grid_w": False}, {"grid_w": 10.0}, {"grid_w": "10"}, {"grid_w": 9}, {"grid_w": 19},
    {"blob_size": True}, {"blob_size": 3.0}, {"blob_size": "3"}, {"blob_size": 2}, {"blob_size": 10},
    {"palette_kind": "default"}, {"texture": "missing_marker"}, {"density": "sparse"},
    {"position_bias": "blob_plus_two_markers"}, {"palette_size": 3}, {"n_distinct_colors": 3}, {"unknown": 1},
])
def test_invalid_and_obsolete_overrides_fail_explicitly(generator, kwargs):
    with pytest.raises((ValueError, TypeError)):
        generator.generate(11, 0, **kwargs)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("h,w,n", [(8, 10, 3), (8, 18, 9), (16, 10, 9), (16, 18, 3), (12, 14, 6)])
def test_cross_band_joint_controls_are_exact_observable(generator, oracle, band, h, w, n):
    kwargs = dict(grid_h=h, grid_w=w, blob_size=n)
    for index in range(4):
        grid = generator.generate(17, index, difficulty=band, **kwargs)
        scene = oracle.facts(grid)
        assert (scene["h"], scene["w"], len(scene["main"])) == (h, w, n)
        assert not generator.self_check(grid)
        observed = generator.observe_overrides(grid)
        assert {axis: observed[axis] for axis in kwargs} == kwargs


def test_none_controls_are_omission_and_replay_returns_fresh_pixels(generator):
    for index in range(4):
        baseline = generator.generate(23, index, difficulty="medium")
        for axis in ("grid_h", "grid_w", "blob_size"):
            assert generator.generate(23, index, difficulty="medium", **{axis: None}) == baseline
        second = generator.generate(23, index, difficulty="medium", grid_h=None, grid_w=None, blob_size=None)
        assert second == baseline and second is not baseline
        assert all(a is not b for a, b in zip(baseline, second))


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_full_contrast_phase_refutes_wrong_object_and_vector_selectors(generator, oracle, band):
    object_rivals = ("all_green", "eight_connected_green", "first_green", "last_green", "largest_nonmarker", "all_nonmarker")
    for seed in (0, 7):
        for index in (0,):
            grid = generator.generate(seed, index, difficulty=band)
            scene = oracle.facts(grid)
            assert len(scene["visible"]) == len(scene["main"])
            expected = oracle.solve(grid)
            for selection in object_rivals:
                assert oracle.predict(grid, selection=selection) != expected, (seed, index, selection)
            if index == 0:
                for vector in ("absolute", "fixed_absolute_3_4", "fixed_signed_3_4", "swapped"):
                    assert oracle.predict(grid, vector=vector) != expected, (seed, index, vector)


@pytest.mark.parametrize("seed", [148, 182])
def test_axis_aligned_phase_zero_is_not_the_signed_fixed_step(generator, oracle, seed):
    grid = generator.generate(seed, 0, difficulty="medium")
    assert oracle.predict(grid, vector="fixed_signed_3_4") != oracle.solve(grid), (seed, oracle.facts(grid)["delta"])


def test_phase_zero_fixed_step_role_is_separated_over_bounded_seed_population(generator, oracle):
    for seed in range(256):
        for band in ("easy", "medium", "hard"):
            grid = generator.generate(seed, 0, difficulty=band)
            assert oracle.predict(grid, vector="fixed_signed_3_4") != oracle.solve(grid), (seed, band, oracle.facts(grid)["delta"])


def test_default_population_exercises_clipping_and_signed_directions(generator, oracle):
    directions, output_profiles = set(), set()
    for seed in range(32):
        for index in range(4):
            grid = generator.generate(seed, index, difficulty="medium")
            scene = oracle.facts(grid)
            dr, dc = scene["delta"]
            directions.add(((dr > 0)-(dr < 0), (dc > 0)-(dc < 0)))
            size, visible = len(scene["main"]), len(scene["visible"])
            profile = "blank" if not visible else "full" if visible == size else "partial"
            output_profiles.add(profile)
            assert profile == ("full", "full", "partial", "blank")[index]
    assert output_profiles == {"full", "partial", "blank"}
    assert directions == {(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc}


def test_every_joint_axis_combination_is_constructive_in_each_phase(generator, oracle):
    for h in range(8, 17):
        for w in range(10, 19):
            for n in range(3, 10):
                for index in range(4):
                    band = ("easy", "medium", "hard")[index % 3]
                    grid = generator.generate(29, index, difficulty=band, grid_h=h, grid_w=w, blob_size=n)
                    scene = oracle.facts(grid)
                    assert (scene["h"], scene["w"], len(scene["main"])) == (h, w, n)
                    assert not generator.self_check(grid)


def test_two_cell_unique_green_component_is_lawful(generator):
    grid = lawful_fixture()
    grid[3][2] = 0
    assert not generator.self_check(grid)


@pytest.mark.parametrize("rows,expected_rows,separators", [
    (
        ["21000000", "00000000", "00300000", "00330000", "00003000", "00000000", "00000000", "00000000"],
        ["00000000", "00000000", "00080000", "00088000", "00000000", "00000000", "00000000", "00000000"],
        ["all_green", "eight_connected_green", "all_nonmarker"],
    ),
    (
        ["21000000", "07700030", "07700000", "00300000", "00330000", "00000000", "00000000", "00000000"],
        ["00000000", "00000000", "00000000", "00080000", "00088000", "00000000", "00000000", "00000000"],
        ["all_green", "first_green", "largest_nonmarker", "all_nonmarker"],
    ),
])
def test_racket_verified_semantic_separator_fixtures(generator, oracle, rows, expected_rows, separators):
    # Explicit portable copies of the two independently authored fixtures whose
    # labels were verified by canonical Racket apply (rule fc4e32aa0363).
    # No outside evidence path is read during test execution.
    grid = [[int(v) for v in row] for row in rows]
    expected = [[int(v) for v in row] for row in expected_rows]
    assert not generator.self_check(grid)
    assert oracle.solve(grid) == expected
    for selection in separators:
        assert oracle.predict(grid, selection=selection) != expected


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_eight_demo_lessons_and_each_single_holdout_separate_declared_rivals(generator, oracle, band):
    required = {"all_green", "green8", "first_green", "last_green", "largest_nonmarker", "all_nonmarker",
                "non_singleton_green", "fixed_step_3_4", "absolute_vector", "reverse_vector",
                "swap_components", "wrap_translation", "avoid_clipping", "no_recolor"}
    assert required <= set(generator.LESSON_COMPETITORS)
    for seed in (0, 11):
        for start in range(4):
            grids = [generator.generate(seed, index, difficulty=band) for index in range(start, start + 9)]
            answers = [oracle.solve(grid) for grid in grids]
            for name, rival in generator.LESSON_COMPETITORS.items():
                wrong = [i for i, (grid, answer) in enumerate(zip(grids, answers)) if rival(deepcopy(grid)) != answer]
                assert not wrong or len(wrong) >= 2, (seed, start, name, wrong)
            for query_position in range(9):
                demos = [{"input": grid, "output": answer} for i, (grid, answer) in enumerate(zip(grids, answers)) if i != query_position]
                query = {"input": grids[query_position], "output": answers[query_position]}
                assert not generator.lesson_identifiable(demos, query), (seed, start, query_position)


def test_public_curriculum_budget_and_schedule_hook_repeat_four_in_every_band(generator):
    assert generator.EXAMPLES_NEEDED == 8
    assert generator.LESSON_SCHEDULE_PERIOD == 4
    for band in ("easy", "medium", "hard"):
        for seed in (0, 11):
            period = [generator.schedule_profile(seed, index, difficulty=band) for index in range(4)]
            assert len(set(period)) == 4
            for index in range(4, 12):
                assert generator.schedule_profile(seed, index, difficulty=band) == period[index % 4]
