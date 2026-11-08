"""Behavioral checks for the opt-in closure-rounds family, not production approval."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import random

import pytest


@pytest.fixture(scope="module")
def prototype():
    path = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"
    assert path.is_file(), "The closure-rounds implementation must exist"
    spec = importlib.util.spec_from_file_location("_closure_rounds_tests", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _chain():
    g = [[0] * 9 for _ in range(10)]
    shapes = [
        {(1, 1), (1, 2), (1, 3), (2, 1), (3, 1)},
        {(3, 5), (4, 5), (5, 4), (5, 5)},
        {(6, 2), (7, 2), (7, 3)},
    ]
    for shape in shapes:
        for r, c in shape:
            g[r][c] = 2
    g[9][8] = 5
    return g


def test_second_round_uses_new_components_and_stops_after_exactly_two(prototype):
    g = _chain()
    original = copy.deepcopy(g)
    once = prototype.mirror(g, {"closure_rounds": 1})
    twice = prototype.mirror(g, {"closure_rounds": 2})
    expected_once = copy.deepcopy(g)
    for r1, c1, r2, c2 in ((1, 1, 3, 3), (3, 4, 5, 5), (6, 2, 7, 3)):
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                expected_once[r][c] = 3
    expected_twice = copy.deepcopy(expected_once)
    for r in range(1, 6):
        for c in range(1, 6):
            expected_twice[r][c] = 3
    assert once == expected_once
    assert twice == expected_twice
    assert once[4][1] == 0 and twice[4][1] == 3
    assert twice[6][1] == 0  # A third pass would fill this cell.
    assert prototype.closure(twice, color=3)[6][1] == 3
    assert twice[9][8] == 5
    assert g == original


def test_default_program_is_exact_selected_authority(prototype):
    from arcpuzzles import Catalog
    from reviewer_support import find_root
    programs = {v["program_solution"] for v in Catalog(find_root(__file__)).get(
        "699479899861")["variants"]}
    assert programs == {prototype.program({"closure_rounds": 1})}
    assert prototype.program({"closure_rounds": 2}).startswith("(rule!")
    assert prototype.program({"closure_rounds": 2}) not in programs


def test_four_connectivity_keeps_diagonal_red_components_separate(prototype):
    grid = [[2, 2, 0, 0], [0, 2, 0, 0], [0, 0, 2, 0], [0, 0, 2, 2]]
    expected = [[3, 3, 0, 0], [3, 3, 0, 0], [0, 0, 3, 3], [0, 0, 3, 3]]
    assert prototype.mirror(grid, {"closure_rounds": 1}) == expected
    assert prototype.mirror(grid, {"closure_rounds": 2}) == expected
    assert len(prototype.components(grid, 2)) == 2
    assert len(prototype.components(grid, 2, connectivity=8)) == 1


def test_counts_prefixes_matched_inputs_and_fresh_determinism(prototype):
    state = random.getstate()
    small = prototype.generate(17, {"closure_rounds": 1}, 2, 1)
    large = prototype.generate(17, {"closure_rounds": 1}, 6, 4)
    alternate = prototype.generate(17, {"closure_rounds": 2}, 6, 4)
    assert random.getstate() == state
    assert small["train"] == large["train"][:2]
    assert small["test"] == large["test"][:1]
    assert large["program_solution"] == prototype.program({"closure_rounds": 1})
    assert alternate["program_solution"] == prototype.program({"closure_rounds": 2})
    for split in ("train", "test"):
        assert [p["input"] for p in large[split]] == [p["input"] for p in alternate[split]]
    assert large == prototype.generate(17, {"closure_rounds": 1}, 6, 4)
    large["train"][0]["input"][0][0] = 9
    assert small == prototype.generate(17, {"closure_rounds": 1}, 2, 1)


def test_minimum_demos_have_real_merges_and_queries_are_distinct(prototype):
    for seed in (0, 17, 2**63 - 1):
        episode = prototype.generate(seed, {"closure_rounds": 2}, 2, 4)
        pairs = episode["train"] + episode["test"]
        assert len({json.dumps(p["input"]) for p in pairs}) == 6
        for pair in pairs:
            grid = pair["input"]
            assert 8 <= len(prototype.components(grid, 2)) <= 10
            once = prototype.mirror(grid, {"closure_rounds": 1})
            twice = pair["output"]
            assert once != twice
            assert prototype.closure(twice, color=3) != twice
            assert all(v != 3 for row in grid for v in row)


def test_exact_30_square_has_substantial_content_and_four_boundary_contacts(prototype):
    pair = prototype.generate(17, {"closure_rounds": 2}, 2, 4)["test"][2]
    grid, output = pair["input"], pair["output"]
    assert len(grid) == len(grid[0]) == 30
    assert any(v == 2 for v in grid[0]) and any(v == 2 for v in grid[-1])
    assert any(row[0] == 2 for row in grid) and any(row[-1] == 2 for row in grid)
    assert sum(v == 3 for row in output for v in row) >= 300
    for r0, r1 in ((0, 15), (15, 30)):
        for c0, c1 in ((0, 15), (15, 30)):
            assert sum(grid[r][c] == 2 for r in range(r0, r1) for c in range(c0, c1)) >= 10


@pytest.mark.parametrize("settings", [None, {}, {"closure_rounds": True},
    {"closure_rounds": 1.0}, {"closure_rounds": "1"}, {"closure_rounds": 0},
    {"closure_rounds": 3}, {"closure_rounds": 1, "extra": 0}])
def test_rejects_undeclared_or_inexact_settings(prototype, settings):
    with pytest.raises(ValueError):
        prototype.program(settings)
    with pytest.raises(ValueError):
        prototype.generate(0, settings)


@pytest.mark.parametrize("seed", [True, -1, 1.0, "0", 2**63])
def test_rejects_inexact_or_out_of_range_seed(prototype, seed):
    with pytest.raises(ValueError, match="seed"):
        prototype.generate(seed, {"closure_rounds": 1})


@pytest.mark.parametrize("demos,queries", [(True, 4), (1, 4), (7, 4), (3.0, 4),
    (3, True), (3, 0), (3, 5), (3, 4.0)])
def test_rejects_unsupported_independent_counts(prototype, demos, queries):
    with pytest.raises(ValueError):
        prototype.generate(0, {"closure_rounds": 1}, demos, queries)


@pytest.mark.parametrize("grid", [[], [[]], [[0], [0, 1]], [[True]], [[1.0]], [[-1]], [[10]], [[0] * 31]])
def test_mirror_rejects_malformed_or_inexact_grids(prototype, grid):
    with pytest.raises(ValueError):
        prototype.mirror(grid, {"closure_rounds": 1})


def test_declared_dihedral_geometry_commutes_with_rule(prototype):
    grid = prototype.generate(41, {"closure_rounds": 2}, 2, 1)["test"][0]["input"]
    for rounds in (1, 2):
        settings = {"closure_rounds": rounds}
        answer = prototype.mirror(grid, settings)
        for code in range(8):
            assert prototype.mirror(prototype.transform(grid, code), settings) == prototype.transform(answer, code)


def _live_second_pass(prototype, grid, reverse):
    output = prototype.closure(grid, 2)
    representatives = sorted((min(cells) for cells in prototype.components(output, 3)), reverse=reverse)
    for point in representatives:
        cells = next(group for group in prototype.components(output, 3) if point in group)
        for r in range(min(p[0] for p in cells), max(p[0] for p in cells) + 1):
            for c in range(min(p[1] for p in cells), max(p[1] for p in cells) + 1):
                output[r][c] = 3
    return output


@pytest.mark.parametrize("seed", [0, 17])
@pytest.mark.parametrize("reverse", [False, True])
def test_two_demos_reject_live_recomputation_in_both_scan_orders(prototype, seed, reverse):
    episode = prototype.generate(seed, {"closure_rounds": 2}, 2, 4)
    assert any(_live_second_pass(prototype, pair["input"], reverse) != pair["output"]
               for pair in episode["train"]), "A live scan must be refuted by demonstrations alone"


def test_component_count_and_topology_extend_beyond_repeated_ell_shapes(prototype):
    episode = prototype.generate(0, {"closure_rounds": 2}, 6, 4)
    groups = [prototype.components(pair["input"], 2)
              for pair in episode["train"] + episode["test"]]
    assert {len(row) for row in groups} == {8, 9, 10}
    # A plus introduces a four-way junction in the minimum teaching prefix;
    # merely changing L sizes or reflecting them cannot satisfy this check.
    assert any(sum((r + dr, c + dc) in cells for dr, dc in
                   ((1, 0), (-1, 0), (0, 1), (0, -1))) == 4
               for row in groups[:2] for cells in row for r, c in cells)
