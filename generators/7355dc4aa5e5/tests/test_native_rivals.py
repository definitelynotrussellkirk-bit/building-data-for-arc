"""Focused semantic controls for the independent native-family audit."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest


PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/rivals.py"
SPEC = importlib.util.spec_from_file_location("_independent_7355dc4aa5e5_rivals", PATH)
rivals = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = rivals
SPEC.loader.exec_module(rivals)


@pytest.mark.parametrize("radius,erased", [
    (1, {(3, 1), (3, 3), (4, 5), (4, 7)}),
    (2, {(1, 8), (4, 0), (4, 4), (5, 8)}),
])
def test_later_crosses_erase_exactly_the_claimed_intermediate_stamps(radius, erased):
    grid = rivals.fixtures()["erased_diagonals_both_radii"]
    facts = rivals.facts(grid)["radii"][str(radius)]
    assert facts["nominal_diagonal_count"] == 12
    assert facts["surviving_green_count"] == 8
    assert set(map(tuple, facts["erased_diagonal_cells"])) == erased
    settings = {"diagonal_radius": radius, "propagation_passes": 2}
    reference = rivals.reference(grid, settings)
    for name in ("nominal_diagonals", "reverse_sweep", "simultaneous_sweep", "skip_a",
                 "retain_intermediate", "intermediate_blue", "repeat_same_grid"):
        assert rivals.predict(grid, settings, name) != reference, name


def test_same_row_later_marker_erases_earlier_red_center():
    grid = rivals.scene(7, 8, [(2, 2), (2, 5)], 4)
    settings = {"diagonal_radius": 1, "propagation_passes": 1}
    result = rivals.reference(grid, settings)
    assert result[2][2] == 1 and result[2][5] == 2
    reverse = rivals.predict(grid, settings, "reverse_sweep")
    assert reverse[2][2] == 2 and reverse[2][5] == 1
    for name in ("simultaneous_sweep", "restore_centers"):
        wrong = rivals.predict(grid, settings, name)
        assert wrong[2][2] == wrong[2][5] == 2


@pytest.mark.parametrize("radius,cell,expected_wrong", [(1, (1, 1), 2), (2, (3, 3), 3)])
def test_original_marker_membership_survives_changes_to_its_current_color(radius, cell, expected_wrong):
    grid = rivals.fixtures()["original_markers_overwritten_before_their_turn"]
    settings = {"diagonal_radius": radius, "propagation_passes": 1}
    correct = rivals.reference(grid, settings)
    wrong = rivals.predict(grid, settings, "dynamic_markers")
    r, c = cell
    assert correct[r][c] == (3 if radius == 1 else 2)
    assert wrong[r][c] == expected_wrong


@pytest.mark.parametrize("radius,greens", [(1, {(1, 1), (5, 7)}), (2, {(2, 2), (4, 6)})])
def test_each_clipped_diagonal_is_independently_kept_or_dropped(radius, greens):
    grid = rivals.scene(7, 9, [(0, 0), (6, 8)], 0)
    settings = {"diagonal_radius": radius, "propagation_passes": 1}
    actual = rivals.reference(grid, settings)
    assert set(rivals.coordinates(actual, 3)) == greens
    assert actual[0][0] == actual[6][8] == 2
    assert actual[3][3] == 0
    for name in ("interior_only", "full_stamp_only", "wrap_diagonals", "clamp_diagonals"):
        assert rivals.predict(grid, settings, name) != actual, name


@pytest.mark.parametrize("radius", (1, 2))
def test_second_stage_only_hypotheses_are_equivalent_in_one_pass(radius):
    grid = rivals.fixtures()["erased_diagonals_both_radii"]
    settings = {"diagonal_radius": radius, "propagation_passes": 1}
    actual = rivals.reference(grid, settings)
    for name in ("skip_a", "nominal_diagonals", "retain_intermediate", "repeat_same_grid", "intermediate_blue"):
        assert rivals.predict(grid, settings, name) == actual


def test_inputs_are_not_mutated_by_any_candidate():
    grid = rivals.fixtures()["shared_rows_columns_and_edges"]
    before = deepcopy(grid)
    for radius in (1, 2):
        for passes in (1, 2):
            for name in ("reference", *rivals.RIVALS):
                rivals.predict(grid, {"diagonal_radius": radius, "propagation_passes": passes}, name)
                assert grid == before


@pytest.mark.parametrize("settings", ({}, {"diagonal_radius": 1},
    {"diagonal_radius": True, "propagation_passes": 1},
    {"diagonal_radius": 1, "propagation_passes": False},
    {"diagonal_radius": 3, "propagation_passes": 1},
    {"diagonal_radius": 1, "propagation_passes": 2, "extra": 1}))
def test_independent_oracle_rejects_malformed_settings(settings):
    with pytest.raises(ValueError):
        rivals.reference(rivals.scene(7, 9, [(0, 0), (6, 8)]), settings)
