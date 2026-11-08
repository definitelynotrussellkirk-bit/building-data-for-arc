"""Behavioral regressions for rotation semantics, overrides, and teaching.

These tests use an independent pixel oracle. Authoritative Racket parity and
the broader lesson census are retained separately by the review workflow.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from importlib import util
from pathlib import Path
import sys

import pytest

# The task-test runner uses pytest's importlib mode, which deliberately does
# not add this directory to sys.path. Bind the helper to this test's own file
# rather than relying on cwd, a sibling checkout, or pytest's import mode.
_ORACLE_SPEC = util.spec_from_file_location(
    "shape_matrix_oracle_84aeaf4792a8",
    Path(__file__).resolve().with_name("shape_matrix_oracle.py"),
)
assert _ORACLE_SPEC is not None and _ORACLE_SPEC.loader is not None
_ORACLE = util.module_from_spec(_ORACLE_SPEC)
sys.modules[_ORACLE_SPEC.name] = _ORACLE
_ORACLE_SPEC.loader.exec_module(_ORACLE)

from shape_matrix_oracle_84aeaf4792a8 import (
    INDEPENDENT_RIVALS, J4, L3, L4, T4,
    assert_domain, canonical, components, distinguishing_grid, draw,
    load_generator, observed, partition, rotation_key, solve,
    supported_shape_classes,
)


BANDS = ("easy", "medium", "hard")
AXIS_BOUNDS = {"grid_h": (8, 18), "grid_w": (12, 22),
               "n_components": (2, 6), "n_families": (1, 6),
               "n_distinct_colors": (1, 6)}
CANONICAL_SHORTCUT_NAMES = set(INDEPENDENT_RIVALS) - {"translation_only"}
TEACHING_RIVAL_NAMES = set(INDEPENDENT_RIVALS) - {"fixed_four"}


@pytest.fixture(scope="module")
def gen():
    return load_generator()


@pytest.mark.parametrize("pair", canonical(), ids=lambda p: f"{p['split']}-{p['pair_index']}")
def test_all_canonical_pairs_are_accepted_and_match_independent_rotation_oracle(gen, pair):
    assert gen.self_check(deepcopy(pair["input"])) == []
    assert solve(pair["input"]) == pair["output"]
    assert_domain(pair["input"])


def test_verified_counterexample_separates_rotation_from_reflection_and_box_statistics(gen):
    grid = distinguishing_grid()
    expected = [[5, 0, 8, 0], [0, 5, 0, 0], [8, 0, 5, 0], [0, 0, 0, 5]]
    assert solve(grid) == expected
    assert gen.self_check(grid) == []
    assert {obj.color for obj in components(grid)} == {2, 3, 4, 5}
    assert len({rotation_key(L4), rotation_key(J4), rotation_key(T4)}) == 3
    for name in TEACHING_RIVAL_NAMES:
        assert INDEPENDENT_RIVALS[name](grid) != expected, name
        assert gen.SEMANTIC_RIVALS[name](deepcopy(grid)) != expected, name


def test_minimal_exact_joint_request_is_not_ignored(gen):
    # This canvas is supported by both the original and repaired generators;
    # failure therefore isolates ignored family/color controls, not scale.
    grid = gen.generate(43, 1, grid_h=10, grid_w=14, n_components=3,
                        n_families=1, n_distinct_colors=1)
    assert observed(grid) == {"grid_h": 10, "grid_w": 14, "n_components": 3,
                              "n_families": 1, "n_distinct_colors": 1}
    assert_domain(grid)


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("count", range(2, 7))
def test_every_feasible_joint_count_family_color_request_is_realized(gen, band, count):
    # Ninety feasible triples per band. The smallest canvas also exercises
    # packing feasibility when all six components have distinct families.
    for families in range(1, count + 1):
        for colors in range(1, count + 1):
            requested = {"grid_h": 8, "grid_w": 12, "n_components": count,
                         "n_families": families, "n_distinct_colors": colors}
            grid = gen.generate(700 + count * 100 + families * 10 + colors,
                                2, difficulty=band, **requested)
            assert observed(grid) == requested
            assert_domain(grid)
            assert gen.self_check(grid) == []


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("height,width", [(8, 12), (8, 22), (18, 12), (18, 22)])
def test_canvas_endpoint_overrides_work_in_every_difficulty(gen, band, height, width):
    grid = gen.generate(941, 0, difficulty=band, grid_h=height, grid_w=width,
                        n_components=6, n_families=6, n_distinct_colors=6)
    assert (len(grid), len(grid[0])) == (height, width)
    assert_domain(grid)
    assert gen.self_check(grid) == []


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("axis", ("n_families", "n_distinct_colors"))
@pytest.mark.parametrize("value", (1, 2, 5, 6))
def test_unpinned_component_count_accommodates_one_explicit_request(gen, band, axis, value):
    for index in (0, 1):
        grid = gen.generate(115, index, difficulty=band, **{axis: value})
        actual = observed(grid)
        assert actual[axis] == value
        assert max(2, value) <= actual["n_components"] <= 6
        assert_domain(grid)
        assert gen.self_check(grid) == []


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("families,colors", [(6, 1), (1, 6), (5, 6), (6, 5)])
def test_unpinned_component_count_accommodates_joint_requests(gen, band, families, colors):
    grid = gen.generate(273, 0, difficulty=band, n_families=families,
                        n_distinct_colors=colors)
    actual = observed(grid)
    assert actual["n_components"] == 6
    assert actual["n_families"] == families
    assert actual["n_distinct_colors"] == colors
    assert_domain(grid)


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("count", range(2, 6))
@pytest.mark.parametrize("axis", ("n_families", "n_distinct_colors"))
def test_explicit_incompatible_counts_fail_instead_of_clipping(gen, band, count, axis):
    with pytest.raises(ValueError):
        gen.generate(22, 0, difficulty=band, n_components=count, **{axis: count + 1})


@pytest.mark.parametrize("axis", AXIS_BOUNDS)
@pytest.mark.parametrize("bad", (True, False, 3.0, "3", None, [], {}))
def test_integer_controls_reject_coercible_and_noninteger_values(gen, axis, bad):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 1, **{axis: bad})


@pytest.mark.parametrize("axis", AXIS_BOUNDS)
def test_out_of_range_controls_reject_both_boundaries(gen, axis):
    low, high = AXIS_BOUNDS[axis]
    for bad in (low - 1, high + 1):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(0, 1, **{axis: bad})


def test_unknown_override_is_rejected(gen):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 1, misspelled_axis=4)


@pytest.mark.parametrize("count", (2, 6))
def test_disconnected_objects_may_share_a_color(gen, count):
    anchors = [(0, 0), (0, 4), (0, 8), (4, 0), (4, 4), (4, 8)]
    grid = draw([(2, anchor, L3) for anchor in anchors[:count]], height=8, width=12)
    assert observed(grid)["n_components"] == count
    assert observed(grid)["n_distinct_colors"] == 1
    assert gen.self_check(grid) == []
    assert_domain(grid)


def invalid_domain_cases():
    valid_specs = [(2, (0, 0), L3), (3, (4, 4), L3)]
    cases = {"empty": [], "empty_row": [[]], "blank": [[0] * 14 for _ in range(12)],
             "single_component": draw(valid_specs[:1]),
             "too_short": draw(valid_specs, height=7),
             "too_tall": draw(valid_specs, height=19),
             "too_narrow": draw(valid_specs, width=11),
             "too_wide": draw(valid_specs, width=23),
             "tiny_component": draw([(2, (0, 0), L3), (3, (4, 4), ((0, 0), (0, 1)))]),
             "large_component": draw([(2, (0, 0), L3), (3, (4, 4),
                                        tuple((r, c) for r in range(2) for c in range(3)))]),
             "long_bbox": draw([(2, (0, 0), L3), (3, (4, 4), tuple((0, c) for c in range(4)))]),
             "diagonal_contact": draw([(2, (1, 1), L3), (3, (3, 2), L3)]),
             "orthogonal_contact": draw([(2, (1, 1), L3), (3, (2, 2), L3)])}
    anchors = [(r, c) for r in (0, 4, 8) for c in (0, 4, 8)]
    cases["seven_components"] = draw([(2 + index % 2, anchor, L3)
                                       for index, anchor in enumerate(anchors[:7])])
    ragged = draw(valid_specs)
    ragged[-1].pop()
    cases["ragged"] = ragged
    for name, value in (("negative", -1), ("color_ten", 10), ("bool", True),
                        ("float", 2.0), ("string", "2"), ("null", None)):
        grid = draw(valid_specs)
        grid[-1][-1] = value
        cases[name] = grid
    return cases


INVALID_CASES = invalid_domain_cases()


@pytest.mark.parametrize("name", INVALID_CASES)
def test_validator_rejects_malformed_and_off_domain_grids_with_reasons(gen, name):
    result = gen.self_check(deepcopy(INVALID_CASES[name]))
    assert isinstance(result, list) and result, name
    assert all(isinstance(reason, str) and reason for reason in result)


def test_every_connected_small_rotation_class_is_reachable(gen):
    expected = supported_shape_classes()
    assert Counter(map(len, expected)) == {3: 2, 4: 6, 5: 11}
    emitted = set()
    for band in BANDS:
        for seed in range(32):
            grid = gen.generate(6000 + seed, 1, difficulty=band, grid_h=12, grid_w=16,
                                n_components=6, n_families=6, n_distinct_colors=4)
            keys = {rotation_key(obj.cells) for obj in components(grid)}
            assert len(keys) == 6
            assert keys <= expected
            emitted.update(keys)
    assert emitted == expected, f"Missing independent shape classes: {expected - emitted}"


def test_canonical_shortcuts_are_real_and_translation_only_is_excluded(gen):
    for declaration in (gen.SEMANTIC_RIVALS, gen.LESSON_COMPETITORS):
        assert set(INDEPENDENT_RIVALS) <= set(declaration)
        assert all(callable(declaration[name]) for name in INDEPENDENT_RIVALS)
    assert CANONICAL_SHORTCUT_NAMES <= set(gen.CANONICAL_SHORTCUTS)
    assert "translation_only" not in gen.CANONICAL_SHORTCUTS
    pairs = canonical()
    for name in CANONICAL_SHORTCUT_NAMES:
        assert all(INDEPENDENT_RIVALS[name](pair["input"]) == pair["output"] for pair in pairs), name
        assert all(gen.CANONICAL_SHORTCUTS[name](deepcopy(pair["input"])) == pair["output"]
                   for pair in pairs), name
    assert any(INDEPENDENT_RIVALS["translation_only"](pair["input"]) != pair["output"]
               for pair in pairs)


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("seed", (2, 19, 71))
def test_unconstrained_teaching_schedule_preserves_scale_and_refutes_shape_rivals(gen, band, seed):
    even_partitions = []
    odd_counts = set()
    for index in range(8):
        grid = gen.generate(seed, index, difficulty=band)
        assert grid == gen.generate(seed, index, difficulty=band)
        assert_domain(grid)
        assert gen.self_check(grid) == []
        if index % 2 == 0:
            assert 12 <= len(grid) <= 13 and 14 <= len(grid[0]) <= 16
            assert {value for row in grid for value in row} == {0, 2, 3, 4, 5}
            assert len(components(grid)) == 4
            even_partitions.append(partition(grid))
            expected = solve(grid)
            for name in TEACHING_RIVAL_NAMES:
                assert INDEPENDENT_RIVALS[name](grid) != expected, (seed, index, band, name)
                assert gen.SEMANTIC_RIVALS[name](deepcopy(grid)) != expected, (seed, index, band, name)
        else:
            count = len(components(grid))
            assert count in {2, 3, 5, 6}
            odd_counts.add(count)
    assert set(even_partitions) == {(2, 1, 1), (2, 2)}
    assert all(a != b for a, b in zip(even_partitions, even_partitions[1:]))
    assert len(odd_counts) >= 2


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("seed", (2, 19, 71))
def test_every_four_pair_window_and_holdout_refutes_the_declared_rivals(gen, band, seed):
    assert gen.EXAMPLES_NEEDED == 3
    declarations = {**gen.SEMANTIC_RIVALS, **gen.LESSON_COMPETITORS,
                    **gen.CANONICAL_SHORTCUTS}
    for start in range(4):
        lesson = []
        for index in range(start, start + 4):
            grid = gen.generate(seed, index, difficulty=band)
            lesson.append({"input": grid, "output": solve(grid)})
        for held_out in range(4):
            demos = [pair for index, pair in enumerate(lesson) if index != held_out]
            query = lesson[held_out]
            for name, rival in declarations.items():
                assert any(rival(deepcopy(pair["input"])) != pair["output"] for pair in demos), (
                    seed, band, start, held_out, name)
            assert gen.lesson_identifiable(deepcopy(demos), deepcopy(query)) == []


def test_lesson_hook_detects_a_canonical_fitting_shortcut_that_changes_the_query(gen):
    demos = [{"input": pair["input"], "output": pair["output"]} for pair in canonical()[:3]]
    query_grid = distinguishing_grid()
    query = {"input": query_grid, "output": solve(query_grid)}
    assert all(INDEPENDENT_RIVALS["area_bbox"](pair["input"]) == pair["output"] for pair in demos)
    assert INDEPENDENT_RIVALS["area_bbox"](query_grid) != query["output"]
    result = gen.lesson_identifiable(deepcopy(demos), deepcopy(query))
    assert isinstance(result, list) and result
    assert all(isinstance(reason, str) and reason for reason in result)


def test_surviving_competitor_that_agrees_on_query_is_not_declared_ambiguous(gen):
    pairs = canonical()
    demos = [{"input": pair["input"], "output": pair["output"]} for pair in pairs[:3]]
    query = {"input": pairs[-1]["input"], "output": pairs[-1]["output"]}
    assert gen.lesson_identifiable(deepcopy(demos), deepcopy(query)) == []
