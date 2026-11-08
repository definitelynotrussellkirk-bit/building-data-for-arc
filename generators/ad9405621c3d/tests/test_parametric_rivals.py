"""Independent semantic and executable-rival regressions for the prototype."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest

PARAMETRIC = Path(__file__).resolve().parents[1] / "workspace" / "parametric"


def load_rivals():
    path = PARAMETRIC / "rivals.py"
    assert path.is_file(), "The independent rival implementation is missing"
    spec = importlib.util.spec_from_file_location("ad9405621c3d_parametric_rivals", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_audit():
    path = PARAMETRIC / "audit.py"
    assert path.is_file(), "The reproducible semantic audit is missing"
    spec = importlib.util.spec_from_file_location("ad9405621c3d_parametric_audit", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def grid_with_cells(cells, endpoints, size=7, color=2):
    grid = [[5] * size for _ in range(size)]
    for row, col in cells:
        grid[row][col] = 0
    for row, col in endpoints:
        grid[row][col] = color
    return grid


def test_independent_oracle_uses_canonical_udlr_shortest_path():
    rivals = load_rivals()
    grid = grid_with_cells(
        [(r, c) for r in range(1, 6) for c in range(1, 6)], [(1, 1), (5, 5)]
    )
    expected = deepcopy(grid)
    for row, col in [(2, 1), (3, 1), (4, 1), (5, 1), (5, 2), (5, 3), (5, 4)]:
        expected[row][col] = 2
    before = deepcopy(grid)
    assert rivals.oracle(grid, {"route_mode": "direct"}) == expected
    assert grid == before


def test_farthest_tie_is_rowmajor_and_both_legs_are_painted():
    rivals = load_rivals()
    cells = [(r, 1) for r in range(1, 6)] + [(3, c) for c in range(1, 4)]
    grid = grid_with_cells(cells, [(3, 1), (3, 3)])
    expected = deepcopy(grid)
    for row, col in [(1, 1), (2, 1), (3, 2)]:
        expected[row][col] = 2
    assert rivals.oracle(grid, {"route_mode": "via_farthest"}) == expected
    details = rivals.describe(grid, {"route_mode": "via_farthest"})
    assert details["waypoint"] == [1, 1]
    assert details["waypoint_distance"] == 2
    assert details["farthest_ties"] == 3


def test_goal_remains_passable_when_finding_and_routing_to_waypoint():
    rivals = load_rivals()
    grid = grid_with_cells([(3, c) for c in range(7)], [(3, 0), (3, 2)])
    expected = deepcopy(grid)
    expected[3] = [2] * 7
    assert rivals.oracle(grid, {"route_mode": "via_farthest"}) == expected
    assert rivals.describe(grid, {"route_mode": "via_farthest"})["waypoint"] == [3, 6]


def test_two_wall_cells_are_rejected_to_preserve_canonical_color_selection():
    rivals = load_rivals()
    with pytest.raises(ValueError, match="three wall"):
        rivals.oracle([[6, 0, 5], [0, 6, 5], [0, 0, 0]], {"route_mode": "direct"})


def test_inherited_interior_monotone_rival_misses_required_detour():
    rivals = load_rivals()
    cells = [(r, c) for r in range(2, 5) for c in (2, 4)] + [(4, 3)]
    grid = grid_with_cells(cells, [(2, 2), (2, 4)])
    rival = next(r for r in rivals.bank({"route_mode": "direct"})
                 if r.name == "interior_monotone")
    assert rival.apply(grid) == grid
    expected = deepcopy(grid)
    for row, col in [(3, 2), (4, 2), (4, 3), (4, 4), (3, 4)]:
        expected[row][col] = 2
    assert rivals.oracle(grid, {"route_mode": "direct"}) == expected


def test_all_shortest_and_endpoint_reversal_are_executable_distinct_rivals():
    rivals = load_rivals()
    grid = grid_with_cells(
        [(r, c) for r in range(1, 6) for c in range(1, 6)], [(1, 1), (5, 5)]
    )
    bank = {r.name: r for r in rivals.bank({"route_mode": "direct"})}
    all_paths = deepcopy(grid)
    for row in range(1, 6):
        for col in range(1, 6):
            all_paths[row][col] = 2
    reverse_path = deepcopy(grid)
    for row, col in [(1, 2), (1, 3), (1, 4), (1, 5), (2, 5), (3, 5), (4, 5)]:
        reverse_path[row][col] = 2
    assert bank["all_shortest_paths"].apply(grid) == all_paths
    assert bank["reverse_endpoints"].apply(grid) == reverse_path


def test_lesson_audit_retains_a_demo_fit_query_disagreement():
    rivals = load_rivals()
    demo = grid_with_cells([(0, c) for c in range(7)], [(0, 0), (0, 6)])
    query = grid_with_cells(
        [(r, c) for r in range(2, 5) for c in (2, 4)] + [(4, 3)],
        [(2, 2), (2, 4)],
    )
    settings = {"route_mode": "direct"}
    pairs = lambda grids: [{"input": g, "output": rivals.oracle(g, settings)} for g in grids]
    episode = {"train": pairs([demo, demo]), "test": pairs([query])}
    result = rivals.audit_lesson(episode, settings)
    finding = next(item for item in result["findings"] if item["rival"] == "interior_monotone")
    assert finding["query_index"] == 0
    assert finding["input"] == query
    assert finding["rival_output"] == query
    assert finding["output"] != query
    assert finding["program"].startswith("(rule!")


def test_up_left_down_right_tie_differs_on_a_lower_left_goal():
    rivals = load_rivals()
    grid = grid_with_cells([(r, c) for r in range(1, 6) for c in range(1, 6)],
                           [(1, 5), (5, 1)])
    bank = {r.name: r for r in rivals.bank({"route_mode": "direct"})}
    assert "neighbor_u_l_d_r" in bank
    expected = deepcopy(grid)
    for row, col in [(1, 1), (1, 2), (1, 3), (1, 4), (2, 1), (3, 1), (4, 1)]:
        expected[row][col] = 2
    assert bank["neighbor_u_l_d_r"].apply(grid) == expected
    assert expected != rivals.oracle(grid, {"route_mode": "direct"})


def test_second_leg_orientation_and_direct_plus_first_are_distinct():
    rivals = load_rivals()
    grid = grid_with_cells([(r, c) for r in range(1, 6) for c in range(1, 6)],
                           [(1, 1), (3, 3)])
    settings = {"route_mode": "via_farthest"}
    bank = {r.name: r for r in rivals.bank(settings)}
    assert "second_leg_from_goal" in bank and "direct_plus_first" in bank
    expected_reverse = deepcopy(grid)
    for row, col in [(2, 1), (3, 1), (4, 1), (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (4, 3)]:
        expected_reverse[row][col] = 2
    expected_direct = deepcopy(grid)
    for row, col in [(2, 1), (3, 1), (4, 1), (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (3, 2)]:
        expected_direct[row][col] = 2
    assert bank["second_leg_from_goal"].apply(grid) == expected_reverse
    assert bank["direct_plus_first"].apply(grid) == expected_direct
    assert expected_reverse != rivals.oracle(grid, settings)
    assert expected_direct != rivals.oracle(grid, settings)


def test_farthest_leaf_does_not_mean_farthest_open_cell():
    rivals = load_rivals()
    grid = grid_with_cells([(r, c) for r in range(1, 6) for c in range(1, 6)] + [(0, 1)],
                           [(1, 1), (3, 3)])
    settings = {"route_mode": "via_farthest"}
    bank = {r.name: r for r in rivals.bank(settings)}
    assert "farthest_leaf" in bank
    expected = deepcopy(grid)
    for row, col in [(0, 1), (2, 1), (3, 1), (3, 2)]:
        expected[row][col] = 2
    assert bank["farthest_leaf"].apply(grid) == expected
    assert expected != rivals.oracle(grid, settings)


def test_down_up_left_right_is_distinct_from_canonical_and_down_left_right_up():
    rivals = load_rivals()
    bank = {r.name: r for r in rivals.bank({"route_mode": "direct"})}
    assert "neighbor_d_u_l_r" in bank
    ring = grid_with_cells([(r, c) for r in (2, 4) for c in range(1, 6)]
                           + [(3, 1), (3, 5)], [(3, 1), (3, 5)])
    expected = deepcopy(ring)
    expected[4][1:6] = [2] * 5
    assert bank["neighbor_d_u_l_r"].apply(ring) == expected
    assert expected != rivals.oracle(ring, {"route_mode": "direct"})
    upper = [(2, 3), (2, 4), (2, 5), (3, 5), (4, 5)]
    lower = [(3, 2), (4, 2), (5, 2), (5, 3), (5, 4)]
    fork = grid_with_cells(upper + lower + [(3, 3), (5, 5)], [(3, 3), (5, 5)])
    expected = deepcopy(fork)
    for row, col in upper:
        expected[row][col] = 2
    assert bank["neighbor_d_u_l_r"].apply(fork) == expected
    assert bank["neighbor_d_l_r_u"].apply(fork) != expected


def test_last_discovery_farthest_tie_differs_from_rowmajor_last():
    rivals = load_rivals()
    grid = grid_with_cells([(r, 3) for r in range(1, 6)]
                           + [(3, c) for c in range(1, 6)], [(3, 3), (3, 4)])
    bank = {r.name: r for r in rivals.bank({"route_mode": "via_farthest"})}
    assert "farthest_tie_discovery_last" in bank
    expected = deepcopy(grid)
    expected[3][5] = 2
    assert bank["farthest_tie_discovery_last"].apply(grid) == expected
    assert bank["farthest_tie_last"].apply(grid) != expected


def test_left_right_up_down_prioritizes_right_when_left_is_blocked():
    rivals = load_rivals()
    upper = [(2, 3), (2, 2), (2, 1), (3, 1), (4, 1), (5, 1), (5, 2)]
    right = [(3, 4), (3, 5), (3, 6), (4, 6), (5, 6), (5, 5), (5, 4)]
    grid = grid_with_cells(upper + right + [(3, 3), (5, 3)], [(3, 3), (5, 3)])
    bank = {r.name: r for r in rivals.bank({"route_mode": "direct"})}
    assert "neighbor_l_r_u_d" in bank
    expected = deepcopy(grid)
    for row, col in right:
        expected[row][col] = 2
    assert bank["neighbor_l_r_u_d"].apply(grid) == expected
    assert bank["neighbor_l_u_r_d"].apply(grid) != expected


def test_outer_boundary_waypoint_is_distinct_from_outer_two_rings():
    rivals = load_rivals()
    grid = grid_with_cells([(0, 1)] + [(1, c) for c in range(1, 6)]
                           + [(r, 5) for r in range(2, 6)], [(1, 1), (1, 3)])
    bank = {r.name: r for r in rivals.bank({"route_mode": "via_farthest"})}
    assert "farthest_outer_boundary" in bank
    expected = deepcopy(grid)
    expected[0][1] = expected[1][2] = 2
    assert bank["farthest_outer_boundary"].apply(grid) == expected
    assert bank["farthest_boundary"].apply(grid) != expected


def test_audit_detects_source_drift_instead_of_claiming_a_current_result(tmp_path):
    audit = load_audit()
    source = tmp_path / "rule.py"
    source.write_text("old source\n")
    before = audit.hash_sources([source])
    source.write_text("new source\n")
    state = audit.source_state(before, audit.hash_sources([source]))
    assert state["unchanged"] is False
    assert state["changed_paths"] == [str(source)]


def test_audit_stress_inputs_have_substantive_connected_content_across_30x30():
    audit = load_audit()
    rivals = load_rivals()
    fixtures = audit.stress_grids()
    assert set(fixtures) == {"serpentine", "cyclic_mesh"}
    for grid in fixtures.values():
        details = rivals.describe(grid, {"route_mode": "via_farthest"})
        assert (details["height"], details["width"]) == (30, 30)
        assert details["open_cells"] >= 250
        assert all(any(value != 5 for value in row) for row in grid)
        assert all(any(row[col] != 5 for row in grid) for col in range(30))
        assert details["via_extra_cells"] > 0


@pytest.mark.parametrize("settings", [{"route_mode": "direct"}, {"route_mode": "via_farthest"}])
def test_protected_racket_rivals_match_python_on_branch_and_cyclic_fixtures(settings):
    rivals = load_rivals()
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    from arcpuzzles.parametric_worker import _real_evaluator

    root = PARAMETRIC.parents[3]
    execute, identity, bridge = _real_evaluator(root / "shared" / "runtime")
    assert identity["backend"] == "racket"
    assert identity["protected"] is True
    grids = [
        grid_with_cells([(r, 1) for r in range(1, 6)] + [(3, c) for c in range(1, 6)],
                        [(3, 1), (3, 3)]),
        grid_with_cells([(r, c) for r in range(1, 6) for c in range(1, 6)],
                        [(1, 1), (5, 5)]),
        grid_with_cells([(r, c) for r in range(2, 5) for c in (2, 4)] + [(4, 3)],
                        [(2, 2), (2, 4)]),
    ]
    try:
        for rival in rivals.bank(settings):
            for grid in grids:
                assert execute(rival.program, grid) == rival.apply(grid), rival.name
    finally:
        bridge.close()
