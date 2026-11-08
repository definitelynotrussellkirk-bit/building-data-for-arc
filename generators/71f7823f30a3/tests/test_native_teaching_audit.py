"""Independent rival semantics and demo-only identification regressions."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "workspace/parametric/audit_native.py"
SPEC = importlib.util.spec_from_file_location("row_mirror_teaching_audit_tests", SOURCE)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def _scene():
    grid = [[0] * 15 for _ in range(4)]
    for row, anchor, colors in ((0, 7, (1, 2, 3)), (1, 6, (4, 5, 6))):
        grid[row][anchor] = 9
        for index, distance in enumerate(range(1, 7)):
            side = -1 if index % 2 == 0 else 1
            grid[row][anchor + side * distance] = colors[index % 3]
    grid[3][1] = 8
    return grid


def test_query_answers_do_not_eliminate_a_demo_consistent_rival():
    result = AUDIT.score_lesson([[[1]], [[2]]], [[[3]], [[4]]],
        {"wrong": [[[1]], [[2]]]}, {"wrong": [[[8]], [[4]]]})
    assert result["surviving_rivals_after_demonstrations"] == ["wrong"]
    assert result["queries"][0]["surviving_disagreeing_rivals"] == ["wrong"]
    assert result["queries"][1]["identified_within_declared_rivals"]
    assert not result["ok"]


def test_refutation_and_query_answer_equivalence_are_distinct():
    result = AUDIT.score_lesson([[[1]], [[2]]], [[[3]], [[4]]],
        {"refuted": [[[9]], [[2]]], "equivalent": [[[1]], [[2]]]},
        {"equivalent": [[[3]], [[4]]]})
    assert result["refuted_rivals"] == ["refuted"]
    assert result["surviving_rivals_after_demonstrations"] == ["equivalent"]
    assert result["ok"]


def test_refuted_rival_does_not_need_query_execution():
    result = AUDIT.score_lesson([[[1]], [[2]]], [[[3]]],
        {"refuted": [[[9]], [[2]]]}, {})
    assert result["ok"]


def test_surviving_rival_requires_query_labels():
    with pytest.raises(ValueError, match="every demo survivor"):
        AUDIT.score_lesson([[[1]], [[2]]], [[[3]]],
            {"survivor": [[[1]], [[2]]]}, {})


def test_partial_demonstration_or_query_labels_are_rejected():
    with pytest.raises(ValueError, match="label count"):
        AUDIT.score_lesson([[[1]], [[2]]], [[[3]]],
            {"partial": [[[1]]]}, {"partial": [[[3]]]})
    with pytest.raises(ValueError, match="label count"):
        AUDIT.score_lesson([[[1]]], [[[3]], [[4]]],
            {"partial": [[[1]]]}, {"partial": [[[3]]]})


def test_undeclared_rival_query_labels_are_rejected():
    with pytest.raises(ValueError, match="undeclared"):
        AUDIT.score_lesson([[[1]]], [[[3]]], {}, {"stray": [[[3]]]})


def test_nearest_color_propagates_to_the_other_same_color_source():
    grid = _scene()
    output = AUDIT.python_intended(grid, {"copy_policy": "nearest_color"})
    assert output[0][8] == 1
    assert output[0][3] == 1
    assert output[0][5] == 0
    assert output[0][10] == 0
    assert output[0][6] == output[0][11] == 1
    assert output != AUDIT.python_rival(grid, {"copy_policy": "nearest_color"}, "nearest_cell")
    assert grid == _scene()


def test_farthest_color_propagates_to_a_nearer_same_color_source():
    grid = _scene()
    output = AUDIT.python_intended(grid, {"copy_policy": "farthest_color"})
    assert output[0][1] == 3
    assert output[0][10] == 3
    assert output[0][3] == 0
    assert output[0][8] == 0
    assert output != AUDIT.python_rival(grid, {"copy_policy": "farthest_color"}, "farthest_cell")


def test_anchor_and_color_cues_are_row_local():
    grid = _scene()
    settings = {"copy_policy": "nearest_color"}
    output = AUDIT.python_intended(grid, settings)
    assert output[1][7] == output[1][2] == 4
    assert output != AUDIT.python_rival(grid, settings, "global_first_anchor")
    assert output != AUDIT.python_rival(grid, settings, "global_nearest_color")


def test_orphan_sources_pass_through_and_rival_reflects_them():
    grid = _scene()
    settings = {"copy_policy": "all"}
    output = AUDIT.python_intended(grid, settings)
    assert output[3] == grid[3]
    rival = AUDIT.python_rival(grid, settings, "reflect_orphans")
    assert rival[3][13] == 8
    assert rival[3][1] == 8
    assert rival != output


def test_movement_rival_deletes_only_selected_sources():
    grid = _scene()
    rival = AUDIT.python_rival(grid, {"copy_policy": "nearest_color"}, "move_sources")
    assert rival[0][6] == rival[0][11] == 0
    assert rival[0][8] == rival[0][3] == 1
    assert rival[0][4] == 3
    assert rival[0][7] == 9
    assert rival[3] == grid[3]


def test_sided_rivals_keep_originals_and_omit_the_opposite_direction():
    grid = _scene()
    left = AUDIT.python_rival(grid, {"copy_policy": "all"}, "left_only")
    right = AUDIT.python_rival(grid, {"copy_policy": "all"}, "right_only")
    assert left[0][8] == 1 and left[0][3] == 0
    assert right[0][3] == 1 and right[0][8] == 0
    assert left[0][11] == right[0][6] == 1


def test_frequency_selectors_count_colors_in_each_row():
    grid = [[0] * 17 for _ in range(4)]
    grid[0][8] = 9
    for distance, color in enumerate((1, 1, 2, 2, 2, 3, 3), 1):
        grid[0][8 - distance] = color
    settings = {"copy_policy": "nearest_color"}
    most = AUDIT.python_rival(grid, settings, "most_frequent_color")
    assert [most[0][8 + distance] for distance in range(1, 8)] == [0, 0, 2, 2, 2, 0, 0]
    least_near = AUDIT.python_rival(grid, settings, "least_frequent_nearest_tie")
    least_far = AUDIT.python_rival(grid, settings, "least_frequent_farthest_tie")
    assert least_near[0][9] == least_near[0][10] == 1
    assert least_far[0][14] == least_far[0][15] == 3


def test_mean_and_extent_rivals_use_the_entire_color_group():
    grid = [[0] * 15 for _ in range(4)]
    grid[0][7] = 9
    for distance, color in ((1, 1), (6, 1), (2, 2), (3, 2), (5, 2)):
        grid[0][7 - distance] = color
    settings = {"copy_policy": "nearest_color"}
    # A has mean 7/2 and B has mean 10/3: integer division loses this order.
    for name in ("minimum_mean_color", "minimum_max_distance_color", "maximum_min_distance_color"):
        output = AUDIT.python_rival(grid, settings, name)
        assert output[0][9] == output[0][10] == output[0][12] == 2
        assert output[0][8] == output[0][13] == 0
    output = AUDIT.python_rival(grid, settings, "maximum_mean_color")
    assert output[0][8] == output[0][13] == 1
    assert output[0][9] == output[0][10] == output[0][12] == 0


def test_unknown_rival_and_policy_fail_explicitly():
    with pytest.raises(ValueError, match="unknown rival"):
        AUDIT.python_rival(_scene(), {"copy_policy": "all"}, "typo")
    with pytest.raises(ValueError, match="copy_policy"):
        AUDIT.python_intended(_scene(), {"copy_policy": "typo"})


def test_all_rivals_are_total_on_empty_and_anchor_only_rows():
    for grid in ([[0] * 7 for _ in range(4)], [[9, 0, 0, 0, 0, 0, 0]] * 4):
        for policy in AUDIT.POLICIES:
            for name in AUDIT.RIVALS:
                output = AUDIT.python_rival(grid, {"copy_policy": policy}, name)
                assert len(output) == 4 and all(len(row) == 7 for row in output)
                assert all(type(color) is int and 0 <= color <= 9 for row in output for color in row)


def test_wrong_axes_never_overwrite_existing_cells_or_create_out_of_bounds_cells():
    grid = _scene()
    for name in ("global_first_anchor", "center_axis"):
        output = AUDIT.python_rival(grid, {"copy_policy": "all"}, name)
        assert len(output) == len(grid)
        assert all(len(row) == len(grid[0]) for row in output)
        assert all(output[r][c] == value for r, row in enumerate(grid)
                   for c, value in enumerate(row) if value)


def test_every_rival_has_a_standalone_rule_program():
    for policy in AUDIT.POLICIES:
        for name in AUDIT.RIVALS:
            program = AUDIT.rival_program({"copy_policy": policy}, name)
            assert program.startswith("(rule! (lambda (g)")
            assert "native_family" not in program
            assert "196a7ec58bbc" not in program


def test_causal_intermediate_records_color_and_nonlocal_consumers():
    selected = AUDIT.intermediate(_scene(), {"copy_policy": "nearest_color"})
    assert selected[0]["selected_color"] == 1
    assert selected[0]["cue_column"] == 6
    assert selected[0]["matching_source_columns"] == [6, 11]
    assert selected[0]["reflected_target_columns"] == [8, 3]
    assert selected[1]["selected_color"] == 4


def test_racket_smoke_native_and_independent_rival_forms():
    family = AUDIT._load_family()
    from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
    runtime = AUDIT.ROOT / "shared/runtime"
    grid = _scene()
    with _local_imports(runtime, AUDIT.HERE.parent):
        apply, _, bridge = _real_evaluator(runtime)
        try:
            for policy in AUDIT.POLICIES:
                settings = {"copy_policy": policy}
                assert _grid(apply(family.program(settings), grid)) == AUDIT.python_intended(grid, settings)
            settings = {"copy_policy": "nearest_color"}
            for name in ("policy_all", "nearest_cell", "farthest_cell", "global_nearest_color",
                         "global_farthest_color", "center_axis", "left_only", "right_only",
                         "most_frequent_color", "most_frequent_nearest_tie", "most_frequent_farthest_tie",
                         "least_frequent_color", "least_frequent_nearest_tie", "least_frequent_farthest_tie",
                         "minimum_mean_color", "maximum_mean_color",
                         "minimum_max_distance_color", "maximum_min_distance_color",
                         "fixed_color_1", "move_sources", "reflect_orphans"):
                assert _grid(apply(AUDIT.rival_program(settings, name), grid)) == AUDIT.python_rival(grid, settings, name)
            fractional = [[0] * 15 for _ in range(4)]
            fractional[0][7] = 9
            for distance, color in ((1, 1), (6, 1), (2, 2), (3, 2), (5, 2)):
                fractional[0][7 - distance] = color
            for name in ("minimum_mean_color", "maximum_mean_color"):
                assert _grid(apply(AUDIT.rival_program(settings, name), fractional)) == AUDIT.python_rival(fractional, settings, name)
        finally:
            bridge.close()
