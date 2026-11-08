"""Rival meaning and failure-path checks for the finite protected audit."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest


PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/audit_native.py"


@pytest.fixture(scope="module")
def audit():
    assert PATH.is_file(), "finite staircase audit is not implemented"
    spec = importlib.util.spec_from_file_location("staircase_native_audit_tests", PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def execute(audit):
    with audit._local_imports(audit.RUNTIME, audit.HOME):
        apply, identity, bridge = audit._real_evaluator(audit.RUNTIME)
        assert identity["backend"] == "racket" and identity["protected"] is True
        try:
            yield audit.CachedEvaluator(apply)
        finally:
            bridge.close()


def staircase(sequence):
    return [[sequence[max(r, c)] for c in range(len(sequence))]
            for r in range(len(sequence))]


def test_first_run_and_color_role_rivals_have_distinct_literal_meanings(audit, execute):
    grid = staircase([1, 1, 2, 1, 3, 2, 2, 0])
    settings = {"output_scale": 2}
    expected = {
        "reference": [1, 1, 2, 1, 3, 2, 2],
        "first_run_per_color": [1, 1, 2, 3],
        "first_color_exempt_first_run": [1, 1, 2, 1, 3],
        "other_colors_exempt_first_run": [1, 1, 2, 3, 2, 2],
        "collapse_contiguous_runs": [1, 2, 1, 3, 2],
        "deduplicate_active": [1, 2, 3],
    }
    for name, cycle in expected.items():
        output = execute(audit.rival_program(settings, name), grid)
        assert output[0] == [cycle[i % len(cycle)] for i in range(16)], name
        assert audit.rival_reference(grid, settings, name) == output
    assert grid == staircase([1, 1, 2, 1, 3, 2, 2, 0])


def test_padding_and_geometry_mistakes_are_observable(audit, execute):
    settings = {"output_scale": 3}
    padded = staircase([4, 5, 4, 6, 0])
    unpadded = staircase([4, 5, 4, 6])
    assert execute(audit.rival_program(settings, "reference"), padded)[0][4] == 4
    assert execute(audit.rival_program(settings, "keep_terminal_zero"), padded)[0][4] == 0
    assert execute(audit.rival_program(settings, "always_drop_last"), unpadded)[0][3] == 4
    assert execute(audit.rival_program(settings, "reference"), unpadded)[0][3] == 6
    assert execute(audit.rival_program(settings, "min_axis"), unpadded)[0][1] == 4
    assert execute(audit.rival_program(settings, "reference"), unpadded)[0][1] == 5


def test_every_executable_hypothesis_matches_its_independent_mirror(audit, execute):
    assert len(audit.RIVALS) == 16
    for settings in audit.SETTINGS:
        for name in ("reference", *audit.RIVALS):
            for grid in (staircase([1, 1, 2, 1, 3, 2, 2, 0]),
                         staircase([4, 5, 4, 6, 5])):
                assert execute(audit.rival_program(settings, name), grid) == audit.rival_reference(grid, settings, name), (settings, name)


def test_fit_decisions_are_frozen_before_queries(audit):
    seen = []
    def execute(program, grid):
        seen.append(grid[0][0])
        return [[1]]
    train = [{"input": [[i]], "output": [[v]]} for i, v in ((1, 1), (2, 1), (3, 2))]
    query = [{"input": [[4]], "output": [[2]]}]
    result = audit.assess("rival", "program", train, query, execute)
    assert seen == [1, 2, 3, 4]
    assert result["survives_demonstrations"] is False
    assert result["survives_first_two"] is True
    assert result["query_disagreement_indices"] == [0]
    assert result["query_checked_for"] == ["first_two_prefix"]


def test_refuted_hypothesis_does_not_borrow_or_execute_queries(audit):
    def execute(program, grid):
        assert grid != [[3]]
        return [[1]]
    train = [{"input": [[1]], "output": [[2]]}, {"input": [[2]], "output": [[2]]}]
    result = audit.assess("rival", "program", train, [{"input": [[3]], "output": [[2]]}], execute)
    assert result["query_outputs"] is None
    assert result["query_disagreement_indices"] is None


def test_runtime_failure_cannot_be_used_as_a_refutation(audit):
    def execute(program, grid):
        raise RuntimeError("racket failure")
    with pytest.raises(RuntimeError, match="racket failure"):
        audit.assess("bad", "program", [{"input": [[1]], "output": [[2]]}], [], execute)


def test_cache_is_exact_and_cannot_be_poisoned_by_mutation(audit):
    seen = []
    def execute(program, grid):
        seen.append((program, deepcopy(grid)))
        if program == "bad":
            raise ValueError("failed execution")
        grid[0][0] = 7
        return grid
    cached = audit.CachedEvaluator(execute)
    original = [[1]]
    result = cached("first", original)
    result[0][0] = 9
    assert original == [[1]] and cached("first", original) == [[7]]
    assert cached.cache_hits == 1 and len(seen) == 1
    cached("second", original)
    for _ in range(2):
        with pytest.raises(ValueError):
            cached("bad", original)
    assert len(seen) == 4
