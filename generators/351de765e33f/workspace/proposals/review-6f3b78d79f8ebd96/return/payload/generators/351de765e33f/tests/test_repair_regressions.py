from __future__ import annotations

import copy
import importlib
import itertools

import pytest


gen = importlib.import_module("puzzle_generators.per_puzzle.351de765e33f.generator")


CANONICAL_INPUTS = [
    [
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 2, 2, 0, 0, 0, 0, 0, 0],
        [0, 2, 2, 0, 0, 0, 3, 3, 0],
        [0, 0, 0, 0, 0, 0, 3, 3, 0],
        [0, 0, 0, 0, 4, 4, 4, 0, 0],
        [0, 0, 0, 0, 4, 4, 4, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ],
    [
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 2, 2, 0, 0, 0],
        [0, 0, 0, 0, 2, 2, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 3, 3, 0],
    ],
    [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 2, 2, 2, 0, 0, 0, 0, 0, 0],
        [0, 2, 2, 2, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 3, 3, 0, 0],
        [0, 0, 0, 0, 0, 0, 3, 3, 0, 0],
        [0, 0, 0, 0, 4, 4, 4, 4, 0, 0],
        [0, 0, 0, 0, 4, 4, 4, 4, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ],
]


def _outputs_differ(left, right):
    return left != right


def test_self_check_accepts_all_exact_canonical_inputs():
    assert [gen.self_check(grid) for grid in CANONICAL_INPUTS] == [[], [], []]


def test_canonical_shortcuts_fit_all_labeled_canonical_pairs():
    intended = [gen.rule_mirror(grid) for grid in CANONICAL_INPUTS]
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert [rival(grid) for grid in CANONICAL_INPUTS] == intended, name


@pytest.mark.parametrize("difficulty", [1.0, 0, True, "bogus", object()])
def test_invalid_difficulty_values_fail_closed(difficulty):
    with pytest.raises((TypeError, ValueError), match="difficulty"):
        gen.generate(1, 0, difficulty=difficulty)


@pytest.mark.parametrize("seed", [True, 1.0, "1", -1])
def test_invalid_seed_values_fail_closed(seed):
    with pytest.raises((TypeError, ValueError), match="seed"):
        gen.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, 1.0, "1", -1])
def test_invalid_sample_index_values_fail_closed(sample_index):
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        gen.generate(1, sample_index)


@pytest.mark.parametrize("profile", [True, 7, "unknown"])
def test_invalid_scene_profile_values_fail_closed(profile):
    with pytest.raises((TypeError, ValueError), match="scene_profile"):
        gen.generate(1, 0, scene_profile=profile)


def test_period_and_declared_semantic_contract_are_present():
    assert gen.LESSON_SCHEDULE_PERIOD == 8
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "second_largest_distinct_size",
        "colorblind_4_connected",
    }
    assert set(gen.LESSON_COMPETITORS) == {
        "second_largest_distinct_size",
        "colorblind_4_connected",
        "colorblind_8_connected",
    }
    assert gen.strict_canonical_like is gen.self_check


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("seed", [17, 48100, 99231])
def test_every_cyclic_five_demo_window_refutes_retained_shortcuts(band, seed):
    period = gen.LESSON_SCHEDULE_PERIOD
    grids = [gen.generate(seed, index, difficulty=band) for index in range(period * 2)]
    for start in range(period):
        demos = grids[start : start + 5]
        assert any(
            _outputs_differ(gen.rule_mirror(grid), gen._second_largest_distinct_size(grid))
            for grid in demos
        ), (band, seed, start, "distinct-size")
        assert any(
            _outputs_differ(gen.rule_mirror(grid), gen._colorblind_4_connected(grid))
            for grid in demos
        ), (band, seed, start, "colorblind-4")
        assert any(
            _outputs_differ(gen.rule_mirror(grid), gen._colorblind_8_connected(grid))
            for grid in demos
        ), (band, seed, start, "colorblind-8")


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_period_emits_all_profiles_and_all_contact_kinds(band):
    grids = [gen.generate(12345, index, difficulty=band) for index in range(8)]
    signatures = [gen.semantic_signature(grid) for grid in grids]
    assert {sig["scene_profile"] for sig in signatures} == set(gen.SCENE_PROFILES)
    assert {sig["contact_kind"] for sig in signatures} == {
        "separated",
        "diagonal_contact",
        "edge_contact",
    }


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_band_has_exact_public_profile_support_and_envelope_support(band):
    grids = [gen.generate(8200, index, difficulty=band) for index in range(20)]
    signatures = [gen.semantic_signature(grid) for grid in grids]
    exact = [sig for sig in signatures if sig["scene_profile"] in gen.PUBLIC_PROFILES]
    assert len(exact) >= 6
    canonical_dims = {
        "canonical_644": (8, 9),
        "canonical_942": (8, 9),
        "canonical_864": (9, 10),
    }
    assert all(
        (len(grid), len(grid[0])) == canonical_dims[sig["scene_profile"]]
        for grid, sig in zip(grids, signatures)
        if sig["scene_profile"] in gen.PUBLIC_PROFILES
    )


def test_edge_and_diagonal_witnesses_change_the_named_rivals():
    grids = [gen.generate(19001, index, difficulty="medium") for index in range(8)]
    by_kind = {gen.semantic_signature(grid)["contact_kind"]: grid for grid in grids}

    edge = by_kind["edge_contact"]
    assert gen.rule_mirror(edge) != gen._colorblind_4_connected(edge)
    assert gen.rule_mirror(edge) != gen._colorblind_8_connected(edge)

    diagonal = by_kind["diagonal_contact"]
    assert gen.rule_mirror(diagonal) == gen._colorblind_4_connected(diagonal)
    assert gen.rule_mirror(diagonal) != gen._colorblind_8_connected(diagonal)


def test_declared_rivals_are_pure_and_deterministic():
    grid = gen.generate(777, 0, difficulty="hard")
    frozen = copy.deepcopy(grid)
    for rival in gen.LESSON_COMPETITORS.values():
        first = rival(grid)
        second = rival(grid)
        assert first == second
        assert first is not second
        assert all(a is not b for a, b in zip(first, second))
        assert grid == frozen


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_stress_generation_preserves_profiles_contracts_and_freshness(band):
    for seed, index in itertools.product(range(12), range(8)):
        grid = gen.generate(seed, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid)["scene_profile"] in gen.SCENE_PROFILES
        assert gen.rule_mirror(grid) != grid
