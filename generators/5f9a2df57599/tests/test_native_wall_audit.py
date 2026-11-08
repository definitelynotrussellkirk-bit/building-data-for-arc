"""Independent semantic and protected-label regressions for the finite audit."""
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest


PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/audit_native.py"
SPEC = importlib.util.spec_from_file_location("wall_audit_under_test", PATH)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def scene(cells, side=8):
    grid = [[5] * side for _ in range(side)]
    for row, col in cells:
        grid[row][col] = 0
    return grid


def pair(grid, policy="canvas_edges"):
    return {"input": grid, "output": audit.reference(grid, policy)}


def test_small_nonadjacent_side_blocker_rejects_l_but_paints_singleton():
    grid = scene([(1, 1), (1, 2), (2, 1), (3, 2)])
    before = deepcopy(grid)
    expected = deepcopy(grid)
    expected[3][2] = 4
    assert audit.reference(grid) == expected
    assert grid == before
    components = audit.facts(grid)
    assert components[0]["side_values"]["bottom"] == [5, 0]
    assert components[0]["walls"] == {"top": True, "bottom": False, "left": True, "right": True}
    assert components[0]["eligible"] is False
    assert components[1]["eligible"] is True
    for rival in ("size_le4", "ignore_walls", "enclosed_components", "skip_bottom", "eight_connected"):
        assert audit.rival_output(grid, "canvas_edges", rival) != expected


def test_full_bbox_side_quantification_in_each_direction():
    # Rotating both the L and disconnected blocker changes the unique failed side.
    grid = scene([(1, 1), (1, 2), (2, 1), (3, 2)])
    seen = set()
    for _ in range(4):
        components = audit.facts(grid)
        region = next(region for region in components if region["size"] == 3)
        failed = [side for side, valid in region["walls"].items() if not valid]
        assert len(failed) == 1
        side = failed[0]
        seen.add(side)
        intended = audit.reference(grid)
        assert audit.rival_output(grid, "canvas_edges", "skip_" + side) != intended
        for other in {"top", "bottom", "left", "right"} - {side}:
            assert audit.rival_output(grid, "canvas_edges", "skip_" + other) == intended
        grid = [list(row) for row in zip(*grid[::-1])]
    assert seen == {"top", "bottom", "left", "right"}


def test_actual_component_painting_preserves_gray_bbox_hole():
    grid = scene([(1, 1), (1, 2), (2, 1)])
    expected = deepcopy(grid)
    for cell in [(1, 1), (1, 2), (2, 1)]:
        expected[cell[0]][cell[1]] = 4
    assert audit.reference(grid) == expected
    assert expected[2][2] == 5
    assert audit.rival_output(grid, "canvas_edges", "bbox_paint")[2][2] == 4
    assert audit.rival_output(grid, "canvas_edges", "only_rectangles") == grid


def test_reject_l3_shortcut_fails_same_shape_with_intact_walls():
    positive_l = [(1, 1), (1, 2), (2, 1)]
    negative_l = [(5, 5), (5, 6), (6, 5)]
    blocker = [(7, 6)]
    four_cell_t = [(1, 6), (1, 7), (1, 8), (2, 7)]
    three_cell_rectangle = [(9, 1), (9, 2), (9, 3)]
    grid = scene(positive_l + negative_l + blocker + four_cell_t + three_cell_rectangle, side=12)
    for policy in audit.POLICIES:
        expected = audit.reference(grid, policy)
        rival = audit.rival_output(grid, policy, "reject_l3")
        assert all(expected[r][c] == 4 and rival[r][c] == 0 for r, c in positive_l)
        assert all(expected[r][c] == rival[r][c] == 0 for r, c in negative_l)
        assert all(expected[r][c] == rival[r][c] == 4
                   for r, c in blocker + four_cell_t + three_cell_rectangle)


def test_side_policy_and_column_zero_exception_are_separate():
    grid = scene([(1, 0), (2, 0), (4, 0), (4, 1), (1, 7), (2, 7)])
    canonical = audit.reference(grid, "canvas_edges")
    strict = audit.reference(grid, "gray_walls")
    assert canonical[1][0] == canonical[2][0] == 0
    assert canonical[4][0] == canonical[4][1] == 4
    assert canonical[1][7] == canonical[2][7] == 4
    assert strict == grid
    assert audit.rival_output(grid, "canvas_edges", "ignore_column0")[1][0] == 4
    assert audit.rival_output(grid, "gray_walls", "ignore_column0") == strict
    assert audit.structural_equivalence("gray_walls", "ignore_column0")["equivalent_to"] == "intended"
    assert audit.structural_equivalence("canvas_edges", "ignore_column0") is None


def test_first_and_largest_component_programs_have_distinct_meanings():
    grid = scene([(1, 1), (4, 4), (4, 5), (5, 4), (5, 5)])
    intended = audit.reference(grid)
    first = audit.rival_output(grid, "canvas_edges", "first_component")
    largest = audit.rival_output(grid, "canvas_edges", "largest_component")
    assert first[1][1] == 4 and first[4][4] == 0
    assert largest[1][1] == 0 and largest[4][4] == 4
    assert first != largest != intended


@pytest.mark.parametrize("policy", [True, 0, "unknown", {}, {"side_boundary_policy": "canvas_edges", "extra": 1}])
def test_unknown_or_extra_settings_rejected(policy):
    with pytest.raises(ValueError):
        audit.reference(scene([(1, 1)]), policy)
    with pytest.raises(ValueError):
        audit.rival_program(policy, "size_le4")


def test_query_labels_do_not_select_or_repair_the_demo_version_space():
    train = [pair(scene([(1, 1)])), pair(scene([(2, 2), (2, 3)]))]
    queries = [pair(scene([(r, c) for r in range(1, 7) for c in range(1, 7)]))]
    queries += [pair(scene([(index + 3, index + 2)])) for index in range(3)]
    intended_program = audit.canonical_program("canvas_edges")
    source_meanings = {audit.rival_program("canvas_edges", name): name for name in audit.RIVALS}
    calls = []

    class DemoBeforeQuery(dict):
        def get(self, key, default=None):
            if key == "test":
                assert len(calls) == len(train) * (len(audit.RIVALS) + 1)
                assert all(grid in [p["input"] for p in train] for grid in calls)
            return super().get(key, default)

    def execute(program, grid):
        calls.append(deepcopy(grid))
        if program == intended_program:
            return audit.reference(grid)
        return audit.rival_output(grid, "canvas_edges", source_meanings[program])

    episode = DemoBeforeQuery(train=train, test=queries, program_solution=intended_program)
    result = audit.audit_episode(episode, "canvas_edges", execute)
    assert "size_le4" in result["demo_survivors_frozen_before_queries"]
    size = next(row for row in result["rivals"] if row["name"] == "size_le4")
    assert size["status"] == "teaching_gap"
    assert size["query_mismatch_indices"] == [0]
    assert result["version_space_used_query_labels"] is False
    assert result["passed"] is False


def test_protected_programs_match_independent_rivals_and_cache_exact_inputs():
    grids = [scene([(1, 1), (1, 2), (2, 1), (3, 2)]),
             scene([(1, 0), (2, 0), (4, 0), (4, 1), (1, 7), (2, 7)]),
             scene([(1, 1), (1, 2), (2, 1), (5, 5)])]
    with audit.CachedEvaluator() as evaluator:
        assert evaluator.identity["backend"] == "racket"
        assert evaluator.identity["protected"] is True
        for policy in audit.POLICIES:
            for grid in grids:
                assert evaluator(audit.canonical_program(policy), grid) == audit.reference(grid, policy)
                for name in audit.RIVALS:
                    assert evaluator(audit.rival_program(policy, name), grid) == audit.rival_output(grid, policy, name)
        actual = evaluator.evaluations
        source = audit.canonical_program("canvas_edges")
        output = evaluator(source, grids[0])
        output[0][0] = 9
        assert evaluator(source, grids[0])[0][0] == 5
        assert evaluator.evaluations == actual
        assert evaluator.cache_hits >= 2
        # Parsing rejects a trailing second form, before sending it to Racket.
        with pytest.raises(ValueError, match="one complete"):
            evaluator(source + " (lambda (g) g)", grids[0])


def test_protected_audit_rejects_corrupted_claim_before_query_access():
    first = pair(scene([(1, 1), (1, 2), (2, 1), (3, 2)]))
    first["output"][1][1] = 4

    class HiddenQueries(dict):
        def get(self, key, default=None):
            if key == "test":
                raise AssertionError("query labels must remain untouched after a demo failure")
            return super().get(key, default)

    episode = HiddenQueries(train=[first, pair(scene([(4, 4)]))],
                            program_solution=audit.canonical_program("canvas_edges"))
    with audit.CachedEvaluator() as evaluator:
        with pytest.raises(ValueError, match="claimed demonstration label differs from protected Racket"):
            audit.audit_episode(episode, "canvas_edges", evaluator)
        assert evaluator.evaluations == 1


def test_equivalent_alias_does_not_become_a_fake_independent_rival():
    assert audit.rival_program("canvas_edges", "enclosed_components") == audit.rival_program("canvas_edges", "ignore_walls")
    assert audit.structural_equivalence("canvas_edges", "enclosed_components")["equivalent_to"] == "ignore_walls"
    assert audit.rival_program("gray_walls", "enclosed_components") != audit.rival_program("gray_walls", "ignore_walls")
