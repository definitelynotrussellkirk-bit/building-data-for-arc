"""Independent literal oracle, exact rival programs and audit lifecycle tests."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest

TASK = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def audit():
    source = TASK / "workspace/parametric/audit_native.py"
    assert source.is_file(), "independent native frames audit is not implemented"
    spec = importlib.util.spec_from_file_location("frames_native_audit_test", source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def paint_frame(grid, top, left, bottom, right):
    for row in range(top, bottom + 1):
        for column in range(left, right + 1):
            if row in (top, bottom) or column in (left, right):
                grid[row][column] = 1


def simple_scene():
    return [[1, 1, 1, 1, 1], [1, 2, 2, 0, 1], [1, 0, 0, 3, 1], [1, 1, 1, 1, 1]]


def nested_scene():
    grid = [[0] * 9 for _ in range(9)]
    paint_frame(grid, 0, 0, 8, 8)
    paint_frame(grid, 3, 3, 5, 5)
    grid[1][1], grid[6][6], grid[4][4] = 2, 4, 3
    return grid


def tied_scene():
    grid = [[0] * 10 for _ in range(5)]
    paint_frame(grid, 0, 0, 3, 3)
    paint_frame(grid, 0, 6, 3, 9)
    grid[1][1], grid[1][7] = 2, 3
    grid[4][3:6] = [4, 4, 4]
    return grid


def open_scene():
    return [[1, 1, 1], [1, 2, 0], [1, 0, 3]]


def test_literal_last_original_seed_fills_entire_interior(audit):
    grid = simple_scene()
    before = deepcopy(grid)
    assert audit.python_intended(grid, {"post": "none"}) == [
        [1, 1, 1, 1, 1], [1, 3, 3, 3, 1], [1, 3, 3, 3, 1], [1, 1, 1, 1, 1]]
    assert grid == before


def test_original_seed_reads_and_row_major_component_writes(audit):
    output = audit.python_intended(nested_scene(), {"post": "none"})
    want = [[1 if row in (0, 8) or col in (0, 8) else 4 for col in range(9)] for row in range(9)]
    want[4][4] = 3
    assert output == want
    for name in ("updated_seeds", "reverse_components", "preserve_blue"):
        assert audit.python_rival(nested_scene(), {"post": "none"}, name) != want


def test_largest_post_uses_filled_component_and_preserves_inner_color(audit):
    output = audit.python_intended(nested_scene(), {"post": "largest_to_8"})
    want = [[1 if row in (0, 8) or col in (0, 8) else 8 for col in range(9)] for row in range(9)]
    want[4][4] = 3
    assert output == want
    assert audit.python_rival(nested_scene(), {"post": "largest_to_8"}, "pre_fill_largest") != want


def test_all_largest_ties_are_highlighted_and_blue_is_ineligible(audit):
    output = audit.python_intended(tied_scene(), {"post": "largest_to_8"})
    assert all(output[row][col] == 8 for row in (1, 2) for col in (1, 2, 7, 8))
    assert output[4][3:6] == [4, 4, 4]
    for name in ("single_largest", "include_blue", "smallest"):
        assert audit.python_rival(tied_scene(), {"post": "largest_to_8"}, name) != output


def test_open_blue_shape_and_freestanding_color_are_total(audit):
    assert audit.python_intended(open_scene(), {"post": "none"}) == open_scene()
    assert audit.python_intended(open_scene(), {"post": "largest_to_8"}) == [
        [1, 1, 1], [1, 8, 0], [1, 0, 8]]


@pytest.mark.parametrize("bad", [None, [], [[]], [[1]], [[0] * 3 for _ in range(3)],
                                  [[1, 1, 1], [1, 0, 1], [1, 1, 1]],
                                  [[1, 1, 1], [1, True, 1], [1, 1, 1]],
                                  [[1, 1, 1], [1, 2.0, 1], [1, 1, 1]],
                                  [[1, 1], [1]], [[1] * 31] * 3,
                                  [[1] * 3] * 31, [(1, 1, 1)] * 3])
def test_independent_native_grammar_rejects_invalid_inputs(audit, bad):
    with pytest.raises(ValueError):
        audit.python_intended(bad, {"post": "none"})


@pytest.mark.parametrize("bad", [None, {}, {"post": True}, {"post": "other"},
                                 {"post": "none", "extra": 1}])
def test_independent_settings_are_strict(audit, bad):
    with pytest.raises(ValueError):
        audit.python_intended(simple_scene(), bad)


@pytest.fixture(scope="module")
def executor(audit):
    with audit.protected_evaluator() as evaluator:
        yield evaluator


def test_exact_racket_rivals_agree_with_independent_python(audit, executor):
    for setting in audit.SETTINGS:
        for name in audit.rivals(setting):
            if name.startswith("native_"):
                continue
            for grid in (simple_scene(), nested_scene(), tied_scene(), open_scene()):
                row = executor.evaluate(audit.rival_program(setting, name), grid)
                assert row["status"] == "ok", (setting, name, row)
                assert row["output"] == audit.python_rival(grid, setting, name), (setting, name)


def test_actual_native_programs_agree_with_independent_python(audit, executor):
    family = audit._load_family()
    for setting in audit.SETTINGS:
        for grid in (simple_scene(), nested_scene(), tied_scene(), open_scene()):
            row = executor.evaluate(family.program(setting), grid)
            assert row["status"] == "ok", row
            assert row["output"] == audit.python_intended(grid, setting)


def _fixed_pair():
    return {"input": [[1, 1, 1], [1, 8, 1], [1, 1, 1]],
            "output": [[1, 1, 1], [1, 8, 1], [1, 1, 1]]}


def test_lesson_keeps_minimal_demo_only_survivor_hole(audit, executor):
    pair = _fixed_pair()
    query = {"input": simple_scene(), "output": audit.python_intended(simple_scene(), {"post": "none"})}
    result = audit.assess_rival(executor, {"post": "none"}, "first_seed", [pair, pair], [query])
    assert result["status"] == "teaching_hole"
    assert result["demo_indices_checked"] == [0, 1]
    assert result["disagreeing_query_indices"] == [0]
    assert result["first_teaching_hole"]["train"] == [pair, pair]


def test_refuted_rival_never_sees_queries(audit, executor):
    pair = {"input": simple_scene(), "output": audit.python_intended(simple_scene(), {"post": "none"})}
    before = executor.request_count
    result = audit.assess_rival(executor, {"post": "none"}, "first_seed", [pair, _fixed_pair()], [_fixed_pair()])
    assert result["status"] == "demo_refuted" and result["refuting_demo_index"] == 0
    assert result["query_indices_checked"] == [] and executor.request_count - before == 1


def test_query_agreeing_survivor_is_explicit(audit, executor):
    pair = _fixed_pair()
    result = audit.assess_rival(executor, {"post": "none"}, "first_seed", [pair, pair], [pair])
    assert result["status"] == "query_agreeing_survivor" and result["first_teaching_hole"] is None


def test_error_never_refutes_rival(audit, executor):
    pair = _fixed_pair()
    result = audit.assess_program(executor, "error", "(rule! (lambda (g) (/ 1 0)))", [pair, pair], [pair])
    assert result["status"] == "execution_error" and result["refuting_demo_index"] is None
    assert result["query_indices_checked"] == []


def test_exact_cache_detaches_mutable_outputs(audit, executor):
    program, grid = "(rule! (lambda (g) g))", nested_scene()
    before = executor.execution_count
    first = executor.evaluate(program, grid)
    first["output"][0][0] = 0
    second = executor.evaluate(program, deepcopy(grid))
    assert second["output"] == grid and executor.execution_count - before == 1
