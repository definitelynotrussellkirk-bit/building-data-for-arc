from __future__ import annotations

import copy
import importlib
import itertools

import pytest

from scripts.canonical_profile_gate import canonical_pairs

GEN = importlib.import_module("puzzle_generators.per_puzzle.0083f06314c3.generator")
PROBE = importlib.import_module("puzzle_generators.per_puzzle.0083f06314c3.workspace.review_probe")


def test_nonoverlap_rival_fits_all_canonical_but_not_union_witness():
    for pair in canonical_pairs(GEN.TASK_ID):
        assert PROBE.disjoint_rival(GEN, pair["input"]) == pair["output"]
    grid = PROBE.overlap_fixture(GEN)
    assert GEN.self_check(grid) == []
    output = GEN.rule_mirror(grid)
    assert sum(v == 8 for row in output for v in row) == 5
    assert PROBE.disjoint_rival(GEN, grid) != output


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("seed", [100, 101])
def test_default_four_slot_lesson_has_overlapping_occurrences(seed, difficulty):
    grids = [GEN.generate(seed, i, difficulty=difficulty) for i in range(8)]
    for start in range(5):
        lessons = grids[start:start + 4]
        assert any(PROBE.disjoint_rival(GEN, g) != GEN.rule_mirror(g) for g in lessons)
    assert sum(not GEN.strict_canonical_like(g) for g in grids) == 4


def test_selector_one_is_reachable_in_default_distribution():
    selectors = {GEN._analyze(GEN.generate(2000 + i, i, difficulty="medium"))["selector"]
                 for i in range(120)}
    assert 1 in selectors


@pytest.mark.parametrize("location", ["template", "selector", "board"])
def test_stray_structural_nine_is_rejected(location):
    grid = copy.deepcopy(canonical_pairs(GEN.TASK_ID)[0]["input"])
    ranges, _ = GEN._panel_ranges(grid)
    if location == "template":
        grid[0][1] = 9  # Inside the template bounding box, but not a divider.
    elif location == "selector":
        grid[1][ranges[2][0]] = 9  # A second nonzero selector, ignored by old check.
    else:
        grid[-1][ranges[3][1]] = 9
    assert GEN.self_check(grid), f"accepted stray structural 9 in {location}"


@pytest.mark.parametrize("bad_value", [True, 0.0, 2.0, "0", None, [], {}])
def test_invalid_arc_color_type_returns_diagnostic_not_exception(bad_value):
    grid = copy.deepcopy(canonical_pairs(GEN.TASK_ID)[0]["input"])
    grid[0][1] = bad_value
    assert GEN.self_check(grid)


def test_single_copy_override_is_not_forced_into_overlap():
    for i in (1, 3):
        grid = GEN.generate(10, i, difficulty="easy", selected_copies=1)
        assert GEN.observe_overrides(grid)["selected_copies"] == 1
        assert GEN.self_check(grid) == []


def test_each_declared_shape_has_an_exact_two_occurrence_overlap_layout():
    for shapes in GEN._SHAPES_BY_SIZE.values():
        for cells in shapes:
            layouts = GEN._overlap_layouts(cells)
            assert layouts
            for union, offsets, reserved in layouts:
                assert len(union) < 2 * len(cells)
                assert set(union) <= set(reserved)
                assert len(offsets) == 2
                board = GEN._template_grid(union, 2)
                template = GEN._template_grid(cells, 2)
                assert set(GEN._match_positions(board, template)) == set(offsets)


@pytest.mark.parametrize("values", itertools.product((6, 8), (3, 4), (8, 12), (3, 5), (1, 2), (1, 2)))
def test_all_axis_corners_remain_exact(values):
    overrides = dict(zip(GEN.AXES, values))
    grid = GEN.generate(11, 3, difficulty="hard", **overrides)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == overrides


def test_four_demo_lessons_refute_registered_rivals():
    assert GEN.EXAMPLES_NEEDED == 4
    for seed in (42, 43):
        grids = [GEN.generate(seed, i, difficulty="medium") for i in range(10)]
        for start in range(6):
            demos = [{"input": g, "output": GEN.rule_mirror(g)} for g in grids[start:start + 4]]
            query = {"input": grids[start + 4]}
            assert GEN.lesson_identifiable(demos, query) == []
