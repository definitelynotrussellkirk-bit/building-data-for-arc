"""Behavioral checks for synchronous one- and two-round corner completion."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import random

import pytest


@pytest.fixture(scope="module")
def prototype():
    path = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"
    assert path.is_file(), "The synchronous completion prototype must exist"
    spec = importlib.util.spec_from_file_location("_corner_round_tests", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_second_round_uses_new_corners(prototype):
    grid = [[1, 1, 0], [0, 1, 1], [0, 0, 1]]
    first = [[1, 1, 1], [1, 1, 1], [0, 1, 1]]
    before = copy.deepcopy(grid)
    assert prototype.complete_once(grid) == first
    assert prototype.mirror(grid, {"completion_rounds": 1}) == first
    assert prototype.mirror(grid, {"completion_rounds": 2}) == [[1] * 3 for _ in range(3)]
    assert grid == before


def test_two_rounds_are_not_full_closure(prototype):
    grid = [[int(c == r or c == r + 1) for c in range(6)] for r in range(6)]
    one = prototype.mirror(grid, {"completion_rounds": 1})
    two = prototype.mirror(grid, {"completion_rounds": 2})
    assert sum(map(sum, grid)) == 11
    assert sum(map(sum, one)) == 20
    assert sum(map(sum, two)) == 35
    assert prototype.complete_once(two) == [[1] * 6 for _ in range(6)]


def test_disconnected_same_color_axes_do_not_join(prototype):
    grid = [[0] * 7 for _ in range(7)]
    for r, c in [(0, 0), (0, 2), (2, 0), (4, 4), (4, 6), (6, 4)]: grid[r][c] = 3
    result = prototype.mirror(grid, {"completion_rounds": 2})
    assert result[2][2] == result[6][6] == 3
    assert sum(v != 0 for row in result for v in row) == 8
    assert result[0][4] == result[4][0] == result[1][1] == 0


def test_complete_and_isolated_marks_are_preserved(prototype):
    grid = [[2, 0, 2], [0, 4, 0], [2, 0, 2]]
    assert prototype.mirror(grid, {"completion_rounds": 2}) == grid


def test_default_source_is_byte_exact_authority(prototype):
    from arcpuzzles import Catalog
    from reviewer_support import find_root
    sources = {v["program_solution"] for v in Catalog(find_root(__file__)).get("d89b3f447c00")["variants"]}
    assert sources == {prototype.program({"completion_rounds": 1})}
    assert prototype.program({"completion_rounds": 2}).startswith("(rule!")
    assert prototype.program({"completion_rounds": 2}) not in sources


def test_inputs_prefixes_and_freshness_are_independent_of_settings_and_counts(prototype):
    state = random.getstate()
    short = prototype.generate(17, {"completion_rounds": 1}, 2, 1)
    full = prototype.generate(17, {"completion_rounds": 1}, 6, 4)
    alternate = prototype.generate(17, {"completion_rounds": 2}, 6, 4)
    assert random.getstate() == state
    assert full["train"][:2] == short["train"]
    assert full["test"][:1] == short["test"]
    for split in ("train", "test"):
        assert [p["input"] for p in full[split]] == [p["input"] for p in alternate[split]]
    assert alternate == prototype.generate(17, {"completion_rounds": 2}, 6, 4)
    full["train"][0]["input"][0][0] = 9
    assert short == prototype.generate(17, {"completion_rounds": 1}, 2, 1)


def test_minimum_demos_need_second_round_but_do_not_teach_fixed_point(prototype):
    for seed in (0, 17, 2**63 - 1):
        pairs = prototype.generate(seed, {"completion_rounds": 2}, 2, 4)["train"]
        color_counts = {len({v for row in p["input"] for v in row if v}) for p in pairs}
        assert color_counts == {1, 4}
        for pair in pairs:
            first = prototype.complete_once(pair["input"])
            assert first != pair["output"]
            assert prototype.complete_once(pair["output"]) != pair["output"]
            assert all(v == 0 or pair["output"][r][c] == v for r, row in enumerate(pair["input"]) for c, v in enumerate(row))


def test_four_queries_are_distinct_and_order_varies(prototype):
    first_shapes = set()
    for seed in range(8):
        ep = prototype.generate(seed, {"completion_rounds": 2}, 2, 4)
        inputs = [repr(p["input"]) for p in ep["train"] + ep["test"]]
        assert len(set(inputs)) == 6
        first = ep["test"][0]["input"]
        first_shapes.add(tuple(sorted((len(first), len(first[0])))))
    assert len(first_shapes) >= 3


def test_minimum_prefix_teaches_productive_single_color_on_a_compact_canvas(prototype):
    for seed in (0, 17):
        for rounds in (1, 2):
            pairs = prototype.generate(seed, {"completion_rounds": rounds}, 2, 4)["train"]
            witnesses = [p for p in pairs if len({v for row in p["input"] for v in row if v}) == 1]
            assert witnesses, "A single-color query needs a productive single-color teaching case"
            for p in witnesses:
                assert max(len(p["input"]), len(p["input"][0])) <= 10
                assert sum(v != 0 for row in p["input"] for v in row) <= 12
                assert p["output"] != p["input"]


def test_thirty_by_thirty_has_real_boundary_content_and_many_cascades(prototype):
    ep = prototype.generate(17, {"completion_rounds": 2}, 3, 4)
    p = next(p for p in ep["test"] if len(p["input"]) == len(p["input"][0]) == 30)
    grid, output = p["input"], p["output"]
    assert sum(v != 0 for row in grid for v in row) >= 60
    assert sum(v != 0 for row in output for v in row) >= 200
    assert any(grid[0]) and any(grid[-1])
    assert any(row[0] for row in grid) and any(row[-1] for row in grid)
    first = prototype.complete_once(grid)
    assert sum(a != b for row_a, row_b in zip(first, output) for a, b in zip(row_a, row_b)) >= 80


def test_rule_commutes_with_all_eight_grid_symmetries(prototype):
    ep = prototype.generate(0, {"completion_rounds": 2}, 2, 1)
    for pair in ep["train"] + ep["test"]:
        for t in range(8):
            assert prototype.mirror(prototype.transform(pair["input"], t), {"completion_rounds": 2}) == prototype.transform(pair["output"], t)


@pytest.mark.parametrize("settings", [None, {}, {"completion_rounds": True},
    {"completion_rounds": 1.0}, {"completion_rounds": "1"}, {"completion_rounds": 0},
    {"completion_rounds": 3}, {"completion_rounds": 1, "extra": 0}])
def test_invalid_settings_are_rejected(prototype, settings):
    with pytest.raises(ValueError): prototype.program(settings)
    with pytest.raises(ValueError): prototype.generate(0, settings)


@pytest.mark.parametrize("seed", [True, -1, 1.0, "0", 2**63])
def test_seed_type_and_range(prototype, seed):
    with pytest.raises(ValueError, match="seed"): prototype.generate(seed, {"completion_rounds": 1})


@pytest.mark.parametrize("demos,queries", [(True, 4), (1, 4), (7, 4), (3.0, 4),
    (3, True), (3, 0), (3, 5), (3, 4.0)])
def test_count_type_and_range(prototype, demos, queries):
    with pytest.raises(ValueError): prototype.generate(0, {"completion_rounds": 1}, demos, queries)


@pytest.mark.parametrize("grid", [[], [[]], [[0], [0, 1]], [[True]], [[1.0]], [[-1]], [[10]], [[0] * 31]])
def test_grid_type_and_range(prototype, grid):
    with pytest.raises(ValueError): prototype.complete_once(grid)
