"""Task-local regression tests for 22304ccc509c."""
from __future__ import annotations

import importlib.util
import os
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "22304ccc509c"
HOME = Path(__file__).resolve().parents[1]
PROFILES = (
    "canonical_6x6_p7",
    "canonical_7x7_p6",
    "canonical_6x6_p5",
    "broad_sparse",
    "broad_dense",
)


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_22304ccc509c", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def _profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def _episode(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_public_contract_is_pinned_minimal_and_observable():
    assert gen.RULE_HASH == "c3638032481f"
    assert gen.VERSION == "3.0.0"
    assert tuple(gen.SCHEDULE_PROFILES) == PROFILES
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.MIN_STRICT_FRAC == 1.0
    assert set(gen.AXES) == {"grid_h", "grid_w", "columns", "palette_size"}
    assert tuple(gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS) == ()
    assert set(gen.CANONICAL_SHORTCUTS) == {"sort_values_then_drop"}
    assert set(gen.SEMANTIC_RIVALS) == {
        "sort_values_then_drop",
        "discard_bottom_row_then_drop",
    }
    assert set(gen.LESSON_COMPETITORS) == set(gen.SEMANTIC_RIVALS)


def test_canonical_inputs_are_accepted_and_python_mirror_matches_every_label():
    assert len(PAIRS) == 3
    for pair in PAIRS:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_declared_sort_shortcut_really_fits_every_canonical_pair():
    rival = gen.CANONICAL_SHORTCUTS["sort_values_then_drop"]
    assert all(rival(pair["input"]) == pair["output"] for pair in PAIRS)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 6, "grid_w": 6, "columns": 2, "palette_size": 1},
        {"grid_h": 7, "grid_w": 7, "columns": 5, "palette_size": 6},
        {"grid_h": 18, "grid_w": 18, "columns": 6, "palette_size": 9},
    ],
)
def test_exact_override_boundaries_are_realized_and_observable(band, overrides):
    grid = gen.generate(91, 7, difficulty=band, **overrides)
    assert gen.self_check(grid, difficulty=band) == []
    assert gen.observe_overrides(grid) == overrides
    assert gen.rule_mirror(grid) != grid


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown": 1},
        {"grid_h": 5},
        {"grid_h": 19},
        {"grid_h": True},
        {"grid_h": "6"},
        {"grid_w": 5},
        {"grid_w": 19},
        {"grid_w": 6.0},
        {"columns": 1},
        {"columns": 7},
        {"columns": False},
        {"palette_size": 0},
        {"palette_size": 10},
        {"palette_size": 3.0},
    ],
)
def test_unknown_invalid_and_coercible_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, **overrides)


def test_every_five_consecutive_indices_cover_the_declared_schedule():
    for band in (None, "easy", "medium", "hard"):
        for start in range(20):
            observed = {
                gen.schedule_profile(123, start + offset, difficulty=band)
                for offset in range(len(PROFILES))
            }
            assert observed == set(PROFILES)


def test_every_band_hits_all_three_canonical_profiles_in_twenty_draws():
    wanted = {(6, 6, 8), (7, 7, 7), (6, 6, 6)}
    for band in ("easy", "medium", "hard"):
        seen = {
            _profile(gen.generate(1234, index, difficulty=band))
            for index in range(20)
        }
        assert wanted <= seen


def test_default_distribution_closes_both_known_shortcuts():
    random.seed(90210)
    state = random.getstate()
    for band in ("easy", "medium", "hard"):
        for index in range(60):
            grid = gen.generate(700 + index, index, difficulty=band)
            assert random.getstate() == state
            assert grid == gen.generate(700 + index, index, difficulty=band)
            assert gen.self_check(grid, difficulty=band) == []
            assert gen.strict_canonical_like(grid) == []
            assert gen.SEMANTIC_WITNESSES["occupied_bottom_row"](grid)
            assert gen.SEMANTIC_WITNESSES["descending_column_order"](grid)
            truth = gen.rule_mirror(grid)
            for name, rival in gen.SEMANTIC_RIVALS.items():
                assert rival(grid) != truth, (band, index, name)


def test_scheduled_lessons_and_every_query_rotation_refute_every_competitor():
    for band in ("easy", "medium", "hard"):
        for start in range(15):
            pairs = [
                _episode(gen.generate(314, start + offset, difficulty=band))
                for offset in range(4)
            ]
            for query_index in range(4):
                query = pairs[query_index]
                demos = pairs[:query_index] + pairs[query_index + 1 :]
                assert gen.lesson_identifiable(demos, query) == []
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(
                        rival(pair["input"]) != pair["output"] for pair in demos
                    ), (band, start, query_index, name)


def test_declared_witness_rival_claims_are_true_when_the_witness_fires():
    for index in range(40):
        grid = gen.generate(2718, index, difficulty="medium")
        truth = gen.rule_mirror(grid)
        for witness_name, rival_names in gen.WITNESS_RIVALS.items():
            if not gen.SEMANTIC_WITNESSES[witness_name](grid):
                continue
            assert any(
                gen.SEMANTIC_RIVALS[name](grid) != truth for name in rival_names
            ), (index, witness_name, rival_names)


def test_self_check_rejects_declared_and_minimal_impostors():
    fixtures = list(gen.mutation_fixtures())
    assert len(fixtures) >= 5
    for name, grid in fixtures:
        assert gen.self_check(grid), name

    assert gen.self_check([])
    assert gen.self_check([[0], [0, 1]])
    assert gen.self_check([[True] * 6 for _ in range(6)])
    assert gen.self_check([[0] * 6 for _ in range(6)])
