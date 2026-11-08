"""Focused regressions for the alternating horizontal tiling generator."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "adcdcbe48f64"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location("generator_under_test", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _canonical():
    return canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def _expected(grid):
    return [row + row[::-1] + row + row[::-1] + row for row in grid]


@pytest.mark.parametrize("pair", _canonical())
def test_canonical_inputs_are_accepted_and_python_rule_matches(pair):
    assert GEN.self_check(pair["input"]) == []
    assert GEN.rule_mirror(pair["input"]) == pair["output"]
    assert _expected(pair["input"]) == pair["output"]


def test_rule_hash_and_public_axis_surface_are_pinned():
    assert GEN.RULE_HASH == "5ed1759c50b3"
    assert set(GEN.AXES) == {"grid_h", "grid_w", "palette_size"}


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 4, "grid_w": 4, "palette_size": 2},
        {"grid_h": 4, "grid_w": 4, "palette_size": 3},
        {"grid_h": 15, "grid_w": 6, "palette_size": 4},
    ],
)
def test_exact_overrides_are_observable_in_every_band(band, overrides):
    grid = GEN.generate(17, 9, difficulty=band, **overrides)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == overrides
    assert len({value for row in grid for value in row}) == overrides["palette_size"]
    assert GEN.rule_mirror(grid) == _expected(grid)


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 4},
        {"grid_h": 1},
        {"grid_h": 3},
        {"grid_h": 16},
        {"grid_h": True},
        {"grid_h": 4.0},
        {"grid_w": 1},
        {"grid_w": 3},
        {"grid_w": 7},
        {"palette_size": 1},
        {"palette_size": 5},
        {"palette_size": "3"},
    ],
)
def test_invalid_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **overrides)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, "1", -1])
def test_invalid_sample_index_is_rejected(sample_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, sample_index)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_valid_deterministic_and_hits_canonical_profile(band):
    profiles = set()
    modes = set()
    for sample_index in range(40):
        grid = GEN.generate(8128, sample_index, difficulty=band)
        assert grid == GEN.generate(8128, sample_index, difficulty=band)
        assert GEN.self_check(grid) == []
        observed = GEN.observe_overrides(grid)
        profiles.add((observed["grid_h"], observed["grid_w"], observed["palette_size"]))
        modes.add(tuple(tuple(row) for row in grid))
        assert observed["grid_h"] == len(grid)
        assert observed["grid_w"] == len(grid[0])
        assert observed["palette_size"] == len({value for row in grid for value in row})
        assert not GEN._is_lr_sym(grid)
    assert any((height, width) == (4, 4) and colors in {2, 3}
               for height, width, colors in profiles)
    assert len(modes) >= 30


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[1, 2], [1]],
        [[True, 2], [3, 4]],
        [[0, 1], [2, 3]],
        [[1, 2]],
        [[1], [2]],
        [[2, 2], [2, 2]],
        [[1, 2, 2, 1], [3, 4, 4, 3]],
    ],
)
def test_self_check_rejects_malformed_or_non_teaching_inputs(grid):
    assert GEN.self_check(grid)



def test_self_check_rejects_minimal_foreground_impostors():
    singleton = [[1] * 4 for _ in range(4)]
    singleton[2][2] = 2
    solid_2x2 = [[1] * 4 for _ in range(4)]
    for row in range(2):
        for col in range(2):
            solid_2x2[row][col] = 2
    assert GEN.self_check(singleton)
    assert GEN.self_check(solid_2x2)


def test_generated_tiles_obey_dense_color_balance_contract():
    for band in (None, "easy", "medium", "hard"):
        for sample_index in range(120):
            grid = GEN.generate(991, sample_index, difficulty=band)
            counts = {}
            for row in grid:
                for value in row:
                    counts[value] = counts.get(value, 0) + 1
            area = len(grid) * len(grid[0])
            assert min(counts.values()) >= 3
            assert max(counts.values()) * 10 <= area * 7

def test_strict_profile_accepts_canonical_and_generated_core_inputs():
    for pair in _canonical():
        assert GEN.strict_canonical_like(pair["input"]) == []
    found = False
    for sample_index in range(80):
        grid = GEN.generate(1234, sample_index)
        if (len(grid), len(grid[0]), len({v for row in grid for v in row})) in {
            (4, 4, 2),
            (4, 4, 3),
        }:
            assert GEN.strict_canonical_like(grid) == []
            found = True
            break
    assert found


def test_semantic_witnesses_and_rivals_are_executable_counterexamples():
    assert set(GEN.SEMANTIC_WITNESSES) == {"visible_lr_mirror"}
    assert set(GEN.SEMANTIC_RIVALS) == {"plain_repeat", "mirror_first"}
    assert GEN.WITNESS_RIVALS == {
        "visible_lr_mirror": ["plain_repeat", "mirror_first"]
    }
    for sample_index in range(20):
        grid = GEN.generate(4401, sample_index)
        intended = GEN.rule_mirror(grid)
        assert GEN.SEMANTIC_WITNESSES["visible_lr_mirror"](grid)
        for rival in GEN.SEMANTIC_RIVALS.values():
            assert rival(grid) != intended


def test_lesson_hook_requires_a_visible_mirror_demonstration():
    pair = _canonical()[0]
    assert GEN.lesson_identifiable([pair], pair) == []
    symmetric = [[1, 2, 2, 1], [3, 4, 4, 3]]
    symmetric_pair = {"input": symmetric, "output": _expected(symmetric)}
    assert GEN.lesson_identifiable([symmetric_pair], symmetric_pair)
