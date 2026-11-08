"""Focused independent controls for semantic audit algorithms, not production."""
import importlib.util
from pathlib import Path
import sys

import pytest


PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/rivals.py"
SPEC = importlib.util.spec_from_file_location("_independent_6afe10b621e4_rivals", PATH)
rivals = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = rivals
SPEC.loader.exec_module(rivals)


def test_bridge_changes_the_selected_object_not_only_its_paint():
    grid = rivals.fixtures()["red_fragments_overtake"]
    original = rivals.reference(grid, {"bridge_mode": "ignore"})
    merged = rivals.reference(grid, {"bridge_mode": "merge"})
    assert sum(v == 4 for row in original for v in row) == 4
    assert sum(v == 4 for row in merged for v in row) == 7
    assert not {(r, c) for r, row in enumerate(original) for c, v in enumerate(row) if v == 4}.intersection(
        (r, c) for r, row in enumerate(merged) for c, v in enumerate(row) if v == 4)
    assert rivals.facts(grid)["two_red_fragments_overtake_original_winner"]
    assert rivals.predict(grid, {"bridge_mode": "merge"}, "select_before_merge") != merged


def test_standalone_8_is_not_conditioned_on_touching_red():
    grid = rivals.fixtures()["standalone_8_and_sparse_bbox"]
    settings = {"bridge_mode": "merge"}
    expected = rivals.reference(grid, settings)
    assert sum(v == 4 for row in expected for v in row) == 8
    assert rivals.facts(grid)["standalone_8_wins_after_merge"]
    for name in ("connected_8_only", "exclude_8_from_size", "erase_bridge_pixels", "ignore_8"):
        assert rivals.predict(grid, settings, name) != expected


def test_sparse_bbox_rival_has_its_stated_meaning():
    grid = rivals.fixtures()["standalone_8_and_sparse_bbox"]
    settings = {"bridge_mode": "ignore"}
    expected = rivals.reference(grid, settings)
    wrong = rivals.predict(grid, settings, "bbox_area")
    assert expected[0][0] == 4 and expected[3][0] == 0
    assert wrong[0][0] == 0 and wrong[3][0] == 4


def test_scan_order_ties_match_stable_canonical_selection():
    grid = rivals.fixtures()["stable_scan_order_ties"]
    assert rivals.reference(grid, {"bridge_mode": "ignore"}) == [
        [4, 0, 0, 0, 1], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]


@pytest.mark.parametrize("name", ("longest_span", "shortest_span", "bbox_perimeter", "cell_perimeter"))
def test_eight_dense_cells_beat_seven_cells_with_greater_geometric_score(name):
    grid = [
        [0, 2, 2, 0, 0, 0, 3],
        [2, 2, 2, 0, 0, 0, 0],
        [2, 2, 2, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [2, 2, 2, 2, 0, 0, 0],
        [2, 0, 0, 0, 0, 0, 0],
        [2, 0, 0, 0, 0, 0, 0],
        [2, 0, 0, 0, 0, 0, 0],
    ]
    settings = {"bridge_mode": "ignore"}
    expected = rivals.reference(grid, settings)
    wrong = rivals.predict(grid, settings, name)
    assert sum(v == 4 for row in expected for v in row) == 8
    assert sum(v == 4 for row in wrong for v in row) == 7


@pytest.mark.parametrize("settings", ({}, {"bridge_mode": True}, {"bridge_mode": "unknown"},
                                      {"bridge_mode": "ignore", "extra": 1}))
def test_independent_oracle_does_not_silently_accept_malformed_settings(settings):
    with pytest.raises(ValueError):
        rivals.reference([[2, 0, 3]], settings)
