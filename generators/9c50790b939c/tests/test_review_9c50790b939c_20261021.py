"""Regression tests added by review review-673f5e1f3b45ba2e.

The packet's baseline ``test_generator_*.py`` is a frozen fixture.  New
review regressions live here so the fixture remains byte-for-byte intact.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from reviewer_support import find_root


TASK_ID = "9c50790b939c"
ROOT = find_root(__file__)
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"generator_{TASK_ID}_review_regressions", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_literal_integer_seeds(bad_seed):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(bad_seed, 0, difficulty="easy")


@pytest.mark.parametrize(
    "bad_sample_index", [True, False, 1.0, 1.75, "1", -1]
)
def test_generate_rejects_invalid_sample_indices(bad_sample_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(991, bad_sample_index, difficulty="hard")


def _ambiguous_half_target_rotation(grids, query_index):
    labelled = [(grid, GEN.rule_mirror(grid)) for grid in grids]
    train = [pair for index, pair in enumerate(labelled) if index != query_index]
    query_grid, query_output = labelled[query_index]
    fits_train = all(
        GEN.CANONICAL_SHORTCUTS["paint_half_target"](grid) == output
        for grid, output in train
    )
    disagrees_query = (
        GEN.CANONICAL_SHORTCUTS["paint_half_target"](query_grid) != query_output
    )
    return fits_train and disagrees_query


def test_frozen_census_lesson_has_no_ambiguous_query_rotation():
    seed = 2701766352
    grids = [
        GEN.generate(seed, sample_index, difficulty="easy")
        for sample_index in range(1, 5)
    ]
    assert not any(
        _ambiguous_half_target_rotation(grids, query_index)
        for query_index in range(len(grids))
    )


def test_default_two_slot_schedule_prevents_half_target_ambiguity_in_all_rotations():
    assert GEN.LESSON_SCHEDULE_PERIOD == 2
    assert GEN.EXAMPLES_NEEDED == 3
    for difficulty in ("easy", "medium", "hard"):
        for seed in (0, 29, 101):
            for start in range(4):
                grids = [
                    GEN.generate(seed, sample_index, difficulty=difficulty)
                    for sample_index in range(start, start + 4)
                ]
                profiles = [
                    GEN.schedule_profile(seed, sample_index, difficulty)
                    for sample_index in range(start, start + 4)
                ]
                assert profiles.count("shortcut_counterexample") == 2
                assert not any(
                    _ambiguous_half_target_rotation(grids, query_index)
                    for query_index in range(len(grids))
                )


@pytest.mark.parametrize("sample_index", [0, 1])
@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_two_cell_source_override_is_lawful_in_every_schedule_slot(
    sample_index, difficulty
):
    grid = GEN.generate(
        37,
        sample_index,
        difficulty=difficulty,
        source_length=2,
        distractor_rails=12,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid)["source_length"] == 2
