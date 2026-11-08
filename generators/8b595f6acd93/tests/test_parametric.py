"""Behavioral tests for the native 8b595f6acd93 parametric family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles.catalog import Catalog


HOME = Path(__file__).resolve().parents[1]
PROTOTYPE = HOME / "workspace/parametric/prototype.py"


def load_prototype():
    assert PROTOTYPE.is_file(), "parametric prototype is missing"
    spec = importlib.util.spec_from_file_location("plus_pair_parametric_test", PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def p():
    return load_prototype()


@pytest.fixture(scope="module")
def reference(p):
    with p.Reference() as runtime:
        yield runtime


def test_default_program_is_exact_catalog_canonical(p):
    catalog = Catalog(HOME.parents[1])
    row = catalog.describe("8b595f6acd93")
    programs = {
        item["program_solution"]
        for item in catalog._variants()[row["rule_task_id"]]
    }
    assert programs == {p.program({"mode": "canonical"})}


def test_updated_state_pair_recolor_and_wrong_order_are_distinct(p, reference):
    grid = [[0] * 7 for _ in range(7)]
    r = c = 3
    for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
        grid[rr][cc] = 3
    grid[r + 1][c + 1] = 4  # diagonal seed; Stage A creates an 8-connected pair

    canonical = p.transform(grid, {"mode": "canonical"})
    composed = p.transform(grid, {"mode": "pair_recolor"})
    assert canonical[r][c] == 4 and canonical[r + 1][c + 1] == 4
    assert composed[r][c] == 8 and composed[r + 1][c + 1] == 8
    assert reference.apply(p.program({"mode": "canonical"}), grid) == canonical
    assert reference.apply(p.program({"mode": "pair_recolor"}), grid) == composed
    wrong = reference.apply(p.wrong_order_program(), grid)
    assert wrong != composed
    assert wrong[r][c] == 4 and wrong[r + 1][c + 1] == 4


def test_exact_pair_logic_rejects_trimers_and_larger_components(p):
    grid = [[0] * 9 for _ in range(9)]
    # One active pair.
    for rr, cc in ((1, 2), (3, 2), (2, 1), (2, 3)):
        grid[rr][cc] = 3
    grid[3][3] = 4
    # One Stage-A trimer: center plus two diagonal seeds.
    for rr, cc in ((5, 6), (7, 6), (6, 5), (6, 7)):
        grid[rr][cc] = 3
    grid[5][5] = 4
    grid[7][7] = 4
    out = p.transform(grid, {"mode": "pair_recolor"})
    assert out[2][2] == out[3][3] == 8
    assert out[6][6] == out[5][5] == out[7][7] == 4


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_identification_and_racket_labels(p, reference, demos):
    for mode in p.MODES:
        episode = p.generate(17, {"mode": mode}, demos, 4)
        certificate = p.verify_episode(episode, reference)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        assert certificate["survivors"] == ["setting:" + mode]
        assert certificate["query_checks"] == [True, True, True, True]


def test_inputs_are_setting_independent_and_count_prefixes_are_stable(p):
    canonical = p.generate(23, {"mode": "canonical"}, 6, 4)
    composed = p.generate(23, {"mode": "pair_recolor"}, 6, 4)
    short_demos = p.generate(23, {"mode": "canonical"}, 2, 4)
    short_queries = p.generate(23, {"mode": "canonical"}, 6, 1)
    for split in ("train", "test"):
        assert [x["input"] for x in canonical[split]] == [x["input"] for x in composed[split]]
    assert canonical["train"][:2] == short_demos["train"]
    assert canonical["test"][:1] == short_queries["test"]
    assert canonical["train"] != composed["train"]


def test_all_inputs_are_distinct_and_largest_query_is_substantive_30_square(p):
    episode = p.generate(5, {"mode": "pair_recolor"}, 6, 4)
    inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == 10
    large = episode["test"][3]["input"]
    assert len(large) == 30 and {len(row) for row in large} == {30}
    for r0 in (0, 15):
        for c0 in (0, 15):
            occupied = sum(cell != 0 for row in large[r0:r0 + 15] for cell in row[c0:c0 + 15])
            assert occupied >= 12


@pytest.mark.parametrize(
    "case",
    [
        {"seed": True},
        {"seed": -1},
        {"demos": 1},
        {"demos": 7},
        {"demos": 3.0},
        {"queries": 0},
        {"queries": 5},
        {"queries": False},
        {"settings": {"mode": "wrong"}},
        {"settings": {"mode": "canonical", "extra": 1}},
    ],
)
def test_invalid_requests_are_rejected(p, case):
    args = {"seed": 0, "settings": {"mode": "canonical"}, "demos": 3, "queries": 4}
    args.update(case)
    with pytest.raises(ValueError):
        p.generate(**args)


def test_verifier_rejects_corruption_duplicates_and_underteaching(p, reference):
    episode = p.generate(8, {"mode": "pair_recolor"}, 2, 4)
    variants = []
    bad = deepcopy(episode)
    bad["test"][0]["output"][0][0] = 9
    variants.append(bad)
    bad = deepcopy(episode)
    bad["test"][0] = deepcopy(bad["train"][0])
    variants.append(bad)
    bad = deepcopy(episode)
    bad["program_solution"] = p.program({"mode": "canonical"})
    variants.append(bad)
    bad = deepcopy(episode)
    blank = [[0] * 8 for _ in range(8)]
    bad["train"] = [{"input": blank, "output": blank}, {"input": [[0] * 9 for _ in range(9)], "output": [[0] * 9 for _ in range(9)]}]
    variants.append(bad)
    for bad in variants:
        with pytest.raises(ValueError):
            p.verify_episode(bad, reference)


def test_native_adapter_is_path_isolated(p):
    adapter_path = HOME / "workspace/parametric/adapter.py"
    spec = importlib.util.spec_from_file_location("plus_pair_adapter_test", adapter_path)
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    settings = {"mode": "pair_recolor"}
    assert adapter.program(settings) == p.program(settings)
    assert adapter.generate(2, settings, 2, 4) == p.generate(2, settings, 2, 4)


def test_minimum_demos_reject_any_color_and_diagonal_only_rivals(p, reference):
    for mode in p.MODES:
        episode = p.generate(29, {"mode": mode}, 2, 4)
        certificate = p.verify_episode(episode, reference)
        assert "any_same_color_arms" in certificate["rejected_by_demo"]
        assert "any_same_color_arms_pair_recolor" in certificate["rejected_by_demo"]
        if mode == "pair_recolor":
            assert "diagonal_pair_only" in certificate["rejected_by_demo"]
