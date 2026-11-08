"""Regression and teaching-contract tests for e91a8e375e64."""
from __future__ import annotations

from copy import deepcopy
import random
import sys
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    freeze,
    intended_output,
    load_generator,
    observed,
    profile,
    recolor_only_output,
    transform_only_output,
    unchanged_query_output,
)

gen = load_generator()


def pair(seed: int, sample_index: int, band: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": intended_output(grid)}


@pytest.mark.parametrize(
    "canonical",
    canonical_pairs(),
    ids=lambda item: f"{item['split']}{item['pair_index']}",
)
def test_authority_pin_accepts_canonical_inputs_and_independent_oracle_matches(canonical):
    assert gen.RULE_HASH == "af51be6e4b66"
    assert gen.self_check(canonical["input"]) == []
    assert intended_output(canonical["input"]) == canonical["output"]
    assert gen.rule_mirror(canonical["input"]) == canonical["output"]


def test_public_axis_surface_contains_only_exactly_observable_controls():
    assert set(gen.AXES) == {"panel_size", "n_map"}
    assert gen.HELPFUL_TEXTURES == ()
    assert gen.DEGENERATE_TEXTURES == ()


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("panel_size", [3, 4, 5])
@pytest.mark.parametrize("n_map", [2, 3, 4])
def test_every_declared_override_combination_round_trips_in_every_band(band, panel_size, n_map):
    requested = {"panel_size": panel_size, "n_map": n_map}
    grid = gen.generate(1729, 23, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert observed(grid) == requested
    assert gen.observe_overrides(grid) == requested
    assert intended_output(grid) == gen.rule_mirror(grid)


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("density", "low"),
        ("texture", "varied"),
        ("panel_size", 2),
        ("panel_size", 6),
        ("panel_size", True),
        ("panel_size", 4.0),
        ("panel_size", "4"),
        ("n_map", 1),
        ("n_map", 5),
        ("n_map", False),
        ("n_map", 3.0),
        ("n_map", "3"),
    ],
)
def test_unknown_obsolete_or_invalid_overrides_fail_loudly(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("bad_seed", [True, 1.5, "1", None])
def test_seed_must_be_an_exact_integer(bad_seed):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_index", [True, 1.5, "1", None, -1])
def test_sample_index_must_be_a_nonnegative_exact_integer(bad_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, bad_index)


@pytest.mark.parametrize("bad_band", ["", "expert", 1, False])
def test_unknown_difficulty_fails_loudly(bad_band):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty=bad_band)


def _component_count(grid):
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0}
    count = 0
    while remaining:
        start = remaining.pop()
        color = grid[start[0]][start[1]]
        stack = [start]
        while stack:
            row, col = stack.pop()
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in remaining and grid[neighbor[0]][neighbor[1]] == color:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        count += 1
    return count


def test_canonical_schedule_overlaps_public_connected_component_grammar():
    canonical_counts = {_component_count(item["input"]) for item in canonical_pairs()}
    assert canonical_counts == {18, 19}
    generated_counts = {
        _component_count(gen.generate(seed, 0, difficulty=band))
        for band in ("easy", "medium", "hard")
        for seed in range(8)
    }
    assert generated_counts & canonical_counts


def test_internal_schedule_replaces_unobservable_texture_knobs_with_real_profiles():
    assert gen.SCHEDULE_PROFILES == ("canonical", "varied", "wide_map", "big_panel")
    assert gen.schedule_profile(0, 0, "easy") == "canonical"
    assert gen.schedule_profile(0, 1, "easy") == "varied"
    assert gen.schedule_profile(0, 2, "easy") == "wide_map"
    assert gen.schedule_profile(0, 3, "easy") == "big_panel"
    assert observed(gen.generate(0, 0, difficulty="hard")) == {"panel_size": 4, "n_map": 2}
    assert observed(gen.generate(0, 2, difficulty="easy"))["n_map"] == 4
    assert observed(gen.generate(0, 3, difficulty="easy"))["panel_size"] == 5


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_is_valid_diverse_and_canonical_anchored(band):
    profiles = set()
    observations = set()
    examples = set()
    canonical_hits = 0
    for sample_index in range(80):
        grid = gen.generate(9100 + sample_index, sample_index, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(9100 + sample_index, sample_index, difficulty=band)
        assert intended_output(grid) == gen.rule_mirror(grid)
        profiles.add(profile(grid))
        observations.add(tuple(sorted(observed(grid).items())))
        examples.add(freeze(grid))
        canonical_hits += profile(grid) == (4, 24, 6)
    assert canonical_hits >= 20
    assert {2, 3, 4} <= {dict(item)["n_map"] for item in observations}
    assert 4 in {dict(item)["panel_size"] for item in observations}
    assert 5 in {dict(item)["panel_size"] for item in observations}
    assert len(profiles) >= 3
    assert len(examples) >= 78


def test_global_random_state_is_not_consumed():
    random.seed(445566)
    expected = [random.random() for _ in range(6)]
    random.seed(445566)
    gen.generate(77, 9, difficulty="medium")
    actual = [random.random() for _ in range(6)]
    assert actual == expected


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_generated_example_visibly_requires_both_operations(band):
    for sample_index in range(32):
        grid = gen.generate(7000 + sample_index, sample_index, difficulty=band)
        authority = intended_output(grid)
        assert recolor_only_output(grid) != authority
        assert transform_only_output(grid) != authority
        assert unchanged_query_output(grid) != authority
        assert gen.SEMANTIC_RIVALS["recolor_only"](grid) == recolor_only_output(grid)
        assert gen.SEMANTIC_RIVALS["transform_only"](grid) == transform_only_output(grid)
        assert gen.SEMANTIC_RIVALS["unchanged_query"](grid) == unchanged_query_output(grid)
        assert all(witness(grid) for witness in gen.SEMANTIC_WITNESSES.values())


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_four_example_window_survives_all_query_rotations(band):
    for start in range(12):
        examples = [pair(88000 + start, start + offset, band) for offset in range(4)]
        for query_index in range(4):
            query = examples[query_index]
            demos = [example for index, example in enumerate(examples) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == []
            for rival in gen.LESSON_COMPETITORS.values():
                assert any(rival(item["input"]) != item["output"] for item in demos)


@pytest.mark.parametrize(
    "mutation",
    ["separator", "transform_pair", "mapping_support", "mapping_identity", "unknown_query_color"],
)
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(55, 4, panel_size=4, n_map=3)
    changed = deepcopy(grid)
    side = len(changed)
    if mutation == "separator":
        changed[0][side] = 0
    elif mutation == "transform_pair":
        changed[0][side + 1] = (changed[0][side + 1] + 1) % 10
    elif mutation == "mapping_support":
        c_left = 2 * (side + 1)
        d_left = 3 * (side + 1)
        for row in range(side):
            for col in range(side):
                if changed[row][c_left + col] != 0:
                    changed[row][d_left + col] = 0
                    break
            else:
                continue
            break
    elif mutation == "mapping_identity":
        c_left = 2 * (side + 1)
        d_left = 3 * (side + 1)
        source = next(
            changed[row][c_left + col]
            for row in range(side)
            for col in range(side)
            if changed[row][c_left + col] != 0
        )
        for row in range(side):
            for col in range(side):
                if changed[row][c_left + col] == source:
                    changed[row][d_left + col] = source
    else:
        q_left = 4 * (side + 1)
        changed[0][q_left] = 9
    assert gen.self_check(changed)


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True] * 24 for _ in range(4)]])
def test_malformed_grid_is_diagnostic_not_exception(bad):
    assert gen.self_check(bad)
