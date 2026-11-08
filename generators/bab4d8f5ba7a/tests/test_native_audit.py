"""Independent literal semantics, tie controls and demo-only audit isolation."""
import importlib.util
import io
import json
from pathlib import Path
import pytest

SOURCE = Path(__file__).parents[1] / "workspace/parametric/audit_native.py"


def test_audit_module_exists():
    assert SOURCE.is_file(), "independent row/component audit is not implemented"


@pytest.fixture(scope="module")
def audit():
    spec = importlib.util.spec_from_file_location("row_component_independent_audit", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def racket(audit):
    with audit._local_imports(audit.RUNTIME, audit.HOME):
        apply, identity, bridge = audit._real_evaluator(audit.RUNTIME)
        assert identity["protected"] is True and identity["backend"] == "racket"
        try:
            yield apply
        finally:
            bridge.close()


MERGE = [
    [2, 8, 2, 8, 5, 0, 0],
    [2, 9, 8, 2, 0, 3, 3],
    [0, 8, 0, 0, 0, 3, 3],
    [4, 8, 0, 5, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
]
ROW_MERGE = [
    [2, 2, 2, 2, 5, 0, 0],
    [2, 9, 2, 2, 0, 3, 3],
    [0, 8, 0, 0, 0, 3, 3],
    [4, 4, 0, 5, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
]
TIES = [
    [0, 8, 8, 0, 0, 0, 0],
    [0, 8, 0, 8, 0, 0, 0],
    [2, 2, 0, 0, 9, 9, 0],
    [0, 2, 0, 0, 0, 9, 0],
]
RIVALS = (
    "identity", "skip_recolor", "global_first_header", "first_marker_only", "last_marker_only",
    "zero_header_recolors", "erase_nonmarker_body", "all_nonzero_body", "drop_headers", "column_header",
    "select_before_recolor", "diagonal_components", "foreground_components", "global_color", "bbox_area",
    "smallest_component", "tie_last_anchor", "tie_low_color", "tie_high_color", "ignore_eights",
    "solid_box", "crop_box", "keep_canvas", "fixed_output2", "fixed_output8",
)


@pytest.mark.parametrize("mode,expected", [
    ("row", ROW_MERGE), ("largest", [[2, 2, 2, 2], [2, 0, 2, 2]])])
def test_literal_recolor_then_component_recomputation(audit, racket, mode, expected):
    settings = {"mode": mode}
    assert audit.reference(MERGE, settings) == expected
    assert racket(audit.rival_program(settings, "reference"), MERGE) == expected


def test_literal_ties_use_actual_minimum_occupied_anchor(audit, racket):
    expected = [[8, 8], [8, 0]]
    assert audit.reference(TIES, {"mode": "largest"}) == expected
    assert racket(audit.rival_program({"mode": "largest"}, "reference"), TIES) == expected
    # The3-shape's bbox starts at(0,1), but its first occupied cell is(0,6).
    # The2-shape's actual anchor(0,2) therefore wins the nine-cell tie.
    grid = [[0, 0, 2, 2, 2, 0, 3]] * 3 + [[0, 3, 3, 3, 3, 3, 3]]
    assert audit.reference(grid, {"mode": "largest"}) == [[2] * 3] * 3
    assert racket(audit.rival_program({"mode": "largest"}, "reference"), grid) == [[2] * 3] * 3


@pytest.mark.parametrize("mode", ["row", "largest"])
@pytest.mark.parametrize("name", RIVALS)
def test_complete_candidate_matches_independent_python(audit, racket, mode, name):
    settings = {"mode": mode}
    for grid in (MERGE, TIES):
        assert racket(audit.rival_program(settings, name), grid) == audit.rival_reference(grid, settings, name)


@pytest.mark.parametrize("mode", ["row", "largest"])
def test_candidates_total_on_zero_width1_and_cyan_header(audit, racket, mode):
    settings = {"mode": mode}
    for grid in ([[0]], [[0, 0], [0, 0]], [[2], [8], [0], [8]], [[8, 8], [0, 8]]):
        for name in ("reference", *audit.RIVALS):
            assert racket(audit.rival_program(settings, name), grid) == audit.rival_reference(grid, settings, name)


def test_component_rival_literal_meanings(audit):
    settings = {"mode": "largest"}
    assert audit.rival_reference(MERGE, settings, "skip_recolor") == [[3, 3], [3, 3]]
    assert audit.rival_reference(MERGE, settings, "solid_box") == [[2] * 4, [2] * 4]
    assert audit.rival_reference(MERGE, settings, "crop_box") == [[2, 2, 2, 2], [2, 9, 2, 2]]
    assert audit.rival_reference(TIES, settings, "tie_last_anchor") == [[9, 9], [0, 9]]
    assert audit.rival_reference(TIES, settings, "tie_low_color") == [[2, 2], [0, 2]]
    assert audit.rival_reference(TIES, settings, "tie_high_color") == [[9, 9], [0, 9]]
    assert audit.rival_reference(TIES, settings, "diagonal_components") == [[8, 8, 0], [8, 0, 8]]
    assert audit.rival_reference(TIES, settings, "global_color") == [[8, 8, 0], [8, 0, 8]]
    assert audit.rival_reference(TIES, settings, "ignore_eights") == [[2, 2], [0, 2]]


def test_fitting_reads_exactly_first_two_demos(audit):
    calls = []
    def apply(program, grid):
        calls.append(grid)
        return [[8]]
    demonstrations = [{"input": [[2]], "output": [[8]]}, {"input": [[3]], "output": [[8]]}, object()]
    assert audit.fit_hypothesis(apply, "program", demonstrations)["survives_demonstrations"]
    assert calls == [[[2]], [[3]]]


def test_candidate_failure_is_not_refutation(audit):
    def fail(program, grid):
        raise RuntimeError("literal candidate failure")
    with pytest.raises(RuntimeError, match="literal candidate failure"):
        audit.fit_hypothesis(fail, "program", [{"input": [[2]], "output": [[0]]}] * 2)


def test_cached_evaluator_preserves_values_and_request_ledger(audit):
    ledger = io.StringIO()
    count = []
    def apply(program, grid):
        count.append(1)
        return [row[:] for row in grid]
    evaluator = audit.CachedEvaluator(apply, ledger=ledger)
    result = evaluator("program", [[2]])
    result[0][0] = 9
    assert evaluator("program", [[2]]) == [[2]]
    records = [json.loads(line) for line in ledger.getvalue().splitlines()]
    assert len(count) == 1 and evaluator.requests == 2 and evaluator.cache_hits == 1
    assert [row["cache_hit"] for row in records] == [False, True]
    assert records[0]["execution_index"] == records[1]["execution_index"] == 1


def test_cached_evaluator_records_error_before_raising(audit):
    ledger = io.StringIO()
    def fail(program, grid):
        raise RuntimeError("unavailable candidate")
    evaluator = audit.CachedEvaluator(fail, ledger=ledger)
    with pytest.raises(RuntimeError, match="unavailable candidate"):
        evaluator("program", [[2]])
    record = json.loads(ledger.getvalue())
    assert record["status"] == "error" and "unavailable candidate" in record["error"]


def test_bad_controls_rejected(audit):
    with pytest.raises(ValueError):
        audit.rival_program({"mode": "other"}, "identity")
    with pytest.raises(ValueError):
        audit.rival_reference([[0]], {"mode": "row"}, "unknown")
    with pytest.raises(ValueError):
        audit.reference([[True]], {"mode": "largest"})
