"""Independent semantic and fail-closed checks for the proposed tally audit."""
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("tally_native_audit_tests", HOME / "workspace/parametric/audit_native.py")
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)


def scene(top, bottom):
    shapes = [((0, 0), (0, 1), (0, 2), (1, 1))] * top
    shapes += [((0, 1), (1, 0), (1, 1), (1, 2))] * bottom
    out = [[0] * 18 for _ in range(max(8, 3 * ((len(shapes) + 3) // 4) + 2))]
    for i, shape in enumerate(shapes):
        r, c = 1 + 3 * (i // 4), 1 + 4 * (i % 4)
        for dr, dc in shape:
            out[r + dr][c + dc] = 2
    return out


def tally(grid):
    return sum(v == 1 for row in grid for v in row), sum(v == 3 for row in grid for v in row)


@pytest.mark.parametrize("top,bottom,expected", [(8, 3, (4, 0)), (2, 5, (0, 3)), (6, 6, (0, 0)), (1, 0, (1, 0))])
def test_cancellation_happens_before_output_saturation(top, bottom, expected):
    grid = scene(top, bottom)
    assert A.facts(grid)["orientation_counts"] == [top, bottom]
    assert tally(A.reference(grid, {"count_mode": "cancel_opposites"})) == expected
    if (top, bottom) == (8, 3):
        assert tally(A.rival_reference(grid, {"count_mode": "cancel_opposites"}, "cap_before_cancel")) == (1, 0)


def test_diagonal_contact_is_two_four_components_but_one_eight_component():
    grid = [[0] * 5 for _ in range(5)]
    for r, c in ((0, 0), (0, 1), (0, 2), (1, 1), (2, 2), (2, 3), (2, 4), (3, 3)):
        grid[r][c] = 2
    assert len(A.components(grid, 4)) == 2
    assert len(A.components(grid, 8)) == 1
    assert tally(A.reference(grid, {"count_mode": "raw"})) == (2, 0)
    assert tally(A.rival_reference(grid, {"count_mode": "raw"}, "connectivity8")) == (1, 0)


def test_equal_counts_distinguish_cancellation_from_tie_preservation():
    grid = scene(3, 3)
    settings = {"count_mode": "cancel_opposites"}
    assert tally(A.reference(grid, settings)) == (0, 0)
    assert tally(A.rival_reference(grid, settings, "tie_preserve")) == (3, 3)


def test_three_roles_do_not_teach_the_opposite_color_saturation():
    settings = {"count_mode": "cancel_opposites"}
    for top, bottom in ((8, 3), (2, 5), (3, 3)):
        grid = scene(top, bottom)
        assert A.reference(grid, settings) == A.rival_reference(grid, settings, "green_cap3")
    assert tally(A.reference(scene(3, 8), settings)) == (0, 4)
    assert tally(A.rival_reference(scene(3, 8), settings, "green_cap3")) == (0, 3)


def test_four_roles_do_not_teach_subcap_counting_for_both_colors():
    settings = {"count_mode": "cancel_opposites"}
    for top, bottom in ((3, 8), (9, 4), (3, 6), (3, 3)):
        grid = scene(top, bottom)
        assert A.reference(grid, settings) == A.rival_reference(grid, settings, "blue_majority_four")
    assert tally(A.reference(scene(10, 8), settings)) == (2, 0)
    assert tally(A.rival_reference(scene(10, 8), settings, "blue_majority_four")) == (4, 0)


def test_demo_survivors_are_frozen_before_queries_and_errors_are_not_refutations():
    train = [{"input": [[1]], "output": [[2]]}, {"input": [[3]], "output": [[4]]}]
    test = [{"input": [[5]], "output": [[6]]}]
    calls = []
    def apply(program, grid):
        calls.append(grid[0][0])
        return [[grid[0][0] + 1]]
    result = A.assess("equivalent", "rule", train, test, apply)
    assert calls == [1, 3, 5]
    assert result["survives_demonstrations"] is True
    assert result["query_disagreement_indices"] == []
    def error(program, grid):
        raise RuntimeError("execution failed")
    with pytest.raises(RuntimeError, match="execution failed"):
        A.assess("broken", "rule", train, test, error)


def test_refuted_hypothesis_never_borrows_query_labels():
    calls = []
    def apply(program, grid):
        calls.append(grid)
        return [[0]]
    result = A.assess("wrong", "rule", [{"input": [[1]], "output": [[2]]}, {"input": [[3]], "output": [[4]]}],
                      [{"input": [[5]], "output": [[6]]}], apply)
    assert len(calls) == 2
    assert result["survives_demonstrations"] is False
    assert result["query_outputs"] is None


def test_short_prefix_diagnostic_does_not_become_a_supported_failure():
    train = [{"input": [[i]], "output": [[i + 1]]} for i in range(1, 6)]
    test = [{"input": [[7]], "output": [[8]]}]
    calls = []
    def apply(program, grid):
        i = grid[0][0]
        calls.append(i)
        return [[i + 1 if i < 5 else 0]]
    result = A.assess("tie_preserve", "rule", train, test, apply, prefix_count=4)
    assert calls == [1, 2, 3, 4, 5, 7]
    assert result["survives_demonstrations"] is False
    assert result["survives_short_prefix"] is True
    assert result["query_checked_for"] == ["first_4_prefix"]
    assert result["rejected_by_demo_indices"] == [4]
    assert result["query_disagreement_indices"] == [0]


def test_wrong_order_repair_preserves_five_teaching_roles_and_novel_query():
    settings = {"count_mode": "cancel_opposites"}
    class Adapter:
        def generate(self, seed, setting, demos, queries):
            assert demos == 5
            grids = [scene(8, 3), scene(3, 8), scene(3, 1), scene(1, 3), scene(2, 2)]
            return {"train": [{"input": grid, "output": A.reference(grid, setting)} for grid in grids]}
    def apply(program, grid):
        if program in ("raw", "cancel_opposites"):
            return A.reference(grid, {"count_mode": program})
        return A.rival_reference(grid, settings, "cap_before_cancel")
    result = A.before_witness(Adapter(), {"raw": "raw", "cancel_opposites": "cancel_opposites"}, A.CachedEvaluator(apply))
    assert result["demo_survivors"] == ["cancel_opposites", "cap_before_cancel"]
    assert result["query_difference_cells"] == 3
    assert result["repair"]["demonstration_count"] == 5
    assert result["repair"]["replaced_demo_index"] == 0
    assert result["repair"]["output_counts_after_repair"] == [[4, 0], [0, 4], [2, 0], [0, 2], [0, 0]]
    assert result["repair"]["remaining_hypotheses"] == ["cancel_opposites"]
    assert result["repair"]["query_remains_novel"] is True


def test_cache_uses_exact_program_and_grid_and_copies_results():
    calls = []
    def apply(program, grid):
        calls.append((program, deepcopy(grid)))
        return grid
    cache = A.CachedEvaluator(apply)
    first = cache("a", [[1]])
    first[0][0] = 9
    assert cache("a", [[1]]) == [[1]]
    assert cache("b", [[1]]) == [[1]]
    assert cache("a", [[2]]) == [[2]]
    assert (cache.requests, cache.evaluations, cache.cache_hits) == (4, 3, 1)


def test_all_racket_rival_meanings_match_independent_python():
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
    grids = [scene(8, 3), scene(2, 5), scene(3, 3)]
    with _local_imports(A.RUNTIME, A.HOME):
        apply, identity, bridge = _real_evaluator(A.RUNTIME)
        try:
            assert identity["protected"] is True
            for settings in A.SETTINGS:
                for name in ("reference", *A.RIVALS):
                    for grid in grids:
                        assert apply(A.rival_program(settings, name), grid) == A.rival_reference(grid, settings, name), name
        finally:
            bridge.close()
