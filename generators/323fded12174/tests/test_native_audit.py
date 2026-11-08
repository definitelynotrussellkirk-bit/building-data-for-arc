from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/audit_native.py"
_AUDIT = None


def audit():
    global _AUDIT
    assert PATH.is_file(), "Independent native audit implementation is missing"
    if _AUDIT is None:
        spec = spec_from_file_location("_323fded12174_audit_tests", PATH)
        _AUDIT = module_from_spec(spec)
        spec.loader.exec_module(_AUDIT)
    return _AUDIT


def padded(values, width):
    return values + [0] * (width-len(values))


A = [padded(row, 10) for row in ([3, 3], [2, 1, 1, 1, 4], [1, 1, 1, 1],
                                [4, 1], [1, 3, 3])]
B = [padded(row, 12) for row in ([9, 9, 9, 2, 2, 3, 3], [3, 3, 3, 3, 3, 3],
                                [9, 9, 2, 2, 2], [9, 9], [9])]
RATIO = [[5, 1, 5, 2, 5, 1, 0, 0], [5, 3, 5, 0, 0, 0, 0, 0],
         [2, 5, 2, 2, 0, 0, 0, 0]]
ANCHOR = {"rank_by": "anchor_color"}
OCCUPANCY = {"rank_by": "occupancy"}


def test_reference_selects_input_derived_color_and_stably_preserves_whole_rows():
    m = audit()
    assert m.reference(A, OCCUPANCY) == [A[i] for i in (1, 2, 4, 0, 3)]
    assert m.reference(A, ANCHOR) == [A[i] for i in (2, 1, 3, 4, 0)]


def test_fraction_orders_two_proper_fractions_without_integer_division():
    m = audit()
    assert m.reference(RATIO, ANCHOR) == RATIO
    assert m.rival_reference(RATIO, ANCHOR, "fraction") == [RATIO[i] for i in (1, 0, 2)]


def test_second_anchor_means_second_highest_occupancy_not_literal_index():
    m = audit()
    scene = [B[i] for i in (2, 0, 3, 1, 4)]
    assert m.facts(scene)["anchor_index"] == 1
    assert m.rival_reference(scene, ANCHOR, "second_occupancy_anchor") == [scene[i] for i in (3, 1, 0, 2, 4)]


def test_zero_is_excluded_from_intended_anchor_mode():
    m = audit()
    assert m.facts(A)["anchor_color"] == 1
    assert m.rival_reference(A, ANCHOR, "anchor_mode_including_zero") != m.reference(A, ANCHOR)


def test_target_count_ties_do_not_use_occupancy_or_reverse_input_order():
    m = audit()
    intended = m.reference(A, ANCHOR)
    for name in ("occupancy_tiebreak", "reverse_ties"):
        assert m.rival_reference(A, ANCHOR, name) != intended


def test_cue_rivals_are_equivalent_when_default_does_not_read_a_cue():
    m = audit()
    for name in ("first_row_anchor", "last_row_anchor", "second_occupancy_anchor",
                 "dominant_anchor", "global_color", "anchor_first_color",
                 "anchor_min_color", "anchor_max_color", "anchor_mode_including_zero",
                 "fraction", "occupancy_tiebreak"):
        assert m.rival_reference(A, OCCUPANCY, name) == m.reference(A, OCCUPANCY)


def test_output_preservation_is_distinct_from_rewriting_row_contents():
    m = audit()
    scene = [[0, value, 0, *row[1:]] for row in RATIO for value in row[:1]]
    for name in ("left_justify", "sort_cells"):
        assert m.rival_reference(scene, ANCHOR, name) != m.reference(scene, ANCHOR)


def test_settings_fail_closed():
    m = audit()
    for settings in ({}, {"rank_by": "bad"}, {"rank_by": "occupancy", "extra": 1}):
        with pytest.raises(ValueError):
            m.reference(A, settings)


def test_exact_cache_does_not_alias_results_or_conflate_programs():
    m = audit()
    calls = []
    def apply(program, grid):
        calls.append((program, grid))
        return grid
    cached = m.CachedEvaluator(apply)
    output = cached("first", [[1]])
    output[0][0] = 9
    assert cached("first", [[1]]) == [[1]]
    assert len(calls) == 1 and cached.cache_hits == 1
    assert cached("second", [[1]]) == [[1]] and len(calls) == 2


def test_candidate_execution_errors_cannot_count_as_refutations():
    m = audit()
    def fail(program, grid):
        raise RuntimeError("candidate failed")
    with pytest.raises(RuntimeError, match="candidate failed"):
        m.fit_hypothesis(fail, "bad", [{"input": [[1]], "output": [[2]]}])


@pytest.mark.parametrize("settings", [OCCUPANCY, ANCHOR])
def test_complete_racket_rivals_match_independent_python(settings):
    m = audit()
    with m._local_imports(m.RUNTIME, m.PARAMETRIC):
        apply, identity, bridge = m._real_evaluator(m.RUNTIME)
        try:
            assert identity["backend"] == "racket" and identity["protected"] is True
            for name in ("reference", *m.RIVALS):
                for grid in (A, B, RATIO):
                    actual = m._grid(apply(m.rival_program(settings, name), grid))
                    assert actual == m.rival_reference(grid, settings, name), (settings, name)
        finally:
            bridge.close()
