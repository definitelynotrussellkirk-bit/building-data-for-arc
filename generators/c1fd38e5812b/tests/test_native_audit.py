from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import pytest


PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/audit_native.py"
SPEC = spec_from_file_location("_c1fd38e5812b_audit_tests", PATH)
audit = module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


RING = [[1, 2, 1, 2, 1], [2, 0, 0, 0, 2], [1, 0, 3, 0, 1],
        [2, 0, 0, 0, 2], [1, 2, 1, 2, 1]]


def test_compression_preserves_nonconsecutive_rows():
    grid = audit.expand(RING, [2, 3, 4, 2, 3], [3, 2, 4, 2, 3])
    assert audit.compress(grid) == RING
    assert audit.compression(grid)[1:] == ([2, 3, 4, 2, 3], [3, 2, 4, 2, 3])


def test_all_colors_zero_winner_preserves_hole():
    expected = [[0, 0, 0], [0, 3, 0], [0, 0, 0]]
    settings = {"view": "largest_component_crop"}
    assert audit.reference(RING, settings) == expected
    for name in ("ignore_zero", "solid_bbox", "isolate_component"):
        assert audit.rival_reference(RING, settings, name) != expected


def test_global_dedup_is_not_consecutive_compression():
    assert audit.rival_reference(RING, {"view": "compressed"}, "global_dedup") != RING


def test_mixed_axes_refute_both_coupled_strides():
    settings = {"view": "compressed"}
    a = audit.expand(RING, [2]*5, [2, 3, 2, 4, 2])
    b = audit.expand(RING, [2, 3, 2, 4, 2], [2]*5)
    assert audit.rival_reference(a, settings, "coupled_cols") != RING
    assert audit.rival_reference(b, settings, "coupled_rows") != RING


def test_reverse_tie_changes_equal_size_choice():
    logical = [[1, 2, 3, 4], [2, 5, 5, 1], [3, 6, 6, 2], [4, 1, 2, 3]]
    settings = {"view": "largest_component_crop"}
    assert audit.reference(logical, settings) == [[5, 5]]
    assert audit.rival_reference(logical, settings, "reverse_tie") == [[6, 6]]


def test_tie_color_rules_only_change_equal_area_order():
    settings = {"view": "largest_component_crop"}
    tied = [[1, 2, 3, 4], [2, 6, 6, 1], [3, 5, 5, 2], [4, 1, 2, 3]]
    assert audit.reference(tied, settings) == [[6, 6]]
    assert audit.rival_reference(tied, settings, "tie_min_color") == [[5, 5]]
    assert audit.rival_reference(tied, settings, "tie_max_color") == [[6, 6]]
    unique = [[1, 2, 3, 4, 1], [2, 6, 6, 6, 2], [3, 5, 5, 1, 3], [4, 1, 2, 3, 4]]
    for name in ("tie_min_color", "tie_max_color"):
        assert audit.rival_reference(unique, settings, name) == [[6, 6, 6]]


def test_first_nontrivial_ignores_singleton_filler_but_not_later_larger_object():
    settings = {"view": "largest_component_crop"}
    logical = [[1, 2, 3, 4, 1, 2], [2, 5, 5, 3, 6, 6],
               [3, 1, 2, 4, 6, 6], [4, 2, 3, 1, 2, 3]]
    assert audit.reference(logical, settings) == [[6, 6], [6, 6]]
    assert audit.rival_reference(logical, settings, "first_nontrivial") == [[5, 5]]
    assert audit.rival_reference([[5, 7], [9, 1]], settings, "first_nontrivial") == [[5]]


def test_physical_area_rival_changes_only_ranking():
    logical = [[1, 2, 3, 4, 1], [2, 5, 5, 5, 2], [3, 6, 6, 1, 3], [4, 1, 2, 3, 4]]
    grid = audit.expand(logical, [2, 2, 7, 2], [2, 2, 2, 2, 2])
    settings = {"view": "largest_component_crop"}
    assert audit.reference(grid, settings) == [[5, 5, 5]]
    assert audit.rival_reference(grid, settings, "physical_area") == [[6, 6]]


def test_bbox_area_rival_uses_area_not_size():
    logical = [[1, 2, 3, 4, 1, 2], [2, 5, 5, 1, 3, 4], [3, 5, 5, 2, 6, 6],
               [4, 1, 2, 3, 6, 4], [1, 2, 3, 4, 6, 1], [2, 3, 4, 1, 2, 3]]
    settings = {"view": "largest_component_crop"}
    # Both have four cells; bbox lex chooses the square, bbox area chooses the L.
    assert audit.reference(logical, settings) == [[5, 5], [5, 5]]
    assert audit.rival_reference(logical, settings, "bbox_area") == [[6, 6], [6, 4], [6, 1]]


def test_cache_is_exact_and_does_not_alias():
    calls = []
    def apply(program, grid):
        calls.append((program, grid))
        return grid
    cached = audit.CachedEvaluator(apply)
    first = cached("p", [[1]])
    first[0][0] = 2
    assert cached("p", [[1]]) == [[1]]
    assert len(calls) == 1 and cached.cache_hits == 1
    assert cached("q", [[1]]) == [[1]] and len(calls) == 2


def test_execution_error_never_refutes_a_hypothesis():
    def fail(program, grid):
        raise RuntimeError("broken candidate")
    with pytest.raises(RuntimeError, match="broken candidate"):
        audit.fit_hypothesis(fail, "candidate", [{"input": [[1]], "output": [[2]]}])


@pytest.mark.parametrize("settings", [{"view": "compressed"}, {"view": "largest_component_crop"}])
def test_racket_meanings_match_independent_python(settings):
    grids = [audit.expand(RING, [2]*5, [2, 3, 2, 4, 2]),
             audit.expand(RING, [2, 3, 2, 4, 2], [2]*5),
             audit.expand([[1, 2, 3, 4], [2, 5, 5, 1], [3, 6, 6, 2], [4, 1, 2, 3]],
                          [2, 2, 4, 2], [2, 3, 2, 2])]
    with audit._local_imports(audit.RUNTIME, audit.HOME):
        apply, identity, bridge = audit._real_evaluator(audit.RUNTIME)
        try:
            assert identity["backend"] == "racket" and identity["protected"] is True
            for name in ("reference", *audit.RIVALS):
                for grid in grids:
                    actual = audit._grid(apply(audit.rival_program(settings, name), grid))
                    assert actual == audit.rival_reference(grid, settings, name), (settings, name)
        finally:
            bridge.close()
