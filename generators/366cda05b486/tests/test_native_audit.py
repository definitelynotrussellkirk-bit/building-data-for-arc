"""Literal geometry and protected execution tests for the independent cluster audit."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest

TASK = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def audit():
    path = TASK / "workspace/parametric/audit_native.py"
    assert path.is_file(), "independent native cluster audit is not implemented"
    spec = importlib.util.spec_from_file_location("cluster_native_audit_test", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def detour_scene():
    grid = [[0] * 19 for _ in range(9)]
    roles = [
        (1, {(3, 3), (3, 4)}),
        (2, {(3, c) for c in range(5, 11)}),
        (8, {(4, 10), (5, 10)} | {(6, c) for c in range(6, 11)}),
        (3, {(6, 5)}), (4, {(6, 4)}), (5, {(5, 4)}),
        (2, {(5, 2), (5, 3), (4, 2)}),
    ]
    for color, cells in roles:
        for r, c in cells:
            grid[r][c] = color
    for r in range(3):
        for c in range(11, 19):
            grid[r][c] = 6 + (r + c) % 2
    return grid


def cycle_scene():
    grid = [[0] * 16 for _ in range(14)]
    roles = [
        (1, {(r, c) for r in (4, 5) for c in (4, 5)}),
        (2, {(r, c) for r in (4, 5) for c in (6, 7)}),
        (4, {(r, c) for r in (6, 7) for c in (6, 7)}),
        (3, {(r, c) for r in (6, 7) for c in (4, 5)}),
        (8, {(2, 3), (2, 4), (3, 4)}),
        (5, {(4, 8), (4, 9)}), (6, {(4, 10), (5, 10), (5, 11)}),
        (7, {(8, 4), (9, 4)}), (3, {(10, 4), (10, 5), (11, 5), (11, 6)}),
        (2, {(6, 12)}), (9, {(6, 13), (7, 13)}),
    ]
    for color, cells in roles:
        for r, c in cells:
            grid[r][c] = color
    return grid


def test_literal_cluster_crop_preserves_zero_holes_and_excludes_diagonal_cluster(audit):
    source = detour_scene()
    before = deepcopy(source)
    assert audit.python_intended(source, {"scope": "cluster"}) == [
        [0, 8, 8, 8, 8, 8, 8, 8, 8],
        [8, 0, 0, 0, 0, 0, 0, 0, 8],
        [8, 8, 8, 0, 0, 0, 0, 0, 8],
        [0, 0, 8, 8, 8, 8, 8, 8, 8],
    ]
    assert source == before


def test_literal_farthest_follows_object_hops_around_detour(audit):
    assert audit.python_intended(detour_scene(), {"scope": "farthest"}) == [[8, 0], [8, 8]]


def test_literal_cycle_keeps_all_maximum_ties_and_complete_objects(audit):
    output = audit.python_intended(cycle_scene(), {"scope": "farthest"})
    assert (len(output), len(output[0])) == (8, 8)
    assert {(r, c) for r, row in enumerate(output) for c, value in enumerate(row) if value} == {
        (0, 6), (1, 6), (1, 7), (6, 0), (6, 1), (7, 1), (7, 2)}


def test_isolated_blue_single_cell_and_multi_cell_are_total(audit):
    for setting in ({"scope": "cluster"}, {"scope": "farthest"}):
        assert audit.python_intended([[1]], setting) == [[8]]
        assert audit.python_intended([[1, 1, 0, 8], [1, 0, 0, 0]], setting) == [[8, 8], [8, 0]]


@pytest.mark.parametrize("bad", [None, [], [[]], [[0]], [[1, 0, 1]], [[True]], [[1.0]],
                                 [[1], [0, 0]], [[1] * 31], [[1]] * 31, [(1,)], [[10]]])
def test_independent_grammar_rejects_invalid_grids_and_seed_counts(audit, bad):
    with pytest.raises(ValueError):
        audit.python_intended(bad, {"scope": "cluster"})


@pytest.mark.parametrize("bad", [None, {}, {"scope": True}, {"scope": "other"},
                                 {"scope": "cluster", "extra": 1}])
def test_independent_oracle_rejects_bad_settings(audit, bad):
    with pytest.raises(ValueError):
        audit.python_intended([[1]], bad)


@pytest.fixture(scope="module")
def executor(audit):
    with audit.protected_evaluator() as evaluator:
        yield evaluator


def test_exact_racket_rivals_match_independent_python(audit, executor):
    for setting in audit.SETTINGS:
        for name in audit.rivals(setting):
            if name.startswith("native_"):
                continue
            for source in (detour_scene(), cycle_scene(), [[1]], [[1, 1, 0, 8], [1, 0, 0, 0]]):
                row = executor.evaluate(audit.rival_program(setting, name), source)
                assert row["status"] == "ok", (setting, name, row)
                assert row["output"] == audit.python_rival(source, setting, name), (setting, name)


def test_actual_native_programs_match_oracle(audit, executor):
    family = audit._load_family()
    for setting in audit.SETTINGS:
        for source in (detour_scene(), cycle_scene(), [[1]]):
            row = executor.evaluate(family.program(setting), source)
            assert row["status"] == "ok", row
            assert row["output"] == audit.python_intended(source, setting)


def test_cell_metric_and_single_tie_are_observably_different(audit):
    intended = audit.python_intended(cycle_scene(), {"scope": "farthest"})
    for name in ("cell_distance_objects", "single_farthest", "graph_leaves", "dfs_depth"):
        assert audit.python_rival(cycle_scene(), {"scope": "farthest"}, name) != intended, name


def _one_cell_pair():
    return {"input": [[1]], "output": [[8]]}


def test_lesson_retains_two_demo_single_query_hole(audit, executor):
    pair = _one_cell_pair()
    query = {"input": detour_scene(), "output": audit.python_intended(detour_scene(), {"scope": "cluster"})}
    report = audit.assess_rival(executor, {"scope": "cluster"}, "seed_only", [pair, pair], [query])
    assert report["status"] == "teaching_hole"
    assert report["demo_indices_checked"] == [0, 1]
    assert report["disagreeing_query_indices"] == [0]
    assert report["first_teaching_hole"]["train"] == [pair, pair]
    assert report["first_teaching_hole"]["test"] == [query]


def test_rival_stops_at_first_demo_refutation(audit, executor):
    pair = {"input": detour_scene(), "output": audit.python_intended(detour_scene(), {"scope": "cluster"})}
    before = executor.request_count
    report = audit.assess_rival(executor, {"scope": "cluster"}, "seed_only", [pair, _one_cell_pair()], [_one_cell_pair()])
    assert report["status"] == "demo_refuted"
    assert report["demo_indices_checked"] == [0] and report["query_indices_checked"] == []
    assert executor.request_count - before == 1


def test_query_agreeing_survivor_stays_explicit(audit, executor):
    pair = _one_cell_pair()
    report = audit.assess_rival(executor, {"scope": "cluster"}, "seed_only", [pair, pair], [pair])
    assert report["status"] == "query_agreeing_survivor"
    assert report["first_teaching_hole"] is None


def test_cache_reuses_exact_program_input_and_detaches_outputs(audit, executor):
    program, source = "(rule! (lambda (g) g))", detour_scene()
    before = executor.execution_count
    first = executor.evaluate(program, source)
    first["output"][0][0] = 9
    second = executor.evaluate(program, deepcopy(source))
    assert second["output"] == source and executor.execution_count - before == 1


def test_execution_error_never_refutes_a_rival(audit, executor):
    pair = _one_cell_pair()
    result = audit.assess_program(executor, "error", "(rule! (lambda (g) (/ 1 0)))", [pair, pair], [pair])
    assert result["status"] == "execution_error" and result["refuting_demo_index"] is None
    assert result["query_indices_checked"] == []
