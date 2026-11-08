"""Independent executable semantics and negative checks for the finite audit."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest


PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/audit_native.py"


@pytest.fixture(scope="module")
def audit():
    assert PATH.is_file(), "finite native audit is not implemented"
    spec = importlib.util.spec_from_file_location("bbox_native_audit_tests", PATH)
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


def corners():
    grid = [[0] * 8 for _ in range(8)]
    for r, c in ((0, 0), (1, 0), (1, 1)):
        grid[r][c] = 2
    for r, c in ((4, 4), (5, 4), (5, 5)):
        grid[r][c] = 3
    return grid


def broad_narrow_broad():
    grid = [[0] * 14 for _ in range(14)]
    for color, u, vs in ((2, 8, (0, 2, 4, 6)), (3, 12, (0, 2)), (4, 16, (0, 2, 4, 6))):
        for v in vs:
            grid[(u + v) // 2][(u - v) // 2] = color
    return grid


def partial_overlap():
    grid = [[0] * 16 for _ in range(16)]
    for color, u, vs in ((2, 8, (0, 2, 4, 6)), (3, 16, (4, 6, 8, 10))):
        for v in vs:
            grid[(u + v) // 2][(u - v) // 2] = color
    return grid


def test_literal_bridge_union_uses_original_objects_and_preserves_pixels(audit, execute):
    grid = corners()
    expected = deepcopy(grid)
    for r, c in ((0, 1), (4, 5), (2, 1), (2, 2), (3, 2), (3, 3), (4, 3)):
        expected[r][c] = 7
    settings = {"completion": "diagonal_gaps"}
    assert audit.reference(grid, settings) == expected
    assert execute(audit.rival_program(settings, "reference"), grid) == expected
    assert execute(audit.rival_program(settings, "resegment_after_bbox"), grid)[2][3] == 7
    assert expected[2][3] == 0
    assert execute(audit.rival_program(settings, "bridges_only"), grid)[0][1] == 0
    assert grid == corners()


def test_literal_pairing_and_parity_rivals_change_the_intended_cells(audit, execute):
    settings = {"completion": "diagonal_gaps"}
    wide = broad_narrow_broad()
    assert audit.reference(wide, settings)[8][4] == 7
    assert execute(audit.rival_program(settings, "nearest_pair"), wide)[8][4] == 0
    assert audit.reference(wide, settings)[8][3] == 7
    assert execute(audit.rival_program(settings, "raw_equal_v"), wide)[8][3] == 0
    partial = partial_overlap()
    assert audit.reference(partial, settings)[6][6] == 0
    assert execute(audit.rival_program(settings, "bridge_union"), partial)[6][6] == 7
    assert audit.reference(partial, settings)[8][4] == 7
    assert execute(audit.rival_program(settings, "same_color_pairs"), partial)[8][4] == 0


def test_every_executable_rival_matches_its_independent_meaning(audit, execute):
    assert len(audit.RIVALS) == 16
    for settings in audit.SETTINGS:
        for name in ("reference", *audit.RIVALS):
            for grid in (corners(), broad_narrow_broad()):
                actual = execute(audit.rival_program(settings, name), grid)
                assert actual == audit.rival_reference(grid, settings, name), (settings, name)


def test_connectivity_is_monochrome_and_four_neighbor_mistake_is_observable(audit, execute):
    grid = [[0] * 9 for _ in range(9)]
    for r, c in ((1, 4), (2, 2), (2, 3), (3, 2)):
        grid[r][c] = 4
    grid[4][2] = 6
    assert len(audit.objects(grid, 8)) == 2
    assert len(audit.objects(grid, 4)) == 3
    for settings in audit.SETTINGS:
        assert audit.reference(grid, settings)[1][2] == 7
        assert execute(audit.rival_program(settings, "bbox4"), grid)[1][2] == 0
        assert audit.reference(grid, settings)[4][3] == 0
        assert execute(audit.rival_program(settings, "color_blind_components"), grid)[4][3] == 7


def test_fit_decisions_use_demos_before_queries(audit):
    seen = []
    def execute(program, grid):
        seen.append(grid[0][0])
        return [[1]]
    train = [{"input": [[i]], "output": [[v]]} for i, v in ((1, 1), (2, 1), (3, 2))]
    test = [{"input": [[4]], "output": [[2]]}]
    result = audit.assess("rival", "program", train, test, execute)
    assert seen == [1, 2, 3, 4]
    assert result["survives_demonstrations"] is False
    assert result["survives_first_two"] is True
    assert result["query_disagreement_indices"] == [0]
    assert result["query_checked_for"] == ["first_two_prefix"]


def test_refutation_does_not_invent_unexecuted_query_outputs(audit):
    def execute(program, grid):
        assert grid != [[3]]
        return [[1]]
    train = [{"input": [[1]], "output": [[2]]}, {"input": [[2]], "output": [[2]]}]
    result = audit.assess("rival", "program", train, [{"input": [[3]], "output": [[2]]}], execute)
    assert result["query_outputs"] is None
    assert result["query_disagreement_indices"] is None


def test_execution_failure_is_not_semantic_refutation(audit):
    def fail(program, grid):
        raise RuntimeError("reference unavailable")
    with pytest.raises(RuntimeError, match="reference unavailable"):
        audit.assess("broken", "program", [{"input": [[1]], "output": [[2]]}], [], fail)


def test_exact_cache_owns_inputs_outputs_and_retries_failures(audit):
    seen = []
    def execute(program, grid):
        seen.append((program, deepcopy(grid)))
        if program == "bad":
            raise ValueError("failure")
        grid[0][0] = 7
        return grid
    cached = audit.CachedEvaluator(execute)
    grid = [[1]]
    result = cached("one", grid)
    result[0][0] = 9
    assert grid == [[1]] and cached("one", grid) == [[7]]
    assert len(seen) == 1 and cached.cache_hits == 1
    cached("two", grid)
    for _ in range(2):
        with pytest.raises(ValueError):
            cached("bad", grid)
    assert len(seen) == 4
