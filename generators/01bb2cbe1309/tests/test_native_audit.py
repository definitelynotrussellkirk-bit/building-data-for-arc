"""Literal controls for the independently authored bounded teaching audit.

No expectation is derived by the family, the audit oracle, or a Racket rival.
The nontrivial scan-count grids were checked window by window before coding.
"""
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/audit_native.py"


@pytest.fixture(scope="module")
def audit():
    assert PATH.is_file(), "The independent audit implementation is missing"
    spec = spec_from_file_location("_diagonal_native_audit_tests", PATH)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


G = [[2, 0, 2, 0], [0, 0, 0, 2], [0, 2, 0, 0]]
G1 = [[2, 0, 2, 2], [0, 0, 2, 2], [0, 2, 0, 0]]
G2 = [[2, 0, 2, 2], [0, 2, 2, 2], [0, 2, 2, 0]]
G3 = [[2, 2, 2, 2], [2, 2, 2, 2], [0, 2, 2, 0]]
G90 = [[0, 0, 2], [2, 0, 0], [0, 0, 2], [0, 2, 0]]
G90_1 = [[0, 0, 2], [2, 0, 0], [0, 2, 2], [0, 2, 2]]
G90_2 = [[0, 0, 2], [2, 2, 0], [2, 2, 2], [0, 2, 2]]
G90_3 = [[0, 2, 2], [2, 2, 2], [2, 2, 2], [0, 2, 2]]
FOUR_WAVES = [[2, 0, 2, 0, 0], [0, 0, 0, 0, 2], [0, 2, 0, 2, 0]]
FOUR_WAVES_3 = [[2, 0, 2, 2, 0], [0, 2, 2, 2, 2], [0, 2, 2, 2, 2]]
FOUR_WAVES_FIXED = [[2, 2, 2, 2, 0], [2, 2, 2, 2, 2], [0, 2, 2, 2, 2]]

# Two original windows compete for the central zero. The later bottom-right
# window wins in row-major order; reversing the window order makes color 2 win.
CONFLICT = [[0, 2, 0], [2, 0, 3], [0, 3, 0]]
CONFLICT_FORWARD = [[2, 2, 0], [2, 3, 3], [0, 3, 3]]
CONFLICT_REVERSE = [[2, 2, 0], [2, 2, 3], [0, 3, 3]]
LATE_CONFLICT = [[0, 2, 0], [0, 0, 2], [2, 0, 3], [3, 0, 0], [0, 3, 0]]
LATE_CONFLICT_2 = [[0, 2, 2], [2, 2, 2], [2, 3, 3], [3, 3, 3], [3, 3, 0]]
LATE_CONFLICT_REVERSE_2 = [[0, 2, 2], [2, 2, 2], [2, 2, 3], [3, 3, 3], [3, 3, 0]]


# Changing each named rival to identity, the intended rule, or a different
# scan count must break at least one literal assertion in this table.
CASES = [
    (1, "reference", [[3, 0], [0, 3]], [[3, 3], [3, 3]]),
    (2, "reference", [[0, 4], [4, 0]], [[4, 4], [4, 4]]),
    (1, "reference", [[3, 9], [0, 3]], [[3, 9], [0, 3]]),
    (1, "reference", [[0, 0], [0, 0]], [[0, 0], [0, 0]]),
    (1, "reference", [[3, 0], [0, 5]], [[3, 0], [0, 5]]),
    (1, "reference", CONFLICT, CONFLICT_FORWARD),
    (1, "snapshot1", G, G1),
    (1, "snapshot2", G, G2),
    (2, "snapshot3", G, G3),
    (1, "snapshot3", FOUR_WAVES, FOUR_WAVES_3),
    (1, "fixedpoint", FOUR_WAVES, FOUR_WAVES_FIXED),
    (1, "identity", [[3, 0], [0, 3]], [[3, 0], [0, 3]]),
    (1, "inplace_forward1", G, G2),
    (2, "inplace_forward2", G, G3),
    (1, "inplace_reverse1", G, G1),
    (2, "inplace_reverse2", G, G3),
    (1, "inplace_forward1", G90, G90_1),
    (2, "inplace_forward2", G90, G90_2),
    (1, "inplace_reverse1", G90, G90_3),
    (2, "inplace_reverse2", G90, G90_3),
    (2, "skip_A", G, G1),
    (1, "main_only", [[0, 3], [3, 0]], [[0, 3], [3, 0]]),
    (1, "main_only", [[3, 0], [0, 3]], [[3, 3], [3, 3]]),
    (1, "anti_only", [[3, 0], [0, 3]], [[3, 0], [0, 3]]),
    (1, "anti_only", [[0, 3], [3, 0]], [[3, 3], [3, 3]]),
    (1, "ignore_blockers", [[3, 9], [0, 3]], [[3, 9], [3, 3]]),
    (1, "ignore_blockers", [[9, 3], [3, 0]], [[9, 3], [3, 3]]),
    (1, "axis_pairs", [[3, 3], [0, 0]], [[3, 3], [3, 3]]),
    (1, "axis_pairs", [[0, 0], [4, 4]], [[4, 4], [4, 4]]),
    (1, "axis_pairs", [[5, 0], [5, 0]], [[5, 5], [5, 5]]),
    (1, "axis_pairs", [[0, 6], [0, 6]], [[6, 6], [6, 6]]),
    (1, "axis_pairs", [[3, 0], [0, 3]], [[3, 3], [3, 3]]),
    (1, "endpoint_mismatch", [[3, 0], [0, 5]], [[3, 3], [3, 5]]),
    (1, "endpoint_mismatch", [[0, 4], [6, 0]], [[4, 4], [6, 4]]),
    (1, "reverse_snapshot", CONFLICT, CONFLICT_REVERSE),
    (2, "reverse_snapshot", LATE_CONFLICT, LATE_CONFLICT_REVERSE_2),
    (2, "reference", LATE_CONFLICT, LATE_CONFLICT_2),
    (1, "fill8", [[3, 0], [0, 3]], [[3, 8], [8, 3]]),
    (1, "main_then_anti", G, G2),
    (1, "main_then_anti", G90, G90_1),
    (1, "anti_then_main", G, G1),
    (1, "anti_then_main", G90, G90_2),
    (2, "reverse_second_snapshot", LATE_CONFLICT, LATE_CONFLICT_REVERSE_2),
    (1, "reverse_second_snapshot", CONFLICT, CONFLICT_FORWARD),
]


@pytest.mark.parametrize("passes,name,grid,want", CASES)
def test_python_rivals_have_literal_meanings(audit, passes, name, grid, want):
    original = deepcopy(grid)
    assert audit.rival_reference(grid, {"passes": passes}, name) == want
    assert grid == original, "An oracle must not mutate its argument"


@pytest.fixture(scope="module")
def protected(audit):
    with audit._local_imports(audit.RUNTIME, audit.HOME):
        apply, identity, bridge = audit._real_evaluator(audit.RUNTIME)
        assert identity["backend"] == "racket" and identity["protected"] is True
        try:
            yield apply
        finally:
            bridge.close()


@pytest.mark.parametrize("passes,name,grid,want", CASES)
def test_protected_racket_rivals_have_literal_meanings(audit, protected, passes, name, grid, want):
    assert protected(audit.rival_program({"passes": passes}, name), grid) == want


def test_every_named_extra_has_a_literal_control(audit):
    assert set(audit.RIVALS) <= {case[1] for case in CASES}


@pytest.mark.parametrize("passes", [1, 2])
def test_every_rival_is_total_on_thin_and_full_size_grids(audit, protected, passes):
    grids = [[[0]], [[8]], [[0, 2, 0, 9]], [[0], [2], [0], [9]],
             [[0] * 30 for _ in range(30)], [[7] * 30 for _ in range(30)]]
    for name in ("reference", "snapshot1", "snapshot2", *audit.RIVALS):
        for grid in grids:
            expected = deepcopy(grid)  # No 2x2 completion can fire on these controls.
            assert audit.rival_reference(grid, {"passes": passes}, name) == expected, name
            assert protected(audit.rival_program({"passes": passes}, name), grid) == expected, name


@pytest.mark.parametrize("bad", [[], [[]], [[True]], [[1.0]], [[10]], [[-1]], [[0], [0, 1]], [[0] * 31]])
def test_python_oracle_rejects_invalid_arc_grids(audit, bad):
    with pytest.raises(ValueError):
        audit.reference(bad, {"passes": 1})


@pytest.mark.parametrize("bad", [{}, {"passes": True}, {"passes": 0}, {"passes": 3}, {"passes": 1, "x": 2}])
def test_python_oracle_rejects_undeclared_settings(audit, bad):
    with pytest.raises(ValueError):
        audit.reference([[0]], bad)


def test_fit_uses_only_first_two_demonstrations(audit, protected):
    demonstrations = [{"input": [[1]], "output": [[1]]},
                      {"input": [[2]], "output": [[2]]},
                      {"input": [[3]], "output": [[4]]}]
    row = audit.fit_hypothesis(protected, audit.rival_program({"passes": 1}, "identity"),
                               demonstrations, lambda grid: grid)
    assert row["survives_demonstrations"] is True
    assert row["executed_demo_indices"] == [0, 1]
    assert row["demo_outputs"] == [[[1]], [[2]]]


def test_fit_executes_both_teaching_demos_and_reports_every_rejection(audit, protected):
    demonstrations = [{"input": [[1]], "output": [[2]]},
                      {"input": [[3]], "output": [[4]]}]
    row = audit.fit_hypothesis(protected, audit.rival_program({"passes": 1}, "identity"),
                               demonstrations, lambda grid: grid)
    assert row["survives_demonstrations"] is False
    assert row["rejected_by_demo_indices"] == [0, 1]


def test_execution_error_is_not_treated_as_a_refutation(audit):
    def broken(program, grid):
        raise RuntimeError("controlled execution failure")
    with pytest.raises(RuntimeError, match="controlled execution failure"):
        audit.fit_hypothesis(broken, "program", [{"input": [[1]], "output": [[1]]}] * 2)


def test_python_racket_semantic_disagreement_fails_closed(audit, protected):
    with pytest.raises(ValueError, match="meaning mismatch"):
        audit.fit_hypothesis(protected, audit.rival_program({"passes": 1}, "identity"),
                             [{"input": [[1]], "output": [[1]]}] * 2, lambda grid: [[2]])


def test_cache_keys_exact_program_and_input_without_output_aliasing(audit):
    calls = []
    def apply(program, grid):
        calls.append((program, deepcopy(grid)))
        return grid
    cached = audit.CachedEvaluator(apply)
    first = cached("p", [[1]])
    first[0][0] = 9
    assert cached("p", [[1]]) == [[1]]
    assert cached("p", [[2]]) == [[2]]
    assert cached("q", [[1]]) == [[1]]
    assert calls == [("p", [[1]]), ("p", [[2]]), ("q", [[1]])]
    assert (cached.requests, cached.evaluations, cached.cache_hits) == (4, 3, 1)
    assert [row["cache_hit"] for row in cached.records] == [False, True, False, False]


def test_cache_keeps_errors_visible_and_never_caches_them(audit):
    def broken(program, grid):
        raise RuntimeError("controlled execution failure")
    cached = audit.CachedEvaluator(broken)
    for _ in range(2):
        with pytest.raises(RuntimeError, match="controlled execution failure"):
            cached("bad", [[1]])
    assert (cached.evaluations, cached.cache_hits) == (2, 0)
    assert len(cached.records) == 2
    assert all(row["status"] == "error" for row in cached.records)


def test_existing_output_is_never_overwritten(audit, tmp_path):
    marker = tmp_path / "retained.txt"
    marker.write_text("preserve these bytes")
    with pytest.raises(FileExistsError):
        audit.run(tmp_path)
    assert marker.read_text() == "preserve these bytes"
