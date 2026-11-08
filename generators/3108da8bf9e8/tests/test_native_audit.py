"""Independent semantics and failure handling for the block-ranking audit."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest


PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/audit_native.py"


@pytest.fixture(scope="module")
def audit():
    assert PATH.is_file(), "finite block-ranking audit is not implemented"
    spec = importlib.util.spec_from_file_location("block_ranking_audit_tests", PATH)
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


def literal_grid(tile_size=3, gaps=(1, 1)):
    masks = [[], [0], [0, 4], [0, 1, 2], [0, 2, 6, 8],
             [0, 2, 4, 6, 8], list(range(6)), list(range(7)), list(range(8))]
    order = [4, 0, 8, 1, 6, 3, 7, 2, 5]
    starts = [0, tile_size + gaps[0], 2 * tile_size + sum(gaps)]
    side = 3 * tile_size + sum(gaps)
    grid = [[0] * side for _ in range(side)]
    for position, count in enumerate(order):
        row, col = starts[position // 3], starts[position % 3]
        for dr in range(tile_size):
            for dc in range(tile_size):
                grid[row + dr][col + dc] = 1 if dr < 3 and dc < 3 and dr * 3 + dc in masks[count] else 2
    return grid


def counts(audit, grid):
    return [sum(v == 1 for row in block for v in row) for block in audit.extract_blocks(grid)]


def test_literal_count_and_connectivity_order(audit, execute):
    grid = literal_grid()
    settings = {"rank_basis": "components_then_cells"}
    assert audit.component_count([[1, 2, 1], [2, 1, 2], [1, 2, 1]]) == 5
    assert audit.component_count([[1, 2, 1], [2, 1, 2], [1, 2, 1]], connectivity=8) == 1
    expected = {
        "reference": [2, 4, 5, 6, 7, 8, 0, 1, 3],
        "components8_then_cells": [7, 8, 4, 3, 5, 6, 0, 1, 2],
        "cell_count": [6, 7, 8, 3, 4, 5, 0, 1, 2],
        "components4_only": [2, 4, 5, 6, 3, 7, 0, 8, 1],
    }
    for name, ordered in expected.items():
        output = execute(audit.rival_program(settings, name), grid)
        assert counts(audit, output) == ordered, name
        assert output == audit.rival_reference(grid, settings, name)


def test_all_rivals_have_independent_racket_meaning(audit, execute):
    grid = literal_grid()
    for settings in audit.SETTINGS:
        first = {"input": grid, "output": audit.reference(grid, settings)}
        fixed_map = audit.learned_map(first)
        for name in ("reference", *audit.RIVALS):
            output = execute(audit.rival_program(settings, name, fixed_map=fixed_map), grid)
            assert output == audit.rival_reference(grid, settings, name, fixed_map=fixed_map), (settings, name)


def test_large_geometry_preserves_wide_separator(audit, execute):
    grid = literal_grid(tile_size=9, gaps=(1, 2))
    settings = {"rank_basis": "components_then_cells"}
    output = execute(audit.rival_program(settings, "reference"), grid)
    assert output == audit.reference(grid, settings)
    assert len(output) == len(output[0]) == 30
    assert sum(v != 0 for row in output for v in row) == 729
    assert all(v == 0 for r in (9, 19, 20) for v in output[r])
    assert all(output[r][c] == 0 for r in range(30) for c in (9, 19, 20))


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


def test_refuted_hypothesis_does_not_execute_queries(audit):
    def execute(program, grid):
        assert grid != [[3]]
        return [[1]]
    train = [{"input": [[1]], "output": [[2]]}, {"input": [[2]], "output": [[2]]}]
    result = audit.assess("rival", "program", train, [{"input": [[3]], "output": [[2]]}], execute)
    assert result["query_outputs"] is None
    assert result["query_disagreement_indices"] is None


def test_runtime_failure_cannot_count_as_refutation(audit):
    def execute(program, grid):
        raise RuntimeError("racket failure")
    with pytest.raises(RuntimeError, match="racket failure"):
        audit.assess("bad", "program", [{"input": [[1]], "output": [[2]]}], [], execute)


def test_cache_is_exact_and_mutation_safe(audit):
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


def test_fixed_map_is_fitted_only_to_first_demo(audit):
    grid = literal_grid()
    settings = {"rank_basis": "components_then_cells"}
    first = {"input": grid, "output": audit.reference(grid, settings)}
    fixed_map = audit.learned_map(first)
    assert audit.rival_reference(grid, settings, "fixed_map_demo1", fixed_map=fixed_map) == first["output"]
    changed = list(reversed(grid))
    assert audit.rival_reference(changed, settings, "fixed_map_demo1", fixed_map=fixed_map) != audit.reference(changed, settings)


def test_connected_prefix_before_witness_really_fits_both_settings(audit, execute):
    for grid in audit.ambiguous_demonstrations():
        cells = execute(audit.rival_program({"rank_basis": "cells"}, "reference"), grid)
        components = execute(audit.rival_program({"rank_basis": "components_then_cells"}, "reference"), grid)
        assert cells == components
        assert all(audit.component_count(block) == 1 for block in audit.extract_blocks(grid))


def test_before_witness_repair_keeps_original_query_novel(audit, execute):
    query = literal_grid()
    distinguishing = list(reversed(literal_grid()))
    class Adapter:
        @staticmethod
        def generate(seed, settings, demos, queries):
            return {"train": [{"input": query}, {"input": distinguishing}]}
    programs = {settings["rank_basis"]: audit.rival_program(settings, "reference") for settings in audit.SETTINGS}
    result = audit.before_witness(Adapter, programs, execute)
    assert result["demo_survivors"] == ["cells", "components_then_cells"]
    assert result["query_difference_cells"] > 0
    assert result["query"]["input"] == query
    repair = result["repair"]
    assert repair["replacement_demo_index"] == 1
    assert repair["pair"]["input"] == distinguishing
    assert repair["remaining_declared_survivors"] == ["components_then_cells"]
    assert len(repair["repaired_train"]) == repair["demonstration_count"] == 2
    assert all(pair["input"] != query for pair in repair["repaired_train"])
