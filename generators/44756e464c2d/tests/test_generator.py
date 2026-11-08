"""Focused regression tests for the 44756e464c2d generator repair."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
LIBRARY = next(
    (parent for parent in HOME.parents if (parent / "shared/runtime").is_dir()),
    None,
)
assert LIBRARY is not None
sys.path.insert(0, str(LIBRARY / "shared/runtime"))
sys.path.insert(0, str(HOME / "workspace"))

from reference_probe import (  # noqa: E402
    authority_record,
    canonical_train_pairs,
    differing_cells,
    intended_output,
    load_generator,
    observed_axes,
    palette,
)

GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
GEN = load_generator(GENERATOR_PATH)

EXPECTED_AXES = {"grid_h", "grid_w", "n_row_marks", "n_col_marks"}


def test_rule_pin_and_honest_control_surface_are_declared():
    assert GEN.RULE_HASH == "a5adc22c1318"
    assert set(GEN.AXES) == EXPECTED_AXES
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.LESSON_SCHEDULE_PERIOD == 4


@pytest.mark.parametrize("pair", canonical_train_pairs(), ids=["train0", "train1"])
def test_canonical_training_inputs_remain_in_domain_and_match_rule(pair):
    assert GEN.self_check(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]
    assert GEN.strict_canonical_like(pair["input"]) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 7, "grid_w": 8, "n_row_marks": 1, "n_col_marks": 1},
        {"grid_h": 10, "grid_w": 10, "n_row_marks": 4, "n_col_marks": 4},
    ],
)
def test_exact_override_boundaries_are_realized_in_every_band(band, overrides):
    grid = GEN.generate(911, 7, difficulty=band, **overrides)
    assert GEN.self_check(grid) == []
    assert observed_axes(grid) == overrides
    assert GEN.observe_overrides(grid) == overrides
    assert intended_output(grid) == intended_output(deepcopy(grid))
    assert GEN.generate(911, 7, difficulty=band, **overrides) == grid


@pytest.mark.parametrize(
    "override",
    [
        {"unknown_axis": 1},
        {"grid_h": 6},
        {"grid_h": 11},
        {"grid_w": 7},
        {"grid_w": 11},
        {"n_row_marks": 0},
        {"n_row_marks": 5},
        {"n_col_marks": 0},
        {"n_col_marks": 5},
        {"grid_h": True},
        {"n_row_marks": 2.5},
        {"n_col_marks": "2"},
    ],
)
def test_invalid_overrides_fail_loudly(override):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **override)


def test_selected_target_code_is_exactly_synchronized_with_canonical_source():
    target = authority_record()["racket_target"]
    assert target["target_code"] == target["raw_code"]


def test_schedule_teaches_color_specific_roles_under_every_three_pair_rotation():
    assert tuple(GEN.SCHEDULE_PROFILES) == (
        "canonical",
        "top_distractor",
        "left_distractor",
        "both_distractors",
    )
    witness = GEN.SEMANTIC_WITNESSES["color_specific_border_roles"]
    for band in ("easy", "medium", "hard"):
        for start in range(GEN.LESSON_SCHEDULE_PERIOD):
            grids = [GEN.generate(313, start + offset, difficulty=band) for offset in range(3)]
            assert all(GEN.self_check(grid) == [] for grid in grids)
            flags = [witness(grid) for grid in grids]
            assert sum(flags) >= 2
            for query_index in range(3):
                assert any(flag for i, flag in enumerate(flags) if i != query_index)


def test_role_swapped_distractors_preserve_the_canonical_palette():
    witness = GEN.SEMANTIC_WITNESSES["color_specific_border_roles"]
    for index in range(GEN.LESSON_SCHEDULE_PERIOD):
        grid = GEN.generate(71, index, difficulty="medium")
        assert palette(grid) == {0, 1, 2}
        assert witness(grid) is (index != 0)
        assert sum(value == 2 for value in grid[0][1:]) <= 1
        assert sum(row[0] == 1 for row in grid[1:]) <= 1


def test_canonical_shortcut_really_fits_canonical_and_generated_witness_refutes_it():
    rival = GEN.CANONICAL_SHORTCUTS["all_nonzero_border_cells_select"]
    assert all(rival(pair["input"]) == pair["output"] for pair in canonical_train_pairs())

    witness_grid = GEN.generate(71, 3, difficulty="medium")
    original = deepcopy(witness_grid)
    assert GEN.SEMANTIC_WITNESSES["color_specific_border_roles"](witness_grid)
    assert rival(witness_grid) != intended_output(witness_grid)
    assert witness_grid == original


def test_each_band_hits_a_canonical_shape_and_palette_in_twenty_default_draws():
    canonical_profiles = {(7, 8, 3), (9, 9, 3), (10, 10, 3)}
    for band in ("easy", "medium", "hard"):
        profiles = {
            (len(grid), len(grid[0]), len(palette(grid)))
            for index in range(20)
            for grid in [GEN.generate(1701, index, difficulty=band)]
        }
        assert profiles & canonical_profiles


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 8 for _ in range(7)]],
)
def test_malformed_inputs_return_diagnostics_instead_of_raising(grid):
    assert GEN.self_check(grid)


@pytest.mark.parametrize(
    "mutation",
    ["origin", "interior_marker", "wrong_border_role", "unknown_color", "too_many_marks"],
)
def test_self_check_rejects_structural_impostors(mutation):
    grid = GEN.generate(301, 3, grid_h=9, grid_w=9, n_row_marks=2, n_col_marks=2)
    if mutation == "origin":
        grid[0][0] = 1
    elif mutation == "interior_marker":
        grid[2][2] = 1
    elif mutation == "wrong_border_role":
        grid[0][1] = 2
        grid[0][2] = 2
    elif mutation == "unknown_color":
        grid[2][2] = 9
    elif mutation == "too_many_marks":
        for c in range(1, 6):
            grid[0][c] = 1
    assert GEN.self_check(grid)


def test_keyed_generation_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(41,13,difficulty='hard')))"
    )
    results = []
    for hash_seed in ("1", "991"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert results[0] == results[1]



def test_retained_role_swapped_counterexample_replays_against_current_source():
    fixture_path = HOME / "counterexamples" / "role-swapped-border-colors.json"
    fixture = json.loads(fixture_path.read_text())
    source_sha = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()

    assert fixture["schema"] == "arcpuzzles-generator-counterexample-v1"
    assert fixture["task_id"] == GEN.TASK_ID
    assert fixture["generator_sha256"] == source_sha
    assert fixture["rule_hash"] == GEN.RULE_HASH

    case = fixture["case"]
    grid = GEN.generate(
        case["seed"],
        case["sample_index"],
        difficulty=case["difficulty"],
        **case.get("overrides", {}),
    )
    rival = GEN.CANONICAL_SHORTCUTS[fixture["rival"]]

    assert grid == fixture["input"]
    assert GEN.self_check(grid) == []
    assert intended_output(grid) == fixture["intended_output"]
    assert rival(grid) == fixture["rival_output"]
    assert [list(cell) for cell in differing_cells(
        fixture["intended_output"], fixture["rival_output"]
    )] == fixture["differing_cells"]
    assert fixture["differing_cells"]
