"""Exact pivot semantics, changed-state branching, and native episode contracts."""
import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

SOURCE = Path(__file__).parents[1] / "workspace/parametric/native_family.py"


def test_native_exists():
    assert SOURCE.is_file(), "native successive-reflection family is not implemented"


@pytest.fixture(scope="module")
def native():
    spec = importlib.util.spec_from_file_location("pivot_passes_under_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_exact_authority_and_minimum(native):
    canonical = native.program({"passes": 1})
    assert hashlib.sha256(canonical.encode()).hexdigest() == "eb5d6fb489a018776ff8676567076341973fa390ea38d12b5199abb7ab143f74"
    assert canonical == (SOURCE.parent / "canonical.rkt").read_text()
    assert native.program({"passes": 2}) != canonical
    assert len(native.generate(0, {"passes": 1})["train"]) == 4
    contract = json.loads((SOURCE.parent / "promotion.json").read_text())
    assert contract["limits"] == {"demos": [4, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 4


def test_literal_second_pass_changes_axis(native):
    g = [[0, 2, 0, 0, 0, 0, 0], [0, 0, 3, 0, 0, 0, 0],
         [0, 0, 0, 9, 0, 0, 0], [0] * 7, [0] * 7]
    one = [[0, 2, 0, 0, 0, 2, 0], [0, 0, 3, 0, 3, 0, 0],
           [0, 0, 0, 9, 0, 0, 0], [0] * 7, [0] * 7]
    two = [one[0], one[1], one[2], [0, 0, 3, 0, 3, 0, 0], [0, 2, 0, 0, 0, 2, 0]]
    before = [row[:] for row in g]
    assert native.axis(g) == "column"
    assert native.axis(native.reflect(g)) == "row"
    assert native.solve(g, 1) == one
    assert native.solve(g, 2) == two
    assert g == before


def test_total_column_clipping_does_not_force_second_axis(native):
    g = [[0] * 7, [0, 0, 4, 0, 0, 0, 0], [9, 0, 0, 0, 0, 0, 0], [0] * 7, [0] * 7]
    assert native.axis(g) == "column"
    assert native.solve(g, 1) == native.solve(g, 2) == g


def test_partial_clipping_second_pass_reads_entire_actual_state(native):
    g = [[0, 0, 0, 0, 3, 0, 0], [0, 0, 2, 0, 0, 0, 0],
         [0, 9, 0, 0, 0, 0, 0], [0] * 7, [0] * 7]
    assert native.solve(g, 2) == [[0, 0, 0, 0, 3, 0, 0], [2, 0, 2, 0, 0, 0, 0],
                                 [0, 9, 0, 0, 0, 0, 0], [2, 0, 2, 0, 0, 0, 0], [0, 0, 0, 0, 3, 0, 0]]


def test_joint_multicolor_geometry_uses_row_branch(native):
    g = [[0] * 5, [0, 2, 0, 3, 0], [0, 0, 9, 0, 0], [0] * 5, [0] * 5]
    expected = [g[0], g[1], g[2], [0, 2, 0, 3, 0], g[4]]
    assert native.axis(g) == "row"
    assert native.solve(g, 1) == native.solve(g, 2) == expected


def test_neither_side_and_empty_are_identity(native):
    g = [[2, 0, 0], [0, 9, 0], [0, 0, 3]]
    assert native.axis(g) is None
    assert native.solve(g, 1) == native.solve(g, 2) == g
    assert native.solve([[9]], 2) == [[9]]


@pytest.mark.parametrize("g,expected", [([[2, 0, 9, 0, 0]], [[2, 0, 9, 0, 2]]),
    ([[2], [0], [9], [0], [0]], [[2], [0], [9], [0], [2]]),
    ([[9, 2]], [[9, 2]]), ([[0], [9]], [[0], [9]])])
def test_thin_minimum_domain(native, g, expected):
    assert native.solve(g, 1) == native.solve(g, 2) == expected


def test_original_examples_remain_in_native_grammar(native):
    root = SOURCE.parents[4]
    rows = (json.loads(line) for line in (root / "shared/data/canonical/puzzles.jsonl").read_text().splitlines())
    task = next(row for row in rows if row["task_id"] == "abe8a3c35e86")
    tests = task["test"] if type(task["test"]) is list else [task["test"]]
    for pair in task["train"] + tests:
        assert native.solve(pair["input"], 1) == pair["output"]
        assert native.solve(pair["input"], 2)


@pytest.mark.parametrize("grid", [[], [[]], [[9], [2, 3]], [[True, 9]], [[9.0]], [[9, 10]],
    [[9, -1]], [[9] + [0] * 30], [[9]] + [[0]] * 30, ((9,),), [[9], (0,)], [[0]], [[9, 9]]])
def test_invalid_grid_rejected(native, grid):
    with pytest.raises(ValueError):
        native.solve(grid)


@pytest.mark.parametrize("settings", [None, {}, {"passes": 0}, {"passes": 3}, {"passes": True},
    {"passes": 1.0}, {"passes": "1"}, {"passes": 1, "extra": 0}])
def test_strict_settings(native, settings):
    with pytest.raises(ValueError):
        native.program(settings)


@pytest.mark.parametrize("kwargs", [{"seed": True}, {"seed": -1}, {"seed": 2**63}, {"seed": 1.0},
    {"demos": 3}, {"demos": 7}, {"demos": True}, {"queries": 0}, {"queries": 5}, {"queries": 1.0}])
def test_strict_controls(native, kwargs):
    arguments = {"seed": 0, "settings": {"passes": 1}, "demos": 4, "queries": 4}
    arguments.update(kwargs)
    with pytest.raises(ValueError):
        native.generate(**arguments)


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_matched_novel_fresh_prefix_banks(native, seed):
    one = native.generate(seed, {"passes": 1}, 6, 4)
    two = native.generate(seed, {"passes": 2}, 6, 4)
    assert [p["input"] for p in one["train"] + one["test"]] == [p["input"] for p in two["train"] + two["test"]]
    assert len({tuple(map(tuple, p["input"])) for p in one["train"] + one["test"]}) == 10
    for d, q in ((4, 1), (5, 4), (6, 2)):
        shorter = native.generate(seed, {"passes": 1}, d, q)
        assert shorter["train"] == one["train"][:d] and shorter["test"] == one["test"][:q]
    assert one["train"][0]["output"] != two["train"][0]["output"]
    before = native.generate(seed, {"passes": 1}, 4, 1)
    one["train"][0]["input"][0][0] = 8
    assert native.generate(seed, {"passes": 1}, 4, 1) == before


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_constructive_branch_core(native, seed):
    demos, _ = native.input_bank(seed)
    assert [native.axis(g) for g in demos[:4]] == ["column", "column", "row", None]
    assert native.axis(native.reflect(demos[0])) == "row"
    assert native.reflect(demos[1]) == demos[1]
    assert native.reflect(demos[2]) != demos[2]
    assert native.solve(demos[3], 2) == demos[3]


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_substantive_thirty_square_boundaries(native, seed):
    demos, queries = native.input_bank(seed)
    large = [g for g in demos + queries if len(g) == len(g[0]) == 30]
    assert len(large) == 2
    assert all(sum(v != 0 for row in g for v in row) > 300 for g in large)
    assert sum(v != 0 for row in native.solve(large[0], 1) for v in row) > 700
    assert native.solve(large[1], 2) == large[1]
    for g in large:
        assert len({v for row in g for v in row if v not in (0, 9)}) >= 3
        assert sum(v == 9 for row in g for v in row) == 1


def test_query_roles_are_seed_shuffled_before_prefix_selection(native):
    orders = {tuple((len(g), len(g[0])) for g in native.input_bank(seed)[1]) for seed in range(4)}
    assert len(orders) > 1
    assert all(set(order) == {(7, 9), (14, 19), (23, 27), (30, 30)} for order in orders)
