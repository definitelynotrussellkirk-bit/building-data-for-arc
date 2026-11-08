"""Task-local contract tests for d38b0f2356c1.

These tests intentionally exercise returned pixels and an independent canonical
reader rather than trusting generator bookkeeping.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_DIR = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_d38b0f2356c1_under_test", TASK_DIR / "generator.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()



def _all_canonical_pairs():
    return canonical_pairs(gen.TASK_ID, root=ROOT, labeled_only=True)

def _signature(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_hash_is_pinned_to_selected_authority():
    assert gen.RULE_HASH == "20d59edf7f3a"


@pytest.mark.parametrize(
    "seed", [True, 1.25, "17", None], ids=["true", "float", "string", "none"]
)
def test_generate_rejects_noninteger_seed(seed):
    with pytest.raises(ValueError, match=r"^seed must be an integer"):
        gen.generate(seed, 3, difficulty="medium")


def test_generate_accepts_negative_integer_seed():
    grid = gen.generate(-7, 3, difficulty="medium")
    assert gen.self_check(grid) == []


@pytest.mark.parametrize(
    "sample_index",
    [True, False, 1.25, "3", -1],
    ids=["true", "false", "float", "string", "negative"],
)
def test_generate_rejects_noninteger_or_negative_sample_index(sample_index):
    with pytest.raises(ValueError, match=r"^sample_index must be a nonnegative integer"):
        gen.generate(17, sample_index, difficulty="medium")


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"clean_block": -1},
        {"clean_block": 9},
        {"template_cells": 0},
        {"template_cells": 10},
        {"distractor_noise": -1},
        {"distractor_noise": 7},
        {"cyan_count": 0},
        {"cyan_count": 4},
        {"template_cells": True},
        {"cyan_count": 1.0},
        {"clean_block": "2"},
    ],
)
def test_rejects_unknown_out_of_range_and_non_integer_overrides(overrides):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_observable_in_returned_pixels(band):
    requested = {
        "clean_block": 8,
        "template_cells": 9,
        "distractor_noise": 0,
        "cyan_count": 3,
    }
    grid = gen.generate(17, 5, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested


def test_difficulty_bands_change_default_instances():
    grids = [gen.generate(811, 23, difficulty=band) for band in ("easy", "medium", "hard")]
    assert len({_signature(grid) for grid in grids}) == 3


def test_generation_is_deterministic_and_schedule_is_explicit():
    for band in (None, "easy", "medium", "hard"):
        for sample_index in range(9):
            first = gen.generate(1234, sample_index, difficulty=band)
            second = gen.generate(1234, sample_index, difficulty=band)
            assert first == second
            assert gen.schedule_profile(1234, sample_index, difficulty=band) in gen.SCHEDULE_PROFILES


@pytest.mark.parametrize("pair", _all_canonical_pairs())
def test_canonical_inputs_remain_strict_and_python_oracle_matches(pair):
    grid = pair["input"]
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert gen._intended_output(grid) == pair["output"]


def test_sparsest_block_shortcut_fits_every_canonical_pair():
    for pair in _all_canonical_pairs():
        assert gen._sparsest_block_rival(pair["input"]) == pair["output"]


@pytest.mark.parametrize("start", range(12))
@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_three_consecutive_demos_refute_sparsest_block_shortcut(start, band):
    grids = [gen.generate(991, start + offset, difficulty=band) for offset in range(3)]
    assert all(gen.self_check(grid) == [] for grid in grids)
    witnesses = [gen.SEMANTIC_WITNESSES["sparser_cyan_distractor"](grid) for grid in grids]
    assert any(witnesses)
    assert any(gen._sparsest_block_rival(grid) != gen._intended_output(grid) for grid in grids)


@pytest.mark.parametrize("start", [0, 1, 7, 11, 22])
@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_three_demo_lesson_is_identifiable_against_declared_shortcut(start, band):
    grids = [gen.generate(77, start + offset, difficulty=band) for offset in range(4)]
    demos = [{"input": grid, "output": gen._intended_output(grid)} for grid in grids[:3]]
    query = {"input": grids[3], "output": gen._intended_output(grids[3])}
    assert gen.lesson_identifiable(demos, query) == []


def test_self_check_rejects_second_clean_block_and_bad_separator():
    grid = gen.generate(41, 2, clean_block=0, cyan_count=1, distractor_noise=2)
    # Remove cyan from a distractor to create a second clean block.
    for r in range(3):
        for c in range(4, 7):
            if grid[r][c] == 8:
                grid[r][c] = 0
    assert any("exactly one" in reason for reason in gen.self_check(grid))

    grid = gen.generate(41, 2)
    grid[3][0] = 0
    assert any("separator" in reason for reason in gen.self_check(grid))


def test_declares_occupancy_outlier_shortcut_and_equal_occupancy_witness():
    assert "unique_occupancy_outlier" in gen.CANONICAL_SHORTCUTS
    assert "unique_occupancy_outlier" in gen.LESSON_COMPETITORS
    assert "equal_occupancy_nonfirst_clean" in gen.SEMANTIC_WITNESSES


def test_every_declared_shortcut_fits_every_canonical_pair():
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        for pair in _all_canonical_pairs():
            assert rival(pair["input"]) == pair["output"], name


@pytest.mark.parametrize("start", range(12))
@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_three_consecutive_demos_refute_every_declared_competitor(start, band):
    grids = [gen.generate(1601, start + offset, difficulty=band) for offset in range(3)]
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert any(rival(grid) != gen._intended_output(grid) for grid in grids), name
    assert any(
        gen.SEMANTIC_WITNESSES["equal_occupancy_nonfirst_clean"](grid)
        for grid in grids
    )
