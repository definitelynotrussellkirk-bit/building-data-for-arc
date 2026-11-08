"""Focused, literal-fixture regressions for the independent tile teaching audit."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest


TASK = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def audit():
    path = TASK / "workspace/parametric/audit_native.py"
    assert path.is_file(), "independent native tile audit is not implemented"
    spec = importlib.util.spec_from_file_location("tile_teaching_audit_test", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def mixed_scene():
    return [
        [2, 2, 0, 9, 2, 0, 0, 9, 0, 0, 0],
        [0, 0, 3, 9, 2, 0, 0, 9, 0, 3, 0],
        [0, 0, 0, 9, 0, 0, 0, 9, 0, 0, 0],
    ]


@pytest.mark.parametrize("settings,expected", [
    ({"turn": "cw", "post": "none"}, [
        [0, 0, 8, 9, 8, 0, 0, 9, 0, 0, 0],
        [0, 0, 8, 9, 8, 0, 0, 9, 0, 0, 0],
        [0, 0, 0, 9, 0, 0, 0, 9, 0, 0, 0]]),
    ({"turn": "ccw", "post": "none"}, [
        [0, 0, 0, 9, 8, 0, 0, 9, 0, 0, 0],
        [8, 0, 0, 9, 8, 0, 0, 9, 0, 0, 0],
        [8, 0, 0, 9, 0, 0, 0, 9, 0, 0, 0]]),
    ({"turn": "cw", "post": "settle_down"}, [
        [0, 0, 0, 9, 0, 0, 0, 9, 0, 0, 0],
        [0, 0, 8, 9, 8, 0, 0, 9, 0, 0, 0],
        [0, 0, 8, 9, 8, 0, 0, 9, 0, 0, 0]]),
    ({"turn": "ccw", "post": "settle_down"}, [
        [0, 0, 0, 9, 0, 0, 0, 9, 0, 0, 0],
        [8, 0, 0, 9, 8, 0, 0, 9, 0, 0, 0],
        [8, 0, 0, 9, 8, 0, 0, 9, 0, 0, 0]]),
])
def test_oracle_turns_only_marked_tiles_and_preserves_separators(audit, settings, expected):
    # Catches wrong direction, unconditional turning, marker retention and aliasing.
    source = mixed_scene()
    before = deepcopy(source)
    assert audit.python_intended(source, settings) == expected
    assert source == before


def disconnected_scene():
    return [
        [0, 0, 0, 0, 0],
        [0, 2, 0, 0, 0],
        [0, 2, 0, 2, 0],
        [0, 0, 0, 0, 0],
        [3, 0, 0, 0, 0],
    ]


def test_settle_translates_all_components_together_after_turn(audit):
    # Catches component settling, per-column packing and pre-turn dropping.
    assert audit.python_intended(disconnected_scene(), {"turn": "cw", "post": "settle_down"}) == [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 8, 8, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 8, 0, 0],
    ]


@pytest.mark.parametrize("bad", [
    [], [[0] * 3] * 2, [[0] * 31] * 3,
    [[True] * 3] * 3, [[2.0] * 3] * 3, [[8] * 3] * 3,
    [[0] * 3, [0] * 3, [0] * 4], [[0] * 4] * 3,
    [[9, 0, 0], [0, 0, 0], [0, 0, 0]],
    [[9, 9, 9], [0, 0, 0], [0, 0, 0]],
    [[0, 0, 0, 9, 9, 0, 0, 0]] * 3,
    [[0, 0, 0, 9, 0, 0, 0, 0]] * 3,
])
def test_independent_grammar_rejects_bad_types_shapes_and_dividers(audit, bad):
    with pytest.raises(ValueError):
        audit.python_intended(bad, {"turn": "cw", "post": "none"})


@pytest.mark.parametrize("bad", [None, {}, {"turn": "cw"}, {"turn": True, "post": "none"},
                                 {"turn": "cw", "post": "other"},
                                 {"turn": "cw", "post": "none", "hidden": 1}])
def test_independent_oracle_rejects_undeclared_settings(audit, bad):
    with pytest.raises(ValueError):
        audit.python_intended(mixed_scene(), bad)


def test_single_tile_30_extension_and_empty_motifs_are_total(audit):
    # The strict lattice extension is required to exercise an exact 30x30 grid.
    source = [[0] * 30 for _ in range(30)]
    source[0][0], source[0][1] = 2, 3
    expected = [[0] * 30 for _ in range(30)]
    expected[29][29] = 8
    assert audit.python_intended(source, {"turn": "cw", "post": "settle_down"}) == expected
    marker_only = [[0, 0, 0], [0, 3, 0], [0, 0, 0]]
    for settings in ({"turn": "cw", "post": "none"}, {"turn": "ccw", "post": "settle_down"}):
        assert audit.python_intended(marker_only, settings) == [[0, 0, 0]] * 3


def core_scene():
    # Hand-selected heterogeneous marker counts/topologies, independent of the sampler.
    roles = [
        ({(0, 0), (1, 0), (2, 0), (2, 1)}, set()),
        ({(0, 1), (1, 1), (2, 1), (2, 2)}, {(0, 2)}),
        ({(0, 0), (0, 1), (2, 3), (3, 4)}, {(2, 2)}),
        ({(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)}, {(0, 4), (4, 4)}),
        ({(0, 3), (1, 3), (2, 3)}, set()),
        ({(0, 3), (1, 1), (1, 3), (2, 1), (3, 4)}, {(1, 0), (4, 2), (4, 4)}),
    ]
    grid = [[9 if row == 5 or col in (5, 11) else 0 for col in range(17)] for row in range(11)]
    for index, (motif, markers) in enumerate(roles):
        row0, col0 = (index // 3) * 6, (index % 3) * 6
        for color, cells in ((2, motif), (3, markers)):
            for row, col in cells:
                grid[row0 + row][col0 + col] = color
    return grid


@pytest.fixture(scope="module")
def executor(audit):
    with audit.protected_evaluator() as evaluator:
        yield evaluator


def test_exact_racket_rivals_agree_with_independent_oracles(audit, executor):
    # Catches malformed protected Racket and semantic drift between implementations.
    for turn in ("cw", "ccw"):
        for post in ("none", "settle_down"):
            settings = {"turn": turn, "post": post}
            for name in audit.rivals(settings):
                for grid in (mixed_scene(), disconnected_scene(), core_scene()):
                    row = executor.evaluate(audit.rival_program(settings, name), grid)
                    assert row["status"] == "ok", (settings, name, row)
                    assert row["output"] == audit.python_rival(grid, settings, name), (settings, name)


def test_marker_pivot_clips_outside_points_before_post_and_handles_empty(audit, executor):
    # About marker (0,2), CW sends motif (0,0) to (-2,2); settling must not rescue it.
    source = [[2, 0, 3], [0, 0, 0], [0, 0, 0]]
    settings = {"turn": "cw", "post": "settle_down"}
    expected = [[0, 0, 0]] * 3
    assert audit.python_rival(source, settings, "marker_pivot_turn") == expected
    row = executor.evaluate(audit.rival_program(settings, "marker_pivot_turn"), source)
    assert row["status"] == "ok" and row["output"] == expected


def test_wrong_order_is_a_real_causal_difference(audit, executor):
    # Moving raw motif to row2 first changes the selected turn's final column.
    source = [[2, 2, 0], [0, 0, 3], [0, 0, 0]]
    settings = {"turn": "cw", "post": "settle_down"}
    intended = [[0, 0, 0], [0, 0, 8], [0, 0, 8]]
    wrong_order = [[8, 0, 0], [8, 0, 0], [0, 0, 0]]
    assert audit.python_intended(source, settings) == intended
    assert audit.python_rival(source, settings, "wrong_order") == wrong_order
    row = executor.evaluate(audit.rival_program(settings, "wrong_order"), source)
    assert row["status"] == "ok" and row["output"] == wrong_order


def _marked_pair():
    return {"input": [[2, 2, 0], [0, 0, 3], [0, 0, 0]],
            "output": [[0, 0, 8], [0, 0, 8], [0, 0, 0]]}


def _unmarked_pair():
    return {"input": [[2, 2, 0], [0, 0, 0], [0, 0, 0]],
            "output": [[8, 8, 0], [0, 0, 0], [0, 0, 0]]}


def test_lesson_retains_minimum_two_demo_one_query_teaching_hole(audit, executor):
    first = _marked_pair()
    second = {"input": [[0, 2, 0], [0, 0, 3], [0, 0, 0]],
              "output": [[0, 0, 0], [0, 0, 8], [0, 0, 0]]}
    query = _unmarked_pair()
    report = audit.assess_rival(executor, {"turn": "cw", "post": "none"}, "rotate_all",
                                [first, second], [query])
    assert report["status"] == "teaching_hole"
    assert report["demo_indices_checked"] == [0, 1]
    assert report["disagreeing_query_indices"] == [0]
    hole = report["first_teaching_hole"]
    assert hole["train"] == [first, second] and hole["test"] == [query]
    assert hole["rival_output"] == [[0, 0, 8], [0, 0, 8], [0, 0, 0]]


def test_rival_stops_at_first_demo_refutation(audit, executor):
    before = executor.request_count
    report = audit.assess_rival(executor, {"turn": "cw", "post": "none"}, "rotate_all",
                                [_unmarked_pair(), _marked_pair()], [_marked_pair()])
    assert report["status"] == "demo_refuted"
    assert report["demo_indices_checked"] == [0] and report["query_indices_checked"] == []
    assert executor.request_count - before == 1


def test_query_agreeing_survivor_is_not_a_refutation(audit, executor):
    pair = _marked_pair()
    report = audit.assess_rival(executor, {"turn": "cw", "post": "none"}, "rotate_all",
                                [pair, pair], [pair])
    assert report["status"] == "query_agreeing_survivor"
    assert report["disagreeing_query_indices"] == [] and report["first_teaching_hole"] is None


def test_cache_reuses_exact_program_input_without_aliasing_outputs(audit, executor):
    program, grid = "(rule! (lambda (g) g))", mixed_scene()
    before = executor.execution_count
    first = executor.evaluate(program, grid)
    first["output"][0][0] = 9
    second = executor.evaluate(program, deepcopy(grid))
    assert second["status"] == "ok" and second["output"] == grid
    assert executor.execution_count - before == 1


def test_protected_runtime_error_never_refutes_a_rival(audit, executor):
    pair = _marked_pair()
    report = audit.assess_program(executor, "error_probe", "(rule! (lambda (g) (/ 1 0)))",
                                  [pair, pair], [pair])
    assert report["status"] == "execution_error"
    assert report["refuting_demo_index"] is None and report["query_indices_checked"] == []
    assert report["error"]["status"] == "error"
