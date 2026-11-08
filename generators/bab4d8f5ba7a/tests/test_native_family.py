"""Focused row semantics, component ordering, grammar and episode contracts."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

SOURCE = Path(__file__).parents[1] / "workspace/parametric/native_family.py"


def test_native_exists():
    assert SOURCE.is_file(), "native row/component family is not implemented"


@pytest.fixture(scope="module")
def native():
    spec = importlib.util.spec_from_file_location("row_component_under_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_exact_default_and_counts(native):
    default = native.program({"mode": "row"})
    assert hashlib.sha256(default.encode()).hexdigest() == "071b2a298d5c565c469357c6b6662d4fe94ec5e123bbe48fa36861d8e40691df"
    assert default == (SOURCE.parent / "canonical.rkt").read_text()
    assert native.program({"mode": "largest"}) != default
    assert len(native.generate(0, {"mode": "row"})["train"]) == 3
    assert json.loads((SOURCE.parent / "promotion.json").read_text())["qualification_demos"] == 3


def test_literal_row_preservation(native):
    g = [[2, 8, 8, 0, 3], [0, 8, 0, 8, 0], [3, 8, 4, 8, 8], [8, 8, 0, 2, 0]]
    before = [row[:] for row in g]
    assert native.solve(g) == [[2, 2, 2, 0, 3], [0, 8, 0, 8, 0], [3, 3, 4, 3, 3], [8, 8, 0, 2, 0]]
    assert native.solve(g, "largest") == [[2, 2, 2]]
    assert g == before


def test_merge_changes_selected_component(native):
    g = [[2, 2, 8, 2, 0], [2, 0, 0, 0, 0], [0, 3, 3, 3, 3]]
    assert native.selected(g)["color"] == 3
    assert native.selected(native.recolor(g))["color"] == 2
    assert native.solve(g, "largest") == [[2, 2, 2, 2], [2, 0, 0, 0]]


def test_component_mask_excludes_interior_clutter(native):
    g = [[0, 2, 2, 2], [0, 2, 3, 2], [0, 2, 2, 2]]
    assert native.solve(g, "largest") == [[2, 2, 2], [2, 0, 2], [2, 2, 2]]


def test_four_connectivity_and_same_color(native):
    assert native.solve([[0, 8, 0], [0, 0, 8]], "largest") == [[8]]
    assert native.solve([[0, 2, 3, 3]], "largest") == [[3, 3]]


def test_tie_uses_first_occupied_coordinate_not_bbox_corner(native):
    g = [[0, 0, 2, 2, 2, 2, 3], [0, 0, 0, 2, 2, 2, 3],
         [0, 0, 0, 0, 2, 2, 3], [0, 3, 3, 3, 3, 3, 3]]
    assert sorted(len(c["cells"]) for c in native.components(g)) == [9, 9]
    assert native.selected(g)["cells"][0] == (0, 2)
    assert native.solve(g, "largest") == [[2, 2, 2, 2], [0, 2, 2, 2], [0, 0, 2, 2]]


@pytest.mark.parametrize("g,expected", [([[0]], [[0]]), ([[0], [0]], [[0]]), ([[8]], [[8]]), ([[8, 8]], [[8, 8]]), ([[2], [2], [3]], [[2], [2]])])
def test_empty_and_width_one_domain(native, g, expected):
    assert native.solve(g, "largest") == expected
    assert native.solve(g, "row") == g


def test_original_examples_remain_in_native_grammar(native):
    root = SOURCE.parents[4]
    rows = (json.loads(line) for line in (root / "shared/data/canonical/puzzles.jsonl").read_text().splitlines())
    row = next(row for row in rows if row["task_id"] == "bab4d8f5ba7a")
    for pair in row["train"] + row["test"]:
        assert native.solve(pair["input"], "row") == pair["output"]
        assert native.solve(pair["input"], "largest")


@pytest.mark.parametrize("grid", [[], [[]], [[0], [2, 3]], [[True]], [[2.0]], [[10]], [[-1]], [[0] * 31], [[0]] * 31, ((0,),), [[0], (0,)]])
def test_invalid_grid_rejected(native, grid):
    with pytest.raises(ValueError):
        native.solve(grid)


@pytest.mark.parametrize("settings", [None, {}, {"mode": "crop"}, {"mode": 1}, {"mode": True}, {"mode": "row", "extra": 0}])
def test_strict_settings(native, settings):
    with pytest.raises(ValueError):
        native.program(settings)


@pytest.mark.parametrize("kwargs", [{"seed": True}, {"seed": -1}, {"seed": 2**63}, {"seed": 1.0}, {"demos": 1}, {"demos": 7}, {"demos": True}, {"queries": 0}, {"queries": 5}, {"queries": 1.0}])
def test_strict_controls(native, kwargs):
    arguments = {"seed": 0, "settings": {"mode": "row"}, "demos": 3, "queries": 4}
    arguments.update(kwargs)
    with pytest.raises(ValueError):
        native.generate(**arguments)


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_matched_fresh_distinct_prefix_banks(native, seed):
    row = native.generate(seed, {"mode": "row"}, 6, 4)
    largest = native.generate(seed, {"mode": "largest"}, 6, 4)
    assert [p["input"] for p in row["train"] + row["test"]] == [p["input"] for p in largest["train"] + largest["test"]]
    assert len({tuple(map(tuple, p["input"])) for p in row["train"] + row["test"]}) == 10
    for d, q in ((2, 1), (3, 4), (6, 2)):
        short = native.generate(seed, {"mode": "row"}, d, q)
        assert short["train"] == row["train"][:d] and short["test"] == row["test"][:q]
    assert all(a["output"] != b["output"] for a, b in zip(row["train"][:2], largest["train"][:2]))
    before = native.generate(seed, {"mode": "row"}, 2, 1)
    row["train"][0]["input"][0][0] = 8
    assert native.generate(seed, {"mode": "row"}, 2, 1) == before


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_core_invariants(native, seed):
    demos, _ = native.input_bank(seed)
    before, after = native.selected(demos[0]), native.selected(native.recolor(demos[0]))
    assert before["color"] != after["color"] and len(before["cells"]) == 16 and len(after["cells"]) == 23
    counts = Counter(v for row in native.recolor(demos[0]) for v in row if v)
    assert max(counts.values()) > counts[after["color"]]
    stage = native.recolor(demos[1])
    tied = [c for c in native.components(stage) if len(c["cells"]) == 16]
    assert len(tied) == 3 and native.selected(stage)["color"] == 8
    assert min(c["color"] for c in tied) < 8 < max(c["color"] for c in tied)


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_large_content_is_distributed_and_novel(native, seed):
    demos, queries = native.input_bank(seed)
    large = [g for g in demos + queries if len(g) == len(g[0]) == 30]
    assert len(large) == 2
    counts = [sum(bool(v) for row in g for v in row) for g in large]
    assert counts == [630, 619]
    for g in large:
        assert len(native.selected(native.recolor(g))["cells"]) >= 169
        for r in (0, 15):
            for c in (0, 15):
                assert sum(bool(g[y][x]) for y in range(r, r + 15) for x in range(c, c + 15)) >= 40


def test_query_roles_are_seed_shuffled_before_prefix_selection(native):
    orders = {tuple((len(g), len(g[0])) for g in native.input_bank(seed)[1]) for seed in range(4)}
    assert len(orders) > 1
    assert all(set(order) == {(4, 7), (14, 19), (23, 27), (30, 30)} for order in orders)
