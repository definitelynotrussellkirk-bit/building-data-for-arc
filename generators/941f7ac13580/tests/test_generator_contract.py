from __future__ import annotations

import copy
import random

import pytest
from reviewer_support import find_root, load_selected_generator

ROOT = find_root(__file__)
TASK_ID = "941f7ac13580"
gen, _, _ = load_selected_generator(TASK_ID, root=ROOT)


def test_exact_controls_are_realized_and_observable() -> None:
    cases = (
        {"grid_h": 10, "grid_w": 22, "n_objects": 5, "size_range": 9, "palette_size": 5},
        {"grid_h": 22, "grid_w": 10, "n_objects": 2, "size_range": 1, "palette_size": 2},
        {"grid_h": 13, "grid_w": 17, "n_objects": 4, "size_range": 7, "palette_size": 3},
    )
    for difficulty in (None, "easy", "medium", "hard"):
        for index, overrides in enumerate(cases):
            requested = {**overrides, "position_bias": "scattered"}
            grid = gen.generate(1000 + index, 50 + index, difficulty=difficulty, **requested)
            facts = gen.semantic_observables(grid)
            assert facts["grid_h"] == requested["grid_h"]
            assert facts["grid_w"] == requested["grid_w"]
            assert facts["n_objects"] == requested["n_objects"]
            assert facts["max_object_size"] == requested["size_range"]
            assert facts["palette_size"] == requested["palette_size"]
            assert facts["one_cell_separated"] is True
            assert gen.observe_overrides(grid) == requested
            assert gen.self_check(grid, difficulty=difficulty, meta={"overrides": requested}) == []


def test_palette_size_override_constrains_unpinned_object_count() -> None:
    for seed in range(32):
        grid = gen.generate(seed, seed % 7, palette_size=5)
        facts = gen.semantic_observables(grid)
        assert facts["palette_size"] == 5
        assert facts["n_objects"] == 5
        assert gen.self_check(grid, meta={"overrides": {"palette_size": 5}}) == []


def test_unknown_malformed_and_incompatible_calls_reject_loudly() -> None:
    bad_calls = (
        ({"difficulty": "bogus"}, ValueError, "difficulty"),
        ({"unknown_axis": 1}, TypeError, "unknown override"),
        ({"grid_h": True}, (TypeError, ValueError), "grid_h"),
        ({"grid_h": 9}, ValueError, "grid_h"),
        ({"grid_w": 23}, ValueError, "grid_w"),
        ({"n_objects": 1}, ValueError, "n_objects"),
        ({"size_range": 10}, ValueError, "size_range"),
        ({"palette_size": 6}, ValueError, "palette_size"),
        ({"n_objects": 2, "palette_size": 3}, ValueError, "palette_size"),
        ({"position_bias": "clustered"}, ValueError, "position_bias"),
        ({"texture": "one_object"}, ValueError, "texture"),
        ({"texture": "two_objects", "n_objects": 3}, ValueError, "two_objects"),
        ({"texture": "two_objects", "palette_size": 3}, ValueError, "palette_size"),
        ({"texture": "single_cells", "size_range": 2}, ValueError, "single_cells"),
    )
    for kwargs, exc, message in bad_calls:
        with pytest.raises(exc, match=message):
            gen.generate(1, 0, **kwargs)


def test_supported_textures_are_structurally_honest() -> None:
    two = gen.generate(7, 1, texture="two_objects")
    assert gen.semantic_observables(two)["n_objects"] == 2
    assert gen.self_check(two) == []

    singles = gen.generate(7, 2, texture="single_cells")
    facts = gen.semantic_observables(singles)
    assert facts["n_objects"] >= 2
    assert set(facts["object_sizes"]) == {1}
    assert gen.self_check(singles) == []


def test_self_check_rejects_diagonal_contact_and_other_impostors() -> None:
    # Two otherwise-valid monochromatic components touch at a corner.
    diagonal = [[0] * 10 for _ in range(10)]
    diagonal[2][2] = 1
    diagonal[3][3] = 2
    errors = gen.self_check(diagonal)
    assert any("separated" in error for error in errors), errors

    merged = [[0] * 10 for _ in range(10)]
    merged[2][2] = 1
    merged[2][3] = 2
    assert gen.self_check(merged)

    oversize = [[0] * 10 for _ in range(10)]
    for col in range(10):
        oversize[0][col] = 3
    assert any("1..9" in error for error in gen.self_check(oversize))


def test_deterministic_fresh_returns_and_bounded_sampler() -> None:
    state = random.getstate()
    first = gen.generate(31337, 9, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(31337, 9, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert second == gen.generate(31337, 9, difficulty="hard")

    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(80):
            grid = gen.generate(seed, seed % 17, difficulty=difficulty)
            assert gen.self_check(grid, difficulty=difficulty) == [], (difficulty, seed)
            facts = gen.semantic_observables(grid)
            assert 2 <= facts["n_objects"] <= 5
            assert 1 <= facts["max_object_size"] <= 9
            assert facts["one_cell_separated"] is True
