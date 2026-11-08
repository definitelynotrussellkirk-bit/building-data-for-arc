"""Task-local regressions for the vertical-run endcap generator."""
from __future__ import annotations

import importlib.util
import random
import sys
from pathlib import Path

import pytest

TASK_DIR = Path(__file__).resolve().parents[1]
REPO = TASK_DIR.parents[1]
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_7946249c9684_under_test", TASK_DIR / "generator.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _signature(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_hash_is_pinned_to_selected_authority():
    assert gen.RULE_HASH == "ab25d2969132"


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"grid_h": 5},
        {"grid_h": 13},
        {"grid_w": 6},
        {"grid_w": 13},
        {"n_runs": 2},
        {"n_runs": 9},
        {"palette_size": 1},
        {"palette_size": 4},
        {"grid_h": True},
        {"n_runs": 4.0},
        {"palette_size": "3"},
    ],
)
def test_rejects_unknown_out_of_range_and_non_integer_overrides(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {"grid_h": 6, "grid_w": 7, "n_runs": 3, "palette_size": 2},
        {"grid_h": 8, "grid_w": 9, "n_runs": 5, "palette_size": 3},
        {"grid_h": 12, "grid_w": 12, "n_runs": 8, "palette_size": 3},
    ],
)
def test_exact_overrides_are_observable_in_returned_pixels(band, requested):
    grid = gen.generate(17, 5, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert _signature(grid) != _signature(gen._intended_output(grid))


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(9917)
    before = random.getstate()
    first = gen.generate(71, 3, difficulty="medium")
    second = gen.generate(71, 3, difficulty="medium")
    assert random.getstate() == before
    assert first == second and first is not second
    assert all(left is not right for left, right in zip(first, second))

from reviewer_support import canonical_pairs, find_root

CANONICAL_PAIRS = canonical_pairs(gen.TASK_ID, root=find_root(__file__))


def test_canonical_pairs_are_strict_and_match_the_independent_mirror():
    for pair in CANONICAL_PAIRS:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen._intended_output(pair["input"]) == pair["output"]


def test_declared_shortcuts_fit_every_canonical_pair():
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "column_extremes",
        "nonzero_component_leaves",
        "same_color_component_leaves",
        "global_color_extremes",
    }
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        for pair in CANONICAL_PAIRS:
            assert rival(pair["input"]) == pair["output"], name


def test_schedule_cycles_through_all_profiles():
    observed = [
        gen.schedule_profile(123, index, difficulty="medium")
        for index in range(len(gen.SCHEDULE_PROFILES))
    ]
    assert observed == list(gen.SCHEDULE_PROFILES)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(6))
def test_every_three_consecutive_demos_refute_every_declared_competitor(band, start):
    grids = [gen.generate(1601, start + offset, difficulty=band) for offset in range(3)]
    demos = [{"input": grid, "output": gen._intended_output(grid)} for grid in grids]
    query_grid = gen.generate(1601, start + 3, difficulty=band)
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert any(rival(demo["input"]) != demo["output"] for demo in demos), name
    assert gen.lesson_identifiable(demos, {"input": query_grid}) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_semantic_witness_fires_and_really_refutes_its_named_rival(band):
    grids = [gen.generate(44, index, difficulty=band) for index in range(9)]
    for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
        hits = [grid for grid in grids if witness(grid)]
        assert hits, witness_name
        for grid in hits:
            for rival_name in gen.WITNESS_RIVALS[witness_name]:
                assert gen.SEMANTIC_RIVALS[rival_name](grid) != gen._intended_output(grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_schedule_cycle_contains_a_strict_canonical_profile(band):
    for cycle in range(4):
        grids = [
            gen.generate(907, cycle * len(gen.SCHEDULE_PROFILES) + offset, difficulty=band)
            for offset in range(len(gen.SCHEDULE_PROFILES))
        ]
        assert sum(gen.strict_canonical_like(grid) == [] for grid in grids) == 1


@pytest.mark.parametrize(
    "bad_grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 0]],
        [[True] * 7 for _ in range(6)],
        [[10] * 7 for _ in range(6)],
    ],
)
def test_self_check_rejects_malformed_grids_without_crashing(bad_grid):
    reasons = gen.self_check(bad_grid)
    assert isinstance(reasons, list) and reasons


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_profile_discriminators_are_constructive_not_seed_accidents(band):
    for seed in range(40):
        boundary = gen.generate(seed, 1, difficulty=band)
        assert gen.SEMANTIC_WITNESSES["multiple_runs_per_column"](boundary)
        assert gen.SEMANTIC_WITNESSES["connected_nonzero_runs"](boundary)
        assert gen.SEMANTIC_WITNESSES["same_color_connected_runs"](boundary)
        assert gen.SEMANTIC_WITNESSES["reused_color_runs"](boundary)

        separated = gen.generate(seed, 2, difficulty=band)
        assert gen.SEMANTIC_WITNESSES["multiple_runs_per_column"](separated)
        assert gen.SEMANTIC_WITNESSES["connected_nonzero_runs"](separated)
        assert gen.SEMANTIC_WITNESSES["same_color_connected_runs"](separated)
        assert gen.SEMANTIC_WITNESSES["reused_color_runs"](separated)
