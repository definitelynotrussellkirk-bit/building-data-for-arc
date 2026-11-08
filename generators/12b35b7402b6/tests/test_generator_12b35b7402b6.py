from __future__ import annotations

import copy
import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

ROOT = find_root(__file__)
TASK_ID = "12b35b7402b6"
gen, _, _ = load_selected_generator(TASK_ID, root=ROOT)


def _canonical_inputs():
    return [pair["input"] for pair in canonical_pairs(TASK_ID, root=ROOT)]


def test_rule_hash_and_all_canonical_inputs_are_lawful():
    assert gen.RULE_HASH == "cb01ed25524c"
    inputs = _canonical_inputs()
    assert len(inputs) == 3
    for grid in inputs:
        assert gen.self_check(grid) == []


def test_exact_overrides_make_scattered_count_distinct_from_span():
    grid = gen.generate(
        1701,
        0,
        difficulty="easy",
        grid_h=9,
        grid_w=12,
        marker_count=3,
        n_objects=3,
        marker_layout="scattered",
    )
    assert len(grid) == 9 and len(grid[0]) == 12
    assert gen.self_check(grid) == []
    facts = gen.semantic_observables(grid)
    assert facts["marker_count"] == 3
    assert facts["marker_span"] > facts["marker_count"]
    assert facts["n_objects"] == 3
    assert facts["matching_object_count"] == 1
    assert gen.observe_overrides(grid) == {
        "grid_h": 9,
        "grid_w": 12,
        "marker_count": 3,
        "n_objects": 3,
        "marker_layout": "scattered",
    }


def test_override_contract_is_strict_and_band_independent():
    exact = {
        "grid_h": 30,
        "grid_w": 30,
        "marker_count": 6,
        "n_objects": 4,
        "marker_layout": "scattered",
    }
    for difficulty in (None, "easy", "medium", "hard"):
        grid = gen.generate(91, 2, difficulty=difficulty, **exact)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == exact

    bad_calls = [
        {"unknown": 1},
        {"texture": "tied_match"},
        {"grid_h": True},
        {"grid_w": 31},
        {"marker_count": 1},
        {"marker_count": "3"},
        {"n_objects": 1},
        {"marker_layout": "left"},
    ]
    for kwargs in bad_calls:
        with pytest.raises((TypeError, ValueError)):
            gen.generate(1, 0, **kwargs)
    with pytest.raises(ValueError):
        gen.generate(1, 0, difficulty="legendary")


def test_default_sampler_is_lawful_varied_and_not_span_locked():
    layouts = set()
    target_ranks = set()
    shapes = set()
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(80):
            grid = gen.generate(seed, seed, difficulty=difficulty)
            assert gen.self_check(grid) == [], (difficulty, seed)
            facts = gen.semantic_observables(grid)
            layouts.add(facts["marker_layout"])
            shapes.add((facts["grid_h"], facts["grid_w"]))
            sizes = facts["blue_component_sizes"]
            target_ranks.add(sorted(sizes).index(facts["marker_count"]))
            assert facts["matching_object_count"] == 1
            if facts["marker_layout"] == "scattered":
                assert facts["marker_span"] > facts["marker_count"]
    assert layouts == {"contiguous", "scattered"}
    assert len(target_ranks) >= 2
    assert len(shapes) >= 10


def test_determinism_fresh_returns_and_global_rng_is_untouched():
    random.seed(8127)
    state = random.getstate()
    first = gen.generate(8127, 4, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(8127, 4, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert first != second


def test_self_check_rejects_the_three_retained_defects_and_bad_numeric_types():
    control = gen.generate(55, 1, marker_count=3, n_objects=3, marker_layout="scattered")
    assert gen.self_check(control) == []
    facts = gen.semantic_observables(control)
    target_size = facts["marker_count"]

    no_markers = copy.deepcopy(control)
    no_markers[0] = [0] * len(no_markers[0])

    no_match = copy.deepcopy(control)
    target = next(comp for comp in gen.blue_components(no_match) if len(comp) == target_size)
    no_match[target[0][0]][target[0][1]] = 0

    tied = copy.deepcopy(control)
    source = next(comp for comp in gen.blue_components(tied) if len(comp) != target_size)
    # A deliberately tiny exact tie fixture is clearer than mutating arbitrary geometry.
    tied = [[0] * 12 for _ in range(9)]
    for c in (0, 2, 4):
        tied[0][c] = 5
    for c in (1, 2, 3, 7, 8, 9):
        tied[3][c] = 1

    gray_below = copy.deepcopy(control)
    gray_below[2][0] = 5

    bool_cell = copy.deepcopy(control)
    bool_cell[1][0] = True

    for name, grid in {
        "no_markers": no_markers,
        "no_match": no_match,
        "tied_match": tied,
        "gray_below": gray_below,
        "bool_cell": bool_cell,
    }.items():
        assert gen.self_check(grid), name
