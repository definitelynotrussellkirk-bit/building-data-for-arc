"""Focused regressions for the independent finite teaching audit."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest


TASK = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def audit():
    path = TASK / "workspace/parametric/audit_native.py"
    assert path.is_file(), "independent native teaching audit is not implemented"
    spec = importlib.util.spec_from_file_location("cap_teaching_audit_test", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def cap_scene():
    return [
        [6, 6, 0, 0, 0, 0, 0, 0, 0],
        [0, 6, 6, 6, 6, 0, 7, 6, 0],
        [0, 0, 0, 6, 0, 0, 0, 0, 0],
        [0, 0, 0, 6, 0, 0, 0, 0, 0],
        [8, 6, 6, 2, 0, 6, 6, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]


def bridge_scene():
    return [
        [0, 6, 6, 0, 0, 0, 0, 8, 0],
        [8, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 6, 6, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 7, 0, 0, 0, 0, 0],
        [0, 6, 6, 0, 0, 0, 0, 8, 0],
    ]


def test_caps_oracle_preserves_singletons_sources_and_occupied_targets(audit):
    # Catches adjacency-only capping, maximum-run restrictions and overwriting.
    source = cap_scene()
    before = deepcopy(source)
    expected = [
        [6, 6, 8, 0, 0, 0, 0, 0, 0],
        [8, 6, 6, 6, 6, 8, 7, 6, 0],
        [0, 0, 0, 6, 0, 0, 0, 0, 0],
        [0, 0, 0, 6, 0, 0, 0, 0, 0],
        [8, 6, 6, 2, 8, 6, 6, 8, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    assert audit.python_intended(source, {"cap_mode": "caps"}) == expected
    assert source == before


def test_bridge_oracle_uses_only_new_caps_and_checks_each_consecutive_interval(audit):
    # Catches old-cyan anchors, cyan pass-through and min/max endpoint pairing.
    source = bridge_scene()
    expected = [
        [8, 6, 6, 8, 0, 0, 0, 8, 0],
        [8, 0, 0, 8, 0, 0, 0, 0, 0],
        [0, 0, 0, 8, 0, 0, 0, 0, 0],
        [8, 6, 6, 8, 0, 0, 0, 0, 0],
        [8, 0, 0, 0, 0, 0, 0, 0, 0],
        [8, 0, 0, 7, 0, 0, 0, 0, 0],
        [8, 6, 6, 8, 0, 0, 0, 8, 0],
    ]
    assert audit.python_intended(source, {"cap_mode": "bridge_caps"}) == expected


@pytest.mark.parametrize("bad", [[], [[0] * 7] * 6, [[0] * 31] * 7,
                                 [[True] * 7] * 7, [[1.0] * 7] * 7,
                                 [[10] * 7] * 7, [[-1] * 7] * 7,
                                 [[0] * 7] * 6 + [[0] * 8]])
def test_independent_grammar_rejects_invalid_typed_grids(audit, bad):
    with pytest.raises(ValueError):
        audit.python_intended(bad, {"cap_mode": "caps"})


@pytest.mark.parametrize("bad", [None, {}, {"cap_mode": True}, {"cap_mode": "other"},
                                 {"cap_mode": "caps", "private": 1}])
def test_independent_oracle_rejects_undeclared_settings(audit, bad):
    with pytest.raises(ValueError):
        audit.python_intended(cap_scene(), bad)


@pytest.fixture(scope="module")
def executor(audit):
    with audit.protected_evaluator() as evaluator:
        yield evaluator


def test_exact_racket_rivals_agree_with_the_independent_oracle_on_literal_scenes(audit, executor):
    # Catches malformed Racket and divergence between the two implementations.
    for mode in ("caps", "bridge_caps"):
        settings = {"cap_mode": mode}
        for name in audit.rivals(settings):
            for grid in (cap_scene(), bridge_scene()):
                row = executor.evaluate(audit.rival_program(settings, name), grid)
                assert row["status"] == "ok", (mode, name, row)
                assert row["output"] == audit.python_rival(grid, settings, name), (mode, name)


def test_bridge_rivals_separate_cyan_pass_through_and_old_cyan_anchors(audit):
    grid = bridge_scene()
    settings = {"cap_mode": "bridge_caps"}
    correct = audit.python_intended(grid, settings)
    passed = audit.python_rival(grid, settings, "allow_cyan_pass")
    anchored = audit.python_rival(grid, settings, "all_cyan_anchors")
    assert correct[2][0] == 0 and passed[2][0] == 8
    assert correct[2][7] == 0 and anchored[2][7] == 8
    assert passed[2][7] == 0


def _lesson_pair(singleton=False):
    grid = [[0] * 7 for _ in range(7)]
    grid[3][2:3 if singleton else 4] = [6] if singleton else [6, 6]
    output = deepcopy(grid)
    if not singleton:
        output[3][1] = output[3][4] = 8
    return {"input": grid, "output": output}


def test_lesson_returns_two_demo_one_query_teaching_hole(audit, executor):
    # A rival matching both demos must remain alive until each query is checked.
    first = _lesson_pair()
    second = {key: list(reversed(value)) for key, value in first.items()}
    second["input"][0][0] = second["output"][0][0] = 2
    query = _lesson_pair(singleton=True)
    settings = {"cap_mode": "caps"}
    report = audit.assess_rival(executor, settings, "adjacent_any6", [first, second], [query])
    assert report["status"] == "teaching_hole"
    assert report["demo_indices_checked"] == [0, 1]
    assert report["disagreeing_query_indices"] == [0]
    hole = report["first_teaching_hole"]
    assert hole["train"] == [first, second]
    assert hole["test"] == [query]
    assert hole["rival_output"][3][1] == 8
    assert hole["rival_output"][3][3] == 8


def test_rival_stops_at_first_demo_refutation(audit, executor):
    # A rejected demonstration must prevent optional second-demo/query work.
    before = executor.request_count
    first = _lesson_pair(singleton=True)
    report = audit.assess_rival(executor, {"cap_mode": "caps"}, "adjacent_any6",
                                [first, _lesson_pair()], [_lesson_pair()])
    assert report["status"] == "demo_refuted"
    assert report["demo_indices_checked"] == [0]
    assert report["query_indices_checked"] == []
    assert executor.request_count - before == 1


def test_query_agreeing_survivor_is_reported_separately(audit, executor):
    pair = _lesson_pair()
    report = audit.assess_rival(executor, {"cap_mode": "caps"}, "adjacent_any6",
                                [pair, pair], [pair])
    assert report["status"] == "query_agreeing_survivor"
    assert report["disagreeing_query_indices"] == []
    assert report["first_teaching_hole"] is None


def test_execution_cache_reuses_exact_program_input_and_does_not_alias_output(audit, executor):
    program = "(rule! (lambda (g) g))"
    grid = cap_scene()
    before = executor.execution_count
    first = executor.evaluate(program, grid)
    first["output"][0][0] = 9
    second = executor.evaluate(program, deepcopy(grid))
    assert second["status"] == "ok" and second["output"] == grid
    assert executor.execution_count - before == 1


def test_runtime_error_is_never_a_demonstration_refutation(audit, executor):
    # Actual protected-Racket errors are audit errors, not evidence against a rule.
    pair = _lesson_pair()
    bad = "(rule! (lambda (g) (/ 1 0)))"
    report = audit.assess_program(executor, "runtime_error_probe", bad, [pair, pair], [pair])
    assert report["status"] == "execution_error"
    assert report["refuting_demo_index"] is None
    assert report["query_indices_checked"] == []
    assert report["error"]["status"] == "error"
