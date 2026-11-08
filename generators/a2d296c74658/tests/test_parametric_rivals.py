"""Independent, hand-derived regressions for the two completion semantics."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest

PARAMETRIC = Path(__file__).resolve().parents[1] / "workspace" / "parametric"
VERTICAL = {"completion_mode": "vertical"}
CASCADE = {"completion_mode": "cascade"}


def local(name):
    path = PARAMETRIC / (name + ".py")
    assert path.is_file(), "The independent semantic implementation is missing"
    spec = importlib.util.spec_from_file_location("_a2d296c74658_test_" + name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def origins():
    return [[0, 0, 0, 0, 7, 0, 0, 0, 7, 0, 7],
            [4, 0, 4, 0, 0, 0, 4, 0, 0, 0, 0],
            [0, 0, 0, 0, 7, 0, 0, 0, 7, 0, 7]]


def chains(gaps=3):
    return [[7 if r % 2 == 0 and c in (0, 2) else 0 for c in range(5)]
            for r in range(2 * gaps + 1)]


def test_independent_oracle_fills_all_vertical_centers_including_edge_columns():
    rivals = local("rivals")
    grid = chains()
    before = deepcopy(grid)
    expected = deepcopy(grid)
    expected[1] = expected[3] = expected[5] = [4, 0, 4, 0, 0]
    assert rivals.oracle(grid, VERTICAL) == expected
    assert grid == before


def test_cascade_uses_old_new_and_mixed_four_endpoints():
    rivals = local("rivals")
    expected = origins()
    expected[1] = [4, 2, 4, 2, 4, 2, 4, 2, 4, 2, 4]
    assert rivals.oracle(origins(), CASCADE) == expected
    assert rivals.describe(origins())["b_endpoint_origins"] == {
        "old_old": 1, "old_new": 2, "new_old": 1, "new_new": 1}


def test_crossing_gives_stage_a_precedence_and_exposes_original_reading():
    rivals = local("rivals")
    grid = [[0, 7, 0], [4, 0, 4], [0, 7, 0]]
    expected = [[0, 7, 0], [4, 4, 4], [0, 7, 0]]
    assert rivals.oracle(grid, CASCADE) == expected
    bank = {r.name: r for r in rivals.bank(CASCADE)}
    wrong = [[0, 7, 0], [4, 2, 4], [0, 7, 0]]
    assert bank["b_before_a"].apply(grid) == wrong
    assert bank["b_reads_original"].apply(grid) == wrong
    assert bank["b_old_four_only"].apply(grid) == expected


def test_four_sevens_make_two_a_cells_then_one_b_cell():
    rivals = local("rivals")
    grid = [[7, 0, 7], [0, 0, 0], [7, 0, 7]]
    assert rivals.first_stage(grid) == [[7, 0, 7], [4, 0, 4], [7, 0, 7]]
    assert rivals.oracle(grid, CASCADE) == [[7, 0, 7], [4, 2, 4], [7, 0, 7]]


def test_retained_cap_and_edge_only_rivals_are_real_counterrules():
    rivals = local("rivals")
    bank = {r.name: r for r in rivals.bank(VERTICAL)}
    grid = chains()
    capped = bank["a_cap_two_per_column"].apply(grid)
    assert capped[1] == capped[3] == [4, 0, 4, 0, 0]
    assert capped[5] == [0, 0, 0, 0, 0]
    edge_only = bank["a_shared_chains_only_at_edges"].apply(grid)
    assert edge_only[1] == edge_only[3] == edge_only[5] == [4, 0, 0, 0, 0]
    assert capped != rivals.oracle(grid, VERTICAL)
    assert edge_only != rivals.oracle(grid, VERTICAL)


def test_blocked_centers_wrong_colors_and_wide_gaps_are_preserved():
    rivals = local("rivals")
    grid = [[7, 3, 7, 0, 4], [5, 0, 0, 0, 0],
            [7, 3, 0, 0, 4], [0, 0, 7, 0, 0]]
    assert rivals.oracle(grid, VERTICAL) == grid
    bank = {r.name: r for r in rivals.bank(VERTICAL)}
    assert bank["a_overwrite_occupied"].apply(grid)[1][0] == 4
    assert bank["a_equal_nonzero_endpoints"].apply(grid)[1][1] == 4
    assert bank["a_fill_wide_gaps"].apply(grid)[1][2] == 4


@pytest.mark.parametrize("grid, expected", [
    ([[0]], [[0]]), ([[7], [0], [7]], [[7], [4], [7]]),
    ([[4, 0, 4]], [[4, 2, 4]]), ([[4, 3, 4]], [[4, 3, 4]]),
])
def test_oracle_honors_thin_rectangular_domain(grid, expected):
    assert local("rivals").oracle(grid, CASCADE) == expected


@pytest.mark.parametrize("grid", [[], [[]], [[True]], [[0], [0, 1]], [[10]], [[0] * 31]])
def test_oracle_rejects_non_arc_values_and_shapes(grid):
    with pytest.raises(ValueError):
        local("rivals").oracle(grid, CASCADE)


def test_origin_selection_rivals_each_miss_required_endpoints():
    rivals = local("rivals")
    bank = {r.name: r for r in rivals.bank(CASCADE)}
    expected = [4, 2, 4, 2, 4, 2, 4, 2, 4, 2, 4]
    for name in ("b_old_four_only", "b_new_four_only", "b_mixed_four_only", "b_at_least_one_new_four"):
        actual = bank[name].apply(origins())
        assert actual[1] != expected, name


def test_demo_first_audit_retains_a_real_query_disagreement():
    rivals = local("rivals")
    pairs = lambda grids: [{"input": g, "output": rivals.oracle(g, VERTICAL)} for g in grids]
    episode = {"train": pairs([chains(2), chains(2)]), "test": pairs([chains(3)])}
    audit = rivals.audit_lesson(episode, VERTICAL)
    finding = next(f for f in audit["findings"] if f["rival"] == "a_cap_two_per_column")
    assert finding["query_index"] == 0
    assert finding["input"] == chains(3)
    assert finding["rival_output"][5] == [0, 0, 0, 0, 0]
    assert finding["output"][5] == [4, 0, 4, 0, 0]
    assert finding["train"] == episode["train"]


def test_execution_errors_are_not_counted_as_demo_refutations():
    rivals = local("rivals")
    episode = {"train": [{"input": [[0]], "output": [[0]]}], "test": []}
    def fail(rival, grid):
        raise RuntimeError("intentional audit failure")
    audit = rivals.audit_lesson(episode, VERTICAL, execute=fail)
    assert audit["errors"]
    assert all(r["status"] == "error" and r["fits_all_demos"] is None for r in audit["rivals"])
    assert not audit["findings"]


@pytest.mark.parametrize("name", ["a_lateral_no_seven", "a_endpoint_lateral_no_seven",
                                  "a_neighborhood_no_third_color"])
def test_context_rivals_miss_a_required_crowded_a_center(name):
    rivals = local("rivals")
    bank = {r.name: r for r in rivals.bank(VERTICAL)}
    assert name in bank, "Confirmed contextual counterrule is missing from the reusable bank"
    grid = [[0, 7, 7, 0, 0], [0, 7, 0, 9, 0], [0, 7, 7, 0, 0]]
    assert rivals.oracle(grid, VERTICAL)[1][2] == 4
    assert bank[name].apply(grid)[1][2] == 0


@pytest.mark.parametrize("name", ["b_vertical_no_four", "b_endpoint_vertical_no_four",
                                  "b_endpoint_outer_lateral_zero", "b_neighborhood_no_third_color"])
def test_context_rivals_miss_a_required_crowded_b_center(name):
    rivals = local("rivals")
    bank = {r.name: r for r in rivals.bank(CASCADE)}
    assert name in bank, "Confirmed contextual counterrule is missing from the reusable bank"
    grid = [[9, 4, 4, 0, 0], [4, 0, 4, 4, 0], [0, 4, 4, 9, 0]]
    assert rivals.oracle(grid, CASCADE)[1][1] == 2
    assert bank[name].apply(grid)[1][1] == 0


def test_four_per_line_and_thirty_two_total_rivals_have_actual_count_caps():
    rivals = local("rivals")
    a_bank = {r.name: r for r in rivals.bank(VERTICAL)}
    b_bank = {r.name: r for r in rivals.bank(CASCADE)}
    assert {"a_cap_four_per_column", "a_cap_thirty_two_total"} <= a_bank.keys()
    assert {"b_cap_four_per_row", "b_cap_thirty_two_total"} <= b_bank.keys()
    a_grid = [[7] * 15 if r % 2 == 0 else [0] * 15 for r in range(11)]
    b_grid = [[4, 0] * 14 + [4] for _ in range(3)]
    assert sum(v == 4 for row in a_bank["a_cap_four_per_column"].apply(a_grid) for v in row) == 60
    assert sum(v == 4 for row in a_bank["a_cap_thirty_two_total"].apply(a_grid) for v in row) == 32
    assert sum(v == 2 for row in b_bank["b_cap_four_per_row"].apply(b_grid) for v in row) == 12
    assert sum(v == 2 for row in b_bank["b_cap_thirty_two_total"].apply(b_grid) for v in row) == 32


def test_edge_and_near_boundary_restrictions_skip_lawful_a_targets():
    rivals = local("rivals")
    bank = {r.name: r for r in rivals.bank(VERTICAL)}
    assert {"a_ignore_edge_columns", "a_ignore_near_boundary_rows"} <= bank.keys()
    assert bank["a_ignore_edge_columns"].apply(chains())[3] == [0, 0, 4, 0, 0]
    output = bank["a_ignore_near_boundary_rows"].apply(chains())
    assert output[1] == output[5] == [0, 0, 0, 0, 0]
    assert output[3] == [4, 0, 4, 0, 0]


def test_axis_adjacent_sevens_do_not_invalidate_a_vertical_completion():
    rivals = local("rivals")
    bank = {r.name: r for r in rivals.bank(VERTICAL)}
    name = "a_endpoint_outer_vertical_no_seven"
    assert name in bank, "Confirmed same-axis endpoint guard is missing"
    grid = [[7], [7], [0], [7]]
    assert rivals.oracle(grid, VERTICAL) == [[7], [7], [4], [7]]
    assert bank[name].apply(grid) == grid


def test_source_binding_detects_a_changed_source(tmp_path):
    audit = local("audit")
    path = tmp_path / "source.py"
    path.write_text("before\n")
    before = audit.hash_sources([path])
    path.write_text("after\n")
    state = audit.source_state(before, audit.hash_sources([path]))
    assert state["unchanged"] is False
    assert state["changed_paths"] == [str(path)]


@pytest.mark.parametrize("settings", [VERTICAL, CASCADE])
def test_protected_racket_rivals_match_python_on_hand_derived_controls(settings):
    rivals = local("rivals")
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
    runtime = PARAMETRIC.parents[3] / "shared" / "runtime"
    fixtures = [origins(), chains(), [[0, 7, 0], [4, 0, 4], [0, 7, 0]],
                [[7, 3, 7, 0, 4], [5, 0, 0, 0, 0], [7, 3, 0, 0, 4], [0, 0, 7, 0, 0]],
                [[4, 0, 4, 0, 4, 0, 4]], [[0]],
                [[0, 7, 7, 0, 0], [0, 7, 0, 9, 0], [0, 7, 7, 0, 0]],
                [[9, 4, 4, 0, 0], [4, 0, 4, 4, 0], [0, 4, 4, 9, 0]],
                [[7] * 15 if r % 2 == 0 else [0] * 15 for r in range(11)],
                [[4, 0] * 14 + [4] for _ in range(3)], [[7], [7], [0], [7]]]
    with _local_imports(runtime, PARAMETRIC):
        execute, identity, bridge = _real_evaluator(runtime)
        assert identity["protected"] is True and identity["backend"] == "racket"
        try:
            for rival in rivals.bank(settings):
                for grid in fixtures:
                    assert execute(rival.program, grid) == rival.apply(grid), rival.name
        finally:
            bridge.close()
