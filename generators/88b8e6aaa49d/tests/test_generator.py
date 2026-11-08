"""Regression and semantic tests for the 180-degree rotation curriculum."""
from __future__ import annotations

from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
import os
from pathlib import Path
import random
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "88b8e6aaa49d"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = spec_from_file_location(f"task_generator_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def _pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _rot180(grid):
    return [list(reversed(row)) for row in reversed(grid)]


def _flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid):
    return [list(row) for row in reversed(grid)]


def _rot90(grid):
    return [list(row) for row in zip(*reversed(grid))]


def _rot270(grid):
    return [list(row) for row in reversed(list(zip(*grid)))]


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _anti_transpose(grid):
    return _transpose(_rot180(grid))


RIVALS = {
    "identity": lambda grid: [list(row) for row in grid],
    "horizontal_flip_only": _flip_lr,
    "vertical_flip_only": _flip_ud,
    "rotate_90": _rot90,
    "rotate_270": _rot270,
    "main_diagonal_reflection": _transpose,
    "anti_diagonal_reflection": _anti_transpose,
}


def test_rule_pin_and_public_contract_are_explicit():
    assert GEN.RULE_HASH == "d4b6baaa86e7"
    assert set(GEN.AXES) == {"grid_h", "grid_w", "palette_size"}
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.LESSON_SCHEDULE_PERIOD == len(GEN.SCHEDULE_PROFILES) == 5
    assert GEN.EXAMPLES_NEEDED == 3


@pytest.mark.parametrize("pair", _pairs())
def test_canonical_inputs_are_valid_and_python_mirror_matches_labels(pair):
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert _rot180(pair["input"]) == pair["output"]
    assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 3, "grid_w": 3, "palette_size": 4},
        {"grid_h": 3, "grid_w": 3, "palette_size": 6},
        {"grid_h": 8, "grid_w": 7, "palette_size": 5},
    ],
)
def test_exact_overrides_round_trip_in_every_band(band, options):
    grid = GEN.generate(314159, 17, difficulty=band, **options)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == options
    assert (len(grid), len(grid[0]), len({v for row in grid for v in row})) == (
        options["grid_h"],
        options["grid_w"],
        options["palette_size"],
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"texture": "noise"},
        {"grid_h": 2},
        {"grid_w": 9},
        {"palette_size": 3},
        {"palette_size": 7},
        {"grid_h": True},
        {"grid_w": "4"},
        {"palette_size": 5.0},
    ],
)
def test_invalid_or_retired_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **overrides)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, "1", -1])
def test_invalid_sample_indexes_are_rejected(sample_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, sample_index)


def test_schedule_covers_all_canonical_profiles_and_generalizations():
    assert tuple(GEN.SCHEDULE_PROFILES) == (
        "canonical_palette_4",
        "canonical_palette_5",
        "canonical_palette_6",
        "rectangular_generalization",
        "larger_square_generalization",
    )
    observed = [GEN.schedule_profile(0, index, "hard") for index in range(5)]
    assert observed == list(GEN.SCHEDULE_PROFILES)

    for band in (None, "easy", "medium", "hard"):
        grids = [GEN.generate(9000, index, difficulty=band) for index in range(5)]
        profiles = [GEN.observe_overrides(grid) for grid in grids]
        assert profiles[:3] == [
            {"grid_h": 3, "grid_w": 3, "palette_size": 4},
            {"grid_h": 3, "grid_w": 3, "palette_size": 5},
            {"grid_h": 3, "grid_w": 3, "palette_size": 6},
        ]
        assert all(GEN.strict_canonical_like(grid) == [] for grid in grids[:3])
        assert profiles[3]["grid_h"] != profiles[3]["grid_w"]
        assert profiles[4]["grid_h"] == profiles[4]["grid_w"] >= 4


def test_default_distribution_hits_profile_floor_and_refutes_every_d4_rival():
    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(12000 + index, index, difficulty=band) for index in range(20)]
        assert all(GEN.self_check(grid) == [] for grid in grids)
        assert sum(GEN.strict_canonical_like(grid) == [] for grid in grids) >= 12
        assert {len({v for row in grid for v in row}) for grid in grids} == {4, 5, 6}
        assert any(len(grid) != len(grid[0]) for grid in grids)
        assert any(len(grid) == len(grid[0]) > 3 for grid in grids)
        for grid in grids:
            expected = _rot180(grid)
            for rival in RIVALS.values():
                assert rival(grid) != expected


def test_generation_is_deterministic_pure_and_does_not_touch_global_random():
    before = random.getstate()
    first = GEN.generate(42, 11, difficulty="hard")
    middle = GEN.generate(999, 12, difficulty="easy")
    second = GEN.generate(42, 11, difficulty="hard")
    after = random.getstate()
    assert before == after
    assert first == second
    assert first != middle
    original = deepcopy(first)
    assert GEN.rule_mirror(first) == _rot180(first)
    assert first == original


@pytest.mark.parametrize(
    "bad",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True, 1, 2], [3, 4, 5], [6, 7, 8]],
        [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
        [[0, 1, 2], [3, 4, 3], [2, 1, 0]],
    ],
)
def test_self_check_rejects_malformed_or_rule_hiding_inputs(bad):
    assert GEN.self_check(bad)


def test_semantic_declarations_are_executable_and_lesson_contract_is_strict():
    assert set(GEN.SEMANTIC_RIVALS) == set(RIVALS)
    assert set(GEN.LESSON_COMPETITORS) == set(RIVALS)
    assert set(GEN.SEMANTIC_WITNESSES) == {
        "asymmetry_refutes_identity",
        "row_and_column_structure_refutes_single_flips",
        "orientation_structure_refutes_quarter_turns",
        "diagonal_structure_refutes_transposes",
    }

    pairs = []
    for index in range(4):
        grid = GEN.generate(777, index, difficulty="medium")
        expected = _rot180(grid)
        for witness in GEN.SEMANTIC_WITNESSES.values():
            assert witness(grid) is True
        for name, rival in GEN.SEMANTIC_RIVALS.items():
            assert rival(grid) == RIVALS[name](grid)
            assert rival(grid) != expected
        pairs.append({"input": grid, "output": expected})

    assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []
    damaged = deepcopy(pairs)
    damaged[0]["output"] = damaged[0]["input"]
    assert GEN.lesson_identifiable(damaged[:3], damaged[3])
