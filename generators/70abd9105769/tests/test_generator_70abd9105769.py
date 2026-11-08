from __future__ import annotations

import copy
import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

ROOT = find_root(__file__)
TASK_ID = "70abd9105769"
gen, _, _ = load_selected_generator(TASK_ID, root=ROOT)


def _canonical_inputs():
    return [pair["input"] for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)]


def test_rule_hash_and_all_canonical_inputs_are_lawful():
    assert gen.RULE_HASH == "82b6dc62b353"
    inputs = _canonical_inputs()
    assert len(inputs) == 5
    for grid in inputs:
        assert gen.self_check(grid) == []


def test_exact_repeated_color_overrides_are_honored():
    grid = gen.generate(
        17,
        0,
        difficulty="hard",
        grid_h=24,
        grid_w=25,
        squares=7,
        n_distinct_colors=2,
    )
    assert len(grid) == 24 and len(grid[0]) == 25
    assert gen.self_check(grid) == []
    facts = gen.semantic_observables(grid)
    assert facts["square_count"] == 7
    assert facts["n_distinct_colors"] == 2
    assert max(facts["objects_per_color"].values()) >= 4
    assert gen.observe_overrides(grid) == {
        "grid_h": 24,
        "grid_w": 25,
        "squares": 7,
        "n_distinct_colors": 2,
    }


def test_override_contract_is_strict_and_difficulty_independent_when_exact():
    exact = {"grid_h": 30, "grid_w": 30, "squares": 10, "n_distinct_colors": 3}
    grids = []
    for difficulty in (None, "easy", "medium", "hard"):
        grid = gen.generate(91, 2, difficulty=difficulty, **exact)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == exact
        grids.append(grid)
    assert grids.count(grids[0]) == len(grids)

    bad = [
        {"unknown": 1},
        {"texture": "hollow_squares"},
        {"palette_size": 2},
        {"grid_h": True},
        {"grid_w": 31},
        {"squares": 0},
        {"squares": "3"},
        {"n_distinct_colors": 0},
        {"n_distinct_colors": 4, "squares": 3},
        {"grid_h": 5, "grid_w": 5, "squares": 2},
    ]
    for kwargs in bad:
        with pytest.raises((TypeError, ValueError)):
            gen.generate(1, 0, **kwargs)
    with pytest.raises(ValueError):
        gen.generate(1, 0, difficulty="legendary")


def test_default_sampler_is_lawful_varied_and_includes_repeated_colors_and_sizes():
    shapes = set()
    color_profiles = set()
    square_sizes = set()
    repeated = 0
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(50):
            grid = gen.generate(seed, seed, difficulty=difficulty)
            assert gen.self_check(grid) == [], (difficulty, seed)
            facts = gen.semantic_observables(grid)
            shapes.add((facts["grid_h"], facts["grid_w"]))
            color_profiles.add((facts["square_count"], facts["n_distinct_colors"]))
            square_sizes.update(facts["square_sizes"])
            repeated += facts["n_distinct_colors"] < facts["square_count"]
    assert len(shapes) >= 12
    assert len(color_profiles) >= 5
    assert repeated >= 20
    assert {3, 5}.issubset(square_sizes)


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


def test_self_check_rejects_malformed_domain_and_bad_numeric_types():
    control = gen.generate(55, 1, grid_h=18, grid_w=18, squares=4, n_distinct_colors=1)
    assert gen.self_check(control) == []
    facts = gen.semantic_observables(control)
    comp = facts["components"][0]

    hollow = copy.deepcopy(control)
    cr = (comp["r1"] + comp["r2"]) // 2
    cc = (comp["c1"] + comp["c2"]) // 2
    hollow[cr][cc] = 0

    even = [[0] * 8 for _ in range(8)]
    for r in range(2, 6):
        for c in range(1, 5):
            even[r][c] = 4

    # Same-color edge-touching squares merge into a non-square 3x6 component.
    # Differently colored squares may legitimately touch in the canonical data.
    touching = [[0] * 10 for _ in range(6)]
    for r in range(3):
        for c in range(3):
            touching[r][c] = 2
            touching[r][c + 3] = 2

    bool_cell = copy.deepcopy(control)
    bool_cell[0][0] = True

    for name, grid in {
        "hollow": hollow,
        "even": even,
        "touching": touching,
        "bool_cell": bool_cell,
        "blank": [[0] * 5 for _ in range(5)],
    }.items():
        assert gen.self_check(grid), name
