"""Task-local regressions for horizontal same-color gap completion."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root


TASK_ID = "8bd971ea3766"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def _profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_canonical_inputs_are_lawful_and_python_oracle_matches():
    pairs = _pairs()
    assert len(pairs) == 3
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_overlapping_targets_use_the_original_input_windows():
    grid = [[2, 0, 2, 0, 2]]
    assert gen.rule_mirror(grid) == [[2, 2, 2, 2, 2]]


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"grid_shape": "3x3"},
        {"grid_shape": 47},
        {"n_colors": 1},
        {"n_colors": 5},
        {"n_colors": True},
        {"palette_kind": "unknown"},
        {"palette_kind": 7},
    ],
)
def test_invalid_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, **overrides)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_shape": "4x7", "n_colors": 4, "palette_kind": "mixed"},
        {"grid_shape": "8x12", "n_colors": 2, "palette_kind": "high"},
    ],
)
def test_exact_overrides_are_observable_in_every_band(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_generated_grid_contains_all_teaching_witnesses(band):
    for index in range(24):
        grid = gen.generate(7100 + index, index, difficulty=band)
        original = deepcopy(grid)
        assert gen.strict_canonical_like(grid) == []
        expected = gen.rule_mirror(grid)
        for name, witness in gen.SEMANTIC_WITNESSES.items():
            assert witness(grid), (band, index, name)
        for name, rival in gen.SEMANTIC_RIVALS.items():
            assert rival(grid) != expected, (band, index, name)
        assert grid == original


def test_declared_canonical_shortcut_really_fits_canonical_examples():
    pairs = _pairs()
    assert gen.CANONICAL_SHORTCUTS
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name
        assert any(
            rival(grid) != gen.rule_mirror(grid)
            for grid in (gen.generate(9100 + index, index) for index in range(12))
        ), name


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_has_source_profiles_in_every_band(band):
    canonical_profiles = {(4, 7, 5), (5, 8, 4), (5, 9, 5)}
    profiles = {
        _profile(gen.generate(5000 + index, 11 * index + 3, difficulty=band))
        for index in range(36)
    }
    assert profiles & canonical_profiles, (band, profiles)


def test_every_four_pair_window_is_identifiable_under_query_rotation():
    for start in range(8):
        lesson = []
        for index in range(start, start + 4):
            grid = gen.generate(12001, index, difficulty="medium")
            lesson.append({"input": grid, "output": gen.rule_mirror(grid)})
        for query_index in range(4):
            query = lesson[query_index]
            demos = [pair for index, pair in enumerate(lesson) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == [], (start, query_index)


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 0]], [[True] * 7 for _ in range(4)], [[0, 11, 0]]],
)
def test_self_check_handles_malformed_grids_without_raising(grid):
    assert gen.self_check(grid)


def test_generation_is_deterministic_for_same_request():
    options = {"grid_shape": "6x10", "n_colors": 3, "palette_kind": "low"}
    assert gen.generate(81, 13, difficulty="hard", **options) == gen.generate(
        81, 13, difficulty="hard", **options
    )

@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_smallest_profile_teaches_single_and_multiple_target_rows(band):
    grid = gen.generate(
        31017,
        8,
        difficulty=band,
        grid_shape="4x7",
        n_colors=4,
        palette_kind="mixed",
    )
    counts = {}
    for row, _, _ in gen._horizontal_targets(grid):
        counts[row] = counts.get(row, 0) + 1
    assert 1 in counts.values(), counts
    assert any(count >= 2 for count in counts.values()), counts
