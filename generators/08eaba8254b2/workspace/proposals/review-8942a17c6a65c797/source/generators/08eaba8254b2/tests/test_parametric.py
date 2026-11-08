"""Behavioral tests for the native 08eaba8254b2 parametric family."""
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
    spec = importlib.util.spec_from_file_location("xor_pair_parametric_test", PROTOTYPE)
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


def make_grid(width: int, mask: set[tuple[int, int]]) -> list[list[int]]:
    grid = [[0] * width for _ in range(9)]
    grid[4] = [5] * width
    for r, c in mask:
        grid[r][c] = 2
    # Shared occupancy keeps both panels visible without changing the XOR mask.
    grid[3][width - 1] = 6
    grid[8][width - 1] = 7
    return grid


def test_default_program_is_exact_catalog_canonical(p):
    catalog = Catalog(HOME.parents[1])
    row = catalog.describe("08eaba8254b2")
    programs = {
        item["program_solution"]
        for item in catalog._variants()[row["rule_task_id"]]
    }
    assert programs == {p.program({"mode": "xor"})}


def test_updated_xor_state_pair_recolor_and_wrong_order_are_distinct(p, reference):
    grid = make_grid(6, {(0, 0), (0, 1), (2, 3), (2, 4), (2, 5)})
    canonical = p.transform(grid, {"mode": "xor"})
    composed = p.transform(grid, {"mode": "xor_pair_recolor"})
    assert canonical[0][0] == canonical[0][1] == 3
    assert composed[0][0] == composed[0][1] == 8
    assert composed[2][3:6] == [3, 3, 3]
    assert reference.apply(p.program({"mode": "xor"}), grid) == canonical
    assert reference.apply(p.program({"mode": "xor_pair_recolor"}), grid) == composed
    wrong = reference.apply(p.wrong_order_program(), grid)
    assert wrong == canonical
    assert wrong != composed


def test_exact_pair_logic_leaves_singletons_trimers_and_blocks_unchanged(p):
    mask = {
        (0, 0), (0, 1),                  # exact pair
        (3, 0),                           # singleton
        (1, 3), (2, 3), (3, 3),          # trimer
        (0, 6), (0, 7), (1, 6), (1, 7),  # 2x2 block
    }
    out = p.transform(make_grid(9, mask), {"mode": "xor_pair_recolor"})
    assert out[0][0:2] == [8, 8]
    assert out[3][0] == 3
    assert [out[r][3] for r in (1, 2, 3)] == [3, 3, 3]
    assert [out[r][c] for r, c in ((0, 6), (0, 7), (1, 6), (1, 7))] == [3] * 4


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
    canonical = p.generate(23, {"mode": "xor"}, 6, 4)
    composed = p.generate(23, {"mode": "xor_pair_recolor"}, 6, 4)
    short_demos = p.generate(23, {"mode": "xor"}, 2, 4)
    short_queries = p.generate(23, {"mode": "xor"}, 6, 1)
    for split in ("train", "test"):
        assert [x["input"] for x in canonical[split]] == [x["input"] for x in composed[split]]
    assert canonical["train"][:2] == short_demos["train"]
    assert canonical["test"][:1] == short_queries["test"]
    assert canonical["train"] != composed["train"]


def test_all_inputs_are_distinct_and_largest_query_is_substantive_9_by_30(p):
    episode = p.generate(5, {"mode": "xor_pair_recolor"}, 6, 4)
    inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == 10
    large_pair = episode["test"][3]
    large = large_pair["input"]
    assert len(large) == 9 and {len(row) for row in large} == {30}
    assert len(large_pair["output"]) == 4 and {len(row) for row in large_pair["output"]} == {30}
    for c0, c1 in ((0, 15), (15, 30)):
        assert sum(cell != 0 for row in large for cell in row[c0:c1]) >= 25
        assert sum(cell != 0 for row in large_pair["output"] for cell in row[c0:c1]) >= 5


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
        {"settings": {"mode": "xor", "extra": 1}},
    ],
)
def test_invalid_requests_are_rejected(p, case):
    args = {"seed": 0, "settings": {"mode": "xor"}, "demos": 3, "queries": 4}
    args.update(case)
    with pytest.raises(ValueError):
        p.generate(**args)


def _ambiguous_singleton_episode(p):
    episode = p.generate(8, {"mode": "xor_pair_recolor"}, 2, 4)
    train = []
    for width in (5, 6):
        grid = make_grid(width, {(0, 0)})
        train.append({"input": grid, "output": p.transform(grid, {"mode": "xor"})})
    episode["train"] = train
    return episode


def test_verifier_rejects_corruption_duplicates_and_underteaching(p, reference):
    episode = p.generate(8, {"mode": "xor_pair_recolor"}, 2, 4)
    variants = []
    bad = deepcopy(episode)
    bad["test"][0]["output"][0][0] = 9
    variants.append(bad)
    bad = deepcopy(episode)
    bad["test"][0] = deepcopy(bad["train"][0])
    variants.append(bad)
    bad = deepcopy(episode)
    bad["program_solution"] = p.program({"mode": "xor"})
    variants.append(bad)
    variants.append(_ambiguous_singleton_episode(p))
    for bad in variants:
        with pytest.raises(ValueError):
            p.verify_episode(bad, reference)


def test_native_adapter_is_path_isolated(p):
    adapter_path = HOME / "workspace/parametric/adapter.py"
    spec = importlib.util.spec_from_file_location("xor_pair_adapter_test", adapter_path)
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    settings = {"mode": "xor_pair_recolor"}
    assert adapter.program(settings) == p.program(settings)
    assert adapter.generate(2, settings, 2, 4) == p.generate(2, settings, 2, 4)
